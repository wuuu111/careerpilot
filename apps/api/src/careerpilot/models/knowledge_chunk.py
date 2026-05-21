from __future__ import annotations

import json
from collections.abc import Sequence
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import UserDefinedType

from careerpilot.config import settings
from careerpilot.db import Base
from careerpilot.utils import new_id, utcnow


class VectorType(UserDefinedType):
    cache_ok = True

    def __init__(self, dimensions: int) -> None:
        self.dimensions = dimensions

    def get_col_spec(self, **_kwargs: object) -> str:
        return f"VECTOR({self.dimensions})"

    def bind_processor(self, _dialect: object) -> Any:
        def process(value: Sequence[float] | None) -> str | None:
            if value is None:
                return None
            return format_vector(value)

        return process

    def result_processor(self, _dialect: object, _coltype: object) -> Any:
        def process(value: object) -> list[float] | None:
            if value is None:
                return None
            if isinstance(value, str):
                return [float(component) for component in json.loads(value)]
            if isinstance(value, Sequence):
                return [float(component) for component in value]
            raise TypeError(f"Unsupported vector payload: {type(value)!r}")

        return process


def format_vector(values: Sequence[float]) -> str:
    return "[" + ",".join(f"{float(value):.12g}" for value in values) + "]"


class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"
    __table_args__ = (
        UniqueConstraint(
            "source_type",
            "source_id",
            "chunk_index",
            name="uq_knowledge_chunks_source_chunk",
        ),
        Index("ix_knowledge_chunks_user_application", "user_id", "application_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    application_id: Mapped[str | None] = mapped_column(
        ForeignKey("applications.id"),
        index=True,
        nullable=True,
    )
    source_id: Mapped[str] = mapped_column(String(36), index=True)
    source_type: Mapped[str] = mapped_column(String(50), index=True)
    source_subtype: Mapped[str] = mapped_column(String(100), index=True)
    chunk_index: Mapped[int] = mapped_column(Integer)
    chunk_text: Mapped[str] = mapped_column(Text)
    token_count: Mapped[int] = mapped_column(Integer)
    embedding: Mapped[list[float]] = mapped_column(VectorType(settings.embedding_dimensions))
    chunk_metadata: Mapped[dict[str, object]] = mapped_column("metadata", JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
