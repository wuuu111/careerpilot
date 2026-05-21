from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import cast

from careerpilot.domain.documents import (
    KnowledgeDocument,
    build_generated_output_document,
    build_job_description_document,
    build_resume_document,
)
from careerpilot.models.knowledge_chunk import KnowledgeChunk
from careerpilot.schemas.generated_outputs import GeneratedOutputContent
from careerpilot.schemas.jobs import JobDescriptionAnalysis
from careerpilot.schemas.resumes import ResumeParseResult
from careerpilot.services.chunking import TextChunker
from careerpilot.services.embeddings import EmbeddingProvider, get_embedding_provider
from careerpilot.services.retrieval import KnowledgeRetrievalService
from sqlalchemy import delete
from sqlalchemy.orm import Session

__all__ = ["KnowledgeIngestionService", "KnowledgeRetrievalService"]


@dataclass(slots=True)
class KnowledgeIngestionService:
    chunker: TextChunker = field(default_factory=TextChunker)
    embeddings: EmbeddingProvider = field(
        default_factory=lambda: cast(EmbeddingProvider, get_embedding_provider())
    )

    def resume_payload(
        self,
        *,
        user_id: str,
        resume_id: str,
        file_name: str,
        raw_text: str,
        parsed: ResumeParseResult,
        created_at: datetime,
    ) -> KnowledgeDocument:
        return build_resume_document(
            user_id=user_id,
            resume_id=resume_id,
            file_name=file_name,
            raw_text=raw_text,
            parsed=parsed,
            created_at=created_at,
        )

    def jd_payload(
        self,
        *,
        user_id: str,
        jd_id: str,
        application_id: str,
        company_name: str,
        job_title: str,
        raw_text: str,
        parsed: JobDescriptionAnalysis,
        created_at: datetime,
    ) -> KnowledgeDocument:
        return build_job_description_document(
            user_id=user_id,
            jd_id=jd_id,
            application_id=application_id,
            company_name=company_name,
            job_title=job_title,
            raw_text=raw_text,
            parsed=parsed,
            created_at=created_at,
        )

    def output_payload(
        self,
        *,
        user_id: str,
        application_id: str,
        output_id: str,
        generated: GeneratedOutputContent,
        created_at: datetime,
    ) -> KnowledgeDocument:
        return build_generated_output_document(
            user_id=user_id,
            application_id=application_id,
            output_id=output_id,
            generated=generated,
            created_at=created_at,
        )

    def ingest_document(
        self,
        session: Session,
        document: KnowledgeDocument,
    ) -> list[KnowledgeChunk]:
        source_metadata = dict(document.metadata)
        user_id = _required_metadata(source_metadata, "user_id")
        source_id = _required_metadata(source_metadata, "source_id")
        source_type = _required_metadata(source_metadata, "source_type")
        source_subtype = _required_metadata(source_metadata, "source_subtype")
        application_id = _optional_metadata(source_metadata, "application_id")

        chunks = self.chunker.chunk_document(document)
        session.execute(
            delete(KnowledgeChunk).where(
                KnowledgeChunk.user_id == user_id,
                KnowledgeChunk.source_type == source_type,
                KnowledgeChunk.source_id == source_id,
            )
        )
        if not chunks:
            session.flush()
            return []

        embeddings = self.embeddings.embed([chunk.chunk_text for chunk in chunks])
        stored_chunks: list[KnowledgeChunk] = []
        for chunk, embedding in zip(chunks, embeddings, strict=True):
            stored_chunks.append(
                KnowledgeChunk(
                    user_id=user_id,
                    application_id=application_id,
                    source_id=source_id,
                    source_type=source_type,
                    source_subtype=source_subtype,
                    chunk_index=chunk.chunk_index,
                    chunk_text=chunk.chunk_text,
                    token_count=chunk.token_count,
                    embedding=embedding,
                    chunk_metadata=chunk.metadata,
                )
            )
        session.add_all(stored_chunks)
        session.flush()
        return stored_chunks

    def ingest_resume(
        self,
        session: Session,
        *,
        user_id: str,
        resume_id: str,
        file_name: str,
        raw_text: str,
        parsed: ResumeParseResult,
        created_at: datetime,
    ) -> list[KnowledgeChunk]:
        return self.ingest_document(
            session,
            self.resume_payload(
                user_id=user_id,
                resume_id=resume_id,
                file_name=file_name,
                raw_text=raw_text,
                parsed=parsed,
                created_at=created_at,
            ),
        )

    def ingest_job_description(
        self,
        session: Session,
        *,
        user_id: str,
        jd_id: str,
        application_id: str,
        company_name: str,
        job_title: str,
        raw_text: str,
        parsed: JobDescriptionAnalysis,
        created_at: datetime,
    ) -> list[KnowledgeChunk]:
        return self.ingest_document(
            session,
            self.jd_payload(
                user_id=user_id,
                jd_id=jd_id,
                application_id=application_id,
                company_name=company_name,
                job_title=job_title,
                raw_text=raw_text,
                parsed=parsed,
                created_at=created_at,
            ),
        )

    def ingest_generated_output(
        self,
        session: Session,
        *,
        user_id: str,
        application_id: str,
        output_id: str,
        generated: GeneratedOutputContent,
        created_at: datetime,
    ) -> list[KnowledgeChunk]:
        return self.ingest_document(
            session,
            self.output_payload(
                user_id=user_id,
                application_id=application_id,
                output_id=output_id,
                generated=generated,
                created_at=created_at,
            ),
        )


def _required_metadata(metadata: dict[str, object], key: str) -> str:
    value = metadata.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"Knowledge document metadata must include {key}")
    return value


def _optional_metadata(metadata: dict[str, object], key: str) -> str | None:
    value = metadata.get(key)
    if value is None:
        return None
    if not isinstance(value, str) or not value:
        raise ValueError(
            f"Knowledge document metadata field {key} must be a non-empty string"
        )
    return value
