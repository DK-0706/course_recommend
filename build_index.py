# build_index.py
from app import query_all
from rec_semantic import build_course_index

if __name__ == "__main__":
    mat = build_course_index(query_all)
    if mat is None:
        print("课程表为空,索引未构建")
    else:
        print(f"课程向量索引构建完成,共 {mat.shape[0]} 门课,维度 {mat.shape[1]}")