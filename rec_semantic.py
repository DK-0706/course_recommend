# rec_semantic.py —— 用 ModelScope 下载 BGE 模型 + FAISS 向量检索
import json
import os
import numpy as np
from modelscope import snapshot_download
from sentence_transformers import SentenceTransformer
import faiss

# 从魔搭下载,国内稳定
model_dir = snapshot_download("AI-ModelScope/bge-small-zh-v1.5")
model = SentenceTransformer(model_dir)

EMB_PATH = "course_emb.npy"
IDS_PATH = "course_ids.json"
INDEX_PATH = "course_faiss.index"

# 全局索引缓存（避免每次读盘）
_index = None
_ids = None

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
    """建课程向量索引（启动时调用一次）"""
    courses = query_all("SELECT id, name, type, teacher, intro FROM course")
    if not courses:
        return None

    texts = [build_course_text(c) for c in courses]
    mat = embed_texts(texts)          # (n, dim)，已归一化

    # 存原始向量（备份用）
    np.save(EMB_PATH, mat)
    ids = [c["id"] for c in courses]
    with open(IDS_PATH, "w") as f:
        json.dump(ids, f)

    # ===== 建 FAISS 索引 =====
    dim = mat.shape[1]
    # IndexFlatIP：内积索引。向量已归一化，内积 = 余弦相似度
    index = faiss.IndexFlatIP(dim)
    index.add(mat)
    faiss.write_index(index, INDEX_PATH)

    # 更新全局缓存
    global _index, _ids
    _index = index
    _ids = ids

    print(f"[FAISS] 索引已建：{len(ids)} 门课程，维度 {dim}")
    return mat

def _load_index():
    """加载 FAISS 索引（带缓存）"""
    global _index, _ids
    if _index is not None and _ids is not None:
        return _index, _ids
    try:
        _index = faiss.read_index(INDEX_PATH)
        with open(IDS_PATH) as f:
            _ids = json.load(f)
        return _index, _ids
    except FileNotFoundError:
        return None, None

def semantic_recall(chosen_ids, top_k=10):
    """语义召回：用 FAISS 检索"""
    index, ids = _load_index()
    if index is None:
        return []

    # 需要原始向量来算用户平均向量
    try:
        mat = np.load(EMB_PATH)
    except FileNotFoundError:
        return []

    id2idx = {cid: i for i, cid in enumerate(ids)}
    idxs = [id2idx[i] for i in chosen_ids if i in id2idx]
    if not idxs:
        return []

    # 用户向量 = 已选课程向量平均，再归一化
    user_vec = mat[idxs].mean(axis=0)
    norm = np.linalg.norm(user_vec)
    if norm == 0:
        return []
    user_vec = (user_vec / norm).astype(np.float32).reshape(1, -1)

    # ===== FAISS 检索 =====
    # 多取一些，因为要排除已选课程
    search_k = min(top_k + len(chosen_ids), index.ntotal)
    D, I = index.search(user_vec, search_k)

    result = []
    for score, idx in zip(D[0], I[0]):
        if idx < 0:      # FAISS 无结果时返回 -1
            continue
        cid = ids[idx]
        if cid in chosen_ids:
            continue
        result.append((cid, float(score)))
        if len(result) >= top_k:
            break
    return result