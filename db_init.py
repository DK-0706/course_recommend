import pymysql

conn = pymysql.connect(
    host="localhost",
    user="root",
    password="123456",
    charset="utf8mb4"
)

cursor = conn.cursor() #新建游标对象
cursor.execute("CREATE DATABASE IF NOT EXISTS course_rec DEFAULT CHARSET utf8mb4") #创建数据库
cursor.execute("USE course_rec")   #切换数据库

# 删除旧表
cursor.execute("DROP TABLE IF EXISTS choose")
cursor.execute("DROP TABLE IF EXISTS course")
cursor.execute("DROP TABLE IF EXISTS student")
cursor.execute("DROP TABLE IF EXISTS teacher")
cursor.execute("DROP TABLE IF EXISTS admin")

# 创建学生表
cursor.execute('''
CREATE TABLE student (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(20) NOT NULL,
    major VARCHAR(30),
    grade VARCHAR(10),
    password VARCHAR(50) NOT NULL
)''')

# 创建教师表
cursor.execute('''
CREATE TABLE teacher (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(20) NOT NULL,
    title VARCHAR(20),
    department VARCHAR(50),
    password VARCHAR(50) NOT NULL
)''')

# 创建管理员表
cursor.execute('''
CREATE TABLE admin (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(20) NOT NULL UNIQUE,
    password VARCHAR(50) NOT NULL
)''')

# 创建课程表
cursor.execute('''
CREATE TABLE course (
    id INT PRIMARY KEY,
    name VARCHAR(50),
    teacher VARCHAR(20),
    teacher_id INT,
    credit INT,
    type VARCHAR(20),
    intro TEXT,
    FOREIGN KEY (teacher_id) REFERENCES teacher(id) ON DELETE SET NULL
)''')

# 创建选课表
cursor.execute('''
CREATE TABLE choose (
    student_id INT,
    course_id INT,
    PRIMARY KEY (student_id, course_id),
    FOREIGN KEY (student_id) REFERENCES student(id) ON DELETE CASCADE,
    FOREIGN KEY (course_id) REFERENCES course(id) ON DELETE CASCADE
)''')

# 初始化教师列表
teachers = [
    (1, "张老师", "副教授", "计算机学院", "123456"),
    (2, "李老师", "讲师", "人工智能学院", "123456"),
    (3, "王老师", "教授", "数据科学学院", "123456"),
    (4, "赵老师", "讲师", "软件工程学院", "123456"),
]
#把数据插入教师表
cursor.executemany("INSERT INTO teacher (id, name, title, department, password) VALUES (%s,%s,%s,%s,%s)", teachers)

#创建课程列表
courses = [
    (101, "Python程序设计", "张老师", 1, 3, "专业课", "Python语言基础与应用开发"),
    (102, "数据结构与算法", "张老师", 1, 4, "专业核心", "数据结构、算法分析与设计"),
    (103, "操作系统", "张老师", 1, 3, "专业核心", "操作系统原理与实现"),
    (104, "计算机网络", "张老师", 1, 3, "专业核心", "TCP/IP协议、网络编程基础"),
    (105, "机器学习基础", "李老师", 2, 3, "专业核心", "监督学习、无监督学习入门"),
    (106, "深度学习", "李老师", 2, 3, "专业课", "神经网络、TensorFlow实践"),
    (107, "自然语言处理", "李老师", 2, 2, "选修课", "文本处理、情感分析基础"),
    (108, "计算机视觉", "李老师", 2, 2, "选修课", "图像分类、目标检测入门"),
    (109, "大数据技术", "王老师", 3, 3, "专业课", "Hadoop、Spark基础"),
    (110, "数据挖掘", "王老师", 3, 3, "专业课", "关联规则、聚类、分类"),
    (111, "数据库系统", "王老师", 3, 3, "专业核心", "SQL、事务管理、索引优化"),
    (112, "NoSQL数据库", "王老师", 3, 2, "选修课", "MongoDB、Redis应用"),
    (113, "软件工程", "赵老师", 4, 3, "专业核心", "软件开发流程、敏捷方法"),
    (114, "Web前端开发", "赵老师", 4, 2, "选修课", "HTML/CSS/JavaScript框架"),
    (115, "移动应用开发", "赵老师", 4, 2, "选修课", "Android/iOS基础"),
    (116, "软件测试", "赵老师", 4, 2, "选修课", "单元测试、自动化测试"),
    (117, "高等数学", "张老师", 1, 4, "公共基础", "微积分、线性代数基础"),
    (118, "概率论与数理统计", "李老师", 2, 3, "公共基础", "概率、统计推断"),
    (119, "大学英语", "王老师", 3, 2, "公共基础", "英语读写听说"),
    (120, "创新创业导论", "赵老师", 4, 1, "通识选修", "创新思维、创业案例"),
    (121, "区块链技术", "王老师", 3, 2, "选修课", "比特币、以太坊、智能合约"),
    (122, "云计算与虚拟化", "王老师", 3, 2, "选修课", "Docker、K8s基础"),
    (123, "推荐系统实战", "李老师", 2, 2, "实践课", "协同过滤、矩阵分解、项目实践"),
]

#把课程数据插入课程表
cursor.executemany("""
    INSERT INTO course (id, name, teacher, teacher_id, credit, type, intro)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
""", courses)

# 初始化学生列表
students = [
    (1, "张三", "计算机科学与技术", "2024级", "123456"),
    (2, "李四", "人工智能", "2025级", "123456"),
    (3, "王芳", "通信工程", "2024级", "123456"),
    (4, "赵磊", "土木工程", "2023级", "123456"),
    (5, "陈思", "会计学", "2022级", "123456"),
]
#把数据插入学生表
cursor.executemany("INSERT INTO student (id, name, major, grade, password) VALUES (%s,%s,%s,%s,%s)", students)

# 初始化选课数据
chooses = [
    (1, 101), (1, 102), (1, 105),
    (2, 101), (2, 104), (2, 111),
    (3, 105), (3, 106), (3, 123),
    (4, 109), (4, 110), (4, 111),
    (5, 101), (5, 102), (5, 113),
]
#把数据插入选课表
cursor.executemany("INSERT INTO choose (student_id, course_id) VALUES (%s,%s)", chooses)

# 数据库插入管理员
cursor.execute("INSERT INTO admin (username, password) VALUES (%s, %s)", ("admin", "123456"))


conn.commit() #保存数据
conn.close() #关闭连接
print("数据库初始化完成！")
