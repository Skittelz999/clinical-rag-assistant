from datetime import datetime
from typing import Literal

from pydantic import BaseModel

DocumentStatus = Literal["uploaded", "processing", "ready", "failed"]
EmbeddingStatus = Literal["not_started", "pending", "processing", "embedded", "failed"]


class DocumentResponse(BaseModel):
    id: str
    filename: str
    status: DocumentStatus
    size_bytes: int
    created_at: datetime
    page_count: int
    chunk_count: int
    extracted_char_count: int
    error_message: str | None
    embedding_status: EmbeddingStatus
    embedded_chunk_count: int
    embedding_model: str | None
    embedding_error: str | None
    embedded_at: datetime | None


class DocumentChunkResponse(BaseModel):
    id: str
    document_id: str
    chunk_index: int
    page_number: int
    text: str
    char_count: int
    created_at: datetime
    embedding_status: EmbeddingStatus
    embedding_model: str | None
    embedding_error: str | None
    embedded_at: datetime | None


class DocumentChunksResponse(BaseModel):
    document_id: str
    chunks: list[DocumentChunkResponse]
