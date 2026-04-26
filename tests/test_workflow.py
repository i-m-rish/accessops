from fastapi.testclient import TestClient
from sqlalchemy import text

from app.main import app
from app.db.session import SessionLocal, engine
from app.models.user import User

client = TestClient(app)


def _wipe_tables() -> None:
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM access_requests"))
        conn.execute(text("DELETE FROM users"))


def _register(email: str, password: str) -> None:
    r = client.post(
        "/auth/register",
        json={"email": email, "password": password},
    )
    assert r.status_code == 201, r.text


def _set_role_for_test(email: str, role: str) -> None:
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).one()
        user.role = role
        db.commit()
    finally:
        db.close()


def _login(email: str, password: str) -> str:
    r = client.post("/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def test_approver_sees_only_pending_requests() -> None:
    _wipe_tables()

    _register("req@example.com", "StrongPass123")
    _register("app@example.com", "StrongPass123")
    _set_role_for_test("app@example.com", "APPROVER")

    req_token = _login("req@example.com", "StrongPass123")
    app_token = _login("app@example.com", "StrongPass123")

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

    req_id = r1.json()["id"]
    client.patch(
        f"/requests/{req_id}/approve",
        headers={"Authorization": f"Bearer {app_token}"},
    )

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

    _register("req2@example.com", "StrongPass123")
    token = _login("req2@example.com", "StrongPass123")

    r = client.get(
        "/requests/pending",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 403
