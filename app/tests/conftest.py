import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.db.session import SessionLocal
from app.main import app


@pytest.fixture(autouse=True)
def _jwt_secret_env(monkeypatch):
    monkeypatch.setenv("JWT_SECRET", os.getenv("JWT_SECRET", "test-secret-not-for-prod"))


@pytest.fixture()
def db_session() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture()
def client(db_session: Session) -> TestClient:
    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
