"""Semantic retrieval over persisted document chunk embeddings."""

from app.repositories.document_repository import DocumentRepository, document_repository
from app.schemas.retrieval import RetrievalResult, RetrievalSearchResponse
from app.services.embedding_service import EmbeddingService, embedding_service


class RetrievalService:
    def __init__(
        self,
        repository: DocumentRepository,
        embedder: EmbeddingService,
    ) -> None:
        self.repository = repository
        self.embedder = embedder

    async def search(self, query: str, top_k: int) -> RetrievalSearchResponse:
        query_embedding = await self.embedder.embed_query(query)
        matches = await self.repository.search_similar_chunks(query_embedding=query_embedding, top_k=top_k)
        return RetrievalSearchResponse(
            query=query,
            top_k=top_k,
            results=[
                RetrievalResult(
                    chunk_id=match.chunk_id,
                    document_id=match.document_id,
                    document_filename=match.document_filename,
                    page_number=match.page_number,
                    chunk_index=match.chunk_index,
                    text=match.text,
                    distance=match.distance,
                    similarity=match.similarity,
                    embedding_model=match.embedding_model,
                    created_at=match.created_at,
                )
                for match in matches
            ],
        )


retrieval_service = RetrievalService(
    repository=document_repository,
    embedder=embedding_service,
)
