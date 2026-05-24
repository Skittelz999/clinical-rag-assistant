# Architecture

## High-level flow

1. User uploads a guideline PDF.
2. Backend extracts text and metadata.
3. Text is chunked into retrieval units.
4. Embeddings are generated and stored in PostgreSQL/pgvector.
5. User asks a question in chat.
6. Retrieval finds relevant authorized chunks.
7. LLM generates an answer using only retrieved evidence.
8. Backend returns answer, citations, and trace metadata.
9. Frontend displays the answer with clickable sources.

## Main services

- `DocumentService`: upload lifecycle and metadata
- `PdfService`: PDF text extraction
- `ChunkingService`: document chunk creation
- `EmbeddingService`: vector creation
- `RetrievalService`: pgvector similarity search
- `RagService`: retrieval + answer generation orchestration
- `CitationService`: validates source references
- `AuditService`: records sensitive actions
