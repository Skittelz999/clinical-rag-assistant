"""Grounded answer generation over retrieved document chunks."""

from dataclasses import dataclass
from datetime import UTC, datetime
import re

from app.schemas.rag import RagAnswerResponse, RagSource
from app.schemas.retrieval import RetrievalResult
from app.services.llm_service import LLMService, llm_service
from app.services.retrieval_service import RetrievalService, retrieval_service

INSUFFICIENT_EVIDENCE_ANSWER = (
    "The uploaded documents do not contain enough information to answer this question."
)

_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")
_LEADING_SENTENCE_START_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9])")
_TOKEN_RE = re.compile(r"[a-z0-9]+")
_SOURCE_STOP_WORDS = {
    "about",
    "and",
    "are",
    "does",
    "for",
    "from",
    "listed",
    "say",
    "says",
    "should",
    "the",
    "this",
    "what",
    "when",
    "which",
    "with",
}


@dataclass(frozen=True)
class ContextChunk:
    source: RetrievalResult
    text: str


class RagContextCleaner:
    def __init__(self, max_chunk_chars: int = 950, max_total_chars: int = 4500) -> None:
        self.max_chunk_chars = max_chunk_chars
        self.max_total_chars = max_total_chars

    def prepare_context(self, chunks: list[RetrievalResult]) -> list[ContextChunk]:
        context_chunks: list[ContextChunk] = []
        seen_sentence_tokens: list[frozenset[str]] = []
        total_chars = 0

        for chunk in chunks:
            cleaned_text = self.clean_context_text(chunk.text, seen_sentence_tokens)
            if not cleaned_text:
                continue

            remaining_chars = self.max_total_chars - total_chars
            if remaining_chars <= 0:
                break

            context_text = self.preview_text(cleaned_text, min(self.max_chunk_chars, remaining_chars))
            if context_text:
                context_chunks.append(ContextChunk(source=chunk, text=context_text))
                total_chars += len(context_text)

        return context_chunks

    def clean_context_text(
        self,
        text: str,
        seen_sentence_tokens: list[frozenset[str]] | None = None,
    ) -> str:
        normalized = self.normalize_whitespace(text)
        if not normalized:
            return ""
        normalized = self.trim_leading_fragment(normalized)

        sentence_tokens = seen_sentence_tokens if seen_sentence_tokens is not None else []
        unique_sentences: list[str] = []
        for sentence in self.split_sentences(normalized):
            sentence = self.normalize_whitespace(sentence)
            if not sentence or self._is_near_duplicate_sentence(sentence, sentence_tokens):
                continue
            unique_sentences.append(sentence)

        return self.normalize_whitespace(" ".join(unique_sentences))

    def normalize_whitespace(self, text: str) -> str:
        return " ".join(text.split())

    def split_sentences(self, text: str) -> list[str]:
        sentences = [sentence.strip() for sentence in _SENTENCE_SPLIT_RE.split(text) if sentence.strip()]
        return sentences or [text]

    def trim_leading_fragment(self, text: str) -> str:
        if not text or text[0].isupper() or text[0].isdigit():
            return text

        match = _LEADING_SENTENCE_START_RE.search(text)
        if match and match.end() <= 320:
            return text[match.end() :].strip()

        return text

    def preview_text(self, text: str, max_chars: int = 500) -> str:
        normalized = self.normalize_whitespace(text)
        if len(normalized) <= max_chars:
            return normalized

        sentence_boundary = max(
            normalized.rfind(". ", 0, max_chars),
            normalized.rfind("! ", 0, max_chars),
            normalized.rfind("? ", 0, max_chars),
        )
        if sentence_boundary >= max(80, int(max_chars * 0.45)):
            return f"{normalized[: sentence_boundary + 1].strip()}..."

        word_boundary = normalized.rfind(" ", 0, max_chars)
        if word_boundary >= max(40, int(max_chars * 0.45)):
            return f"{normalized[:word_boundary].strip()}..."

        return f"{normalized[:max_chars].strip()}..."

    def _is_near_duplicate_sentence(
        self,
        sentence: str,
        seen_sentence_tokens: list[frozenset[str]],
    ) -> bool:
        tokens = frozenset(_TOKEN_RE.findall(sentence.lower()))
        if not tokens:
            return True

        for seen_tokens in seen_sentence_tokens:
            overlap = len(tokens & seen_tokens) / max(len(tokens), len(seen_tokens))
            if overlap >= 0.9:
                return True

        seen_sentence_tokens.append(tokens)
        return False


class RagPromptBuilder:
    def __init__(self, cleaner: RagContextCleaner | None = None) -> None:
        self.cleaner = cleaner or RagContextCleaner()

    def prepare_context(self, chunks: list[RetrievalResult]) -> list[ContextChunk]:
        return self.cleaner.prepare_context(chunks)

    def build_system_prompt(self) -> str:
        return (
            "You are a demo clinical knowledge assistant for uploaded guideline documents. "
            "Answer only from the provided context and only answer the user's question. "
            "Do not use outside knowledge. Answer concisely in 2 to 5 sentences. "
            "Do not repeat the same fact, and do not copy raw chunks unless a short "
            "phrase is necessary. If the context does not contain enough information, "
            "say that the uploaded documents do not contain enough information. "
            "Do not invent medical advice, unsupported facts, definitive diagnoses, "
            "or personalized treatment instructions. Cite the source labels you used. "
            "Return JSON with keys answer and insufficient_evidence."
        )

    def build_user_prompt(self, question: str, chunks: list[ContextChunk]) -> str:
        if not chunks:
            return (
                f"Question: {question}\n\n"
                "Context is empty.\n\n"
                "Return JSON with answer and insufficient_evidence."
            )

        context_blocks = []
        for index, context_chunk in enumerate(chunks, start=1):
            chunk = context_chunk.source
            context_blocks.append(
                "\n".join(
                    [
                        f"[Source {index}]",
                        f"Document: {chunk.document_filename}",
                        f"Document ID: {chunk.document_id}",
                        f"Chunk ID: {chunk.chunk_id}",
                        f"Page: {chunk.page_number}",
                        f"Chunk index: {chunk.chunk_index}",
                        f"Similarity: {chunk.similarity:.4f}",
                        f"Distance: {chunk.distance:.4f}",
                        f"Text: {context_chunk.text}",
                    ]
                )
            )

        context = "\n\n".join(context_blocks)
        return (
            f"Question: {question}\n\n"
            "Context:\n"
            f"{context}\n\n"
            "Return JSON with answer and insufficient_evidence."
        )


class RagService:
    def __init__(
        self,
        retriever: RetrievalService,
        llm: LLMService,
        prompt_builder: RagPromptBuilder | None = None,
    ) -> None:
        self.retriever = retriever
        self.llm = llm
        self.prompt_builder = prompt_builder or RagPromptBuilder()

    async def answer(self, question: str, top_k: int) -> RagAnswerResponse:
        retrieval = await self.retriever.search(query=question, top_k=top_k)
        retrieved_chunks = retrieval.results
        context_chunks = self.prompt_builder.prepare_context(retrieved_chunks)

        if not context_chunks:
            return RagAnswerResponse(
                answer=INSUFFICIENT_EVIDENCE_ANSWER,
                used_sources=[],
                retrieved_chunks=[],
                insufficient_evidence=True,
                provider=self.llm.provider.provider_name,
                model=self.llm.provider.model_name,
                created_at=datetime.now(UTC),
            )

        system_prompt = self.prompt_builder.build_system_prompt()
        user_prompt = self.prompt_builder.build_user_prompt(question=question, chunks=context_chunks)
        draft = await self.llm.generate_grounded_answer(system_prompt=system_prompt, user_prompt=user_prompt)
        used_sources = (
            []
            if draft.insufficient_evidence
            else self._sources_from_context(context_chunks, question=question)
        )

        return RagAnswerResponse(
            answer=draft.answer,
            used_sources=used_sources,
            retrieved_chunks=retrieved_chunks,
            insufficient_evidence=draft.insufficient_evidence,
            provider=draft.provider,
            model=draft.model,
            created_at=datetime.now(UTC),
        )

    def _sources_from_context(self, chunks: list[ContextChunk], question: str) -> list[RagSource]:
        selected_chunks = self._select_source_chunks(chunks, question)
        return [
            RagSource(
                document_id=chunk.source.document_id,
                document_filename=chunk.source.document_filename,
                page_number=chunk.source.page_number,
                chunk_index=chunk.source.chunk_index,
                chunk_id=chunk.source.chunk_id,
                similarity=chunk.source.similarity,
                distance=chunk.source.distance,
                text_preview=self._preview_text(chunk.text, question=question),
            )
            for chunk in selected_chunks
        ]

    def _select_source_chunks(self, chunks: list[ContextChunk], question: str) -> list[ContextChunk]:
        question_tokens = self._content_tokens(question)
        if not question_tokens:
            return chunks[:5]

        minimum_overlap = 2 if len(question_tokens) >= 2 else 1
        scored_chunks: list[tuple[int, int, ContextChunk]] = []
        for index, chunk in enumerate(chunks):
            overlap = len(self._content_tokens(chunk.text) & question_tokens)
            if overlap >= minimum_overlap:
                scored_chunks.append((overlap, index, chunk))

        if not scored_chunks:
            return chunks[:5]

        readable_scored_chunks = [
            item for item in scored_chunks if self._is_readable_context_text(item[2].text)
        ]
        if readable_scored_chunks:
            scored_chunks = readable_scored_chunks

        scored_chunks.sort(key=lambda item: (-item[0], item[1]))
        return [chunk for _, _, chunk in scored_chunks[:5]]

    def _content_tokens(self, text: str) -> set[str]:
        return {
            token
            for token in _TOKEN_RE.findall(text.lower())
            if len(token) > 2 and token not in _SOURCE_STOP_WORDS
        }

    def _is_readable_context_text(self, text: str) -> bool:
        stripped = text.strip()
        if not stripped or not stripped.endswith((".", "!", "?")):
            return False
        return stripped[0].isupper() or stripped[0].isdigit()

    def _preview_text(self, text: str, question: str = "") -> str:
        question_tokens = self._content_tokens(question)
        if question_tokens:
            minimum_overlap = 2 if len(question_tokens) >= 2 else 1
            relevant_sentences = [
                sentence
                for sentence in self.prompt_builder.cleaner.split_sentences(
                    self.prompt_builder.cleaner.normalize_whitespace(text)
                )
                if len(self._content_tokens(sentence) & question_tokens) >= minimum_overlap
            ]
            if relevant_sentences:
                return self.prompt_builder.cleaner.preview_text(" ".join(relevant_sentences[:2]), 500)

        return self.prompt_builder.cleaner.preview_text(text, 500)


rag_service = RagService(
    retriever=retrieval_service,
    llm=llm_service,
)
