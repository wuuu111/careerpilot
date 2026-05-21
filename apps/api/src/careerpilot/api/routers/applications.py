from __future__ import annotations

from careerpilot.api.deps import get_current_user
from careerpilot.config import settings
from careerpilot.db import get_db
from careerpilot.domain.documents import KnowledgeDocument
from careerpilot.errors import AppError
from careerpilot.models.application import Application
from careerpilot.models.auth import User
from careerpilot.models.company_profile import CompanyProfile
from careerpilot.models.generated_output import GeneratedOutput
from careerpilot.models.job_description import JobDescription
from careerpilot.models.resume import Resume
from careerpilot.models.run import AgentRun, AgentStep
from careerpilot.schemas.applications import (
    AgentRunRequest,
    ApplicationCreateRequest,
    ApplicationResponse,
    CompanyProfileResponse,
    GeneratedOutputType,
)
from careerpilot.schemas.generated_outputs import (
    CoverLetterGenerateRequest,
    GeneratedOutputCompareResponse,
    GeneratedOutputHistoryResponse,
    GeneratedOutputResponse,
)
from careerpilot.schemas.jobs import JobDescriptionAnalysis
from careerpilot.services.celery_app import run_full_application
from careerpilot.services.generated_outputs import (
    build_output_compare_response,
    build_output_history_response,
    fetch_latest_output_for_application,
)
from careerpilot.services.generation import build_cover_letter
from careerpilot.services.jobs import analyze_jd_with_fallback
from careerpilot.services.knowledge import KnowledgeIngestionService, KnowledgeRetrievalService
from careerpilot.services.provider import DeepSeekProvider
from careerpilot.services.workflow import execute_full_application_workflow
from careerpilot.utils import new_id, utcnow
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api", tags=["applications"])


def _get_owned_application(session: Session, user_id: str, application_id: str) -> Application:
    application = session.get(Application, application_id)
    if not application or application.user_id != user_id:
        raise AppError(
            "APPLICATION_NOT_FOUND",
            "Application not found.",
            404,
            {"application_id": application_id},
        )
    return application


def _get_company_profile(session: Session, application_id: str) -> CompanyProfile | None:
    return session.scalar(
        select(CompanyProfile).where(CompanyProfile.application_id == application_id)
    )


def _sanitize_trace_payload(value: object) -> object:
    sensitive_keys = {"user_id", "source_id", "application_id", "embedding_text"}
    if isinstance(value, dict):
        sanitized: dict[str, object] = {}
        for key, nested in value.items():
            if key in sensitive_keys:
                sanitized[key] = "[redacted]"
            else:
                sanitized[key] = _sanitize_trace_payload(nested)
        return sanitized
    if isinstance(value, list):
        return [_sanitize_trace_payload(item) for item in value]
    if isinstance(value, str) and len(value) > 320:
        return value[:320] + "... [truncated]"
    return value


@router.post(
    "/applications", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED
)
def create_application(
    payload: ApplicationCreateRequest,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApplicationResponse:
    resume = session.get(Resume, payload.resume_id)
    if not resume or resume.user_id != current_user.id:
        raise AppError(
            "RESUME_NOT_FOUND", "Resume not found.", 404, {"resume_id": payload.resume_id}
        )

    provider = DeepSeekProvider()
    created_at = utcnow()
    application_id = new_id()
    jd_id = new_id()
    application = Application(
        id=application_id,
        user_id=current_user.id,
        resume_id=resume.id,
        jd_id=jd_id,
        status="draft",
        created_at=created_at,
    )

    parsed = analyze_jd_with_fallback(
        payload.company_name, payload.job_title, payload.job_description, provider
    )
    knowledge = KnowledgeIngestionService().jd_payload(
        user_id=current_user.id,
        jd_id=jd_id,
        application_id=application_id,
        company_name=payload.company_name,
        job_title=payload.job_title,
        raw_text=payload.job_description,
        parsed=parsed,
        created_at=created_at,
    )
    jd = JobDescription(
        id=jd_id,
        user_id=current_user.id,
        company_name=payload.company_name,
        job_title=payload.job_title,
        raw_text=payload.job_description,
        parsed_json=parsed.model_dump(),
        embedding_text=knowledge.embedding_text,
        embedding_metadata=knowledge.metadata,
        created_at=created_at,
    )
    session.add(jd)
    session.add(application)
    ingestion_service = KnowledgeIngestionService()
    ingestion_service.ingest_job_description(
        session,
        user_id=current_user.id,
        jd_id=jd_id,
        application_id=application_id,
        company_name=payload.company_name,
        job_title=payload.job_title,
        raw_text=payload.job_description,
        parsed=parsed,
        created_at=created_at,
    )
    company_profile = None
    if payload.company_context:
        created_at = utcnow()
        company_profile = CompanyProfile(
            id=new_id(),
            application_id=application_id,
            user_id=current_user.id,
            company_name=payload.company_name,
            content=payload.company_context,
            embedding_text="\n".join(
                [
                    f"company: {payload.company_name}",
                    f"job_title: {payload.job_title}",
                    f"context: {payload.company_context}",
                ]
            ),
            embedding_metadata={
                "user_id": current_user.id,
                "application_id": application_id,
                "source_type": "company",
                "source_subtype": "company_profile",
                "version": "v1",
                "language": "en",
                "created_at": created_at.isoformat(),
            },
            created_at=created_at,
        )
        session.add(company_profile)
        ingestion_service.ingest_document(
            session,
            KnowledgeDocument(
                embedding_text=company_profile.embedding_text,
                metadata=company_profile.embedding_metadata | {"source_id": company_profile.id},
            ),
        )
    session.commit()
    session.refresh(application)
    return ApplicationResponse(
        id=application.id,
        resume_id=application.resume_id,
        jd_id=application.jd_id,
        company_name=jd.company_name,
        job_title=jd.job_title,
        status=application.status,
        created_at=application.created_at,
        jd_analysis=parsed,
        has_company_context=company_profile is not None,
    )


@router.get("/applications", response_model=list[ApplicationResponse])
def list_applications(
    session: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> list[ApplicationResponse]:
    applications = session.scalars(
        select(Application)
        .where(Application.user_id == current_user.id)
        .order_by(Application.created_at.desc())
    ).all()
    results: list[ApplicationResponse] = []
    for application in applications:
        jd = session.get(JobDescription, application.jd_id)
        if jd:
            company_profile = _get_company_profile(session, application.id)
            results.append(
                ApplicationResponse(
                    id=application.id,
                    resume_id=application.resume_id,
                    jd_id=application.jd_id,
                    company_name=jd.company_name,
                    job_title=jd.job_title,
                    status=application.status,
                    created_at=application.created_at,
                    jd_analysis=JobDescriptionAnalysis.model_validate(jd.parsed_json),
                    has_company_context=company_profile is not None,
                )
            )
    return results


@router.get("/applications/{application_id}", response_model=ApplicationResponse)
def get_application(
    application_id: str,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApplicationResponse:
    application = _get_owned_application(session, current_user.id, application_id)
    jd = session.get(JobDescription, application.jd_id)
    company_profile = _get_company_profile(session, application.id)
    assert jd is not None
    return ApplicationResponse(
        id=application.id,
        resume_id=application.resume_id,
        jd_id=application.jd_id,
        company_name=jd.company_name,
        job_title=jd.job_title,
        status=application.status,
        created_at=application.created_at,
        jd_analysis=JobDescriptionAnalysis.model_validate(jd.parsed_json),
        has_company_context=company_profile is not None,
    )


@router.get(
    "/applications/{application_id}/company-profile",
    response_model=CompanyProfileResponse,
)
def get_company_profile(
    application_id: str,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CompanyProfileResponse:
    application = _get_owned_application(session, current_user.id, application_id)
    company_profile = _get_company_profile(session, application.id)
    if not company_profile:
        raise AppError(
            "COMPANY_PROFILE_NOT_FOUND",
            "Company profile not found.",
            404,
            {"application_id": application_id},
        )
    return CompanyProfileResponse(
        id=company_profile.id,
        application_id=company_profile.application_id,
        company_name=company_profile.company_name,
        content=company_profile.content,
        created_at=company_profile.created_at,
    )


@router.post("/agent-runs")
def create_agent_run(
    payload: AgentRunRequest,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, str]:
    application = _get_owned_application(session, current_user.id, payload.application_id)
    run = AgentRun(
        application_id=application.id, workflow_type=payload.workflow_type, status="queued"
    )
    session.add(run)
    application.status = "queued"
    session.commit()
    session.refresh(run)
    if settings.celery_task_always_eager:
        execute_full_application_workflow(session, run)
    else:
        run_full_application.delay(run.id)
    session.refresh(run)
    return {"run_id": run.id, "status": run.status}


@router.get("/agent-runs/{run_id}")
def get_agent_run(
    run_id: str, session: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> dict[str, object]:
    run = session.get(AgentRun, run_id)
    if not run:
        raise AppError("RUN_NOT_FOUND", "Agent run not found.", 404, {"run_id": run_id})
    application = _get_owned_application(session, current_user.id, run.application_id)
    return {
        "run_id": run.id,
        "application_id": application.id,
        "status": run.status,
        "workflow_type": run.workflow_type,
        "started_at": run.started_at,
        "finished_at": run.finished_at,
    }


@router.get("/agent-runs/{run_id}/steps")
def get_agent_steps(
    run_id: str, session: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> dict[str, object]:
    run = session.get(AgentRun, run_id)
    if not run:
        raise AppError("RUN_NOT_FOUND", "Agent run not found.", 404, {"run_id": run_id})
    _get_owned_application(session, current_user.id, run.application_id)
    steps = session.scalars(
        select(AgentStep).where(AgentStep.run_id == run_id).order_by(AgentStep.created_at.asc())
    ).all()
    return {
        "run_id": run_id,
        "steps": [
            {
                "step_id": step.id,
                "agent_name": step.agent_name,
                "input": _sanitize_trace_payload(step.input_json),
                "output": _sanitize_trace_payload(step.output_json),
                "status": step.status,
                "latency_ms": step.latency_ms,
                "error_message": step.error_message,
                "created_at": step.created_at,
            }
            for step in steps
        ],
    }


@router.get("/applications/{application_id}/matching-report")
def get_matching_report(
    application_id: str,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, object]:
    _get_owned_application(session, current_user.id, application_id)
    output = fetch_latest_output_for_application(session, application_id, "matching_report")
    return output.output_metadata


@router.post("/applications/{application_id}/cover-letter", response_model=GeneratedOutputResponse)
def generate_cover_letter(
    application_id: str,
    payload: CoverLetterGenerateRequest,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> GeneratedOutputResponse:
    application = _get_owned_application(session, current_user.id, application_id)
    resume = session.get(Resume, application.resume_id)
    jd = session.get(JobDescription, application.jd_id)
    assert resume is not None and jd is not None
    from careerpilot.schemas.resumes import ResumeParseResult
    jd_analysis = JobDescriptionAnalysis.model_validate(jd.parsed_json)
    retrieval_query = " ".join(
        [jd.job_title, jd.company_name, *jd_analysis.required_skills]
    )
    retrieval_context = KnowledgeRetrievalService().search(
        session,
        application_id=application.id,
        user_id=current_user.id,
        query=retrieval_query,
        limit=5,
    )

    generated = build_cover_letter(
        ResumeParseResult.model_validate(resume.parsed_json),
        jd_analysis,
        DeepSeekProvider(),
        style=payload.style,
        language=payload.language,
        retrieved_context=retrieval_context,
    )
    generated.metadata.setdefault("citations", retrieval_context)
    created_at = utcnow()
    output = GeneratedOutput(
        application_id=application.id,
        output_type="cover_letter",
        content=generated.content,
        output_metadata=generated.metadata,
        embedding_text="",
        embedding_metadata={},
        created_at=created_at,
    )
    session.add(output)
    session.flush()
    document = KnowledgeIngestionService().output_payload(
        user_id=current_user.id,
        application_id=application.id,
        output_id=output.id,
        generated=generated,
        created_at=created_at,
    )
    output.embedding_text = document.embedding_text
    output.embedding_metadata = document.metadata
    session.commit()
    session.refresh(output)
    return GeneratedOutputResponse(
        output_type="cover_letter",
        content=output.content,
        metadata=output.output_metadata,
        created_at=output.created_at,
    )


@router.get(
    "/applications/{application_id}/generated-outputs", response_model=GeneratedOutputResponse
)
def get_generated_output(
    application_id: str,
    type: GeneratedOutputType = Query(...),  # noqa: A002
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> GeneratedOutputResponse:
    _get_owned_application(session, current_user.id, application_id)
    output = fetch_latest_output_for_application(session, application_id, type)
    history = build_output_history_response(session, application_id, type)
    version = next((item.version for item in history.items if item.output_id == output.id), "v1")
    return GeneratedOutputResponse(
        output_type=output.output_type,
        content=output.content,
        metadata=output.output_metadata,
        created_at=output.created_at,
        version=version,
    )


@router.get(
    "/applications/{application_id}/generated-outputs/history",
    response_model=GeneratedOutputHistoryResponse,
)
def get_generated_output_history(
    application_id: str,
    type: GeneratedOutputType = Query(...),  # noqa: A002
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> GeneratedOutputHistoryResponse:
    _get_owned_application(session, current_user.id, application_id)
    return build_output_history_response(session, application_id, type)


@router.get(
    "/applications/{application_id}/generated-outputs/compare",
    response_model=GeneratedOutputCompareResponse,
)
def compare_generated_outputs(
    application_id: str,
    type: GeneratedOutputType = Query(...),  # noqa: A002
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> GeneratedOutputCompareResponse:
    _get_owned_application(session, current_user.id, application_id)
    return build_output_compare_response(session, application_id, type)
