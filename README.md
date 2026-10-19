# Course Recommendation System

Flask course selection application with hybrid recommendation (user-based collaborative filtering + FAISS semantic recall), personalized RAG explanations, and a LangGraph chat recommendation workflow.

## Setup

Use Python 3.10 or newer. Install the application dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Install the Vue frontend dependencies in a second terminal:

```powershell
cd frontend
npm install
```

Start MySQL, then configure the environment variables before launching Flask. Redis is optional; when unavailable, cache reads and writes are skipped.

```powershell
$env:DB_HOST = "localhost"
$env:DB_USER = "root"
$env:DB_PASSWORD = "your-password"
$env:DB_NAME = "course_rec"
$env:REDIS_URL = "redis://localhost:6379/0"
$env:OPENAI_API_KEY = "your-api-key"
$env:OPENAI_BASE_URL = "your-compatible-api-base-url"
$env:OPENAI_MODEL = "agnes-3.0-flash"
python app.py
```

For local development, keep Flask running in that terminal and start Vite in the frontend terminal:

```powershell
cd frontend
npm run dev
```

Open the Vite URL shown in the terminal (usually `http://localhost:5173`). Vite proxies `/api` requests to Flask at `http://127.0.0.1:5000`. For a single Flask-served production build, run `npm run build` inside `frontend`, then start Flask; it serves the generated `frontend/dist` files.

`db_init.py` recreates and seeds the application tables, so only run it against a fresh or disposable database. The semantic model is downloaded on first application startup; `build_index.py` rebuilds the local FAISS course index after the course catalog changes.

## Chat Agent Flow

The `/api/student/chat` endpoint runs a LangGraph workflow:

1. Load the student's selected courses and retrieve eligible courses from MySQL.
2. Ask the model to rank only those candidates and return a Pydantic-validated JSON payload.
3. Validate IDs against the retrieved set, remove duplicates, and retry once if the model output is invalid.
4. Fall back to eligible retrieved courses if the model still returns invalid output.

Structured logs include a request ID, candidate/result counts, retry count, and latency. They avoid logging prompts and course histories.

## Recommendation Evaluation

Run `python rec_eval.py` to evaluate leave-one-out course ranking with a fixed seed. It reports HitRate@K, Precision@K, Recall@K, MRR@K, and NDCG@K for collaborative filtering, semantic recall, and hybrid ranking. Collaborative filtering is computed from the training interactions for each split to avoid leaking the held-out course.

## Configuration

Database, Redis, and model credentials can be configured through `DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`, `DB_CHARSET`, `REDIS_URL`, `OPENAI_API_KEY`, `OPENAI_BASE_URL`, and `OPENAI_MODEL`.
