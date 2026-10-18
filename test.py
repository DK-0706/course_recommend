import random
from app import query_all, execute_sql

random.seed(42)

# ========== 1. 补学生到 50 个 ==========
majors = [
    "计算机科学与技术", "软件工程", "人工智能",
    "数据科学", "网络工程", "通信工程",
]
grades = ["2022级", "2023级", "2024级", "2025级"]

existing = query_all("SELECT id FROM student")
existing_ids = {r["id"] for r in existing}
max_id = max(existing_ids) if existing_ids else 0

added_students = 0
for i in range(max_id + 1, 51):
    if i in existing_ids:
        continue
    try:
        execute_sql(
            "INSERT INTO student (id, name, major, grade, password) VALUES (%s, %s, %s, %s, %s)",
            (i, f"学生{i}", random.choice(majors), random.choice(grades), "123456"),
        )
        added_students += 1
    except Exception as e:
        print(f"插入学生 {i} 失败：{e}")

print(f"新增学生：{added_students} 个")

# ========== 2. 取真实课程 ID ==========
course_rows = query_all("SELECT id FROM course")
course_ids = [r["id"] for r in course_rows]
print(f"课程总数：{len(course_ids)}")

if len(course_ids) < 5:
    print("课程太少,无法生成有意义的选课数据")
    exit()

# ========== 3. 按专业造选课记录 ==========
# 用真实课程 ID 的前 6 门作为"计算机类"课程池
cs_pool = course_ids[:6]

major_pools = {
    "计算机科学与技术": cs_pool,
    "软件工程":         cs_pool,
    "人工智能":         cs_pool,
    "数据科学":         cs_pool,
    "网络工程":         cs_pool,
    "通信工程":         cs_pool,
}

added_choose = 0
for sid in range(1, 51):
    srow = query_all("SELECT major FROM student WHERE id=%s", (sid,))
    if not srow:
        continue
    major = srow[0]["major"]
    pool = major_pools.get(major, course_ids)

    # 关键修复：确保 pool 至少有 4 门课
    if len(pool) < 4:
        pool = course_ids
    if len(pool) < 4:
        continue

    n = random.randint(4, min(7, len(pool)))
    chosen = random.sample(pool, n)

    others = [c for c in course_ids if c not in chosen]
    if others:
        chosen += random.sample(others, min(2, len(others)))

    for cid in chosen:
        try:
            execute_sql(
                "INSERT INTO choose (student_id, course_id) VALUES (%s, %s)",
                (sid, cid),
            )
            added_choose += 1
        except Exception:
            pass

print(f"新增选课记录：{added_choose} 条")
print("完成！")