# rec_reason.py —— 大模型生成推荐理由,结构化输出
import json
from pydantic import BaseModel, ValidationError
from rec_semantic import client

class RecItem(BaseModel):
    course_id: int
    reason: str
    confidence: float

class RecResult(BaseModel):
    items: list[RecItem]

def generate_reasons(student_profile, candidates):
    prompt = f"""你是课程推荐助手。根据学生画像和候选课程,为每门课写一句推荐理由。

学生画像：{student_profile}

候选课程：
{json.dumps(candidates, ensure_ascii=False, indent=2)}

要求：
1. 只推荐候选列表中的课程,不得新增
2. 每门课理由不超过 20 字,具体、不空泛
3. confidence 表示推荐把握,0~1
4. 严格按 JSON 返回,不要任何额外文字
"""
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},   # 强制 JSON
        temperature=0.3,
    )
    raw = resp.choices[0].message.content
    try:
        return RecResult.model_validate_json(raw)   # Pydantic 二次校验
    except ValidationError as e:
        print("结构化输出校验失败,降级：", e)
        return RecResult(items=[
            RecItem(course_id=c["id"], reason="", confidence=0.0) for c in candidates
        ])