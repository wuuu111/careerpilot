from __future__ import annotations

from careerpilot.api.deps import get_current_user
from careerpilot.config import settings
from careerpilot.db import get_db
from careerpilot.errors import AppError
from careerpilot.models.auth import User
from careerpilot.models.resume import Resume
from careerpilot.schemas.resumes import ResumeParseResult, ResumeResponse
from careerpilot.services.knowledge import KnowledgeIngestionService
from careerpilot.services.parsing import extract_text, heuristic_resume_parse
from careerpilot.services.provider import DeepSeekProvider
from careerpilot.utils import new_id, utcnow
from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/resumes", tags=["resumes"])


@router.post("/upload", response_model=ResumeResponse, status_code=status.HTTP_201_CREATED)
async def upload_resume(
    file: UploadFile = File(...),
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ResumeResponse:
    content = await file.read()
    if len(content) > settings.max_upload_mb * 1024 * 1024:
        raise AppError("FILE_TOO_LARGE", "Uploaded file exceeds the maximum allowed size.", 400, {})
    raw_text = extract_text(file.filename, content)
    provider = DeepSeekProvider()
    parsed = provider.extract_resume_structured(raw_text) or heuristic_resume_parse(raw_text)
    created_at = utcnow()
    resume_id = new_id()
    knowledge = KnowledgeIngestionService().resume_payload(
        user_id=current_user.id,
        resume_id=resume_id,
        file_name=file.filename,
        raw_text=raw_text,
        parsed=parsed,
        created_at=created_at,
    )
    resume = Resume(
        id=resume_id,
        user_id=current_user.id,
        file_name=file.filename,
        raw_text=raw_text,
        parsed_json=parsed.model_dump(),
        embedding_text=knowledge.embedding_text,
        embedding_metadata=knowledge.metadata,
        created_at=created_at,
    )
    session.add(resume)
    KnowledgeIngestionService().ingest_resume(
        session,
        user_id=current_user.id,
        resume_id=resume_id,
        file_name=file.filename,
        raw_text=raw_text,
        parsed=parsed,
        created_at=created_at,
    )
    session.commit()
    session.refresh(resume)
    return ResumeResponse(
        id=resume.id, file_name=resume.file_name, parsed_result=parsed, created_at=resume.created_at
    )


@router.get("", response_model=list[ResumeResponse])
def list_resumes(
    session: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> list[ResumeResponse]:
    items = session.scalars(
        select(Resume).where(Resume.user_id == current_user.id).order_by(Resume.created_at.desc())
    ).all()
    return [
        ResumeResponse(
            id=item.id,
            file_name=item.file_name,
            parsed_result=ResumeParseResult.model_validate(item.parsed_json),
            created_at=item.created_at,
        )
        for item in items
    ]


@router.get("/{resume_id}", response_model=ResumeResponse)
def get_resume(
    resume_id: str,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ResumeResponse:
    resume = session.get(Resume, resume_id)
    if not resume or resume.user_id != current_user.id:
        raise AppError("RESUME_NOT_FOUND", "Resume not found.", 404, {"resume_id": resume_id})
    return ResumeResponse(
        id=resume.id,
        file_name=resume.file_name,
        parsed_result=ResumeParseResult.model_validate(resume.parsed_json),
        created_at=resume.created_at,
    )
