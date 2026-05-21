from __future__ import annotations

from pydantic import BaseModel


class JobDescriptionAnalysis(BaseModel):
    role_type: str
    responsibilities: list[str]
    required_skills: list[str]
    preferred_skills: list[str]
    keywords: list[str]
    business_scenario: str
    seniority_level: str
