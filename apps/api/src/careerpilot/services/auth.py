from __future__ import annotations

from careerpilot.errors import AppError, bad_request, unauthorized
from careerpilot.models.auth import User
from careerpilot.schemas.auth import LoginRequest, RegisterRequest
from careerpilot.security import create_access_token, hash_password, verify_password
from sqlalchemy import select
from sqlalchemy.orm import Session


def register_user(session: Session, payload: RegisterRequest) -> User:
    existing = session.scalar(select(User).where(User.email == payload.email))
    if existing:
        raise bad_request("EMAIL_ALREADY_EXISTS", "A user with that email already exists.")
    user = User(
        name=payload.name, email=payload.email, password_hash=hash_password(payload.password)
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def login_user(session: Session, payload: LoginRequest) -> str:
    user = session.scalar(select(User).where(User.email == payload.email))
    if not user or not verify_password(payload.password, user.password_hash):
        raise unauthorized("Invalid email or password.")
    return create_access_token(user.id)


def get_user_by_id(session: Session, user_id: str) -> User:
    user = session.get(User, user_id)
    if not user:
        raise AppError("USER_NOT_FOUND", "User not found.", 404, {"user_id": user_id})
    return user
