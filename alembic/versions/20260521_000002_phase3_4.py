"""phase 3-4 knowledge chunks

Revision ID: 20260521_000002
Revises: 20260521_000001
Create Date: 2026-05-21 00:00:02
"""
from __future__ import annotations

import sqlalchemy as sa
from careerpilot.config import settings
from sqlalchemy.types import UserDefinedType

from alembic import op

revision = "20260521_000002"
down_revision = "20260521_000001"
branch_labels = None
depends_on = None


class VectorType(UserDefinedType):
    cache_ok = True

    def __init__(self, dimensions: int) -> None:
        self.dimensions = dimensions

    def get_col_spec(self, **_kwargs: object) -> str:
        return f"VECTOR({self.dimensions})"


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "knowledge_chunks",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column(
            "application_id",
            sa.String(length=36),
            sa.ForeignKey("applications.id"),
            nullable=True,
        ),
        sa.Column("source_id", sa.String(length=36), nullable=False),
        sa.Column("source_type", sa.String(length=50), nullable=False),
        sa.Column("source_subtype", sa.String(length=100), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("chunk_text", sa.Text(), nullable=False),
        sa.Column("token_count", sa.Integer(), nullable=False),
        sa.Column("embedding", VectorType(settings.embedding_dimensions), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "source_type",
            "source_id",
            "chunk_index",
            name="uq_knowledge_chunks_source_chunk",
        ),
    )
    op.create_index("ix_knowledge_chunks_user_id", "knowledge_chunks", ["user_id"], unique=False)
    op.create_index(
        "ix_knowledge_chunks_application_id",
        "knowledge_chunks",
        ["application_id"],
        unique=False,
    )
    op.create_index(
        "ix_knowledge_chunks_source_id",
        "knowledge_chunks",
        ["source_id"],
        unique=False,
    )
    op.create_index(
        "ix_knowledge_chunks_source_type",
        "knowledge_chunks",
        ["source_type"],
        unique=False,
    )
    op.create_index(
        "ix_knowledge_chunks_source_subtype",
        "knowledge_chunks",
        ["source_subtype"],
        unique=False,
    )
    op.create_index(
        "ix_knowledge_chunks_user_application",
        "knowledge_chunks",
        ["user_id", "application_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_knowledge_chunks_user_application", table_name="knowledge_chunks")
    op.drop_index("ix_knowledge_chunks_source_subtype", table_name="knowledge_chunks")
    op.drop_index("ix_knowledge_chunks_source_type", table_name="knowledge_chunks")
    op.drop_index("ix_knowledge_chunks_source_id", table_name="knowledge_chunks")
    op.drop_index("ix_knowledge_chunks_application_id", table_name="knowledge_chunks")
    op.drop_index("ix_knowledge_chunks_user_id", table_name="knowledge_chunks")
    op.drop_table("knowledge_chunks")
