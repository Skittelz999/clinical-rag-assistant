from fastapi import APIRouter, HTTPException, status

from app.schemas.retrieval import RetrievalSearchRequest, RetrievalSearchResponse
from app.services.embedding_service import EmbeddingError
from app.services.retrieval_service import retrieval_service

router = APIRouter()


@router.post("/search", response_model=RetrievalSearchResponse)
async def search_chunks(
    payload: RetrievalSearchRequest,
) -> RetrievalSearchResponse:
    try:
        return await retrieval_service.search(query=payload.query, top_k=payload.top_k)
    except EmbeddingError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Embedding provider failed: {exc}",
        ) from exc
