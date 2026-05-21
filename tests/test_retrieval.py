from __future__ import annotations

from datetime import UTC, datetime

from careerpilot.config import settings
from careerpilot.domain.documents import KnowledgeDocument
from careerpilot.models.auth import User
from careerpilot.services.chunking import TextChunker
from careerpilot.services.embeddings import DeterministicEmbeddingProvider
from careerpilot.services.knowledge import KnowledgeIngestionService, KnowledgeRetrievalService


def _document(
    *,
    user_id: str,
    source_id: str,
    source_type: str,
    source_subtype: str,
    text: str,
    application_id: str | None = None,
) -> KnowledgeDocument:
    metadata = {
        "user_id": user_id,
        "source_id": source_id,
        "source_type": source_type,
        "source_subtype": source_subtype,
        "created_at": datetime(2026, 5, 21, tzinfo=UTC).isoformat(),
    }
    if application_id is not None:
        metadata["application_id"] = application_id
    return KnowledgeDocument(embedding_text=text, metadata=metadata)


def test_retrieval_ranks_relevant_chunks_and_enforces_scope(db_session) -> None:
    db_session.add_all(
        [
            User(id="user-1", name="Ada", email="ada@example.com", password_hash="pw"),
            User(id="user-2", name="Grace", email="grace@example.com", password_hash="pw"),
        ]
    )
    db_session.commit()

    embeddings = DeterministicEmbeddingProvider(dimensions=settings.embedding_dimensions)
    ingestion = KnowledgeIngestionService(
        chunker=TextChunker(target_tokens=12, overlap_tokens=2),
        embeddings=embeddings,
    )
    retrieval = KnowledgeRetrievalService(embeddings=embeddings)

    ingestion.ingest_document(
        db_session,
        _document(
            user_id="user-1",
            source_id="resume-1",
            source_type="resume",
            source_subtype="resume_document",
            application_id="app-1",
            text="python fastapi agents retrieval ranking orchestration",
        ),
    )
    ingestion.ingest_document(
        db_session,
        _document(
            user_id="user-1",
            source_id="resume-2",
            source_type="resume",
            source_subtype="resume_document",
            application_id="app-2",
            text="brand marketing social campaigns content analytics",
        ),
    )
    ingestion.ingest_document(
        db_session,
        _document(
            user_id="user-2",
            source_id="resume-3",
            source_type="resume",
            source_subtype="resume_document",
            application_id="app-1",
            text="python fastapi agents retrieval ranking orchestration",
        ),
    )

    matches = retrieval.search(
        db_session,
        query="python fastapi retrieval agents",
        user_id="user-1",
        application_id="app-1",
        limit=3,
    )

    assert [match["source_id"] for match in matches] == ["resume-1"]
    assert matches[0]["source_type"] == "resume"
    assert matches[0]["application_id"] == "app-1"
    assert matches[0]["score"] > 0


def test_retrieval_fallback_order_is_deterministic_for_tied_scores(db_session) -> None:
    db_session.add(User(id="user-1", name="Ada", email="ada@example.com", password_hash="pw"))
    db_session.commit()

    embeddings = DeterministicEmbeddingProvider(dimensions=settings.embedding_dimensions)
    ingestion = KnowledgeIngestionService(
        chunker=TextChunker(target_tokens=8, overlap_tokens=0),
        embeddings=embeddings,
    )
    retrieval = KnowledgeRetrievalService(embeddings=embeddings)

    for source_id in ("resume-1", "resume-2"):
        ingestion.ingest_document(
            db_session,
            _document(
                user_id="user-1",
                source_id=source_id,
                source_type="resume",
                source_subtype="resume_document",
                text="shared deterministic ranking tokens",
            ),
        )

    matches = retrieval.search(
        db_session,
        query="shared deterministic ranking tokens",
        user_id="user-1",
        limit=2,
    )

    assert [match["source_id"] for match in matches] == ["resume-1", "resume-2"]
