import os

import pytest

from app.core.jwt import create_access_token, decode_access_token
from app.core.security import hash_password, verify_password


def test_password_hash_and_verify() -> None:
    pw = "S3cret!123"
    h = hash_password(pw)

    assert h != pw
    assert verify_password(pw, h) is True
    assert verify_password("wrong", h) is False


def test_jwt_roundtrip() -> None:
    os.environ["JWT_SECRET"] = "dev-secret-for-tests"
    os.environ["JWT_ALGORITHM"] = "HS256"
    os.environ["JWT_EXPIRES_MINUTES"] = "60"

    token = create_access_token(sub="user-123", role="REQUESTER")
    decoded = decode_access_token(token)

    assert decoded["sub"] == "user-123"
    assert decoded["role"] == "REQUESTER"


def test_jwt_missing_secret_fails() -> None:
    os.environ.pop("JWT_SECRET", None)
    with pytest.raises(RuntimeError):
        create_access_token(sub="x", role="REQUESTER")
