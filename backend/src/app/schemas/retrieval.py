from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class RetrievalSearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    top_k: int = Field(default=5, ge=1, le=20)

    @field_validator("query")
    @classmethod
    def query_must_not_be_blank(cls, value: str) -> str:
        query = value.strip()
        if not query:
            raise ValueError("Query cannot be empty.")
        return query


class RetrievalResult(BaseModel):
    chunk_id: str
    document_id: str
    document_filename: str
    page_number: int
    chunk_index: int
    text: str
    distance: float
    similarity: float
    embedding_model: str | None
    created_at: datetime


class RetrievalSearchResponse(BaseModel):
    query: str
    top_k: int
    results: list[RetrievalResult]

