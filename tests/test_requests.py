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


def _register(email: str, password: str, role: str | None = None) -> dict:
    payload = {"email": email, "password": password}
    if role is not None:
        payload["role"] = role
    r = client.post("/auth/register", json=payload)
    assert r.status_code in (201, 400, 409, 422), r.text
    return r.json()


def _create_user_direct(email: str, password: str, role: str) -> None:
    r = client.post("/auth/register", json={"email": email, "password": password})
    assert r.status_code in (201, 400), r.text
    with engine.begin() as conn:
        conn.execute(text("UPDATE users SET role = :role WHERE email = :email"), {"role": role, "email": email})


def _user_id(email: str) -> str:
    with engine.begin() as conn:
        return str(conn.execute(text("SELECT id FROM users WHERE email = :email"), {"email": email}).scalar_one())


def _login(email: str, password: str) -> str:
    r = client.post("/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def test_registration_rejects_client_supplied_role() -> None:
    _wipe_tables()

    r = client.post(
        "/auth/register",
        json={"email": "evil@example.com", "password": "StrongPass123", "role": "ADMIN"},
    )

    assert r.status_code == 422, r.text


def test_registration_defaults_to_requester() -> None:
    _wipe_tables()

    r = client.post("/auth/register", json={"email": "req0@example.com", "password": "StrongPass123"})

    assert r.status_code == 201, r.text
    assert r.json()["role"] == "REQUESTER"


def test_admin_can_update_user_role() -> None:
    _wipe_tables()

    _create_user_direct("admin@example.com", "StrongPass123", "ADMIN")
    _register("target@example.com", "StrongPass123")

    admin_token = _login("admin@example.com", "StrongPass123")
    target_id = _user_id("target@example.com")

    r = client.patch(
        f"/admin/users/{target_id}/role",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"role": "APPROVER"},
    )

    assert r.status_code == 200, r.text
    assert r.json()["role"] == "APPROVER"


def test_non_admin_cannot_update_user_role() -> None:
    _wipe_tables()

    _register("requester@example.com", "StrongPass123")
    _register("target2@example.com", "StrongPass123")

    requester_token = _login("requester@example.com", "StrongPass123")
    target_id = _user_id("target2@example.com")

    r = client.patch(
        f"/admin/users/{target_id}/role",
        headers={"Authorization": f"Bearer {requester_token}"},
        json={"role": "APPROVER"},
    )

    assert r.status_code == 403, r.text


def test_requester_can_create_and_list_own_requests() -> None:
    _wipe_tables()

    _register("req1@example.com", "StrongPass123")
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

    _register("req2@example.com", "StrongPass123")
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

    _register("req3@example.com", "StrongPass123")
    _create_user_direct("app1@example.com", "StrongPass123", "APPROVER")

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

