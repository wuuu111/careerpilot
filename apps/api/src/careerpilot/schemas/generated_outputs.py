from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

OutputType = Literal[
    "matching_report",
    "rewritten_resume",
    "cover_letter",
    "interview_prep",
    "evaluation",
]


class GeneratedOutputContent(BaseModel):
    output_type: OutputType
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None


class GeneratedOutputResponse(GeneratedOutputContent):
    created_at: datetime
    version: str = "v1"


class GeneratedOutputHistoryItem(GeneratedOutputResponse):
    output_id: str


class GeneratedOutputHistoryResponse(BaseModel):
    output_type: OutputType
    items: list[GeneratedOutputHistoryItem]


class GeneratedOutputCompareResponse(BaseModel):
    output_type: OutputType
    current: GeneratedOutputHistoryItem
    previous: GeneratedOutputHistoryItem | None = None
    diff: dict[str, Any] = Field(default_factory=dict)


class CoverLetterGenerateRequest(BaseModel):
    style: str = "student-like"
    language: str = "en"
