"""Document metadata and chunk persistence."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from math import sqrt

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.db.session import AsyncSessionLocal
from app.models.chunk import DocumentChunk
from app.models.document import Document


@dataclass(frozen=True)
class DocumentRecord:
    id: str
    filename: str
    status: str
    size_bytes: int
    created_at: datetime
    storage_path: str
    original_filename: str | None = None
    content_type: str | None = None
    page_count: int = 0
    chunk_count: int = 0
    extracted_char_count: int = 0
    error_message: str | None = None
    embedding_status: str = "not_started"
    embedded_chunk_count: int = 0
    embedding_model: str | None = None
    embedding_error: str | None = None
    embedded_at: datetime | None = None


@dataclass(frozen=True)
class DocumentChunkRecord:
    id: str
    document_id: str
    chunk_index: int
    page_number: int
    text: str
    char_count: int
    created_at: datetime
    embedding: list[float] | None = None
    embedding_model: str | None = None
    embedding_status: str = "pending"
    embedding_error: str | None = None
    embedded_at: datetime | None = None


@dataclass(frozen=True)
class ChunkEmbeddingRecord:
    chunk_id: str
    embedding: list[float]
    embedding_model: str
    embedding_status: str
    embedding_error: str | None
    embedded_at: datetime


@dataclass(frozen=True)
class RetrievalChunkRecord:
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


class DocumentRepository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession] = AsyncSessionLocal) -> None:
        self.session_factory = session_factory

    async def add(self, document: DocumentRecord) -> DocumentRecord:
        async with self.session_factory() as session:
            model = Document(
                id=document.id,
                filename=document.filename,
                original_filename=document.original_filename or document.filename,
                storage_path=document.storage_path,
                content_type=document.content_type,
                size_bytes=document.size_bytes,
                status=document.status,
                page_count=document.page_count,
                chunk_count=document.chunk_count,
                extracted_char_count=document.extracted_char_count,
                error_message=document.error_message,
                embedding_status=document.embedding_status,
                embedded_chunk_count=document.embedded_chunk_count,
                embedding_model=document.embedding_model,
                embedding_error=document.embedding_error,
                embedded_at=document.embedded_at,
                created_at=document.created_at,
                updated_at=document.created_at,
            )
            session.add(model)
            await session.commit()
            await session.refresh(model)
            return self._to_document_record(model)

    async def update(self, document_id: str, **updates: object) -> DocumentRecord | None:
        async with self.session_factory() as session:
            document = await session.get(Document, document_id)
            if document is None:
                return None

            for field, value in updates.items():
                setattr(document, field, value)

            await session.commit()
            await session.refresh(document)
            return self._to_document_record(document)

    async def list(self) -> list[DocumentRecord]:
        async with self.session_factory() as session:
            result = await session.execute(select(Document).order_by(Document.created_at.desc()))
            return [self._to_document_record(document) for document in result.scalars()]

    async def get(self, document_id: str) -> DocumentRecord | None:
        async with self.session_factory() as session:
            document = await session.get(Document, document_id)
            if document is None:
                return None
            return self._to_document_record(document)

    async def add_chunks(
        self,
        document_id: str,
        chunks: list[DocumentChunkRecord],
    ) -> list[DocumentChunkRecord]:
        async with self.session_factory() as session:
            await session.execute(delete(DocumentChunk).where(DocumentChunk.document_id == document_id))
            models = [
                DocumentChunk(
                    id=chunk.id,
                    document_id=chunk.document_id,
                    chunk_index=chunk.chunk_index,
                    page_number=chunk.page_number,
                    text=chunk.text,
                    char_count=chunk.char_count,
                    embedding=chunk.embedding,
                    embedding_model=chunk.embedding_model,
                    embedding_status=chunk.embedding_status,
                    embedding_error=chunk.embedding_error,
                    embedded_at=chunk.embedded_at,
                    created_at=chunk.created_at,
                )
                for chunk in chunks
            ]
            session.add_all(models)
            await session.commit()
            return chunks

    async def update_chunk_embeddings(
        self,
        embeddings: list[ChunkEmbeddingRecord],
    ) -> None:
        if not embeddings:
            return

        async with self.session_factory() as session:
            for embedding in embeddings:
                chunk = await session.get(DocumentChunk, embedding.chunk_id)
                if chunk is None:
                    continue

                chunk.embedding = embedding.embedding
                chunk.embedding_model = embedding.embedding_model
                chunk.embedding_status = embedding.embedding_status
                chunk.embedding_error = embedding.embedding_error
                chunk.embedded_at = embedding.embedded_at

            await session.commit()

    async def mark_chunks_embedding_failed(self, document_id: str, error_message: str) -> None:
        async with self.session_factory() as session:
            result = await session.execute(
                select(DocumentChunk).where(DocumentChunk.document_id == document_id)
            )
            for chunk in result.scalars():
                chunk.embedding = None
                chunk.embedding_model = None
                chunk.embedding_status = "failed"
                chunk.embedding_error = error_message
                chunk.embedded_at = None

            await session.commit()

    async def list_chunks(self, document_id: str) -> list[DocumentChunkRecord]:
        async with self.session_factory() as session:
            result = await session.execute(
                select(DocumentChunk)
                .where(DocumentChunk.document_id == document_id)
                .order_by(DocumentChunk.chunk_index.asc())
            )
            return [self._to_chunk_record(chunk) for chunk in result.scalars()]

    async def search_similar_chunks(
        self,
        query_embedding: list[float],
        top_k: int,
    ) -> list[RetrievalChunkRecord]:
        async with self.session_factory() as session:
            if session.bind and session.bind.dialect.name == "postgresql":
                return await self._search_similar_chunks_postgres(session, query_embedding, top_k)
            return await self._search_similar_chunks_in_python(session, query_embedding, top_k)

    async def get_chunk_count(self, document_id: str) -> int:
        async with self.session_factory() as session:
            result = await session.execute(
                select(func.count()).select_from(DocumentChunk).where(DocumentChunk.document_id == document_id)
            )
            return int(result.scalar_one())

    async def clear_chunks(self, document_id: str) -> None:
        async with self.session_factory() as session:
            await session.execute(delete(DocumentChunk).where(DocumentChunk.document_id == document_id))
            await session.commit()

    async def clear(self) -> None:
        async with self.session_factory() as session:
            await session.execute(delete(DocumentChunk))
            await session.execute(delete(Document))
            await session.commit()

    def _to_document_record(self, document: Document) -> DocumentRecord:
        return DocumentRecord(
            id=document.id,
            filename=document.filename,
            original_filename=document.original_filename,
            storage_path=document.storage_path,
            content_type=document.content_type,
            status=document.status,
            size_bytes=document.size_bytes,
            created_at=document.created_at,
            page_count=document.page_count,
            chunk_count=document.chunk_count,
            extracted_char_count=document.extracted_char_count,
            error_message=document.error_message,
            embedding_status=document.embedding_status,
            embedded_chunk_count=document.embedded_chunk_count,
            embedding_model=document.embedding_model,
            embedding_error=document.embedding_error,
            embedded_at=document.embedded_at,
        )

    def _to_chunk_record(self, chunk: DocumentChunk) -> DocumentChunkRecord:
        return DocumentChunkRecord(
            id=chunk.id,
            document_id=chunk.document_id,
            chunk_index=chunk.chunk_index,
            page_number=chunk.page_number,
            text=chunk.text,
            char_count=chunk.char_count,
            created_at=chunk.created_at,
            embedding=self._embedding_to_list(chunk.embedding),
            embedding_model=chunk.embedding_model,
            embedding_status=chunk.embedding_status,
            embedding_error=chunk.embedding_error,
            embedded_at=chunk.embedded_at,
        )

    async def _search_similar_chunks_postgres(
        self,
        session: AsyncSession,
        query_embedding: list[float],
        top_k: int,
    ) -> list[RetrievalChunkRecord]:
        distance = DocumentChunk.embedding.cosine_distance(query_embedding).label("distance")
        result = await session.execute(
            select(DocumentChunk, Document.filename, distance)
            .join(Document, Document.id == DocumentChunk.document_id)
            .where(
                Document.status == "ready",
                DocumentChunk.embedding_status == "embedded",
                DocumentChunk.embedding.is_not(None),
            )
            .order_by(distance.asc())
            .limit(top_k)
        )

        records: list[RetrievalChunkRecord] = []
        for chunk, filename, distance_value in result.all():
            numeric_distance = float(distance_value)
            records.append(
                RetrievalChunkRecord(
                    chunk_id=chunk.id,
                    document_id=chunk.document_id,
                    document_filename=filename,
                    page_number=chunk.page_number,
                    chunk_index=chunk.chunk_index,
                    text=chunk.text,
                    distance=numeric_distance,
                    similarity=1.0 - numeric_distance,
                    embedding_model=chunk.embedding_model,
                    created_at=chunk.created_at,
                )
            )
        return records

    async def _search_similar_chunks_in_python(
        self,
        session: AsyncSession,
        query_embedding: list[float],
        top_k: int,
    ) -> list[RetrievalChunkRecord]:
        result = await session.execute(
            select(DocumentChunk, Document.filename)
            .join(Document, Document.id == DocumentChunk.document_id)
            .where(
                Document.status == "ready",
                DocumentChunk.embedding_status == "embedded",
                DocumentChunk.embedding.is_not(None),
            )
        )

        records: list[RetrievalChunkRecord] = []
        for chunk, filename in result.all():
            chunk_embedding = self._embedding_to_list(chunk.embedding)
            if chunk_embedding is None:
                continue
            distance = self._cosine_distance(query_embedding, chunk_embedding)
            records.append(
                RetrievalChunkRecord(
                    chunk_id=chunk.id,
                    document_id=chunk.document_id,
                    document_filename=filename,
                    page_number=chunk.page_number,
                    chunk_index=chunk.chunk_index,
                    text=chunk.text,
                    distance=distance,
                    similarity=1.0 - distance,
                    embedding_model=chunk.embedding_model,
                    created_at=chunk.created_at,
                )
            )

        return sorted(records, key=lambda record: record.distance)[:top_k]

    def _cosine_distance(self, left: list[float], right: list[float]) -> float:
        dot_product = sum(left_value * right_value for left_value, right_value in zip(left, right, strict=True))
        left_norm = sqrt(sum(value * value for value in left))
        right_norm = sqrt(sum(value * value for value in right))
        if left_norm == 0 or right_norm == 0:
            return 1.0
        similarity = dot_product / (left_norm * right_norm)
        return 1.0 - similarity

    def _embedding_to_list(self, embedding: object) -> list[float] | None:
        if embedding is None:
            return None
        if isinstance(embedding, str):
            return [float(value) for value in embedding.strip("[]").split(",") if value]
        if hasattr(embedding, "tolist"):
            return [float(value) for value in embedding.tolist()]
        return [float(value) for value in embedding]


document_repository = DocumentRepository()
