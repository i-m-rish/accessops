set -euo pipefail

ROOT="$(pwd)"

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

cd "$BACKEND_DIR"

PY="python"
command -v python3 >/dev/null 2>&1 && PY="python3"

if [[ -f "requirements.txt" ]]; then
  $PY -m pip install -q -r requirements.txt || true
fi

$PY -m pytest -q -k "auth" || true
$PY -m pytest -q -k "request and not workflow" || true
$PY -m pytest -q -k "workflow or pending or policy or lifecycle" || true
$PY -m pytest -q
