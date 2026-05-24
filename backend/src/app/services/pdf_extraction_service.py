"""PDF text extraction for the demo document pipeline."""

from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader

NO_EXTRACTABLE_TEXT_MESSAGE = "No extractable text found. Scanned PDFs are not supported in this demo."


@dataclass(frozen=True)
class ExtractedPage:
    page_number: int
    text: str


class PdfProcessingError(Exception):
    pass


class PdfExtractionService:
    def extract_pages(self, file_path: Path) -> list[ExtractedPage]:
        try:
            reader = PdfReader(str(file_path))
        except Exception as exc:
            raise PdfProcessingError("Unable to read PDF. Upload a valid text-based PDF.") from exc

        pages: list[ExtractedPage] = []
        try:
            for page_index, page in enumerate(reader.pages, start=1):
                text = self._clean_text(page.extract_text() or "")
                pages.append(ExtractedPage(page_number=page_index, text=text))
        except Exception as exc:
            raise PdfProcessingError("Unable to extract text from this PDF.") from exc

        if not any(page.text for page in pages):
            raise PdfProcessingError(NO_EXTRACTABLE_TEXT_MESSAGE)

        return pages

    def _clean_text(self, text: str) -> str:
        lines = [line.strip() for line in text.splitlines()]
        return "\n".join(line for line in lines if line).strip()


pdf_extraction_service = PdfExtractionService()
