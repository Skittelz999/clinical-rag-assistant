"""Embedding provider abstraction and chunk embedding orchestration."""

from __future__ import annotations

from datetime import UTC, datetime
from hashlib import sha256
from math import sqrt
from typing import Protocol

from openai import AsyncOpenAI

from app.core.config import settings
from app.core.embeddings import DEMO_EMBEDDING_MODEL, EMBEDDING_VECTOR_DIMENSIONS
from app.repositories.document_repository import ChunkEmbeddingRecord, DocumentChunkRecord


class EmbeddingError(Exception):
    pass


class EmbeddingProvider(Protocol):
    model_name: str
    dimensions: int

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        pass


class DeterministicDemoEmbeddingProvider:
    """Local deterministic embeddings for development without external API calls."""

    model_name = DEMO_EMBEDDING_MODEL
    dimensions = EMBEDDING_VECTOR_DIMENSIONS

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_text(text) for text in texts]

    def _embed_text(self, text: str) -> list[float]:
        seed = sha256(text.encode("utf-8")).digest()
        values = [((seed[index % len(seed)] / 127.5) - 1.0) for index in range(self.dimensions)]
        norm = sqrt(sum(value * value for value in values))
        if norm == 0:
            return values
        return [value / norm for value in values]


class OpenAIEmbeddingProvider:
    dimensions = EMBEDDING_VECTOR_DIMENSIONS

    def __init__(self, api_key: str | None, model_name: str) -> None:
        self.api_key = api_key
        self.model_name = model_name
        self._client: AsyncOpenAI | None = None

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not self.api_key or self.api_key == "replace-me":
            raise EmbeddingError("OPENAI_API_KEY is required when EMBEDDING_PROVIDER=openai.")

        try:
            response = await self._get_client().embeddings.create(
                model=self.model_name,
                input=texts,
            )
        except Exception as exc:
            raise EmbeddingError("Embedding provider request failed.") from exc

        ordered_items = sorted(response.data, key=lambda item: item.index)
        return [list(item.embedding) for item in ordered_items]

    def _get_client(self) -> AsyncOpenAI:
        if self._client is None:
            self._client = AsyncOpenAI(api_key=self.api_key)
        return self._client


class EmbeddingService:
    def __init__(self, provider: EmbeddingProvider) -> None:
        self.provider = provider

    async def embed_query(self, query: str) -> list[float]:
        embeddings = await self.provider.embed_texts([query])
        self._validate_embeddings(embeddings, expected_count=1)
        return embeddings[0]

    async def embed_chunks(self, chunks: list[DocumentChunkRecord]) -> list[ChunkEmbeddingRecord]:
        if not chunks:
            return []

        embeddings = await self.provider.embed_texts([chunk.text for chunk in chunks])
        self._validate_embeddings(embeddings, expected_count=len(chunks))

        now = datetime.now(UTC)
        return [
            ChunkEmbeddingRecord(
                chunk_id=chunk.id,
                embedding=embedding,
                embedding_model=self.provider.model_name,
                embedding_status="embedded",
                embedding_error=None,
                embedded_at=now,
            )
            for chunk, embedding in zip(chunks, embeddings, strict=True)
        ]

    def _validate_embeddings(self, embeddings: list[list[float]], expected_count: int) -> None:
        if len(embeddings) != expected_count:
            raise EmbeddingError("Embedding provider returned an unexpected number of vectors.")

        for embedding in embeddings:
            if len(embedding) != EMBEDDING_VECTOR_DIMENSIONS:
                raise EmbeddingError(
                    f"Embedding provider returned {len(embedding)} dimensions; "
                    f"expected {EMBEDDING_VECTOR_DIMENSIONS}."
                )


def build_embedding_provider() -> EmbeddingProvider:
    provider = settings.embedding_provider.lower().strip()
    if provider == "openai":
        return OpenAIEmbeddingProvider(
            api_key=settings.openai_api_key,
            model_name=settings.openai_embedding_model,
        )
    if provider in {"deterministic", "demo", "local"}:
        return DeterministicDemoEmbeddingProvider()

    raise ValueError(f"Unsupported EMBEDDING_PROVIDER value: {settings.embedding_provider}")


embedding_service = EmbeddingService(build_embedding_provider())
