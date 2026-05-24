"""Initial document and chunk tables.

Revision ID: 0001_initial_documents
Revises:
Create Date: 2026-05-23 00:00:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision: str = "0001_initial_documents"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _has_table(table_name: str) -> bool:
    return inspect(op.get_bind()).has_table(table_name)


def _has_index(table_name: str, index_name: str) -> bool:
    if not _has_table(table_name):
        return False
    return any(index["name"] == index_name for index in inspect(op.get_bind()).get_indexes(table_name))


def _create_index_if_missing(index_name: str, table_name: str, columns: list[str]) -> None:
    if not _has_index(table_name, index_name):
        op.create_index(index_name, table_name, columns)


def upgrade() -> None:
    if not _has_table("documents"):
        op.create_table(
            "documents",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("filename", sa.String(length=255), nullable=False),
            sa.Column("original_filename", sa.String(length=255), nullable=True),
            sa.Column("storage_path", sa.Text(), nullable=False),
            sa.Column("content_type", sa.String(length=120), nullable=True),
            sa.Column("size_bytes", sa.Integer(), nullable=False),
            sa.Column("status", sa.String(length=32), nullable=False),
            sa.Column("page_count", sa.Integer(), nullable=False),
            sa.Column("chunk_count", sa.Integer(), nullable=False),
            sa.Column("extracted_char_count", sa.Integer(), nullable=False),
            sa.Column("error_message", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )

    if not _has_table("document_chunks"):
        op.create_table(
            "document_chunks",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("document_id", sa.String(length=36), nullable=False),
            sa.Column("chunk_index", sa.Integer(), nullable=False),
            sa.Column("page_number", sa.Integer(), nullable=False),
            sa.Column("text", sa.Text(), nullable=False),
            sa.Column("char_count", sa.Integer(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )

    _create_index_if_missing("ix_documents_status", "documents", ["status"])
    _create_index_if_missing("ix_document_chunks_document_id", "document_chunks", ["document_id"])
    _create_index_if_missing(
        "ix_document_chunks_document_id_chunk_index",
        "document_chunks",
        ["document_id", "chunk_index"],
    )


def downgrade() -> None:
    if _has_index("document_chunks", "ix_document_chunks_document_id_chunk_index"):
        op.drop_index("ix_document_chunks_document_id_chunk_index", table_name="document_chunks")
    if _has_index("document_chunks", "ix_document_chunks_document_id"):
        op.drop_index("ix_document_chunks_document_id", table_name="document_chunks")
    if _has_index("documents", "ix_documents_status"):
        op.drop_index("ix_documents_status", table_name="documents")
    if _has_table("document_chunks"):
        op.drop_table("document_chunks")
    if _has_table("documents"):
        op.drop_table("documents")
