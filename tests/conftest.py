from __future__ import annotations

import os
import importlib
import pkgutil
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
import pytest

@pytest.fixture(autouse=True)
def _env_defaults(monkeypatch):
    monkeypatch.setenv("JWT_SECRET", "dev-secret-for-tests")
    monkeypatch.setenv("JWT_ALGORITHM", "HS256")
    monkeypatch.setenv("JWT_EXPIRES_MINUTES", "60")

# IMPORTANT:
# Set env before importing app modules that may read env at import-time.
def pytest_configure() -> None:
    os.environ.setdefault("JWT_SECRET", "test-secret")
    # If your branch enforces issuer/audience, set them here too.
    os.environ.setdefault("JWT_ISSUER", "test-issuer")
    os.environ.setdefault("JWT_AUDIENCE", "test-audience")

    # Use a deterministic sqlite DB for tests.
    os.environ.setdefault("DATABASE_URL", "sqlite://")


def _import_all_models() -> None:
    """
    Ensure all SQLAlchemy models are imported so Base.metadata knows about them
    before create_all() runs.
    """
    try:
        import app.models  # type: ignore
    except Exception:
        return

    pkg = app.models  # type: ignore
    for m in pkgutil.iter_modules(pkg.__path__, pkg.__name__ + "."):
        importlib.import_module(m.name)


# Base lives here in your repo (you already rg'd it).
from app.db.base import Base  # noqa: E402


@pytest.fixture(scope="session")
def engine():
    """
    In-memory SQLite with StaticPool so the DB persists across connections
    during the test session.
    """
    _import_all_models()

    eng = create_engine(
        os.environ["DATABASE_URL"],
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    Base.metadata.create_all(bind=eng)
    try:
        yield eng
    finally:
        Base.metadata.drop_all(bind=eng)


@pytest.fixture()
def db_session(engine) -> Generator[Session, None, None]:
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()


@pytest.fixture()
def client(db_session: Session) -> Generator[TestClient, None, None]:
    from app.main import app  # import after env is set
    from app.db.deps import get_db

    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()
