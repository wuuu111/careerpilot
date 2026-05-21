from __future__ import annotations

import json
from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="CAREERPILOT_", extra="ignore")

    app_name: str = "CareerPilot API"
    environment: str = "development"
    database_url: str = Field(default="postgresql://postgres:postgres@localhost:5432/careerpilot")
    jwt_secret: str = Field(default="")
    jwt_algorithm: str = "HS256"
    jwt_expiry_minutes: int = 60 * 12
    jwt_issuer: str = "careerpilot-api"
    jwt_audience: str = "careerpilot-web"
    auth_cookie_name: str = "careerpilot_session"
    auth_cookie_domain: str | None = None
    auth_cookie_path: str = "/"
    auth_cookie_samesite: Literal["lax", "strict", "none"] = "lax"
    auth_cookie_secure: bool | None = None
    auth_cookie_max_age_seconds: int | None = None
    auth_csrf_cookie_name: str = "careerpilot_csrf_token"
    auth_csrf_header_name: str = "X-CSRF-Token"
    deepseek_api_key: str | None = None
    deepseek_base_url: str = "https://api.deepseek.com/v1"
    redis_url: str = "redis://localhost:6379/0"
    max_upload_mb: int = 10
    embedding_provider: str = "local"
    embedding_dimensions: int = 16
    knowledge_chunk_size_tokens: int = 120
    knowledge_chunk_overlap_tokens: int = 20
    cors_origins: list[str] = Field(default_factory=list)
    cors_origin_regex: str | None = r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$"
    celery_task_always_eager: bool = False

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: object) -> object:
        if not isinstance(value, str):
            return value
        if not value.strip():
            return []
        if value.lstrip().startswith("["):
            return json.loads(value)
        return [item.strip() for item in value.split(",") if item.strip()]

    @field_validator("jwt_secret")
    @classmethod
    def validate_jwt_secret(cls, value: str) -> str:
        blocked = {
            "",
            "change-me-please-use-at-least-32-bytes",
            "replace-with-a-random-secret-at-least-32-bytes-long",
        }
        if value in blocked or len(value) < 32:
            raise ValueError(
                "CAREERPILOT_JWT_SECRET must be set to a random value "
                "with at least 32 bytes."
            )
        return value

    @field_validator("auth_cookie_samesite", mode="before")
    @classmethod
    def normalize_auth_cookie_samesite(cls, value: object) -> object:
        if isinstance(value, str):
            return value.lower()
        return value


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


class SettingsProxy:
    def __getattr__(self, name: str) -> object:
        return getattr(get_settings(), name)


settings = SettingsProxy()
