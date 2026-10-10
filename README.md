# 课程推荐系统

这是一个基于 Flask + MySQL 的简单课程推荐系统，包含学生端、教师端和管理员端。

系统会根据学生的选课记录，使用协同过滤算法推荐可能感兴趣的课程。

## 功能简介

### 学生端
- 学生注册、登录
- 查看所有课程
- 选课、退课
- 查看推荐课程
- 推荐逻辑：根据选课记录计算学生之间的相似度，推荐相似学生已选但自己未选的课程

### 教师端
- 教师注册、登录
- 添加课程
- 编辑自己的课程
- 查看选修自己课程的学生名单

### 管理员端
- 管理员注册、登录
- 查看、添加、删除学生
- 查看、添加、删除教师
- 查看、添加、删除课程
- 重置学生/教师密码
- 查看异常日志

## 技术栈

- Python 3
- Flask
- MySQL
- PyMySQL
- pandas
- scikit-learn
- Jinja2 模板
- HTML / CSS / JavaScript

## 项目目录结构

```text
course_recommend/
├── app.py                # Flask 主程序
├── db_init.py            # 数据库初始化脚本
├── error.log             # 异常日志文件，运行后自动生成
├── templates/            # HTML 模板目录
│   ├── login_student.html
│   ├── register.html
│   ├── student_index.html
│   ├── login_teacher.html
│   ├── register_teacher.html
│   ├── teacher_index.html
│   ├── teacher_edit_course.html
│   ├── teacher_add_course.html
│   ├── teacher_course_students.html
│   ├── login_admin.html
│   ├── register_admin.html
│   ├── admin_index.html
│   └── admin_logs.html
└── static/               # 静态文件目录，可选
```

> 注意：`app.py` 中使用了多个 `render_template()`，所以必须保证 `templates/` 目录下存在对应 HTML 文件，否则会报 `TemplateNotFound`。

## 环境要求

- Python 3.8 及以上
- MySQL 5.7 或 MySQL 8.0
- pip

## 安装依赖

在项目根目录执行：

```bash
pip install flask pandas scikit-learn pymysql
```

如果使用虚拟环境：

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install flask pandas scikit-learn pymysql
```

## 数据库配置

默认数据库配置在 `app.py` 和 `db_init.py` 中：

```python
host = "localhost"
user = "root"
password = "123456"
database = "course_rec"
charset = "utf8mb4"
```

如果你的 MySQL 用户名、密码不同，请修改这两个文件中的配置。

## 初始化数据库

先启动 MySQL，然后运行：

```bash
python db_init.py
```

该脚本会：

1. 创建数据库 `course_rec`
2. 删除旧表
3. 创建学生表、教师表、管理员表、课程表、选课表
4. 插入示例教师、课程、学生、选课数据
5. 创建默认管理员账号

> 警告：`db_init.py` 会删除旧表并重新创建，请不要在正式数据上直接运行。

## 启动项目

```bash
python app.py
```

启动后访问：

```text
http://127.0.0.1:5000/
```

首页会自动跳转到学生登录页。

## 推荐算法说明

推荐逻辑位于 `app.py` 的 `recommend()` 函数中。

基本流程：

1. 查询当前学生已选课程。
2. 如果当前学生没有选课，直接返回前 4 门课程，作为冷启动推荐。
3. 查询所有学生的选课记录。
4. 构造学生-课程 0/1 矩阵。
5. 使用余弦相似度计算学生之间的相似度。
6. 找到与当前学生最相似的 3 个学生。
7. 收集这些相似学生已选、但当前学生未选的课程。
8. 去重后最多推荐 4 门课程。

## 常见问题

### 1. 报错 TemplateNotFound

例如：

```text
jinja2.exceptions.TemplateNotFound: login_student.html
```

原因：缺少 HTML 模板文件。

解决：检查 `templates/` 目录，确保以下文件存在：

```text
login_student.html
register.html
student_index.html
login_teacher.html
register_teacher.html
teacher_index.html
teacher_edit_course.html
teacher_add_course.html
teacher_course_students.html
login_admin.html
register_admin.html
admin_index.html
admin_logs.html
```

### 2. 数据库连接失败

请检查：

- MySQL 是否启动
- 用户名、密码是否正确
- 数据库 `course_rec` 是否已创建
- 是否先运行了 `python db_init.py`

### 3. 推荐课程为空

可能原因：

- 当前学生没有选课
- 选课数据太少
- 数据库中没有其他学生选课记录

可以先使用默认学生账号登录，并进行选课后再查看推荐。

### 4. 端口 5000 被占用

可以修改 `app.py` 最后一行：

```python
app.run(debug=True, port=5001)
```

然后访问：

```text
http://127.0.0.1:5001/
```

## 注意事项

- 本项目适合作为课程设计、学习 Demo 使用。
- 当前密码是明文存储，正式项目应使用密码哈希。
- `app.run(debug=True)` 仅用于开发环境，不要直接用于生产环境。
- 删除教师时，相关课程的 `teacher_id` 会被置空。
- 删除学生、课程时，相关选课记录会通过外键级联删除。

## 快速启动命令

```bash
pip install flask pandas scikit-learn pymysql
python db_init.py
python app.py
```

然后浏览器打开：

```text
http://127.0.0.1:5000/
```
