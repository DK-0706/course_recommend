from rec_semantic import semantic_recall
from rec_reason import generate_reasons
from rec_chat import chat_recommend
from flask import Flask, render_template, jsonify, request, redirect, session, abort, Response
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
import pymysql
from contextlib import contextmanager
import traceback
import csv
import io


app = Flask(__name__) #创建flask实例
app.secret_key = "course_rec_2026" #密码

#定义DB_CONFIG字典,存储连接数据库的参数
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "123456",
    "database": "course_rec",
    "charset": "utf8mb4",
    "cursorclass": pymysql.cursors.DictCursor,
}

@contextmanager#上下文管理器,配合with语句
def get_db():
    conn = pymysql.connect(**DB_CONFIG)
    try:
        yield conn #暂停,执行with里面的代码
    finally:
        conn.close()
#查询单条记录
def query_one(sql, params=None):
    with get_db() as conn:
        cursor = conn.cursor() #游标对象
        cursor.execute(sql, params or ()) #执行sql语句
        return cursor.fetchone() #返回第一行
#查询所有数据
def query_all(sql, params=None):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(sql, params or ())
        return cursor.fetchall()   #返回所有
#增删改数据
def execute_sql(sql, params=None):
    with get_db() as conn:
        cursor = conn.cursor()
        affected = cursor.execute(sql, params or ()) #发给数据库处理
        conn.commit() #保存
        return affected #返回受影响的行数

def is_ajax():   #判断http请求是否为AJAX请求
    return request.headers.get('X-Requested-With') == 'XMLHttpRequest'

# 路由
@app.route("/")
def root():
    return redirect("/login/student") #自动跳转学生登录

# ==================== 协同过滤 ====================
def get_chosen_course_ids(student_id):
    rows = query_all("SELECT course_id FROM choose WHERE student_id=%s", (student_id,))
    return [row["course_id"] for row in rows]

def cf_recall_with_score(student_id, chosen_ids, top_k=10):
    # 协同过滤召回,返回 [(course_id, score), ...]
    records = query_all("SELECT student_id, course_id FROM choose")
    if not records:
        return []
    df = pd.DataFrame(records)
    df["val"] = 1
    matrix = df.pivot_table(index="student_id", columns="course_id",
                            values="val", fill_value=0)
    if student_id not in matrix.index:
        return []
    sim = cosine_similarity(matrix)
    sim_df = pd.DataFrame(sim, index=matrix.index, columns=matrix.index)
    # 显式排除自己,不再用 [1:4] 硬编码
    sim_series = sim_df[student_id].drop(labels=[student_id], errors="ignore")
    sim_users = sim_series.sort_values(ascending=False).head(3).index

    score_map = {}
    for uid in sim_users:
        w = float(sim_series[uid])          # 用相似度当权重,而非等权
        cs = query_all("SELECT course_id FROM choose WHERE student_id=%s", (uid,))
        for c in cs:
            cid = c["course_id"]
            if cid in chosen_ids:
                continue
            score_map[cid] = score_map.get(cid, 0.0) + w   # 加权累加
    ranked = sorted(score_map.items(), key=lambda x: -x[1])
    return ranked[:top_k]

def hot_courses(chosen_ids, top_k=4):
    # 热门兜底:按选课人数排序,替代 LIMIT 4
    rows = query_all("""
        SELECT c.id, COUNT(ch.student_id) AS cnt
        FROM course c LEFT JOIN choose ch ON c.id = ch.course_id
        GROUP BY c.id ORDER BY cnt DESC
    """)
    result = [r["id"] for r in rows if r["id"] not in chosen_ids]
    return result[:top_k]

def recommend(student_id):
    try:
        chosen_ids = get_chosen_course_ids(student_id)
        if not chosen_ids:
            return fetch_courses(hot_courses(chosen_ids))   # 冷启动:热门兜底

        cf_list = cf_recall_with_score(student_id, chosen_ids, top_k=20)
        sem_list = semantic_recall(chosen_ids, top_k=20)

        if not cf_list and not sem_list:
            return fetch_courses(hot_courses(chosen_ids))

        # 两路分数 min-max 归一化后加权融合
        def norm(pairs):
            if not pairs:
                return {}
            vals = [p[1] for p in pairs]
            lo, hi = min(vals), max(vals)
            rng = (hi - lo) or 1.0
            return {i: (v - lo) / rng for i, v in pairs}

        a, b = norm(cf_list), norm(sem_list)
        alpha = 0.5
        merged = {}
        for cid in set(a) | set(b):
            merged[cid] = alpha * a.get(cid, 0.0) + (1 - alpha) * b.get(cid, 0.0)

        final_ids = [i for i, _ in sorted(merged.items(), key=lambda x: -x[1])][:4]
        if not final_ids:
            return fetch_courses(hot_courses(chosen_ids))

        # ===== 新增：RAG 生成个性化推荐理由 =====
        rec_courses = fetch_courses(final_ids)
        try:
            from rec_reason import generate_reasons
            chosen_courses = fetch_courses(chosen_ids)
            reasons = generate_reasons(student_id, chosen_courses, rec_courses)
            for c in rec_courses:
                c["reason"] = reasons.get(c["id"], "")
        except Exception as e:
            print("RAG 理由生成失败,降级：", e)
            for c in rec_courses:
                c["reason"] = f"根据你的选课记录，{c['name']}与你的学习方向匹配"

        return rec_courses
    except Exception as e:
        print("推荐报错：", e)
        return []

def fetch_courses(course_ids):
    # 按给定顺序返回课程详情,保持排序结果
    result = []
    for cid in course_ids:
        course = query_one("SELECT * FROM course WHERE id=%s", (cid,))
        if course:
            result.append(course)
    return result  #异常处理

@app.route('/api/student/chat', methods=['POST'])
def api_chat():
    data = request.get_json()
    sid = session.get('user_id')
    if not sid:
        return jsonify({"success": False, "msg": "请先登录"})

    message = (data.get('message') or '').strip()
    history = data.get('history') or []      # 多轮历史
    shown_ids = data.get('shown_ids') or []  # 已展示过的课程ID（用于"再换一批"）

    if not message:
        return jsonify({"success": False, "msg": "请输入内容"})

    try:
        result = chat_recommend(sid, message, history, shown_ids)
        return jsonify({"success": True, **result})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"success": False, "msg": f"出错了：{e}"})
# ==================== 学生端 ====================
@app.route("/login/student", methods=["GET", "POST"])
def login_student():
    if request.method == "GET":
        return render_template("login_student.html")
    name = request.form.get("name")
    password = request.form.get("password")
    user = query_one("SELECT * FROM student WHERE name=%s AND password=%s", (name, password))
    if user:
        session["role"] = "student"
        session["user_id"] = user["id"]
        session["name"] = user["name"]
        return redirect("/student")
    return render_template("login_student.html", msg="姓名或密码错误")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")
    name = request.form.get("name")
    major = request.form.get("major")
    grade = request.form.get("grade")
    password = request.form.get("password")   #post请求,获取表单数据
    if query_one("SELECT * FROM student WHERE name=%s", (name,)):
        return render_template("register.html", msg="该姓名已注册")  #防止用户名重复
    execute_sql("INSERT INTO student (name, major, grade, password) VALUES (%s,%s,%s,%s)",
                (name, major, grade, password))  #插入记录
    return redirect("/login/student")   #跳转到登录界面

@app.route("/student")  #学生主页
def student_index():
    if session.get("role") != "student":
        return redirect("/login/student")  #如果身份不是学生,返回登录界面
    courses = query_all("SELECT * FROM course")
    chooses = query_all("SELECT student_id, course_id FROM choose")
    chosen_dict = {}
    for r in chooses:
        chosen_dict.setdefault(r["student_id"], []).append(r["course_id"])
    return render_template("student_index.html", courses=courses, chosen_dict=chosen_dict)
    #展示所有课程和已选课程

@app.route("/api/student/recommend") #推荐课程的api
def api_student_rec():
    if session.get("role") != "student":
        return jsonify([])  #验证身份
    sid = session.get("user_id")
    return jsonify(recommend(sid))  #返回推荐课程

@app.route("/api/student/choose", methods=["POST"]) #学生选课退课的api
def api_student_choose():
    if session.get("role") != "student":
        return jsonify({"msg": "请先登录"})
    data = request.json
    sid = data["sid"]
    cid = data["cid"]
    typ = data["type"]
    if typ == "add":
        if query_one("SELECT * FROM choose WHERE student_id=%s AND course_id=%s", (sid, cid)):
            return jsonify({"msg": "已选过该课程"})
        execute_sql("INSERT INTO choose (student_id, course_id) VALUES (%s,%s)", (sid, cid))
    else:   #退课
        execute_sql("DELETE FROM choose WHERE student_id=%s AND course_id=%s", (sid, cid))
    return jsonify({"msg": "操作成功"})

@app.route("/logout") #退出登录
def logout():
    session.clear()
    return redirect("/login/student")

# ==================== 教师端 ====================
@app.route("/login/teacher", methods=["GET", "POST"]) #教师登录
def login_teacher():
    if request.method == "GET":
        return render_template("login_teacher.html") #渲染登录界面
    name = request.form.get("name")
    password = request.form.get("password")  #post请求,获取表单数据
    user = query_one("SELECT * FROM teacher WHERE name=%s AND password=%s", (name, password)) #查重
    if user:
        session["role"] = "teacher"
        session["user_id"] = user["id"]
        session["name"] = user["name"]
        return redirect("/teacher")  #登录成功,跳转
    return render_template("login_teacher.html", msg="姓名或密码错误") #登录失败

@app.route("/register/teacher", methods=["GET", "POST"]) #教师注册
def register_teacher():
    if request.method == "GET":
        return render_template("register_teacher.html")
    name = request.form.get("name")
    title = request.form.get("title")  #职称
    department = request.form.get("department") #院系
    password = request.form.get("password")
    if query_one("SELECT * FROM teacher WHERE name=%s", (name,)):
        return render_template("register_teacher.html", msg="该教师名已存在")
    execute_sql("INSERT INTO teacher (name, title, department, password) VALUES (%s,%s,%s,%s)",
                (name, title, department, password))
    return redirect("/login/teacher") #跳转登录

@app.route("/teacher") #教师主页
def teacher_index():
    if session.get("role") != "teacher":
        return redirect("/login/teacher") #验证身份
    teacher_id = session["user_id"]
    my_courses = query_all("SELECT * FROM course WHERE teacher_id=%s", (teacher_id,)) #查询该教师的课程
    return render_template("teacher_index.html", courses=my_courses) #显示教师的课程

@app.route("/teacher/course/edit/<int:course_id>", methods=["GET", "POST"]) #教师编辑课程信息
def teacher_edit_course(course_id):
    if session.get("role") != "teacher":
        return redirect("/login/teacher")  #验证身份
    teacher_id = session["user_id"]  #获取教师id
    course = query_one("SELECT * FROM course WHERE id=%s AND teacher_id=%s", (course_id, teacher_id))
    if not course:
        abort(404)  #如果课程不属于该教师,报错
    if request.method == "GET":
        return render_template("teacher_edit_course.html", course=course) #显示编辑课程的界面
    name = request.form.get("name")
    credit = request.form.get("credit")
    type_ = request.form.get("type")
    intro = request.form.get("intro")   #post请求,获取表单数据
    execute_sql("UPDATE course SET name=%s, credit=%s, type=%s, intro=%s WHERE id=%s",
                (name, credit, type_, intro, course_id))    #修改数据库的数据
    return redirect("/teacher")    #返回教师主页

@app.route("/teacher/course/add", methods=["GET", "POST"])   #教师添加课程
def teacher_add_course():
    if session.get("role") != "teacher":
        return redirect("/login/teacher")    #验证身份
    if request.method == "GET":
        return render_template("teacher_add_course.html")   #get请求,渲染界面
    cid = request.form.get("id")
    name = request.form.get("name")
    credit = request.form.get("credit")
    type_ = request.form.get("type")
    intro = request.form.get("intro")  #post请求,获取表单数据
    teacher_id = session["user_id"]   #从session中取出教师id
    teacher = query_one("SELECT name FROM teacher WHERE id=%s", (teacher_id,))
    teacher_name = teacher["name"] if teacher else "未知"  #查询教师id和姓名
    if query_one("SELECT * FROM course WHERE id=%s", (cid,)):
        return render_template("teacher_add_course.html", msg="课程ID已存在")
    execute_sql("INSERT INTO course (id, name, teacher, teacher_id, credit, type, intro) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                (cid, name, teacher_name, teacher_id, credit, type_, intro))  #添加课程
    return redirect("/teacher")  #返回教师主页

@app.route("/teacher/course/students/<int:course_id>")  #查看某门课程的学生名单
def teacher_course_students(course_id):
    if session.get("role") != "teacher":
        return redirect("/login/teacher")  #验证身份
    teacher_id = session["user_id"]  #获取教师id
    course = query_one("SELECT * FROM course WHERE id=%s AND teacher_id=%s", (course_id, teacher_id))
    if not course:
        abort(404)  #课程不属于该教师,报错
    students = query_all("""
        SELECT s.id, s.name, s.major, s.grade 
        FROM choose c JOIN student s ON c.student_id = s.id 
        WHERE c.course_id=%s
    """, (course_id,))  #查询选修该课程的所有学生
    return render_template("teacher_course_students.html", course=course, students=students)  #返回结果

# ==================== 管理员端 ====================
@app.route("/login/admin", methods=["GET", "POST"])  #管理员登录
def login_admin():
    if request.method == "GET":
        return render_template("login_admin.html") #渲染界面
    username = request.form.get("username")
    password = request.form.get("password")  #post请求,获取表单数据
    user = query_one("SELECT * FROM admin WHERE username=%s AND password=%s", (username, password))
    if user:
        session["role"] = "admin"
        session["user_id"] = user["id"]
        session["username"] = user["username"]
        return redirect("/admin")  #登录成功
    return render_template("login_admin.html", msg="用户名或密码错误") #登录失败

@app.route("/register/admin", methods=["GET", "POST"])  #管理员注册
def register_admin():
    if request.method == "GET":
        return render_template("register_admin.html")  #渲染界面
    username = request.form.get("username")
    password = request.form.get("password")  #post请求,获取表单数据
    if query_one("SELECT * FROM admin WHERE username=%s", (username,)):
        return render_template("register_admin.html", msg="用户名已存在") #查重
    execute_sql("INSERT INTO admin (username, password) VALUES (%s,%s)",
                (username, password)) #插入数据
    return redirect("/login/admin") #跳转登录

@app.route("/admin")  #管理员首页
def admin_index():
    if session.get("role") != "admin":
        return redirect("/login/admin")
    return render_template("admin_index.html")

@app.route("/api/admin/students")   #查询所有学生信息的api
def api_admin_students():
    if session.get("role") != "admin":
        return jsonify([])
    students = query_all("SELECT * FROM student")
    return jsonify(students)

@app.route("/api/admin/teachers")   #查询所有教师信息的api
def api_admin_teachers():
    if session.get("role") != "admin":
        return jsonify([])
    teachers = query_all("SELECT * FROM teacher")
    return jsonify(teachers)

@app.route("/api/admin/courses")   #查询所有课程信息的api
def api_admin_courses():
    if session.get("role") != "admin":
        return jsonify([])
    courses = query_all("SELECT * FROM course")
    return jsonify(courses)

@app.route("/admin/student/add", methods=["POST"])   #添加学生信息
def admin_add_student():
    if session.get("role") != "admin":
        if is_ajax():
            return jsonify({"msg": "无权限"})  #ajax请求,就显示无权限
        return redirect("/login/admin")   #普通表单提交,跳转登录界面
    name = request.form.get("name")
    major = request.form.get("major")
    grade = request.form.get("grade")
    password = request.form.get("password", "123456")  #post请求,获取表单数据
    execute_sql("INSERT INTO student (name, major, grade, password) VALUES (%s,%s,%s,%s)",
                (name, major, grade, password)) #插入数据
    if is_ajax():
        return jsonify({"success": True})  #如果是ajax请求,无刷新更新学生表格
    return redirect("/admin")  #普通表单提交,刷新界面

@app.route("/admin/student/delete/<int:sid>")  #删除学生信息
def admin_del_student(sid):
    if session.get("role") != "admin":
        if is_ajax() :
            return jsonify({"msg": "无权限"})
        return redirect("/login/admin")  #验证身份
    execute_sql("DELETE FROM student WHERE id=%s", (sid,))  #删除学生数据
    if is_ajax():
        return jsonify({"success": True, "deleted_id": sid})
    return redirect("/admin")   #更新界面

@app.route("/admin/teacher/add", methods=["POST"])   #添加教师信息
def admin_add_teacher():
    if session.get("role") != "admin":
        if is_ajax():
            return jsonify({"msg": "无权限"})
        return redirect("/login/admin")  #验证身份
    name = request.form.get("name")
    title = request.form.get("title")
    department = request.form.get("department")
    password = request.form.get("password", "123456") #post请求,获取表单数据
    execute_sql("INSERT INTO teacher (name, title, department, password) VALUES (%s,%s,%s,%s)",
                (name, title, department, password)) #插入数据
    if is_ajax():
        return jsonify({"success": True})
    return redirect("/admin")  #更新界面

@app.route("/admin/teacher/delete/<int:tid>")   #删除教师信息
def admin_del_teacher(tid):
    if session.get("role") != "admin":
        if is_ajax():
            return jsonify({"msg": "无权限"})
        return redirect("/login/admin")  #验证身份
    execute_sql("UPDATE course SET teacher_id=NULL, teacher='已删除' WHERE teacher_id=%s", (tid,)) #删除教师和课程的关联
    execute_sql("DELETE FROM teacher WHERE id=%s", (tid,)) #删除教师
    if is_ajax():
        return jsonify({"success": True, "deleted_id": tid})
    return redirect("/admin") #更新界面

@app.route("/admin/course/add", methods=["POST"])  #添加课程
def admin_add_course():
    if session.get("role") != "admin":
        if is_ajax():
            return jsonify({"msg": "无权限"})
        return redirect("/login/admin")  # 验证身份
    cid = request.form.get("id")
    name = request.form.get("name")
    teacher_id = request.form.get("teacher_id")
    credit = request.form.get("credit")
    type_ = request.form.get("type")
    intro = request.form.get("intro")  #post请求,获取表单数据
    teacher = query_one("SELECT name FROM teacher WHERE id=%s", (teacher_id,))
    teacher_name = teacher["name"] if teacher else "未知"  #获取教师姓名
    if query_one("SELECT * FROM course WHERE id=%s", (cid,)):
        if is_ajax():
            return jsonify({"success": False, "msg": "课程ID已存在"})
        return render_template("admin_index.html", msg="课程ID已存在")  #查重
    execute_sql("INSERT INTO course (id, name, teacher, teacher_id, credit, type, intro) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                (cid, name, teacher_name, teacher_id, credit, type_, intro)) #插入数据
    if is_ajax():
        return jsonify({"success": True})
    return redirect("/admin")  #更新界面

@app.route("/admin/course/delete/<int:cid>")  #删除课程
def admin_del_course(cid):
    if session.get("role") != "admin":
        if is_ajax():
            return jsonify({"msg": "无权限"})
        return redirect("/login/admin")  # 验证身份
    execute_sql("DELETE FROM course WHERE id=%s", (cid,))  #删除课程
    if is_ajax():
        return jsonify({"success": True, "deleted_id": cid})
    return redirect("/admin")  #更新界面

@app.route("/admin/reset_password", methods=["POST"])  #重置密码
def admin_reset_password():
    if session.get("role") != "admin":
        if is_ajax():
            return jsonify({"msg": "无权限"})
        return redirect("/login/admin")  # 验证身份
    user_type = request.form.get("type")
    user_id = request.form.get("id")
    new_pwd = request.form.get("new_password", "123456")  #post请求,获取表单数据
    if user_type == "student":
        execute_sql("UPDATE student SET password=%s WHERE id=%s", (new_pwd, user_id))  #修改学生密码
    elif user_type == "teacher":
        execute_sql("UPDATE teacher SET password=%s WHERE id=%s", (new_pwd, user_id))  #修改教师密码
    if is_ajax():
        return jsonify({"success": True})
    return redirect("/admin")  #刷新界面

@app.route("/admin/logs")  #显示日志
def admin_logs():
    if session.get("role") != "admin":
        return redirect("/login/admin")  #验证身份
    try:
        with open("error.log", "r", encoding="utf-8") as f:
            logs = f.readlines()[-50:]  #读取最后50行日志
    except FileNotFoundError:
        logs = ["暂无异常日志"]
    return render_template("admin_logs.html", logs=logs)  #刷新界面

# ==================== 全局异常处理 ====================
from werkzeug.exceptions import HTTPException  #导入异常类

@app.errorhandler(Exception)
def handle_exception(e):
    if isinstance(e, HTTPException):   #http异常
        return e
    with open("error.log", "a", encoding="utf-8") as f:
        f.write(f"{traceback.format_exc()}\n")  #非http异常记录到日志
    return "服务器内部错误", 500  #通用错误响应

# ==================== 启动 ====================
if __name__ == "__main__":
    app.run(debug=True)