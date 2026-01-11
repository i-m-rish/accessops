set -euo pipefail

BACKEND_DIR=""
for d in backend api server app; do
  if [[ -d "$d" ]]; then
    BACKEND_DIR="$d"
    break
  fi
done

if [[ -z "$BACKEND_DIR" ]]; then
  echo "BACKEND_DIR_NOT_FOUND"
  exit 1
fi

export JWT_SECRET="${JWT_SECRET:-test-secret-not-for-prod}"
export ENV="${ENV:-test}"
export PYTHONUNBUFFERED=1

if [[ -f "docker-compose.yml" || -f "docker-compose.yaml" ]]; then
  docker compose up -d
  docker compose ps
fi

for p in 8000 8080 5000; do
  if curl -fsS "http://localhost:${p}/health" >/dev/null 2>&1; then
    curl -fsS "http://localhost:${p}/health"
    curl -fsS "http://localhost:${p}/openapi.json" >/dev/null 2>&1 || true
    break
  fi
done

ROOT="$(pwd)"
PY="$ROOT/.venv/Scripts/python.exe"

if [[ ! -f "$PY" ]]; then
  echo "VENV_PYTHON_NOT_FOUND:$PY"
  exit 1
fi

if [[ -f "$ROOT/requirements.txt" ]]; then
  "$PY" -m pip install -q -r "$ROOT/requirements.txt" || true
elif [[ -f "$ROOT/$BACKEND_DIR/requirements.txt" ]]; then
  "$PY" -m pip install -q -r "$ROOT/$BACKEND_DIR/requirements.txt" || true
fi

"$PY" -m pytest -q "$BACKEND_DIR" -k "auth" || true
"$PY" -m pytest -q "$BACKEND_DIR" -k "request and not workflow" || true
"$PY" -m pytest -q "$BACKEND_DIR" -k "workflow or pending or policy or lifecycle" || true
"$PY" -m pytest -q "$BACKEND_DIR"
