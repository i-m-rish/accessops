from __future__ import annotations

import os
from pathlib import Path

import sqlalchemy as sa
from alembic import command
from alembic.config import Config


def test_alembic_upgrade_head_creates_schema(tmp_path: Path, monkeypatch) -> None:
    # Fresh DB path
    db_file = tmp_path / "migtest.db"
    db_url = f"sqlite:///{db_file}"

    # Ensure Alembic env uses the intended DB
    monkeypatch.setenv("DATABASE_URL", db_url)

    # Run migrations to head
    cfg = Config("alembic.ini")
    command.upgrade(cfg, "head")

    # Verify core tables exist
    engine = sa.create_engine(db_url, future=True)
    insp = sa.inspect(engine)
    tables = set(insp.get_table_names())

    assert "users" in tables
    assert "access_requests" in tables
    assert "audit_events" in tables
