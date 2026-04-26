# AccessOps

AccessOps is an IAM/IGA-inspired access request, policy, provisioning lifecycle, and audit service.

## Current Scope

- FastAPI backend
- Next.js UI
- JWT authentication
- Server-side RBAC
- Secure requester registration
- Protected role management
- Access request approval/rejection
- Separate provisioning lifecycle tracking
- Audit events
- Alembic migrations
- Backend CI with PostgreSQL + pytest

## Documentation

| Document | Purpose |
|---|---|
| [Architecture](docs/ARCHITECTURE.md) | HLD, LLD, Mermaid diagrams, entity model, API table, lifecycle matrix. |
| [Backend Guardrails](README_GUARDRAILS.md) | Required engineering invariants and reproducibility checks. |

## Run Everything Locally

Prerequisites:
- Python 3.11+
- PostgreSQL running locally with database/user matching `DATABASE_URL`
- Node.js + npm if running the UI

Run backend validation:

```bash
bash scripts/run_all.sh
```

Run backend validation, then start backend and UI dev servers:

```bash
bash scripts/run_all.sh --serve
```

Default local environment used by the script:

```bash
DATABASE_URL=postgresql+psycopg://accessops:accessops@localhost:5432/accessops
JWT_SECRET=dev-secret-for-local-run
JWT_ALGORITHM=HS256
JWT_EXPIRES_MINUTES=60
```

## CI

GitHub Actions runs:

```bash
alembic upgrade head
pytest -q
```

against a PostgreSQL service.
