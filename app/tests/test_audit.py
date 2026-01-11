import uuid

from sqlalchemy import text


def _u(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}@example.com"


def _register(client, email: str, password: str, role: str):
    r = client.post(
        "/auth/register",
        json={"email": email, "password": password, "role": role},
    )
    assert r.status_code in (200, 201), r.text


def _login(client, email: str, password: str) -> str:
    r = client.post("/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def _auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _create_request(client, requester_token: str) -> str:
    r = client.post(
        "/requests",
        headers=_auth_header(requester_token),
        json={"resource": "app:veracode", "action": "read", "justification": "need access"},
    )
    assert r.status_code == 201, r.text
    return r.json()["id"]


def test_approve_emits_audit_event(client, db_session):
    req_email = _u("req_audit")
    appr_email = _u("appr_audit")

    _register(client, req_email, "Passw0rd!", "REQUESTER")
    _register(client, appr_email, "Passw0rd!", "APPROVER")

    requester_token = _login(client, req_email, "Passw0rd!")
    approver_token = _login(client, appr_email, "Passw0rd!")

    request_id = _create_request(client, requester_token)

    r = client.patch(f"/requests/{request_id}/approve", headers=_auth_header(approver_token))
    assert r.status_code == 200, r.text

    rows = db_session.execute(
        text("select action, entity_type from audit_events where entity_id = :eid"),
        {"eid": request_id},
    ).fetchall()

    assert len(rows) == 1
    assert rows[0][0] == "access_request.approved"
    assert rows[0][1] == "access_request"


def test_reject_emits_audit_event(client, db_session):
    req_email = _u("req_audit")
    appr_email = _u("appr_audit")

    _register(client, req_email, "Passw0rd!", "REQUESTER")
    _register(client, appr_email, "Passw0rd!", "APPROVER")

    requester_token = _login(client, req_email, "Passw0rd!")
    approver_token = _login(client, appr_email, "Passw0rd!")

    request_id = _create_request(client, requester_token)

    r = client.patch(f"/requests/{request_id}/reject", headers=_auth_header(approver_token))
    assert r.status_code == 200, r.text

    rows = db_session.execute(
        text("select action, entity_type from audit_events where entity_id = :eid"),
        {"eid": request_id},
    ).fetchall()

    assert len(rows) == 1
    assert rows[0][0] == "access_request.rejected"
    assert rows[0][1] == "access_request"
