from __future__ import annotations

from careerpilot.schemas.jobs import JobDescriptionAnalysis
from careerpilot.services.provider import DeepSeekProvider


def analyze_jd_with_fallback(
    company_name: str, job_title: str, job_description: str, provider: DeepSeekProvider
) -> JobDescriptionAnalysis:
    parsed = provider.analyze_job_description(company_name, job_title, job_description)
    if parsed:
        return parsed
    lines = [line.strip() for line in job_description.splitlines() if line.strip()]
    keywords = [
        token.strip(",. ")
        for token in job_description.split()
        if token.lower() in {"python", "fastapi", "react", "langgraph", "llm"}
    ]
    return JobDescriptionAnalysis(
        role_type=job_title,
        responsibilities=lines[:5],
        required_skills=keywords[:6],
        preferred_skills=[],
        keywords=keywords[:10],
        business_scenario=company_name,
        seniority_level="intern" if "intern" in job_title.lower() else "general",
    )
