# 基于协同过滤策略的选修课程个性化推荐系统

## Personalized Recommendation System for Elective Courses Based on Collaborative Filtering

一个面向高校选修课程场景的个性化推荐系统。

本项目针对高校选课过程中存在的：

- 课程信息过载
- 学生选课盲目
- 兴趣匹配效率低
- 热门课程资源分配不均

等问题，设计并实现了一套基于 **用户协同过滤算法（User-Based Collaborative Filtering）** 的课程推荐系统。

系统结合学生历史选课行为建立用户兴趣模型，通过分析用户之间的相似性，为学生推荐可能感兴趣且未选择过的课程。

---

# 项目介绍

## 研究方向

- 推荐系统（Recommendation System）
- 协同过滤算法（Collaborative Filtering）
- Web系统开发
- 个性化教育服务

## 项目类型

本科毕业设计项目

## 核心技术

- Python
- Flask
- MySQL
- Scikit-learn
- Pandas

---

# 系统架构

系统采用分层架构设计：

```
                用户

                 |

            Web交互层

                 |

            Flask应用层

                 |

        -----------------

        |               |

 推荐算法引擎      业务逻辑模块

        |               |

        -----------------

                 |

              MySQL数据库

```

系统主要包括：

- 表现层
- 应用层
- 推荐引擎层
- 数据存储层


---

# 核心功能

## 1. 个性化课程推荐

系统根据学生历史选课记录：

```
学生选课数据

       ↓

构建用户-课程矩阵

       ↓

计算用户相似度

       ↓

寻找兴趣相近用户

       ↓

生成课程推荐列表

```

最终向学生推荐：

- 潜在感兴趣课程
- 未选择课程


---

# 推荐算法优化

传统协同过滤算法在高校场景存在：

## 数据稀疏问题

部分学生历史选课较少，难以建立有效兴趣模型。

## 冷启动问题

新用户没有历史行为，无法直接生成推荐。

## 重复推荐问题

传统算法可能推荐学生已经选择过的课程。


针对以上问题，本项目进行了场景优化。


---

## （1）冷启动处理

对于缺少历史选课记录的新用户：

- 提供热门课程推荐
- 保证系统可用性


---

## （2）已选课程过滤

推荐生成后：

- 自动过滤学生已选择课程
- 避免重复推荐
- 提升推荐有效性


---

# 推荐算法设计

## 用户协同过滤算法

核心思想：

> 兴趣相似的用户，未来可能具有相似的课程需求。


算法流程：

```
获取学生历史选课记录

          ↓

生成用户-课程交互矩阵

          ↓

计算用户之间相似度

          ↓

寻找兴趣相近用户

          ↓

预测课程兴趣

          ↓

输出推荐结果

```


---

## 相似度计算

采用：

**余弦相似度（Cosine Similarity）**

计算用户兴趣向量之间的夹角：

```
Similarity(A,B)

=
(A · B) / (||A|| × ||B||)

```

相似度越高，表示两个用户兴趣越接近。


---

# 系统功能模块


## 学生端

主要功能：

- 用户注册登录
- 浏览课程信息
- 选择课程
- 退选课程
- 获取个性化课程推荐


---

## 教师端

主要功能：

- 课程管理
- 查看选课学生
- 修改课程信息


---

## 管理员端

主要功能：

- 用户管理
- 课程管理
- 数据维护
- 系统管理


---

# 技术栈


## Backend

```
Python

Flask

PyMySQL

```


## Recommendation Algorithm

```
Pandas

Scikit-learn

User-Based Collaborative Filtering

Cosine Similarity

```


## Database

```
MySQL

```


## Frontend

```
HTML

CSS

JavaScript

Jinja2

```


---

# 数据库设计


主要数据表：

```
student

课程信息

teacher

choose（学生选课记录）

管理员信息

```


其中：

`choose`

记录学生与课程之间的交互关系，是推荐算法的数据基础。


---

# 项目目录结构


```
course_recommend/

│
├── app.py                 # Flask主程序
│
├── db_init.py             # 数据库初始化脚本
│
├── database/              # 数据库相关文件
│
├── templates/             # HTML模板文件
│
├── static/                # 静态资源文件
│
└── README.md              # 项目说明文档

```


---

# 项目运行


## 环境要求

- Python >= 3.8
- MySQL >= 5.7


---

## 安装依赖


```bash
pip install flask pymysql pandas scikit-learn

```


---

## 初始化数据库


```bash
python db_init.py

```


---

## 启动项目


```bash
python app.py

```


访问：

```
http://127.0.0.1:5000/

```


---

# 项目成果


本项目完成：

- 推荐系统理论研究
- 协同过滤算法实现
- 推荐算法场景优化
- Web系统开发
- 数据库设计
- 系统测试


实现完整流程：

```
算法设计

↓

系统开发

↓

业务应用

↓

测试验证

```


---

# Future Improvements


## 推荐算法方向

未来进一步优化：

- 矩阵分解模型（Matrix Factorization）
- 深度学习推荐模型
- 图神经网络推荐模型（GNN）
- 知识图谱增强推荐


---

## AI增强方向


结合大语言模型（LLM）：

- 学生学习目标理解
- 智能课程规划
- 个性化学习路径生成


---

## 工程优化方向


- Docker容器化部署
- Redis缓存优化
- 推荐服务API化
- 云端部署


---

# Author


**李源**

Computer Science and Technology

China Jiliang University

2026
