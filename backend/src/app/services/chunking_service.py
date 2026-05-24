"""Chunk extracted page text into stable, page-scoped windows."""

from dataclasses import dataclass

from app.services.pdf_extraction_service import ExtractedPage

DEFAULT_CHUNK_SIZE = 1200
DEFAULT_CHUNK_OVERLAP = 200


@dataclass(frozen=True)
class DocumentChunkDraft:
    document_id: str
    chunk_index: int
    page_number: int
    text: str
    char_count: int


class ChunkingService:
    def __init__(
        self,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    ) -> None:
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_pages(
        self,
        document_id: str,
        pages: list[ExtractedPage],
    ) -> list[DocumentChunkDraft]:
        chunks: list[DocumentChunkDraft] = []

        for page in pages:
            page_text = page.text.strip()
            if not page_text:
                continue

            start = 0
            while start < len(page_text):
                end = min(start + self.chunk_size, len(page_text))
                chunk_text = page_text[start:end].strip()

                if chunk_text:
                    chunks.append(
                        DocumentChunkDraft(
                            document_id=document_id,
                            chunk_index=len(chunks),
                            page_number=page.page_number,
                            text=chunk_text,
                            char_count=len(chunk_text),
                        )
                    )

                if end >= len(page_text):
                    break

                next_start = max(end - self.chunk_overlap, start + 1)
                while next_start < len(page_text) and page_text[next_start].isspace():
                    next_start += 1
                start = next_start

        return chunks


chunking_service = ChunkingService()
