from fastapi import APIRouter, HTTPException, status

from app.schemas.rag import RagAnswerRequest, RagAnswerResponse
from app.services.embedding_service import EmbeddingError
from app.services.llm_service import LLMError
from app.services.rag_service import rag_service

router = APIRouter()


@router.post("/answer", response_model=RagAnswerResponse)
async def answer_question(
    payload: RagAnswerRequest,
) -> RagAnswerResponse:
    try:
        return await rag_service.answer(question=payload.question, top_k=payload.top_k)
    except EmbeddingError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Embedding provider failed: {exc}",
        ) from exc
    except LLMError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Answer generation provider failed: {exc}",
        ) from exc
