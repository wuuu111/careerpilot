from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from careerpilot.models.knowledge_chunk import KnowledgeChunk, format_vector
from careerpilot.services.embeddings import EmbeddingProvider, get_embedding_provider
from sqlalchemy.orm import Session


class KnowledgeRetrievalService:
    def __init__(self, *, embeddings: EmbeddingProvider | None = None) -> None:
        self.embeddings = embeddings or get_embedding_provider()

    def search(
        self,
        session: Session,
        *,
        query: str,
        user_id: str,
        application_id: str | None = None,
        source_types: Sequence[str] | None = None,
        limit: int = 5,
    ) -> list[dict[str, object]]:
        if limit <= 0 or not query.strip():
            return []

        query_embedding = self.embeddings.embed([query])[0]
        if session.bind is not None and session.bind.dialect.name == "postgresql":
            return self._search_postgres(
                session,
                query_embedding=query_embedding,
                user_id=user_id,
                application_id=application_id,
                source_types=source_types,
                limit=limit,
            )
        return self._search_fallback(
            session,
            query_embedding=query_embedding,
            user_id=user_id,
            application_id=application_id,
            source_types=source_types,
            limit=limit,
        )

    def _base_statement(
        self,
        *,
        user_id: str,
        application_id: str | None,
        source_types: Sequence[str] | None,
    ) -> sa.Select[tuple[KnowledgeChunk]]:
        statement = sa.select(KnowledgeChunk).where(*self._filters(
            user_id=user_id,
            application_id=application_id,
            source_types=source_types,
        ))
        return statement

    def _filters(
        self,
        *,
        user_id: str,
        application_id: str | None,
        source_types: Sequence[str] | None,
    ) -> list[sa.ColumnElement[bool]]:
        filters: list[sa.ColumnElement[bool]] = [KnowledgeChunk.user_id == user_id]
        if application_id is not None:
            filters.append(
                sa.or_(
                    KnowledgeChunk.application_id == application_id,
                    KnowledgeChunk.application_id.is_(None),
                )
            )
        if source_types:
            filters.append(KnowledgeChunk.source_type.in_(list(source_types)))
        return filters

    def _search_postgres(
        self,
        session: Session,
        *,
        query_embedding: Sequence[float],
        user_id: str,
        application_id: str | None,
        source_types: Sequence[str] | None,
        limit: int,
    ) -> list[dict[str, object]]:
        vector_literal = format_vector(query_embedding)
        query_value = sa.cast(sa.literal(vector_literal), KnowledgeChunk.embedding.type)
        distance = KnowledgeChunk.embedding.op("<->")(query_value)
        statement = (
            sa.select(KnowledgeChunk, distance.label("distance"))
            .where(*self._filters(
                user_id=user_id,
                application_id=application_id,
                source_types=source_types,
            ))
            .order_by(
                distance,
                KnowledgeChunk.source_id,
                KnowledgeChunk.chunk_index,
                KnowledgeChunk.id,
            )
            .limit(limit)
        )
        rows = session.execute(statement).all()
        return [
            self._serialize_match(chunk, 1.0 / (1.0 + float(raw_distance)))
            for chunk, raw_distance in rows
        ]

    def _search_fallback(
        self,
        session: Session,
        *,
        query_embedding: Sequence[float],
        user_id: str,
        application_id: str | None,
        source_types: Sequence[str] | None,
        limit: int,
    ) -> list[dict[str, object]]:
        statement = self._base_statement(
            user_id=user_id,
            application_id=application_id,
            source_types=source_types,
        )
        chunks = session.scalars(statement).all()
        ranked = sorted(
            (
                (self._cosine_similarity(query_embedding, chunk.embedding), chunk)
                for chunk in chunks
            ),
            key=lambda item: (
                -item[0],
                item[1].source_id,
                item[1].chunk_index,
                item[1].id,
            ),
        )
        return [
            self._serialize_match(chunk, score)
            for score, chunk in ranked[:limit]
        ]

    def _serialize_match(self, chunk: KnowledgeChunk, score: float) -> dict[str, object]:
        return {
            "chunk_id": chunk.id,
            "source_id": chunk.source_id,
            "source_type": chunk.source_type,
            "source_subtype": chunk.source_subtype,
            "application_id": chunk.application_id,
            "chunk_index": chunk.chunk_index,
            "chunk_text": chunk.chunk_text,
            "token_count": chunk.token_count,
            "metadata": chunk.chunk_metadata,
            "score": score,
        }

    @staticmethod
    def _cosine_similarity(left: Sequence[float], right: Sequence[float]) -> float:
        if not left or not right:
            return 0.0
        return float(
            sum(
                left_value * right_value
                for left_value, right_value in zip(left, right, strict=False)
            )
        )
