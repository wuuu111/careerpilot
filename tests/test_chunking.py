from __future__ import annotations

from datetime import UTC, datetime

from careerpilot.config import settings
from careerpilot.domain.documents import KnowledgeDocument, build_resume_document
from careerpilot.models.auth import User
from careerpilot.models.knowledge_chunk import KnowledgeChunk
from careerpilot.schemas.resumes import ResumeParseResult
from careerpilot.services.chunking import TextChunker
from careerpilot.services.embeddings import DeterministicEmbeddingProvider
from careerpilot.services.knowledge import KnowledgeIngestionService


def test_text_chunker_splits_on_token_boundaries_with_overlap() -> None:
    document = KnowledgeDocument(
        embedding_text="alpha beta gamma delta epsilon zeta eta theta",
        metadata={
            "user_id": "user-1",
            "source_id": "resume-1",
            "source_type": "resume",
            "source_subtype": "resume_document",
            "created_at": datetime(2026, 5, 21, tzinfo=UTC).isoformat(),
        },
    )

    chunks = TextChunker(target_tokens=4, overlap_tokens=1).chunk_document(document)

    assert [chunk.chunk_text for chunk in chunks] == [
        "alpha beta gamma delta",
        "delta epsilon zeta eta",
        "eta theta",
    ]
    assert [chunk.token_count for chunk in chunks] == [4, 4, 2]
    assert [chunk.chunk_index for chunk in chunks] == [0, 1, 2]
    assert chunks[1].metadata["source_type"] == "resume"


def test_ingestion_persists_chunks_and_replaces_existing_source_rows(db_session) -> None:
    db_session.add(
        User(
            id="user-1",
            name="Ada",
            email="ada@example.com",
            password_hash="not-used",
        )
    )
    db_session.commit()

    document = build_resume_document(
        user_id="user-1",
        resume_id="resume-1",
        file_name="resume.pdf",
        raw_text=(
            "Ada Lovelace built python agents with fastapi and retrieval systems for "
            "career search orchestration and evaluation workflows."
        ),
        parsed=ResumeParseResult(
            basic_info={
                "name": "Ada Lovelace",
                "email": "ada@example.com",
                "phone": "123",
                "location": "London",
            },
            education=["BSc Mathematics"],
            skills=["Python", "FastAPI", "Retrieval"],
            projects=["Built a career agent platform"],
            experience=["Developed ranking pipelines"],
            awards=["Programming Prize"],
        ),
        created_at=datetime(2026, 5, 21, tzinfo=UTC),
    )
    service = KnowledgeIngestionService(
        chunker=TextChunker(target_tokens=8, overlap_tokens=2),
        embeddings=DeterministicEmbeddingProvider(dimensions=settings.embedding_dimensions),
    )

    first_pass = service.ingest_document(db_session, document)
    second_pass = service.ingest_document(db_session, document)
    stored_chunks = (
        db_session.query(KnowledgeChunk)
        .order_by(KnowledgeChunk.source_id, KnowledgeChunk.chunk_index)
        .all()
    )

    assert len(first_pass) >= 2
    assert len(second_pass) == len(first_pass)
    assert len(stored_chunks) == len(first_pass)
    assert stored_chunks[0].user_id == "user-1"
    assert stored_chunks[0].source_id == "resume-1"
    assert stored_chunks[0].source_type == "resume"
    assert stored_chunks[0].chunk_metadata["source_subtype"] == "resume_document"
    assert stored_chunks[0].token_count > 0
    assert len(stored_chunks[0].embedding) == settings.embedding_dimensions
    assert "Ada Lovelace" in stored_chunks[0].chunk_text
