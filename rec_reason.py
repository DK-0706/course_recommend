# rec_reason.py —— 用 agnes-3.0-flash 生成推荐理由
import os
import json
from pydantic import BaseModel, ValidationError
from openai import OpenAI

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL"),
    timeout=60.0,
)

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
        model="agnes-3.0-flash",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0.3,
    )
    raw = resp.choices[0].message.content
    try:
        return RecResult.model_validate_json(raw)
    except ValidationError as e:
        print("结构化输出校验失败,降级：", e)
        return RecResult(items=[
            RecItem(course_id=c["id"], reason="", confidence=0.0) for c in candidates
        ])