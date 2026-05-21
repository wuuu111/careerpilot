from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class BasicInfo(BaseModel):
    name: str = ""
    email: str = ""
    phone: str = ""
    location: str = ""


class ResumeParseResult(BaseModel):
    basic_info: BasicInfo
    education: list[str]
    skills: list[str]
    projects: list[str]
    experience: list[str]
    awards: list[str]


class ResumeResponse(BaseModel):
    id: str
    file_name: str
    parsed_result: ResumeParseResult
    created_at: datetime
