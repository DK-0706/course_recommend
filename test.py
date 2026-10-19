from rec_reason import generate_reasons

chosen = [
    {"id": 1, "name": "Python程序设计", "type": "必修"},
    {"id": 2, "name": "数据结构", "type": "必修"},
]
rec = [
    {"id": 12, "name": "机器学习", "type": "选修"},
    {"id": 15, "name": "深度学习", "type": "选修"},
]

reasons = generate_reasons(7, chosen, rec)
print("reasons:", reasons)