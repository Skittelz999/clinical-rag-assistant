from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.schemas.retrieval import RetrievalResult


class RagAnswerRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    top_k: int = Field(default=5, ge=1, le=20)

    @field_validator("question")
    @classmethod
    def question_must_not_be_blank(cls, value: str) -> str:
        question = value.strip()
        if not question:
            raise ValueError("Question cannot be empty.")
        return question


class RagSource(BaseModel):
    document_id: str
    document_filename: str
    page_number: int
    chunk_index: int
    chunk_id: str
    similarity: float
    distance: float
    text_preview: str


class RagAnswerResponse(BaseModel):
    answer: str
    used_sources: list[RagSource]
    retrieved_chunks: list[RetrievalResult]
    insufficient_evidence: bool
    provider: str
    model: str
    created_at: datetime

