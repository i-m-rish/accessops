from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt

from app.core.config import jwt_algorithm, jwt_expires_minutes, jwt_secret


def create_access_token(*, sub: str, role: str) -> str:
    now = datetime.now(timezone.utc)
    exp = now + timedelta(minutes=jwt_expires_minutes())
    payload: dict[str, Any] = {"sub": sub, "role": role, "iat": int(now.timestamp()), "exp": exp}
    return jwt.encode(payload, jwt_secret(), algorithm=jwt_algorithm())


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, jwt_secret(), algorithms=[jwt_algorithm()])
    except JWTError as e:
        raise ValueError("Invalid token") from e
