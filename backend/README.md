# Backend

FastAPI backend for the Clinical RAG Assistant.

## Run locally without Docker

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e .[dev]
uvicorn app.main:app --reload --app-dir src
```
