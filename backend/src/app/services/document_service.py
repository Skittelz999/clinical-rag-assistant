"""Document upload lifecycle, PDF processing, and metadata handling."""

from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.core.config import settings
from app.repositories.document_repository import (
    DocumentRepository,
    DocumentChunkRecord,
    DocumentRecord,
    document_repository,
)
from app.schemas.document import DocumentChunkResponse, DocumentChunksResponse, DocumentResponse
from app.services.chunking_service import ChunkingService, chunking_service
from app.services.embedding_service import EmbeddingError, EmbeddingService, embedding_service
from app.services.pdf_extraction_service import (
    PdfExtractionService,
    PdfProcessingError,
    pdf_extraction_service,
)

CHUNK_SIZE_BYTES = 1024 * 1024
DEMO_MAX_UPLOAD_MB = 10


class DocumentValidationError(Exception):
    pass


class DocumentTooLargeError(Exception):
    pass


class DocumentStorageError(Exception):
    pass


class DocumentProcessingUnexpectedError(Exception):
    pass


class DocumentNotFoundError(Exception):
    pass


class DocumentService:
    def __init__(
        self,
        repository: DocumentRepository,
        upload_dir: Path | None = None,
        pdf_extractor: PdfExtractionService = pdf_extraction_service,
        chunker: ChunkingService = chunking_service,
        embedder: EmbeddingService = embedding_service,
    ) -> None:
        self.repository = repository
        self.pdf_extractor = pdf_extractor
        self.chunker = chunker
        self.embedder = embedder
        backend_root = Path(__file__).resolve().parents[3]
        self.upload_dir = upload_dir or backend_root / "storage" / "uploads"

    async def upload_pdf(self, file: UploadFile | None) -> DocumentResponse:
        if file is None:
            raise DocumentValidationError("A PDF file is required.")

        filename = self._validate_pdf_metadata(file)
        document_id = str(uuid4())
        target_path = self.upload_dir / f"{document_id}.pdf"
        max_upload_bytes = self._max_upload_bytes()

        try:
            self.upload_dir.mkdir(parents=True, exist_ok=True)
            size_bytes = await self._write_upload(file, target_path, max_upload_bytes)
        except DocumentValidationError:
            target_path.unlink(missing_ok=True)
            raise
        except DocumentTooLargeError:
            target_path.unlink(missing_ok=True)
            raise
        except Exception as exc:
            target_path.unlink(missing_ok=True)
            raise DocumentStorageError("Unable to store the uploaded document.") from exc
        finally:
            await file.close()

        await self.repository.add(
            DocumentRecord(
                id=document_id,
                filename=filename,
                original_filename=filename,
                content_type=file.content_type,
                status="uploaded",
                size_bytes=size_bytes,
                created_at=datetime.now(UTC),
                storage_path=str(target_path),
            )
        )
        record = await self._update_document(document_id, status="processing")

        try:
            pages = self.pdf_extractor.extract_pages(target_path)
            chunks = self.chunker.chunk_pages(document_id=document_id, pages=pages)
            now = datetime.now(UTC)
            chunk_records = [
                DocumentChunkRecord(
                    id=str(uuid4()),
                    document_id=chunk.document_id,
                    chunk_index=chunk.chunk_index,
                    page_number=chunk.page_number,
                    text=chunk.text,
                    char_count=chunk.char_count,
                    created_at=now,
                )
                for chunk in chunks
            ]
            await self.repository.add_chunks(document_id, chunk_records)
            await self._update_document(
                document_id,
                embedding_status="processing",
                embedded_chunk_count=0,
                embedding_model=None,
                embedding_error=None,
                embedded_at=None,
            )
            chunk_embeddings = await self.embedder.embed_chunks(chunk_records)
            await self.repository.update_chunk_embeddings(chunk_embeddings)
            embedded_at = chunk_embeddings[0].embedded_at if chunk_embeddings else None
            record = await self._update_document(
                document_id,
                status="ready",
                page_count=len(pages),
                chunk_count=len(chunk_records),
                extracted_char_count=sum(len(page.text) for page in pages),
                error_message=None,
                embedding_status="embedded",
                embedded_chunk_count=len(chunk_embeddings),
                embedding_model=self.embedder.provider.model_name,
                embedding_error=None,
                embedded_at=embedded_at,
            )
        except PdfProcessingError as exc:
            await self.repository.clear_chunks(document_id)
            record = await self._update_document(
                document_id,
                status="failed",
                chunk_count=0,
                extracted_char_count=0,
                error_message=str(exc),
                embedding_status="not_started",
                embedded_chunk_count=0,
                embedding_model=None,
                embedding_error=None,
                embedded_at=None,
            )
        except EmbeddingError as exc:
            await self.repository.mark_chunks_embedding_failed(document_id, str(exc))
            record = await self._update_document(
                document_id,
                status="failed",
                chunk_count=len(chunk_records),
                extracted_char_count=sum(len(page.text) for page in pages),
                error_message=f"Embedding generation failed: {exc}",
                embedding_status="failed",
                embedded_chunk_count=0,
                embedding_model=self.embedder.provider.model_name,
                embedding_error=str(exc),
                embedded_at=None,
            )
        except Exception as exc:
            await self.repository.mark_chunks_embedding_failed(
                document_id,
                "Document processing failed. Please try another PDF.",
            )
            await self._update_document(
                document_id,
                status="failed",
                chunk_count=0,
                extracted_char_count=0,
                error_message="Document processing failed. Please try another PDF.",
                embedding_status="failed",
                embedded_chunk_count=0,
                embedding_model=None,
                embedding_error="Document processing failed. Please try another PDF.",
                embedded_at=None,
            )
            raise DocumentProcessingUnexpectedError("Unexpected document processing error.") from exc

        return self._to_response(record)

    async def list_documents(self) -> list[DocumentResponse]:
        return [self._to_response(document) for document in await self.repository.list()]

    async def get_document(self, document_id: str) -> DocumentResponse:
        document = await self.repository.get(document_id)
        if document is None:
            raise DocumentNotFoundError("Document not found.")
        return self._to_response(document)

    async def list_document_chunks(self, document_id: str) -> DocumentChunksResponse:
        document = await self.repository.get(document_id)
        if document is None:
            raise DocumentNotFoundError("Document not found.")

        chunks = [] if document.status == "failed" else await self.repository.list_chunks(document_id)
        return DocumentChunksResponse(
            document_id=document_id,
            chunks=[self._to_chunk_response(chunk) for chunk in chunks],
        )

    def _validate_pdf_metadata(self, file: UploadFile) -> str:
        filename = Path(file.filename or "").name
        if not filename:
            raise DocumentValidationError("A filename is required.")

        is_pdf_content_type = file.content_type == "application/pdf"
        is_pdf_extension = filename.lower().endswith(".pdf")
        if not (is_pdf_content_type or is_pdf_extension):
            raise DocumentValidationError("Only PDF files are supported.")

        return filename

    async def _write_upload(
        self,
        file: UploadFile,
        target_path: Path,
        max_upload_bytes: int,
    ) -> int:
        size_bytes = 0
        with target_path.open("wb") as destination:
            while True:
                chunk = await file.read(CHUNK_SIZE_BYTES)
                if not chunk:
                    break

                size_bytes += len(chunk)
                if size_bytes > max_upload_bytes:
                    raise DocumentTooLargeError(
                        f"PDF files must be {max_upload_bytes // 1024 // 1024} MB or smaller."
                    )

                destination.write(chunk)

        if size_bytes == 0:
            raise DocumentValidationError("Uploaded PDF cannot be empty.")

        return size_bytes

    def _max_upload_bytes(self) -> int:
        upload_mb = min(settings.max_upload_mb, DEMO_MAX_UPLOAD_MB)
        return upload_mb * 1024 * 1024

    async def _update_document(self, document_id: str, **updates: object) -> DocumentRecord:
        document = await self.repository.update(document_id, **updates)
        if document is None:
            raise DocumentNotFoundError("Document not found.")
        return document

    def _to_response(self, document: DocumentRecord) -> DocumentResponse:
        return DocumentResponse(
            id=document.id,
            filename=document.filename,
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

    def _to_chunk_response(self, chunk: DocumentChunkRecord) -> DocumentChunkResponse:
        return DocumentChunkResponse(
            id=chunk.id,
            document_id=chunk.document_id,
            chunk_index=chunk.chunk_index,
            page_number=chunk.page_number,
            text=chunk.text,
            char_count=chunk.char_count,
            created_at=chunk.created_at,
            embedding_status=chunk.embedding_status,
            embedding_model=chunk.embedding_model,
            embedding_error=chunk.embedding_error,
            embedded_at=chunk.embedded_at,
        )


document_service = DocumentService(document_repository)
