# rec_eval.py —— deterministic leave-one-out ranking evaluation
import random
import math
from app import query_all
from rec_semantic import semantic_recall

K = 4

def get_user_history():
    """返回 {student_id: [course_id, ...]}"""
    rows = query_all("SELECT student_id, course_id FROM choose")
    hist = {}
    for r in rows:
        hist.setdefault(r["student_id"], []).append(r["course_id"])
    return hist

def make_holdout(hist, seed=42):
    """Create one repeatable train/test split per user for fair comparisons."""
    rng = random.Random(seed)
    split = {}
    for sid, courses in hist.items():
        unique_courses = list(dict.fromkeys(courses))
        if len(unique_courses) >= 2:
            test = rng.choice(unique_courses)
            split[sid] = ([cid for cid in unique_courses if cid != test], test)
    return split


def cf_from_training_data(student_id, train, hist, k):
    """User-based CF computed only from the training interactions."""
    import numpy as np

    users = list(hist)
    if student_id not in users:
        return []
    item_ids = sorted({cid for courses in hist.values() for cid in courses})
    item_index = {cid: idx for idx, cid in enumerate(item_ids)}
    matrix = np.zeros((len(users), len(item_ids)), dtype=float)
    for row, uid in enumerate(users):
        courses = train if uid == student_id else hist[uid]
        for cid in courses:
            matrix[row, item_index[cid]] = 1.0
    target = matrix[users.index(student_id)]
    target_norm = np.linalg.norm(target)
    if not target_norm:
        return []
    scores = {}
    for row, uid in enumerate(users):
        if uid == student_id:
            continue
        denom = target_norm * np.linalg.norm(matrix[row])
        similarity = float(target @ matrix[row] / denom) if denom else 0.0
        if similarity <= 0:
            continue
        for cid in hist[uid]:
            if cid not in train:
                scores[cid] = scores.get(cid, 0.0) + similarity
    return [cid for cid, _ in sorted(scores.items(), key=lambda pair: -pair[1])[:k]]

def rec_sem(sid, train, k):
    return [i for i, _ in semantic_recall(train, top_k=k)]


def rec_cf(sid, train, hist, k):
    return cf_from_training_data(sid, train, hist, k)

def rec_hybrid(sid, train, hist, k, alpha=0.5):
    cf_ids = cf_from_training_data(sid, train, hist, 20)
    sem = semantic_recall(train, top_k=20)

    def norm(pairs):
        if not pairs:
            return {}
        vals = [p[1] for p in pairs]
        lo, hi = min(vals), max(vals)
        rng = (hi - lo) or 1.0
        return {i: (v - lo) / rng for i, v in pairs}

    a = {cid: (len(cf_ids) - index) / max(len(cf_ids), 1) for index, cid in enumerate(cf_ids)}
    b = norm(sem)
    merged = {}
    for cid in set(a) | set(b):
        merged[cid] = alpha * a.get(cid, 0.0) + (1 - alpha) * b.get(cid, 0.0)
    return [i for i, _ in sorted(merged.items(), key=lambda x: -x[1])][:k]


def evaluate(rec_func, split, k=K):
    """Report HitRate, Precision, Recall, MRR, and NDCG at K."""
    if not split:
        return {name: 0.0 for name in ("HitRate", "Precision", "Recall", "MRR", "NDCG")}
    hits = precision = recall = mrr = ndcg = 0.0
    for sid, (train, target) in split.items():
        recs = rec_func(sid, train, k)
        hit = target in recs
        hits += int(hit)
        precision += int(hit) / k
        recall += int(hit)
        if hit:
            rank = recs.index(target) + 1
            mrr += 1 / rank
            ndcg += 1 / math.log2(rank + 1)
    count = len(split)
    return {
        "HitRate": hits / count,
        "Precision": precision / count,
        "Recall": recall / count,
        "MRR": mrr / count,
        "NDCG": ndcg / count,
    }

if __name__ == "__main__":
    hist = get_user_history()
    print(f"用户数：{len(hist)}")
    split = make_holdout(hist)
    print(f"留一法样本数：{len(split)}（固定 seed=42）")
    print(f"纯协同过滤 @{K}: {evaluate(lambda sid, train, k: rec_cf(sid, train, hist, k), split)}")
    print(f"纯语义 @{K}: {evaluate(lambda sid, train, k: rec_sem(sid, train, k), split)}")
    for alpha in [0.3, 0.5, 0.7]:
        metrics = evaluate(
            lambda sid, train, k: rec_hybrid(sid, train, hist, k, alpha), split
        )
        print(f"混合召回 α={alpha} @{K}: {metrics}")
