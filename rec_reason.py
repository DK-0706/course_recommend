# rec_reason.py —— 用 agnes-3.0-flash大模型生成推荐理由
import os
import json
from openai import OpenAI
from pydantic import BaseModel, ValidationError

# 从环境变量读配置
client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
    base_url=os.environ.get("OPENAI_BASE_URL"),
)

MODEL = os.environ.get("OPENAI_MODEL", "agnes-3.0-flash")

class ReasonItem(BaseModel):
    course_id: int
    reason: str

class ReasonList(BaseModel):
    items: list[ReasonItem]

def generate_reasons(student_id, chosen_courses, rec_courses):
    """
    chosen_courses: [{"id":.., "name":.., "type":..}, ...]
    rec_courses:    [{"id":.., "name":.., "type":.., "teacher":..}, ...]
    返回: {course_id: reason}
    """
    chosen_text = "、".join(f"{c['name']}({c['type']})" for c in chosen_courses)
    rec_text = "\n".join(
        f"- id={c['id']} {c['name']}（{c['type']}，{c.get('teacher', '')}）"
        for c in rec_courses
    )

    prompt = f"""你是一个课程推荐助手。学生已选课程：{chosen_text}。

请为以下推荐课程各写一句个性化推荐理由（30字以内，说明为什么适合该学生）：
{rec_text}

严格按 JSON 输出，格式：
{{"items": [{{"course_id": 101, "reason": "..."}}]}}
"""

    try:
        resp = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.7,
        )
        data = json.loads(resp.choices[0].message.content)
        parsed = ReasonList(**data)
        return {item.course_id: item.reason for item in parsed.items}
    except (ValidationError, json.JSONDecodeError, Exception) as e:
        print("RAG 生成失败,降级为模板理由：", e)
        return {
            c["id"]: f"根据你的选课记录，{c['name']}与你的学习方向匹配"
            for c in rec_courses
        }