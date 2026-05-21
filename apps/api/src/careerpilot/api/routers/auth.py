from __future__ import annotations

from careerpilot.api.deps import get_current_user
from careerpilot.db import get_db
from careerpilot.models.auth import User
from careerpilot.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from careerpilot.security import clear_session_cookie, create_csrf_token, set_session_cookie
from careerpilot.services.auth import login_user, register_user
from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, session: Session = Depends(get_db)) -> UserResponse:
    user = register_user(session, payload)
    return UserResponse.model_validate(user, from_attributes=True)


@router.post("/login", response_model=TokenResponse)
def login(
    payload: LoginRequest,
    response: Response,
    session: Session = Depends(get_db),
) -> TokenResponse:
    token = login_user(session, payload)
    set_session_cookie(response, token, create_csrf_token())
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse.model_validate(current_user, from_attributes=True)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response) -> Response:
    clear_session_cookie(response)
    response.status_code = status.HTTP_204_NO_CONTENT
    return response
