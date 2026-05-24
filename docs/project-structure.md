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

The backend owns document ingestion, PDF extraction, chunking, embeddings, retrieval, grounded answer generation, and source metadata.

## Frontend responsibility

The frontend owns the portfolio demo UX: product overview, document upload/status inspection, semantic search/debugging, chat, and source panels.

## AI/RAG responsibility

The RAG pipeline is separated into ingestion, embedding, retrieval, generation, source formatting, and safety boundaries. This makes the project easier to explain in interviews.
