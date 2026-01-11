from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import text

from app.db.session import engine
from app.main import app

client = TestClient(app)


def _wipe_tables() -> None:
    # Delete child rows first to avoid FK violations, even if cascade changes later.
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM access_requests"))
        conn.execute(text("DELETE FROM users"))


def _register(email: str, password: str, role: str) -> None:
    r = client.post("/auth/register", json={"email": email, "password": password, "role": role})
    assert r.status_code in (201, 409), r.text


def _login(email: str, password: str) -> str:
    r = client.post("/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def test_requester_can_create_and_list_own_requests() -> None:
    _wipe_tables()

    _register("req1@example.com", "StrongPass123", "REQUESTER")
    token = _login("req1@example.com", "StrongPass123")

    r = client.post(
        "/requests",
        headers={"Authorization": f"Bearer {token}"},
        json={"resource": "jira", "action": "READ", "justification": "Ticket triage"},
    )
    assert r.status_code == 201, r.text

    r2 = client.get("/requests", headers={"Authorization": f"Bearer {token}"})
    assert r2.status_code == 200, r2.text
    items = r2.json()
    assert len(items) == 1
    assert items[0]["resource"] == "jira"
    assert items[0]["status"] == "PENDING"


def test_requester_cannot_approve() -> None:
    _wipe_tables()

    _register("req2@example.com", "StrongPass123", "REQUESTER")
    token = _login("req2@example.com", "StrongPass123")

    r = client.post(
        "/requests",
        headers={"Authorization": f"Bearer {token}"},
        json={"resource": "confluence", "action": "WRITE"},
    )
    assert r.status_code == 201, r.text
    req_id = r.json()["id"]

    r2 = client.patch(
        f"/requests/{req_id}/approve",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r2.status_code == 403, r2.text


def test_approver_can_approve_and_list_all() -> None:
    _wipe_tables()

    _register("req3@example.com", "StrongPass123", "REQUESTER")
    _register("app1@example.com", "StrongPass123", "APPROVER")

    req_token = _login("req3@example.com", "StrongPass123")
    appr_token = _login("app1@example.com", "StrongPass123")

    r = client.post(
        "/requests",
        headers={"Authorization": f"Bearer {req_token}"},
        json={"resource": "aws", "action": "ADMIN"},
    )
    assert r.status_code == 201, r.text
    req_id = r.json()["id"]

    r2 = client.patch(
        f"/requests/{req_id}/approve",
        headers={"Authorization": f"Bearer {appr_token}"},
    )
    assert r2.status_code == 200, r2.text
    assert r2.json()["status"] == "APPROVED"

    r3 = client.get("/requests", headers={"Authorization": f"Bearer {appr_token}"})
    assert r3.status_code == 200, r3.text
    assert any(x["id"] == req_id for x in r3.json())

