# Project structure

```text
clinical-rag-assistant/
  frontend/                 Vue 3 + TypeScript client
  backend/                  FastAPI API + RAG pipeline
  infra/                    Database/init/deployment files
  docs/                     Architecture and portfolio documentation
  data/                     Demo-only data folder
```

## Backend responsibility

The backend owns authentication, document ingestion, chunking, embeddings, retrieval, answer generation, citations, case notes, and audit events.

## Frontend responsibility

The frontend owns product UX: login, document upload, chat, source panels, case notes, settings, and admin/role-aware views.

## AI/RAG responsibility

The RAG pipeline is separated into ingestion, embedding, retrieval, generation, citation validation, and safety guards. This makes the project easier to explain in interviews.
