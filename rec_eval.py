# rec_eval.py —— 离线评测
import numpy as np
from app import query_all, cf_recall_with_score, get_chosen_course_ids
from rec_semantic import semantic_recall

def build_eval_set(holdout_ratio=0.2):
    # 留一法:从每个学生历史里藏起最近的部分课程
    rows = query_all("SELECT student_id, course_id FROM choose ORDER BY student_id")
    history = {}
    for r in rows:
        history.setdefault(r["student_id"], []).append(r["course_id"])
    eval_set = []
    for uid, courses in history.items():
        if len(courses) < 3:
            continue
        n_hold = max(1, int(len(courses) * holdout_ratio))
        eval_set.append({"uid": uid, "train": courses[:-n_hold], "target": courses[-n_hold:]})
    return eval_set

def hit_rate_at_k(recall_fn, eval_set, k=4):
    hit = 0
    for case in eval_set:
        recs = [cid for cid, _ in recall_fn(case["uid"], case["train"], top_k=k)]
        if set(recs) & set(case["target"]):
            hit += 1
    return hit / len(eval_set) if eval_set else 0.0

def overlap_at_k(list_a, list_b, k=4):
    a = {cid for cid, _ in list_a[:k]}
    b = {cid for cid, _ in list_b[:k]}
    return len(a & b) / k if k else 0.0

if __name__ == "__main__":
    eval_set = build_eval_set()
    hr_cf = hit_rate_at_k(cf_recall_with_score, eval_set)
    hr_sem = hit_rate_at_k(
        lambda uid, train, top_k: semantic_recall(train, top_k), eval_set
    )
    print(f"协同过滤 HitRate@4 = {hr_cf:.3f}")
    print(f"语义召回 HitRate@4 = {hr_sem:.3f}")

    ov = np.mean([
        overlap_at_k(
            cf_recall_with_score(c["uid"], c["train"], 4),
            semantic_recall(c["train"], 4),
        )
        for c in eval_set[:20]
    ])
    print(f"两路召回平均重合度 = {ov:.3f}")