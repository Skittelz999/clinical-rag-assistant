# Architecture

## High-level flow

1. User uploads a guideline PDF.
2. Backend extracts text and metadata.
3. Text is chunked into retrieval units.
4. Embeddings are generated and stored in PostgreSQL/pgvector.
5. User asks a question in chat.
6. Retrieval finds relevant ready, embedded chunks.
7. LLM generates an answer using only retrieved evidence.
8. Backend returns the answer, source cards, and retrieval metadata.
9. Frontend displays the answer with source cards.

## Main services

- `DocumentService`: upload lifecycle and metadata
- `PdfExtractionService`: PDF text extraction
- `ChunkingService`: document chunk creation
- `EmbeddingService`: vector creation
- `RetrievalService`: pgvector similarity search
- `RagService`: retrieval + answer generation orchestration
