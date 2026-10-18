# rec_chat.py —— 对话式课程推荐（多轮）
import os
import json
from openai import OpenAI

client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
    base_url=os.environ.get("OPENAI_BASE_URL"),
)
MODEL = os.environ.get("OPENAI_MODEL", "agnes-3.0-flash")

MAX_COURSES_TO_LLM = 100   # 课程超过100门时先粗筛

def _get_all_courses():
    """取全部课程"""
    from app import query_all
    return query_all(
        "SELECT id, name, teacher, credit, type, intro FROM course"
    )

def _get_chosen(sid):
    """取学生已选课程"""
    from app import query_all
    return query_all(
        "SELECT c.id, c.name, c.type FROM course c "
        "JOIN choose ch ON c.id = ch.course_id WHERE ch.student_id = %s",
        (sid,)
    )

def _coarse_filter(courses, message):
    """课程太多时按关键词粗筛"""
    if len(courses) <= MAX_COURSES_TO_LLM:
        return courses
    hit = [c for c in courses if any(
        kw in ((c.get('name') or '') + (c.get('intro') or '') + (c.get('type') or ''))
        for kw in message
    )]
    return hit[:MAX_COURSES_TO_LLM] if hit else courses[:MAX_COURSES_TO_LLM]

def chat_recommend(sid, message, history=None, shown_ids=None):
    """
    多轮对话推荐
    返回: {"reply": "...", "courses": [...]}
    """
    history = history or []
    shown_ids = shown_ids or []

    all_courses = _get_all_courses()
    chosen = _get_chosen(sid)
    candidates = _coarse_filter(all_courses, message)

    # 课程清单
    course_text = "\n".join(
        f"- id={c['id']} {c['name']}（{c.get('type') or ''}，{c.get('credit') or ''}学分，"
        f"{c.get('teacher') or ''}）简介：{(c.get('intro') or '')[:40]}"
        for c in candidates
    )

    chosen_text = "、".join(f"{c['name']}({c['type']})" for c in chosen) or "暂无"

    # 多轮历史（最近6条）
    history_text = ""
    if history:
        history_text = "\n".join(
            f"{'用户' if h.get('role') == 'user' else '助手'}：{h.get('content', '')}"
            for h in history[-6:]
        )

    shown_text = ""
    if shown_ids:
        shown_text = f"\n已经推荐过这些课程（用户说'再换一批'时请避开）：{shown_ids}"

    prompt = f"""你是一个课程推荐助手，帮学生选课。

学生已选课程：{chosen_text}

对话历史：
{history_text}

用户最新说："{message}"
{shown_text}

可选课程清单：
{course_text}

请根据用户需求，从清单中挑选最合适的 4 门课程（必须用清单里的 id）。
如果用户说"再换一批"，请避开已推荐过的课程。
如果用户说"简单点的"，优先选学分低、简介简单的课。

严格输出 JSON：
{{
  "reply": "一句自然的回复，说明为什么推荐这些",
  "course_ids": [101, 102, 103, 104]
}}
只输出 JSON，不要多余文字。"""

    resp = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0.7,
    )
    data = json.loads(resp.choices[0].message.content)

    reply = data.get("reply", "为你推荐以下课程")
    ids = data.get("course_ids", [])[:4]

    id_map = {c['id']: c for c in all_courses}
    courses = []
    for cid in ids:
        c = id_map.get(cid)
        if c:
            courses.append({
                "id": c['id'],
                "name": c['name'],
                "type": c.get('type') or '',
                "credit": c.get('credit') or '',
                "teacher": c.get('teacher') or '',
                "reason": "",
            })

    return {"reply": reply, "courses": courses}