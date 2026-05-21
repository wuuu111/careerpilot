from __future__ import annotations

from datetime import timedelta
from secrets import token_urlsafe
from uuid import uuid4

import jwt
from argon2 import PasswordHasher
from starlette.responses import Response

from careerpilot.config import get_settings, settings
from careerpilot.errors import AppError, unauthorized
from careerpilot.utils import utcnow

password_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return password_hasher.verify(password_hash, password)
    except Exception:
        return False


def create_access_token(user_id: str) -> str:
    issued_at = utcnow()
    expires_at = issued_at + timedelta(minutes=settings.jwt_expiry_minutes)
    payload = {
        "sub": user_id,
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
        "iat": issued_at,
        "nbf": issued_at,
        "exp": expires_at,
        "jti": str(uuid4()),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict[str, object]:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
            audience=settings.jwt_audience,
            issuer=settings.jwt_issuer,
        )
    except jwt.PyJWTError as exc:
        raise unauthorized("Invalid or expired token.") from exc
    if "sub" not in payload:
        raise AppError("INVALID_TOKEN", "Token subject missing.", 401, {})
    return payload


def get_session_cookie_name() -> str:
    return str(settings.auth_cookie_name)


def get_csrf_cookie_name() -> str:
    return str(settings.auth_csrf_cookie_name)


def get_csrf_header_name() -> str:
    return str(settings.auth_csrf_header_name)


def get_session_cookie_options() -> dict[str, object]:
    current_settings = get_settings()
    secure = current_settings.auth_cookie_secure
    if secure is None:
        secure = current_settings.environment.lower() not in {
            "development",
            "dev",
            "test",
            "testing",
            "local",
        }
    max_age = current_settings.auth_cookie_max_age_seconds
    if max_age is None:
        max_age = current_settings.jwt_expiry_minutes * 60
    return {
        "httponly": True,
        "secure": secure,
        "samesite": current_settings.auth_cookie_samesite,
        "path": current_settings.auth_cookie_path,
        "domain": current_settings.auth_cookie_domain,
        "max_age": max_age,
    }


def get_csrf_cookie_options() -> dict[str, object]:
    options = get_session_cookie_options()
    return {
        **options,
        "httponly": False,
    }


def create_csrf_token() -> str:
    return token_urlsafe(32)


def set_session_cookie(response: Response, token: str, csrf_token: str) -> None:
    response.set_cookie(get_session_cookie_name(), token, **get_session_cookie_options())
    response.set_cookie(get_csrf_cookie_name(), csrf_token, **get_csrf_cookie_options())


def clear_session_cookie(response: Response) -> None:
    options = get_session_cookie_options()
    response.delete_cookie(
        get_session_cookie_name(),
        path=str(options["path"]),
        domain=options["domain"],
        secure=bool(options["secure"]),
        httponly=bool(options["httponly"]),
        samesite=str(options["samesite"]),
    )
    csrf_options = get_csrf_cookie_options()
    response.delete_cookie(
        get_csrf_cookie_name(),
        path=str(csrf_options["path"]),
        domain=csrf_options["domain"],
        secure=bool(csrf_options["secure"]),
        httponly=bool(csrf_options["httponly"]),
        samesite=str(csrf_options["samesite"]),
    )
