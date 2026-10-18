# rec_eval.py —— 留一法评测 HitRate@K 测评脚本
import random
from app import query_all,  cf_recall_with_score
from rec_semantic import semantic_recall

K = 4

def get_user_history():
    """返回 {student_id: [course_id, ...]}"""
    rows = query_all("SELECT student_id, course_id FROM choose")
    hist = {}
    for r in rows:
        hist.setdefault(r["student_id"], []).append(r["course_id"])
    return hist

def hit_rate_at_k(rec_func, hist, k=K):
    """留一法：每次留出一门课做测试,看推荐里有没有"""
    hits, total = 0, 0
    for sid, courses in hist.items():
        if len(courses) < 2:
            continue
        test = random.choice(courses)
        train = [c for c in courses if c != test]
        recs = rec_func(sid, train, k)
        total += 1
        if test in recs:
            hits += 1
    return hits / total if total else 0.0

def mrr_at_k(rec_func, hist, k=K):
    """MRR：命中课程的排名倒数均值(排第1得1分,第2得0.5分,第4得0.25分)"""
    total_rr, total = 0.0, 0
    for sid, courses in hist.items():
        if len(courses) < 2:
            continue
        test = random.choice(courses)
        train = [c for c in courses if c != test]
        recs = rec_func(sid, train, k)
        total += 1
        if test in recs:
            rank = recs.index(test) + 1   # 第几位(从1开始)
            total_rr += 1.0 / rank
    return total_rr / total if total else 0.0

def rec_cf(sid, train, k):
    return [i for i, _ in cf_recall_with_score(sid, train, top_k=k)]

def rec_sem(sid, train, k):
    return [i for i, _ in semantic_recall(train, top_k=k)]

def rec_hybrid(sid, train, k, alpha=0.5):
    cf = cf_recall_with_score(sid, train, top_k=20)
    sem = semantic_recall(train, top_k=20)

    def norm(pairs):
        if not pairs:
            return {}
        vals = [p[1] for p in pairs]
        lo, hi = min(vals), max(vals)
        rng = (hi - lo) or 1.0
        return {i: (v - lo) / rng for i, v in pairs}

    a, b = norm(cf), norm(sem)
    merged = {}
    for cid in set(a) | set(b):
        merged[cid] = alpha * a.get(cid, 0.0) + (1 - alpha) * b.get(cid, 0.0)
    return [i for i, _ in sorted(merged.items(), key=lambda x: -x[1])][:k]

if __name__ == "__main__":
    random.seed(42)   # 固定随机种子,保证结果可复现
    hist = get_user_history()
    print(f"用户数：{len(hist)}")

    print(f"\n--- HitRate@{K} ---")
    print(f"纯 CF      HitRate@{K} = {hit_rate_at_k(rec_cf, hist):.4f}")
    print(f"纯语义     HitRate@{K} = {hit_rate_at_k(rec_sem, hist):.4f}")
    for alpha in [0.3, 0.5, 0.7]:
        hr = hit_rate_at_k(lambda s, t, k: rec_hybrid(s, t, k, alpha), hist)
        print(f"融合 α={alpha}  HitRate@{K} = {hr:.4f}")

    print(f"\n--- MRR@{K} ---")
    print(f"纯 CF      MRR@{K} = {mrr_at_k(rec_cf, hist):.4f}")
    print(f"纯语义     MRR@{K} = {mrr_at_k(rec_sem, hist):.4f}")
    for alpha in [0.3, 0.5, 0.7]:
        mrr = mrr_at_k(lambda s, t, k: rec_hybrid(s, t, k, alpha), hist)
        print(f"融合 α={alpha}  MRR@{K} = {mrr:.4f}")