# AccessOps Build Tasks (Codex Execution Plan)

## Task 01 — Scaffold API + Docker + Health
- Add FastAPI app skeleton
- GET /health returns {"status":"ok"}
- requirements.txt pinned
- Dockerfile
- docker-compose.yml with api + postgres
- tests/test_health.py

Acceptance:
- `uvicorn app.main:app --reload` runs
- `pytest -q` passes
- `docker compose up --build` works
- GET /health works locally and via docker

---

## Task 02 — Database Base + Migrations (Alembic)
- Add Alembic setup
- Add database connection config
- Create empty initial migration (no domain models yet)

Acceptance:
- `alembic current` works
- `alembic upgrade head` works

---

## Task 03 — Auth v1 (Register/Login/JWT)
- POST /auth/register
- POST /auth/login
- JWT access token
- User model: email, password_hash, role
- RBAC dependency helper

Acceptance:
- Can register, login, call a protected endpoint
- Password hashing implemented
- Tests for register/login

---

## Task 04 — Core Domain Models
- AccessRequest
- ApprovalDecision
- AuditEvent (append-only)
- ProvisioningJob

Acceptance:
- Alembic migration creates tables
- Basic CRUD via DB session works in tests

---

## Task 05 — Requests API (Create + View)
- POST /requests (REQUESTER)
- GET /requests/me (REQUESTER)
- GET /requests/{id} (owner or ADMIN)
- On create: write AuditEvent(REQUEST_CREATED)
- Policy evaluation sets required_approvals

Acceptance:
- Tests cover: create request, view me, view by id

---

## Task 06 — Approvals API (Approve/Reject)
- GET /approvals/pending (APPROVER)
- POST /requests/{id}/approve
- POST /requests/{id}/reject
- On decision: write AuditEvent
- On reject: request -> REJECTED
- On sufficient approvals: request -> APPROVED and enqueue ProvisioningJob

Acceptance:
- Tests cover approval flow, rejection flow, RBAC

---

## Task 07 — Provisioning Worker (Simulated)
- Background job runner (simple: FastAPI BackgroundTasks or a minimal worker service)
- ProvisioningJob transitions: QUEUED -> RUNNING -> SUCCEEDED/FAILED
- Audit events for start/success/failure

Acceptance:
- Tests verify job status change and audit events

---

## Task 08 — Audit API
- GET /audit (ADMIN only)
- Filter by entity_type/entity_id

Acceptance:
- Tests cover RBAC + filtering
