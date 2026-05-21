from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from careerpilot.schemas.generated_outputs import GeneratedOutputContent
from careerpilot.schemas.jobs import JobDescriptionAnalysis
from careerpilot.schemas.resumes import ResumeParseResult


@dataclass(slots=True)
class KnowledgeDocument:
    embedding_text: str
    metadata: dict[str, object]


def _base_metadata(
    *,
    user_id: str,
    source_id: str,
    source_type: str,
    source_subtype: str,
    created_at: datetime,
    application_id: str | None = None,
) -> dict[str, object]:
    metadata = {
        "user_id": user_id,
        "source_id": source_id,
        "source_type": source_type,
        "source_subtype": source_subtype,
        "version": "v1",
        "language": "en",
        "created_at": created_at.isoformat(),
    }
    if application_id:
        metadata["application_id"] = application_id
    return metadata


def build_resume_document(
    *,
    user_id: str,
    resume_id: str,
    file_name: str,
    raw_text: str,
    parsed: ResumeParseResult,
    created_at: datetime,
) -> KnowledgeDocument:
    embedding_text = "\n".join(
        [
            f"file_name: {file_name}",
            f"name: {parsed.basic_info.name}",
            f"summary_raw: {raw_text}",
            f"education: {'; '.join(parsed.education)}",
            f"skills: {'; '.join(parsed.skills)}",
            f"projects: {'; '.join(parsed.projects)}",
            f"experience: {'; '.join(parsed.experience)}",
            f"awards: {'; '.join(parsed.awards)}",
        ]
    )
    return KnowledgeDocument(
        embedding_text=embedding_text,
        metadata=_base_metadata(
            user_id=user_id,
            source_id=resume_id,
            source_type="resume",
            source_subtype="resume_document",
            created_at=created_at,
        ),
    )


def build_job_description_document(
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
    embedding_text = "\n".join(
        [
            f"company: {company_name}",
            f"job_title: {job_title}",
            f"role_type: {parsed.role_type}",
            f"raw_text: {raw_text}",
            f"responsibilities: {'; '.join(parsed.responsibilities)}",
            f"required_skills: {'; '.join(parsed.required_skills)}",
            f"preferred_skills: {'; '.join(parsed.preferred_skills)}",
            f"keywords: {'; '.join(parsed.keywords)}",
            f"business_scenario: {parsed.business_scenario}",
            f"seniority_level: {parsed.seniority_level}",
        ]
    )
    return KnowledgeDocument(
        embedding_text=embedding_text,
        metadata=_base_metadata(
            user_id=user_id,
            source_id=jd_id,
            source_type="jd",
            source_subtype="job_description",
            created_at=created_at,
            application_id=application_id,
        ),
    )


def build_generated_output_document(
    *,
    user_id: str,
    application_id: str,
    output_id: str,
    generated: GeneratedOutputContent,
    created_at: datetime,
) -> KnowledgeDocument:
    embedding_text = "\n".join(
        [
            f"output_type: {generated.output_type}",
            f"content: {generated.content}",
            f"metadata: {generated.metadata}",
        ]
    )
    return KnowledgeDocument(
        embedding_text=embedding_text,
        metadata=_base_metadata(
            user_id=user_id,
            source_id=output_id,
            source_type="generated_output",
            source_subtype=generated.output_type,
            created_at=created_at,
            application_id=application_id,
        ),
    )
