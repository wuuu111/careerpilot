from __future__ import annotations

from datetime import datetime
from typing import Literal

from careerpilot.schemas.jobs import JobDescriptionAnalysis
from pydantic import BaseModel, Field


class ApplicationCreateRequest(BaseModel):
    resume_id: str
    company_name: str = Field(min_length=1)
    job_title: str = Field(min_length=1)
    job_description: str = Field(min_length=1)
    company_context: str | None = None


class ApplicationResponse(BaseModel):
    id: str
    resume_id: str
    jd_id: str
    company_name: str
    job_title: str
    status: str
    created_at: datetime
    jd_analysis: JobDescriptionAnalysis
    has_company_context: bool = False


GeneratedOutputType = Literal[
    "matching_report",
    "rewritten_resume",
    "cover_letter",
    "interview_prep",
    "evaluation",
]


class AgentRunRequest(BaseModel):
    application_id: str
    workflow_type: str = "full_application"


class CompanyProfileResponse(BaseModel):
    id: str
    application_id: str
    company_name: str
    content: str
    created_at: datetime
