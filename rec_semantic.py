# rec_semantic.py —— 用 ModelScope 下载 BGE 模型
import json
import numpy as np
from modelscope import snapshot_download
from sentence_transformers import SentenceTransformer

# 从魔搭下载,国内稳定
model_dir = snapshot_download("AI-ModelScope/bge-small-zh-v1.5")
model = SentenceTransformer(model_dir)

EMB_PATH = "course_emb.npy"
IDS_PATH = "course_ids.json"

def build_course_text(course):
    return (
        f"课程名称：{course['name']}。"
        f"课程类型：{course['type']}。"
        f"授课教师：{course['teacher']}。"
        f"课程简介：{course['intro'] or '暂无简介'}。"
    )

def embed_texts(texts):
    vecs = model.encode(texts, normalize_embeddings=True)
    return np.array(vecs, dtype=np.float32)

def build_course_index(query_all):
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
    try:
        mat = np.load(EMB_PATH)
        ids = json.load(open(IDS_PATH))
    except FileNotFoundError:
        return []
    id2idx = {cid: i for i, cid in enumerate(ids)}
    idxs = [id2idx[i] for i in chosen_ids if i in id2idx]
    if not idxs:
        return []
    user_vec = mat[idxs].mean(axis=0)
    norm = np.linalg.norm(user_vec)
    if norm == 0:
        return []
    user_vec /= norm
    scores = mat @ user_vec
    order = np.argsort(-scores)
    return [(ids[i], float(scores[i])) for i in order if ids[i] not in chosen_ids][:top_k]