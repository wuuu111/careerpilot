from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from careerpilot.api.routers.applications import router as application_router
from careerpilot.api.routers.auth import router as auth_router
from careerpilot.api.routers.resumes import router as resume_router
from careerpilot.config import settings
from careerpilot.errors import AppError, forbidden
from careerpilot.security import get_csrf_cookie_name, get_csrf_header_name, get_session_cookie_name

UNSAFE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
CSRF_EXEMPT_PATHS = {"/api/auth/login", "/api/auth/register"}


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_origin_regex=(
            settings.cors_origin_regex if settings.environment == "development" else None
        ),
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", settings.auth_csrf_header_name],
    )
    app.include_router(auth_router)
    app.include_router(resume_router)
    app.include_router(application_router)

    @app.middleware("http")
    async def enforce_csrf(request: Request, call_next):
        session_cookie = request.cookies.get(get_session_cookie_name())
        authorization = request.headers.get("Authorization")
        if (
            request.method in UNSAFE_METHODS
            and request.url.path not in CSRF_EXEMPT_PATHS
            and session_cookie
            and not authorization
        ):
            csrf_cookie = request.cookies.get(get_csrf_cookie_name())
            csrf_header = request.headers.get(get_csrf_header_name())
            if not csrf_cookie or not csrf_header or csrf_cookie != csrf_header:
                error = forbidden("CSRF_VALIDATION_FAILED", "CSRF validation failed.")
                return JSONResponse(status_code=error.status_code, content=error.to_payload())
        return await call_next(request)

    @app.exception_handler(AppError)
    async def handle_app_error(_request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content=exc.to_payload())

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        _request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                "error_code": "VALIDATION_ERROR",
                "message": "Request validation failed.",
                "details": {"errors": exc.errors()},
            },
        )

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
