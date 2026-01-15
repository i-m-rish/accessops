# AccessOps Backend Guardrails

## Reproducibility (must pass)
- Clean run:
  rm -f test.db && JWT_SECRET="test-secret" pytest -q

## Invariants
- JWT_SECRET is mandatory; no silent defaults.
- RBAC is enforced server-side; UI is never an authority.
- Alembic is the schema source of truth; no production create_all.
- Tests must not rely on old DB state; failures like "no such table" are harness regressions first.
