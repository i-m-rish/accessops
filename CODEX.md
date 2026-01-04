# CODEX Operating Manual — AccessOps

## Source of Truth
- PRD.md is authoritative. If any ambiguity exists, ask questions in comments, do NOT invent features.

## Scope Discipline
- Implement only what is explicitly required for the current task.
- Do NOT add “nice-to-haves”, extra endpoints, extra tables, or extra libraries.

## Code Style
- Python 3.11
- FastAPI
- SQLAlchemy 2.0
- Pydantic v2
- Postgres (via docker-compose)
- Keep code minimal, clean, production-style.
- Prefer explicitness over “magic”.

## Architecture Rules
- API routers in `app/routers`
- DB session in `app/db/session.py`
- Settings in `app/core/config.py`
- Models in `app/models`
- Schemas in `app/schemas` (create when needed)
- Services in `app/services` (create when needed)
- Tests in `tests/`

## Security Rules (v1)
- No secrets committed (use env vars / .env)
- Passwords must be hashed (when auth is implemented)
- RBAC enforced at endpoint layer
- Audit events are append-only

## Testing Rules
- Every new endpoint must have at least one test.
- Use pytest.
- Keep tests small and deterministic.

## Git / PR Rules
- Work in small increments.
- Each task = one coherent commit.
- Do not refactor unrelated files.

## Output Format
When you finish a task, provide:
1) List of files changed/created
2) How to run locally
3) How to run tests
4) Any known limitations
