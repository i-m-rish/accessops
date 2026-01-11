from fastapi.testclient import TestClient
from sqlalchemy import text

from app.main import app
from app.db.session import engine

client = TestClient(app)


def _wipe_tables() -> None:
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM access_requests"))
        conn.execute(text("DELETE FROM users"))


def _register(email: str, password: str, role: str) -> None:
    r = client.post(
        "/auth/register",
        json={"email": email, "password": password, "role": role},
    )
    assert r.status_code == 201, r.text


def _login(email: str, password: str) -> str:
    r = client.post("/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def test_approver_sees_only_pending_requests() -> None:
    _wipe_tables()

    _register("req@example.com", "StrongPass123", "REQUESTER")
    _register("app@example.com", "StrongPass123", "APPROVER")

    req_token = _login("req@example.com", "StrongPass123")
    app_token = _login("app@example.com", "StrongPass123")

    # Create two requests
    r1 = client.post(
        "/requests",
        headers={"Authorization": f"Bearer {req_token}"},
        json={"resource": "jira", "action": "READ"},
    )
    r2 = client.post(
        "/requests",
        headers={"Authorization": f"Bearer {req_token}"},
        json={"resource": "aws", "action": "ADMIN"},
    )
    assert r1.status_code == 201
    assert r2.status_code == 201

    # Approve one
    req_id = r1.json()["id"]
    client.patch(
        f"/requests/{req_id}/approve",
        headers={"Authorization": f"Bearer {app_token}"},
    )

    # Fetch pending queue
    r = client.get(
        "/requests/pending",
        headers={"Authorization": f"Bearer {app_token}"},
    )
    assert r.status_code == 200, r.text

    items = r.json()
    assert len(items) == 1
    assert items[0]["resource"] == "aws"
    assert items[0]["status"] == "PENDING"


def test_requester_cannot_access_pending_queue() -> None:
    _wipe_tables()

    _register("req2@example.com", "StrongPass123", "REQUESTER")
    token = _login("req2@example.com", "StrongPass123")

    r = client.get(
        "/requests/pending",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 403
