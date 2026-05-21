from __future__ import annotations

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from careerpilot.db import get_db
from careerpilot.errors import unauthorized
from careerpilot.models.auth import User
from careerpilot.security import decode_access_token, get_session_cookie_name
from careerpilot.services.auth import get_user_by_id

bearer = HTTPBearer(auto_error=False)


def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    session: Session = Depends(get_db),
) -> User:
    cookie_token = request.cookies.get(get_session_cookie_name())
    token = credentials.credentials if credentials is not None else cookie_token
    if token is None:
        raise unauthorized()
    payload = decode_access_token(token)
    return get_user_by_id(session, str(payload["sub"]))
