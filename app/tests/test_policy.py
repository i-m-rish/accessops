import uuid


def _u(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}@example.com"


def _register(client, email: str, password: str, role: str):
    r = client.post("/auth/register", json={"email": email, "password": password, "role": role})
    assert r.status_code in (200, 201), r.text


def _login(client, email: str, password: str) -> str:
    r = client.post("/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def _h(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_self_approval_forbidden(client):
    email = _u("selfappr")
    _register(client, email, "Passw0rd!", "APPROVER")
    token = _login(client, email, "Passw0rd!")

    r = client.post(
        "/requests",
        headers=_h(token),
        json={"resource": "app:x", "action": "read", "justification": "need"},
    )
    assert r.status_code == 201, r.text
    rid = r.json()["id"]

    r2 = client.patch(f"/requests/{rid}/approve", headers=_h(token))
    assert r2.status_code == 403, r2.text


def test_approve_non_pending_fails(client):
    req_email = _u("req")
    appr_email = _u("appr")

    _register(client, req_email, "Passw0rd!", "REQUESTER")
    _register(client, appr_email, "Passw0rd!", "APPROVER")

    req_token = _login(client, req_email, "Passw0rd!")
    appr_token = _login(client, appr_email, "Passw0rd!")

    r = client.post(
        "/requests",
        headers=_h(req_token),
        json={"resource": "app:y", "action": "read", "justification": "need"},
    )
    assert r.status_code == 201, r.text
    rid = r.json()["id"]

    r1 = client.patch(f"/requests/{rid}/approve", headers=_h(appr_token))
    assert r1.status_code == 200, r1.text

    r2 = client.patch(f"/requests/{rid}/approve", headers=_h(appr_token))
    assert r2.status_code == 400, r2.text
