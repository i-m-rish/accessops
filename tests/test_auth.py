from fastapi.testclient import TestClient
from sqlalchemy import text

from app.main import app
from app.db.session import engine

client = TestClient(app)


def _wipe_users() -> None:
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM users"))


def test_register_and_login() -> None:
    _wipe_users()

    r = client.post(
        "/auth/register",
        json={"email": "a@example.com", "password": "StrongPass123", "role": "REQUESTER"},
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["email"] == "a@example.com"
    assert body["role"] == "REQUESTER"
    assert "id" in body

    l = client.post("/auth/login", json={"email": "a@example.com", "password": "StrongPass123"})
    assert l.status_code == 200, l.text
    tok = l.json()
    assert "access_token" in tok
    assert tok["token_type"] == "bearer"


def test_register_duplicate_email_rejected() -> None:
    _wipe_users()

    r1 = client.post("/auth/register", json={"email": "dup@example.com", "password": "StrongPass123"})
    assert r1.status_code == 201, r1.text

    r2 = client.post("/auth/register", json={"email": "dup@example.com", "password": "StrongPass123"})
    assert r2.status_code == 400, r2.text
