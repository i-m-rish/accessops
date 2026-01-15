from __future__ import annotations

import os
import pytest

from app.db.base import Base
from app.db.session import engine


@pytest.fixture( autouse=True)
def _env_defaults(monkeypatch):
    monkeypatch.setenv("JWT_SECRET", "test-secret")
    monkeypatch.setenv("JWT_ALGORITHM", "HS256")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///./test.db")

@pytest.fixture(scope="session", autouse=True)
def _schema() -> None:
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
