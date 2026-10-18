# rec_semantic.py —— 语义召回模块
import json
import numpy as np
from openai import OpenAI

client = OpenAI(api_key="YOUR_KEY", base_url="YOUR_BASE_URL")
EMB_PATH = "course_emb.npy"
IDS_PATH = "course_ids.json"

def build_course_text(course):
    # 用你 course 表的真实字段拼描述文本
    return (
        f"课程名称：{course['name']}。"
        f"课程类型：{course['type']}。"
        f"授课教师：{course['teacher']}。"
        f"课程简介：{course['intro'] or '暂无简介'}。"
    )

def embed_texts(texts):
    resp = client.embeddings.create(model="text-embedding-3-small", input=texts)
    vecs = np.array([d.embedding for d in resp.data], dtype=np.float32)
    return vecs / np.linalg.norm(vecs, axis=1, keepdims=True)  # 归一化,点积即余弦

def build_course_index(query_all):
    # 离线跑一次,生成课程向量库
    courses = query_all("SELECT id, name, type, teacher, intro FROM course")
    if not courses:
        return None
    texts = [build_course_text(c) for c in courses]
    mat = embed_texts(texts)
    np.save(EMB_PATH, mat)
    with open(IDS_PATH, "w") as f:
        json.dump([c["id"] for c in courses], f)
    return mat

def semantic_recall(chosen_ids, top_k=10):
    # 用户画像向量 = 已选课程向量均值
    try:
        mat = np.load(EMB_PATH)
        ids = json.load(open(IDS_PATH))
    except FileNotFoundError:
        return []                      # 索引未构建,降级
    id2idx = {cid: i for i, cid in enumerate(ids)}
    idxs = [id2idx[i] for i in chosen_ids if i in id2idx]
    if not idxs:
        return []                      # 冷启动,交给热门兜底
    user_vec = mat[idxs].mean(axis=0)
    norm = np.linalg.norm(user_vec)
    if norm == 0:
        return []
    user_vec /= norm
    scores = mat @ user_vec            # 一次矩阵乘法算全部相似度
    order = np.argsort(-scores)
    return [(ids[i], float(scores[i])) for i in order if ids[i] not in chosen_ids][:top_k]