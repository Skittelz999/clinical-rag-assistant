"""Add pgvector embeddings for document chunks.

Revision ID: 0002_add_chunk_embeddings
Revises: 0001_initial_documents
Create Date: 2026-05-24 00:00:00
"""

from collections.abc import Sequence

from alembic import op
from pgvector.sqlalchemy import Vector
import sqlalchemy as sa
from sqlalchemy import inspect

from app.core.embeddings import EMBEDDING_VECTOR_DIMENSIONS

revision: str = "0002_add_chunk_embeddings"
down_revision: str | None = "0001_initial_documents"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _dialect_name() -> str:
    return op.get_bind().dialect.name


def _column_names(table_name: str) -> set[str]:
    inspector = inspect(op.get_bind())
    if not inspector.has_table(table_name):
        return set()
    return {column["name"] for column in inspector.get_columns(table_name)}


def _add_column_if_missing(table_name: str, column: sa.Column) -> None:
    if column.name not in _column_names(table_name):
        op.add_column(table_name, column)


def _drop_column_if_present(table_name: str, column_name: str) -> None:
    if column_name in _column_names(table_name):
        op.drop_column(table_name, column_name)


def upgrade() -> None:
    if _dialect_name() == "postgresql":
        op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    _add_column_if_missing(
        "documents",
        sa.Column(
            "embedding_status",
            sa.String(length=32),
            nullable=False,
            server_default="not_started",
        ),
    )
    _add_column_if_missing(
        "documents",
        sa.Column("embedded_chunk_count", sa.Integer(), nullable=False, server_default="0"),
    )
    _add_column_if_missing("documents", sa.Column("embedding_model", sa.String(length=120), nullable=True))
    _add_column_if_missing("documents", sa.Column("embedding_error", sa.Text(), nullable=True))
    _add_column_if_missing("documents", sa.Column("embedded_at", sa.DateTime(timezone=True), nullable=True))

    _add_column_if_missing(
        "document_chunks",
        sa.Column("embedding", Vector(EMBEDDING_VECTOR_DIMENSIONS), nullable=True),
    )
    _add_column_if_missing(
        "document_chunks",
        sa.Column("embedding_model", sa.String(length=120), nullable=True),
    )
    _add_column_if_missing(
        "document_chunks",
        sa.Column("embedding_status", sa.String(length=32), nullable=False, server_default="pending"),
    )
    _add_column_if_missing("document_chunks", sa.Column("embedding_error", sa.Text(), nullable=True))
    _add_column_if_missing("document_chunks", sa.Column("embedded_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    _drop_column_if_present("document_chunks", "embedded_at")
    _drop_column_if_present("document_chunks", "embedding_error")
    _drop_column_if_present("document_chunks", "embedding_status")
    _drop_column_if_present("document_chunks", "embedding_model")
    _drop_column_if_present("document_chunks", "embedding")
    _drop_column_if_present("documents", "embedded_at")
    _drop_column_if_present("documents", "embedding_error")
    _drop_column_if_present("documents", "embedding_model")
    _drop_column_if_present("documents", "embedded_chunk_count")
    _drop_column_if_present("documents", "embedding_status")

