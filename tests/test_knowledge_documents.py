from __future__ import annotations

from datetime import UTC, datetime

from careerpilot.domain.documents import (
    build_generated_output_document,
    build_job_description_document,
    build_resume_document,
)
from careerpilot.schemas.generated_outputs import GeneratedOutputContent
from careerpilot.schemas.jobs import JobDescriptionAnalysis
from careerpilot.schemas.resumes import ResumeParseResult


def test_build_resume_document_contains_embedding_text_and_metadata() -> None:
    parsed = ResumeParseResult(
        basic_info={
            "name": "Ada Lovelace",
            "email": "ada@example.com",
            "phone": "123",
            "location": "London",
        },
        education=["BSc Mathematics"],
        skills=["Python", "FastAPI"],
        projects=["Built an agent orchestration service"],
        experience=["Research assistant on analytics"],
        awards=["Programming Prize"],
    )

    document = build_resume_document(
        user_id="user-1",
        resume_id="resume-1",
        file_name="resume.pdf",
        raw_text="raw resume text",
        parsed=parsed,
        created_at=datetime(2026, 5, 20, tzinfo=UTC),
    )

    assert "Ada Lovelace" in document.embedding_text
    assert "Built an agent orchestration service" in document.embedding_text
    assert document.metadata["source_type"] == "resume"
    assert document.metadata["source_subtype"] == "resume_document"


def test_build_job_description_document_contains_required_skill_context() -> None:
    analysis = JobDescriptionAnalysis(
        role_type="AI Agent Developer",
        responsibilities=["Build agent workflows"],
        required_skills=["Python", "LangGraph"],
        preferred_skills=["PostgreSQL"],
        keywords=["agent", "workflow"],
        business_scenario="career tools",
        seniority_level="intern",
    )

    document = build_job_description_document(
        user_id="user-1",
        jd_id="jd-1",
        application_id="app-1",
        company_name="ByteDance",
        job_title="AI Agent Developer Intern",
        raw_text="jd raw text",
        parsed=analysis,
        created_at=datetime(2026, 5, 20, tzinfo=UTC),
    )

    assert "LangGraph" in document.embedding_text
    assert document.metadata["source_type"] == "jd"
    assert document.metadata["application_id"] == "app-1"


def test_build_generated_output_document_tracks_output_type() -> None:
    content = GeneratedOutputContent(
        output_type="cover_letter",
        content="Dear team, I built robust agent systems.",
        metadata={"style": "technical"},
    )

    document = build_generated_output_document(
        user_id="user-1",
        application_id="app-1",
        output_id="out-1",
        generated=content,
        created_at=datetime(2026, 5, 20, tzinfo=UTC),
    )

    assert "Dear team" in document.embedding_text
    assert document.metadata["source_type"] == "generated_output"
    assert document.metadata["source_subtype"] == "cover_letter"
