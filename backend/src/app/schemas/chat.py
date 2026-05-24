from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    question: str = Field(min_length=2)
    conversation_id: str | None = None
    document_ids: list[str] = []


class Citation(BaseModel):
    document_id: str
    title: str
    page: int | None = None
    snippet: str


class ChatResponse(BaseModel):
    answer: str
    citations: list[Citation]
