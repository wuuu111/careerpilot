from __future__ import annotations

from pydantic import BaseModel, Field


class MatchingReportPayload(BaseModel):
    overall_score: int
    dimension_scores: dict[str, int]
    matched_keywords: list[str]
    missing_keywords: list[str]
    recommendations: list[str]


class ResumeRewriteItem(BaseModel):
    original_bullet: str
    rewritten_bullet: str
    reason: str
    risk_level: str


class RewrittenResumePayload(BaseModel):
    items: list[ResumeRewriteItem]


class CoverLetterPayload(BaseModel):
    cover_letter: str
    style: str
    word_count: int
    used_evidence: list[str] = Field(default_factory=list)


class InterviewPrepPayload(BaseModel):
    hr_questions: list[str]
    technical_questions: list[str]
    project_deep_dive_questions: list[str]
    review_plan: list[str]
    model_answers: list[str]


class EvaluationPayload(BaseModel):
    faithfulness: int
    jd_coverage: int
    specificity: int
    readability: int
    hallucination_risk: str
    suggestions: list[str]
    evaluated_types: list[str]
