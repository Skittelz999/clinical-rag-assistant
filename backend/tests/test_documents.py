import asyncio
from datetime import UTC, datetime
from io import BytesIO
from pathlib import Path
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from pypdf import PdfWriter
from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.embeddings import EMBEDDING_VECTOR_DIMENSIONS
from app.main import app
from app.repositories.document_repository import DocumentChunkRecord, DocumentRecord, DocumentRepository
from app.services.document_service import document_service
from app.services.embedding_service import EmbeddingError, EmbeddingService
from app.services.llm_service import DeterministicDemoLLMProvider, LLMAnswer, LLMError, LLMService
from app.services.pdf_extraction_service import NO_EXTRACTABLE_TEXT_MESSAGE
from app.services.rag_service import rag_service
from app.services.retrieval_service import retrieval_service


BACKEND_ROOT = Path(__file__).resolve().parents[1]


class FakeEmbeddingProvider:
    model_name = "fake-test-embedding"
    dimensions = EMBEDDING_VECTOR_DIMENSIONS

    def __init__(self) -> None:
        self.calls: list[list[str]] = []

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        self.calls.append(texts)
        return [self._embed_text(text) for text in texts]

    def _embed_text(self, text: str) -> list[float]:
        lower_text = text.lower()
        vector = [0.0] * EMBEDDING_VECTOR_DIMENSIONS
        vector[0] = 1.0 if "alpha" in lower_text else 0.0
        vector[1] = 1.0 if "beta" in lower_text else 0.0
        vector[2] = 1.0 if "gamma" in lower_text else 0.0
        vector[3] = 1.0
        return vector


class FailingEmbeddingProvider:
    model_name = "failing-test-embedding"
    dimensions = EMBEDDING_VECTOR_DIMENSIONS

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        raise EmbeddingError("Test embedding provider failed.")


class FakeLLMProvider:
    provider_name = "fake-llm"
    model_name = "fake-rag-model"

    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    async def generate_grounded_answer(self, system_prompt: str, user_prompt: str) -> LLMAnswer:
        self.calls.append((system_prompt, user_prompt))
        if "Context is empty." in user_prompt:
            return LLMAnswer(
                answer="The uploaded documents do not contain enough information to answer this question.",
                insufficient_evidence=True,
                provider=self.provider_name,
                model=self.model_name,
            )

        first_text_line = next(
            (line.removeprefix("Text: ").strip() for line in user_prompt.splitlines() if line.startswith("Text: ")),
            "No context text was supplied.",
        )
        return LLMAnswer(
            answer=f"Fake grounded answer from retrieved context: {first_text_line[:120]}",
            insufficient_evidence=False,
            provider=self.provider_name,
            model=self.model_name,
        )


class FailingLLMProvider:
    provider_name = "failing-llm"
    model_name = "failing-rag-model"

    async def generate_grounded_answer(self, system_prompt: str, user_prompt: str) -> LLMAnswer:
        raise LLMError("Test LLM provider failed.")


def _run_migrations(database_url: str) -> None:
    config = Config(str(BACKEND_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_ROOT / "migrations"))
    config.attributes["database_url"] = database_url
    command.upgrade(config, "head")


@pytest.fixture
def client(tmp_path) -> TestClient:
    database_path = tmp_path / "documents_test.db"
    database_url = f"sqlite+aiosqlite:///{database_path.as_posix()}"
    _run_migrations(database_url)
    engine = create_async_engine(database_url)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    original_repository = document_service.repository
    original_upload_dir = document_service.upload_dir
    original_embedder = document_service.embedder
    original_retrieval_repository = retrieval_service.repository
    original_retrieval_embedder = retrieval_service.embedder
    original_rag_retriever = rag_service.retriever
    original_rag_llm = rag_service.llm
    fake_embedding_provider = FakeEmbeddingProvider()
    fake_embedder = EmbeddingService(fake_embedding_provider)
    fake_llm_provider = FakeLLMProvider()
    fake_llm = LLMService(fake_llm_provider)
    repository = DocumentRepository(session_factory)

    document_service.repository = repository
    document_service.upload_dir = tmp_path
    document_service.embedder = fake_embedder
    retrieval_service.repository = repository
    retrieval_service.embedder = fake_embedder
    rag_service.retriever = retrieval_service
    rag_service.llm = fake_llm

    try:
        test_client = TestClient(app)
        test_client.embedding_provider = fake_embedding_provider
        test_client.llm_provider = fake_llm_provider
        yield test_client
    finally:
        document_service.repository = original_repository
        document_service.upload_dir = original_upload_dir
        document_service.embedder = original_embedder
        retrieval_service.repository = original_retrieval_repository
        retrieval_service.embedder = original_retrieval_embedder
        rag_service.retriever = original_rag_retriever
        rag_service.llm = original_rag_llm
        asyncio.run(engine.dispose())


def test_initial_migration_creates_document_tables(tmp_path) -> None:
    database_path = tmp_path / "migration_test.db"
    database_url = f"sqlite+aiosqlite:///{database_path.as_posix()}"

    _run_migrations(database_url)

    async def inspect_schema() -> dict[str, list[str]]:
        engine = create_async_engine(database_url)
        async with engine.connect() as connection:
            tables = await connection.run_sync(lambda sync_connection: inspect(sync_connection).get_table_names())
            document_columns = await connection.run_sync(
                lambda sync_connection: [
                    column["name"] for column in inspect(sync_connection).get_columns("documents")
                ]
            )
            chunk_columns = await connection.run_sync(
                lambda sync_connection: [
                    column["name"] for column in inspect(sync_connection).get_columns("document_chunks")
                ]
            )
        await engine.dispose()
        return {
            "tables": tables,
            "document_columns": document_columns,
            "chunk_columns": chunk_columns,
        }

    schema = asyncio.run(inspect_schema())

    assert "documents" in schema["tables"]
    assert "document_chunks" in schema["tables"]
    assert {"id", "filename", "status", "page_count", "chunk_count", "updated_at"}.issubset(
        schema["document_columns"]
    )
    assert {
        "embedding_status",
        "embedded_chunk_count",
        "embedding_model",
        "embedding_error",
        "embedded_at",
    }.issubset(schema["document_columns"])
    assert {"id", "document_id", "chunk_index", "page_number", "text", "char_count"}.issubset(
        schema["chunk_columns"]
    )
    assert {"embedding", "embedding_status", "embedding_model", "embedding_error", "embedded_at"}.issubset(
        schema["chunk_columns"]
    )


def _pdf_text_literal(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _build_text_pdf(page_texts: list[str]) -> bytes:
    objects: list[bytes] = [
        b"",
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    page_ids: list[int] = []

    for text in page_texts:
        escaped_text = _pdf_text_literal(text)
        content = f"BT /F1 12 Tf 72 720 Td ({escaped_text}) Tj ET".encode("ascii")
        content_id = len(objects)
        objects.append(b"<< /Length " + str(len(content)).encode("ascii") + b" >>\nstream\n")
        objects[content_id] += content + b"\nendstream"

        page_id = len(objects)
        page = (
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            f"/Resources << /Font << /F1 3 0 R >> >> /Contents {content_id} 0 R >>"
        )
        objects.append(page.encode("ascii"))
        page_ids.append(page_id)

    kids = " ".join(f"{page_id} 0 R" for page_id in page_ids)
    objects[2] = f"<< /Type /Pages /Kids [{kids}] /Count {len(page_ids)} >>".encode("ascii")

    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for object_id, content in enumerate(objects[1:], start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{object_id} 0 obj\n".encode("ascii"))
        pdf.extend(content)
        pdf.extend(b"\nendobj\n")

    xref_offset = len(pdf)
    pdf.extend(f"xref\n0 {len(objects)}\n0000000000 65535 f \n".encode("ascii"))
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    pdf.extend(
        f"trailer\n<< /Size {len(objects)} /Root 1 0 R >>\n"
        f"startxref\n{xref_offset}\n%%EOF\n".encode("ascii")
    )
    return bytes(pdf)


def _build_blank_pdf() -> bytes:
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    output = BytesIO()
    writer.write(output)
    return output.getvalue()


def _add_manual_document_with_chunk(
    repository: DocumentRepository,
    *,
    filename: str,
    status: str,
    text: str,
    embedding: list[float] | None,
    embedding_status: str,
) -> tuple[str, str]:
    document_id = str(uuid4())
    chunk_id = str(uuid4())
    now = datetime.now(UTC)

    async def add_records() -> None:
        await repository.add(
            DocumentRecord(
                id=document_id,
                filename=filename,
                original_filename=filename,
                content_type="application/pdf",
                status=status,
                size_bytes=123,
                created_at=now,
                storage_path=f"/tmp/{document_id}.pdf",
                page_count=1,
                chunk_count=1,
                extracted_char_count=len(text),
                embedding_status="embedded" if embedding is not None else "pending",
                embedded_chunk_count=1 if embedding is not None else 0,
                embedding_model=FakeEmbeddingProvider.model_name if embedding is not None else None,
            )
        )
        await repository.add_chunks(
            document_id,
            [
                DocumentChunkRecord(
                    id=chunk_id,
                    document_id=document_id,
                    chunk_index=0,
                    page_number=1,
                    text=text,
                    char_count=len(text),
                    created_at=now,
                    embedding=embedding,
                    embedding_model=FakeEmbeddingProvider.model_name if embedding is not None else None,
                    embedding_status=embedding_status,
                    embedded_at=now if embedding is not None else None,
                )
            ],
        )

    asyncio.run(add_records())
    return document_id, chunk_id


def test_upload_pdf_processes_chunks_and_list_documents(client: TestClient, tmp_path) -> None:
    pdf_text = "Clinical guideline demo text for extraction and chunking. " * 80

    upload_response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("guideline.pdf", _build_text_pdf([pdf_text]), "application/pdf")},
    )

    assert upload_response.status_code == 201
    uploaded = upload_response.json()
    assert uploaded["filename"] == "guideline.pdf"
    assert uploaded["status"] == "ready"
    assert uploaded["size_bytes"] > 0
    assert uploaded["page_count"] == 1
    assert uploaded["chunk_count"] > 0
    assert uploaded["extracted_char_count"] > 0
    assert uploaded["error_message"] is None
    assert uploaded["embedding_status"] == "embedded"
    assert uploaded["embedded_chunk_count"] == uploaded["chunk_count"]
    assert uploaded["embedding_model"] == FakeEmbeddingProvider.model_name
    assert uploaded["embedding_error"] is None
    assert uploaded["embedded_at"] is not None
    assert (tmp_path / f"{uploaded['id']}.pdf").exists()
    assert getattr(client, "embedding_provider").calls

    list_response = client.get("/api/v1/documents")

    assert list_response.status_code == 200
    assert list_response.json() == [uploaded]


def test_list_document_chunks_returns_stored_chunks(client: TestClient) -> None:
    pdf_text = "Clinical guideline chunk preview text. " * 50
    upload_response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("chunks.pdf", _build_text_pdf([pdf_text]), "application/pdf")},
    )
    uploaded = upload_response.json()

    chunks_response = client.get(f"/api/v1/documents/{uploaded['id']}/chunks")

    assert chunks_response.status_code == 200
    body = chunks_response.json()
    assert body["document_id"] == uploaded["id"]
    assert len(body["chunks"]) == uploaded["chunk_count"]
    assert body["chunks"][0]["document_id"] == uploaded["id"]
    assert body["chunks"][0]["chunk_index"] == 0
    assert body["chunks"][0]["page_number"] == 1
    assert body["chunks"][0]["char_count"] > 0
    assert "Clinical guideline chunk preview text" in body["chunks"][0]["text"]
    assert body["chunks"][0]["embedding_status"] == "embedded"
    assert body["chunks"][0]["embedding_model"] == FakeEmbeddingProvider.model_name
    assert body["chunks"][0]["embedding_error"] is None
    assert body["chunks"][0]["embedded_at"] is not None


def test_repository_can_list_data_from_new_repository_instance(client: TestClient) -> None:
    pdf_text = "Persistent repository text. " * 60
    upload_response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("persisted.pdf", _build_text_pdf([pdf_text]), "application/pdf")},
    )
    uploaded = upload_response.json()
    second_repository = DocumentRepository(document_service.repository.session_factory)

    documents = asyncio.run(second_repository.list())
    chunks = asyncio.run(second_repository.list_chunks(uploaded["id"]))

    assert [document.id for document in documents] == [uploaded["id"]]
    assert len(chunks) == uploaded["chunk_count"]
    assert chunks[0].text.startswith("Persistent repository text.")
    assert chunks[0].embedding is not None
    assert len(chunks[0].embedding) == EMBEDDING_VECTOR_DIMENSIONS
    assert chunks[0].embedding_status == "embedded"
    assert chunks[0].embedding_model == FakeEmbeddingProvider.model_name


def test_retrieval_returns_nearest_chunks_for_query(client: TestClient) -> None:
    alpha_text = "Alpha clinical guidance for retrieval ranking. " * 80
    beta_text = "Beta clinical guidance for retrieval ranking. " * 80
    upload_response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("retrieval.pdf", _build_text_pdf([alpha_text, beta_text]), "application/pdf")},
    )
    uploaded = upload_response.json()

    response = client.post("/api/v1/retrieval/search", json={"query": "alpha", "top_k": 1})

    assert response.status_code == 200
    body = response.json()
    assert body["query"] == "alpha"
    assert body["top_k"] == 1
    assert len(body["results"]) == 1
    result = body["results"][0]
    assert result["document_id"] == uploaded["id"]
    assert result["document_filename"] == "retrieval.pdf"
    assert result["page_number"] == 1
    assert result["chunk_index"] == 0
    assert "Alpha clinical guidance" in result["text"]
    assert result["distance"] < 0.01
    assert result["similarity"] > 0.99
    assert result["embedding_model"] == FakeEmbeddingProvider.model_name
    assert getattr(client, "embedding_provider").calls[-1] == ["alpha"]


def test_retrieval_ignores_chunks_without_embeddings(client: TestClient) -> None:
    provider = getattr(client, "embedding_provider")
    embedded_document_id, embedded_chunk_id = _add_manual_document_with_chunk(
        document_service.repository,
        filename="embedded.pdf",
        status="ready",
        text="Alpha embedded chunk.",
        embedding=provider._embed_text("Alpha embedded chunk."),
        embedding_status="embedded",
    )
    pending_document_id, pending_chunk_id = _add_manual_document_with_chunk(
        document_service.repository,
        filename="pending.pdf",
        status="ready",
        text="Alpha pending chunk without an embedding.",
        embedding=None,
        embedding_status="pending",
    )

    response = client.post("/api/v1/retrieval/search", json={"query": "alpha", "top_k": 5})

    assert response.status_code == 200
    result_chunk_ids = [result["chunk_id"] for result in response.json()["results"]]
    result_document_ids = [result["document_id"] for result in response.json()["results"]]
    assert embedded_chunk_id in result_chunk_ids
    assert embedded_document_id in result_document_ids
    assert pending_chunk_id not in result_chunk_ids
    assert pending_document_id not in result_document_ids


def test_retrieval_ignores_documents_that_are_not_ready(client: TestClient) -> None:
    provider = getattr(client, "embedding_provider")
    processing_document_id, processing_chunk_id = _add_manual_document_with_chunk(
        document_service.repository,
        filename="processing.pdf",
        status="processing",
        text="Alpha processing chunk with embedding.",
        embedding=provider._embed_text("Alpha processing chunk with embedding."),
        embedding_status="embedded",
    )

    response = client.post("/api/v1/retrieval/search", json={"query": "alpha", "top_k": 5})

    assert response.status_code == 200
    assert response.json()["results"] == []
    assert processing_document_id
    assert processing_chunk_id


def test_retrieval_respects_top_k(client: TestClient) -> None:
    provider = getattr(client, "embedding_provider")
    for index in range(3):
        _add_manual_document_with_chunk(
            document_service.repository,
            filename=f"alpha-{index}.pdf",
            status="ready",
            text=f"Alpha top k chunk {index}.",
            embedding=provider._embed_text(f"Alpha top k chunk {index}."),
            embedding_status="embedded",
        )

    response = client.post("/api/v1/retrieval/search", json={"query": "alpha", "top_k": 2})

    assert response.status_code == 200
    assert len(response.json()["results"]) == 2


def test_retrieval_rejects_empty_query(client: TestClient) -> None:
    response = client.post("/api/v1/retrieval/search", json={"query": "   ", "top_k": 5})

    assert response.status_code == 422


def test_retrieval_endpoint_returns_stable_error_when_query_embedding_fails(
    client: TestClient,
) -> None:
    original_embedder = retrieval_service.embedder
    retrieval_service.embedder = EmbeddingService(FailingEmbeddingProvider())

    try:
        response = client.post("/api/v1/retrieval/search", json={"query": "alpha", "top_k": 1})
    finally:
        retrieval_service.embedder = original_embedder

    assert response.status_code == 502
    assert response.json()["detail"] == "Embedding provider failed: Test embedding provider failed."


def test_rag_endpoint_returns_answer_with_sources(client: TestClient) -> None:
    alpha_text = "Alpha treatment guidance appears in this uploaded document. " * 80
    upload_response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("rag-alpha.pdf", _build_text_pdf([alpha_text]), "application/pdf")},
    )
    uploaded = upload_response.json()

    response = client.post("/api/v1/rag/answer", json={"question": "What does alpha say?", "top_k": 3})

    assert response.status_code == 200
    body = response.json()
    assert body["insufficient_evidence"] is False
    assert body["provider"] == FakeLLMProvider.provider_name
    assert body["model"] == FakeLLMProvider.model_name
    assert "Fake grounded answer" in body["answer"]
    assert body["used_sources"]
    assert body["used_sources"][0]["document_id"] == uploaded["id"]
    assert body["used_sources"][0]["document_filename"] == "rag-alpha.pdf"
    assert body["used_sources"][0]["page_number"] == 1
    assert body["used_sources"][0]["chunk_id"] == body["retrieved_chunks"][0]["chunk_id"]
    assert "Alpha treatment guidance" in body["used_sources"][0]["text_preview"]
    assert getattr(client, "llm_provider").calls
    system_prompt, user_prompt = getattr(client, "llm_provider").calls[-1]
    assert "Answer only from the provided context" in system_prompt
    assert "Do not repeat the same fact" in system_prompt
    assert "Alpha treatment guidance" in user_prompt
    assert user_prompt.count("Alpha treatment guidance appears in this uploaded document.") == 1


def test_rag_context_cleanup_preserves_source_metadata(client: TestClient) -> None:
    provider = getattr(client, "embedding_provider")
    repeated_text = (
        "Alpha emergency warning signs require urgent review. "
        "Alpha emergency warning signs require urgent review. "
        "Follow-up should happen after the warning signs are addressed."
    )
    document_id, chunk_id = _add_manual_document_with_chunk(
        document_service.repository,
        filename="rag-cleanup.pdf",
        status="ready",
        text=repeated_text,
        embedding=provider._embed_text(repeated_text),
        embedding_status="embedded",
    )

    response = client.post(
        "/api/v1/rag/answer",
        json={"question": "What alpha emergency warning signs are listed?", "top_k": 1},
    )

    assert response.status_code == 200
    body = response.json()
    source = body["used_sources"][0]
    assert source["document_id"] == document_id
    assert source["chunk_id"] == chunk_id
    assert source["document_filename"] == "rag-cleanup.pdf"
    assert source["page_number"] == 1
    assert source["chunk_index"] == 0
    assert source["text_preview"].count("Alpha emergency warning signs require urgent review.") == 1

    _, user_prompt = getattr(client, "llm_provider").calls[-1]
    assert user_prompt.count("Alpha emergency warning signs require urgent review.") == 1
    assert "Follow-up should happen after the warning signs are addressed." in user_prompt


def test_rag_context_cleanup_trims_leading_chunk_fragment(client: TestClient) -> None:
    provider = getattr(client, "embedding_provider")
    fragment_text = (
        "egnancy without specialist review. "
        "Alpha emergency warning signs include chest pain and fainting."
    )
    _add_manual_document_with_chunk(
        document_service.repository,
        filename="rag-fragment.pdf",
        status="ready",
        text=fragment_text,
        embedding=provider._embed_text(fragment_text),
        embedding_status="embedded",
    )

    response = client.post(
        "/api/v1/rag/answer",
        json={"question": "What alpha emergency warning signs are listed?", "top_k": 1},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["used_sources"][0]["text_preview"].startswith("Alpha emergency warning signs")

    _, user_prompt = getattr(client, "llm_provider").calls[-1]
    assert "egnancy without specialist review" not in user_prompt
    assert "Alpha emergency warning signs include chest pain and fainting." in user_prompt


def test_deterministic_llm_provider_returns_readable_non_repetitive_answer() -> None:
    provider = DeterministicDemoLLMProvider()
    user_prompt = (
        "Question: What emergency warning signs and urgent review are listed?\n\n"
        "Context:\n"
        "[Source 1]\n"
        "Text: -line treatment first-line management Emergency warning signs urgent escalation. "
        "Follow-up should occur within one week. "
        "Emergency warning signs include chest pain. "
        "Emergency warning signs include chest pain. Seek urgent review for severe symptoms.\n\n"
        "Return JSON with answer and insufficient_evidence."
    )

    answer = asyncio.run(
        provider.generate_grounded_answer(system_prompt="Answer concisely.", user_prompt=user_prompt)
    )

    assert answer.insufficient_evidence is False
    assert answer.answer.startswith("Based on the uploaded documents:")
    assert "Text:" not in answer.answer
    assert "-line treatment" not in answer.answer
    assert "Follow-up should occur within one week." not in answer.answer
    assert answer.answer.count("Emergency warning signs include chest pain.") == 1
    assert "Seek urgent review for severe symptoms." in answer.answer


def test_deterministic_llm_provider_handles_empty_context() -> None:
    provider = DeterministicDemoLLMProvider()

    answer = asyncio.run(
        provider.generate_grounded_answer(
            system_prompt="Answer concisely.",
            user_prompt="Question: What warning signs are listed?\n\nContext:\n[Source 1]\nText:    ",
        )
    )

    assert answer.insufficient_evidence is True
    assert answer.answer == "The uploaded documents do not contain enough information to answer this question."


def test_rag_endpoint_handles_insufficient_evidence(client: TestClient) -> None:
    response = client.post("/api/v1/rag/answer", json={"question": "What does gamma say?", "top_k": 5})

    assert response.status_code == 200
    body = response.json()
    assert body["insufficient_evidence"] is True
    assert body["answer"] == "The uploaded documents do not contain enough information to answer this question."
    assert body["used_sources"] == []
    assert body["retrieved_chunks"] == []
    assert getattr(client, "llm_provider").calls == []


def test_rag_endpoint_respects_top_k(client: TestClient) -> None:
    provider = getattr(client, "embedding_provider")
    for index in range(3):
        _add_manual_document_with_chunk(
            document_service.repository,
            filename=f"rag-top-k-{index}.pdf",
            status="ready",
            text=f"Alpha RAG top k chunk {index}.",
            embedding=provider._embed_text(f"Alpha RAG top k chunk {index}."),
            embedding_status="embedded",
        )

    response = client.post("/api/v1/rag/answer", json={"question": "alpha", "top_k": 2})

    assert response.status_code == 200
    body = response.json()
    assert len(body["retrieved_chunks"]) == 2
    assert len(body["used_sources"]) == 2


def test_rag_endpoint_rejects_empty_question(client: TestClient) -> None:
    response = client.post("/api/v1/rag/answer", json={"question": "   ", "top_k": 5})

    assert response.status_code == 422


def test_rag_endpoint_returns_stable_error_when_llm_fails(client: TestClient) -> None:
    provider = getattr(client, "embedding_provider")
    _add_manual_document_with_chunk(
        document_service.repository,
        filename="rag-provider-failure.pdf",
        status="ready",
        text="Alpha context that should reach the failing LLM.",
        embedding=provider._embed_text("Alpha context that should reach the failing LLM."),
        embedding_status="embedded",
    )
    original_llm = rag_service.llm
    rag_service.llm = LLMService(FailingLLMProvider())

    try:
        response = client.post("/api/v1/rag/answer", json={"question": "alpha", "top_k": 1})
    finally:
        rag_service.llm = original_llm

    assert response.status_code == 502
    assert response.json()["detail"] == "Answer generation provider failed: Test LLM provider failed."


def test_rag_endpoint_returns_stable_error_when_query_embedding_fails(client: TestClient) -> None:
    original_embedder = retrieval_service.embedder
    retrieval_service.embedder = EmbeddingService(FailingEmbeddingProvider())

    try:
        response = client.post("/api/v1/rag/answer", json={"question": "alpha", "top_k": 1})
    finally:
        retrieval_service.embedder = original_embedder

    assert response.status_code == 502
    assert response.json()["detail"] == "Embedding provider failed: Test embedding provider failed."


def test_embedding_failure_marks_document_failed(client: TestClient) -> None:
    original_embedder = document_service.embedder
    document_service.embedder = EmbeddingService(FailingEmbeddingProvider())

    try:
        response = client.post(
            "/api/v1/documents/upload",
            files={
                "file": (
                    "embedding-failure.pdf",
                    _build_text_pdf(["Embedding failure text. " * 80]),
                    "application/pdf",
                )
            },
        )
    finally:
        document_service.embedder = original_embedder

    assert response.status_code == 201
    uploaded = response.json()
    assert uploaded["status"] == "failed"
    assert uploaded["chunk_count"] > 0
    assert uploaded["embedding_status"] == "failed"
    assert uploaded["embedded_chunk_count"] == 0
    assert uploaded["embedding_model"] == FailingEmbeddingProvider.model_name
    assert uploaded["embedding_error"] == "Test embedding provider failed."
    assert uploaded["error_message"] == "Embedding generation failed: Test embedding provider failed."

    chunks = asyncio.run(document_service.repository.list_chunks(uploaded["id"]))
    assert chunks
    assert chunks[0].embedding is None
    assert chunks[0].embedding_status == "failed"
    assert chunks[0].embedding_error == "Test embedding provider failed."


def test_rejects_non_pdf_upload(client: TestClient) -> None:

    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("notes.txt", b"not a pdf", "text/plain")},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Only PDF files are supported."


def test_rejects_empty_pdf(client: TestClient) -> None:

    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("empty.pdf", b"", "application/pdf")},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Uploaded PDF cannot be empty."


def test_rejects_large_pdf(client: TestClient) -> None:
    oversized_pdf = b"%PDF-1.4\n" + (b"0" * (10 * 1024 * 1024))

    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("large.pdf", oversized_pdf, "application/pdf")},
    )

    assert response.status_code == 413
    assert response.json()["detail"] == "PDF files must be 10 MB or smaller."


def test_pdf_with_no_extractable_text_results_in_failed_status(client: TestClient) -> None:

    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("blank.pdf", _build_blank_pdf(), "application/pdf")},
    )

    assert response.status_code == 201
    uploaded = response.json()
    assert uploaded["status"] == "failed"
    assert uploaded["chunk_count"] == 0
    assert uploaded["extracted_char_count"] == 0
    assert uploaded["error_message"] == NO_EXTRACTABLE_TEXT_MESSAGE

    chunks_response = client.get(f"/api/v1/documents/{uploaded['id']}/chunks")
    assert chunks_response.status_code == 200
    assert chunks_response.json()["chunks"] == []


def test_invalid_document_id_returns_404(client: TestClient) -> None:
    response = client.get("/api/v1/documents/missing-document/chunks")

    assert response.status_code == 404
    assert response.json()["detail"] == "Document not found."

    document_response = client.get("/api/v1/documents/missing-document")
    assert document_response.status_code == 404
    assert document_response.json()["detail"] == "Document not found."
