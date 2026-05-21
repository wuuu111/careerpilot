from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class ErrorEnvelope(BaseModel):
    error_code: str
    message: str
    details: dict[str, object]


class MessageResponse(BaseModel):
    message: str


class TimestampedModel(BaseModel):
    created_at: datetime | None = None
