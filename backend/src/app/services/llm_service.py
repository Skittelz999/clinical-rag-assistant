"""LLM provider abstraction for grounded answer generation."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Protocol

from openai import AsyncOpenAI

from app.core.config import settings

_DEMO_STOP_WORDS = {
    "about",
    "after",
    "also",
    "and",
    "are",
    "does",
    "for",
    "from",
    "how",
    "into",
    "listed",
    "say",
    "says",
    "should",
    "the",
    "this",
    "what",
    "when",
    "where",
    "which",
    "with",
}


class LLMError(Exception):
    pass


@dataclass(frozen=True)
class LLMAnswer:
    answer: str
    insufficient_evidence: bool
    provider: str
    model: str


class LLMProvider(Protocol):
    provider_name: str
    model_name: str

    async def generate_grounded_answer(self, system_prompt: str, user_prompt: str) -> LLMAnswer:
        pass


class DeterministicDemoLLMProvider:
    provider_name = "deterministic"
    model_name = "deterministic-demo-llm-v1"

    async def generate_grounded_answer(self, system_prompt: str, user_prompt: str) -> LLMAnswer:
        if "Context is empty." in user_prompt:
            return self._insufficient_answer()

        context_sentences = self._extract_context_sentences(user_prompt)
        if not context_sentences:
            return self._insufficient_answer()

        answer_sentences = self._select_relevant_sentences(
            context_sentences,
            self._extract_question_tokens(user_prompt),
        )
        if not answer_sentences:
            return self._insufficient_answer()

        answer_text = self._trim_answer(" ".join(answer_sentences[:3]))
        return LLMAnswer(
            answer=f"Based on the uploaded documents: {answer_text}",
            insufficient_evidence=False,
            provider=self.provider_name,
            model=self.model_name,
        )

    def _insufficient_answer(self) -> LLMAnswer:
        return LLMAnswer(
            answer="The uploaded documents do not contain enough information to answer this question.",
            insufficient_evidence=True,
            provider=self.provider_name,
            model=self.model_name,
        )

    def _extract_context_sentences(self, user_prompt: str) -> list[str]:
        seen_sentence_keys: set[str] = set()
        sentences: list[str] = []

        for line in user_prompt.splitlines():
            if line.startswith("Text: "):
                for sentence in self._split_sentences(line.removeprefix("Text: ")):
                    sentence_key = self._sentence_key(sentence)
                    if sentence_key and sentence_key not in seen_sentence_keys:
                        seen_sentence_keys.add(sentence_key)
                        sentences.append(sentence)

        return sentences

    def _extract_question_tokens(self, user_prompt: str) -> set[str]:
        for line in user_prompt.splitlines():
            if line.startswith("Question: "):
                return self._content_tokens(line.removeprefix("Question: "))
        return set()

    def _select_relevant_sentences(
        self,
        sentences: list[str],
        question_tokens: set[str],
    ) -> list[str]:
        if not question_tokens:
            return sentences[:3]

        minimum_overlap = 2 if len(question_tokens) >= 2 else 1
        ranked_sentences: list[tuple[int, int, str]] = []
        for index, sentence in enumerate(sentences):
            overlap = len(self._content_tokens(sentence) & question_tokens)
            if overlap >= minimum_overlap:
                ranked_sentences.append((overlap, index, sentence))

        readable_ranked_sentences = [
            item for item in ranked_sentences if self._is_readable_sentence(item[2])
        ]
        if readable_ranked_sentences:
            ranked_sentences = readable_ranked_sentences

        ranked_sentences.sort(key=lambda item: (-item[0], item[1]))
        return self._deduplicate_sentences([sentence for _, _, sentence in ranked_sentences])[:3]

    def _split_sentences(self, text: str) -> list[str]:
        normalized = self._normalize_whitespace(text)
        if not normalized:
            return []
        return [
            sentence.strip()
            for sentence in re.split(r"(?<=[.!?])\s+", normalized)
            if sentence.strip()
        ]

    def _sentence_key(self, sentence: str) -> str:
        return " ".join(re.findall(r"[a-z0-9]+", sentence.lower()))

    def _content_tokens(self, text: str) -> set[str]:
        return {
            token
            for token in re.findall(r"[a-z0-9]+", text.lower())
            if len(token) > 2 and token not in _DEMO_STOP_WORDS
        }

    def _is_readable_sentence(self, sentence: str) -> bool:
        stripped = sentence.strip()
        if len(stripped) > 450 or not stripped.endswith((".", "!", "?")):
            return False
        return bool(stripped) and (stripped[0].isupper() or stripped[0].isdigit())

    def _deduplicate_sentences(self, sentences: list[str]) -> list[str]:
        selected_sentences: list[str] = []
        selected_tokens: list[set[str]] = []
        for sentence in sentences:
            tokens = self._content_tokens(sentence)
            if not tokens:
                continue
            if any(len(tokens & seen) / max(len(tokens), len(seen)) >= 0.85 for seen in selected_tokens):
                continue
            selected_sentences.append(sentence)
            selected_tokens.append(tokens)
        return selected_sentences

    def _normalize_whitespace(self, text: str) -> str:
        return " ".join(text.split())

    def _trim_answer(self, text: str, max_chars: int = 750) -> str:
        normalized = self._normalize_whitespace(text)
        if len(normalized) <= max_chars:
            return normalized

        sentence_boundary = max(
            normalized.rfind(". ", 0, max_chars),
            normalized.rfind("! ", 0, max_chars),
            normalized.rfind("? ", 0, max_chars),
        )
        if sentence_boundary >= 120:
            return f"{normalized[: sentence_boundary + 1].strip()}..."

        word_boundary = normalized.rfind(" ", 0, max_chars)
        if word_boundary >= 80:
            return f"{normalized[:word_boundary].strip()}..."

        return f"{normalized[:max_chars].strip()}..."


class OpenAILLMProvider:
    provider_name = "openai"

    def __init__(self, api_key: str | None, model_name: str) -> None:
        self.api_key = api_key
        self.model_name = model_name
        self._client: AsyncOpenAI | None = None

    async def generate_grounded_answer(self, system_prompt: str, user_prompt: str) -> LLMAnswer:
        if not self.api_key or self.api_key == "replace-me":
            raise LLMError("OPENAI_API_KEY is required when LLM_PROVIDER=openai.")

        try:
            response = await self._get_client().chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0,
                response_format={"type": "json_object"},
            )
        except Exception as exc:
            raise LLMError("LLM provider request failed.") from exc

        content = response.choices[0].message.content or "{}"
        try:
            payload = json.loads(content)
        except json.JSONDecodeError as exc:
            raise LLMError("LLM provider returned invalid JSON.") from exc

        answer = payload.get("answer")
        insufficient_evidence = payload.get("insufficient_evidence")
        if not isinstance(answer, str) or not isinstance(insufficient_evidence, bool):
            raise LLMError("LLM provider returned an unexpected response shape.")

        return LLMAnswer(
            answer=answer,
            insufficient_evidence=insufficient_evidence,
            provider=self.provider_name,
            model=self.model_name,
        )

    def _get_client(self) -> AsyncOpenAI:
        if self._client is None:
            self._client = AsyncOpenAI(api_key=self.api_key)
        return self._client


class LLMService:
    def __init__(self, provider: LLMProvider) -> None:
        self.provider = provider

    async def generate_grounded_answer(self, system_prompt: str, user_prompt: str) -> LLMAnswer:
        return await self.provider.generate_grounded_answer(system_prompt, user_prompt)


def build_llm_provider() -> LLMProvider:
    provider = settings.llm_provider.lower().strip()
    if provider == "openai":
        return OpenAILLMProvider(
            api_key=settings.openai_api_key,
            model_name=settings.openai_chat_model,
        )
    if provider in {"deterministic", "demo", "local"}:
        return DeterministicDemoLLMProvider()

    raise ValueError(f"Unsupported LLM_PROVIDER value: {settings.llm_provider}")


llm_service = LLMService(build_llm_provider())
