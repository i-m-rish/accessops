#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

MODE="${1:-test}"
PYTHON_BIN="${PYTHON_BIN:-}"

export DATABASE_URL="${DATABASE_URL:-postgresql+psycopg://accessops:accessops@localhost:5432/accessops}"
export JWT_SECRET="${JWT_SECRET:-dev-secret-for-local-run}"
export JWT_ALGORITHM="${JWT_ALGORITHM:-HS256}"
export JWT_EXPIRES_MINUTES="${JWT_EXPIRES_MINUTES:-60}"

echo "== AccessOps run_all =="
echo "Mode: $MODE"
echo "Root: $ROOT_DIR"
echo

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing required command: $1" >&2
    exit 1
  fi
}

pick_python() {
  if [[ -n "$PYTHON_BIN" ]]; then
    echo "$PYTHON_BIN"
    return
  fi

  if command -v python3 >/dev/null 2>&1; then
    echo "python3"
    return
  fi

  if command -v python >/dev/null 2>&1; then
    echo "python"
    return
  fi

  echo "Missing Python. On macOS, install with: brew install python" >&2
  exit 1
}

PYTHON_CMD="$(pick_python)"

if [[ "$OSTYPE" == darwin* ]]; then
  echo "macOS detected. If PostgreSQL is not running, start it with one of:"
  echo "  brew services start postgresql@16"
  echo "  brew services start postgresql"
  echo
fi

if [[ ! -d .venv ]]; then
  echo "Creating Python virtual environment with $PYTHON_CMD..."
  "$PYTHON_CMD" -m venv .venv
fi

# shellcheck disable=SC1091
source .venv/bin/activate

python -m pip install --upgrade pip
pip install -r requirements.txt

echo "Running database migrations..."
alembic upgrade head

echo "Running backend tests..."
pytest -q

if [[ "$MODE" == "--serve" || "$MODE" == "serve" ]]; then
  require_cmd npm

  echo "Installing UI dependencies..."
  (cd accessops-ui && npm install)

  echo "Starting backend on http://127.0.0.1:8000 and UI on http://localhost:3000"
  uvicorn app.main:app --reload --host 127.0.0.1 --port 8000 &
  API_PID=$!

  cleanup() {
    kill "$API_PID" >/dev/null 2>&1 || true
  }
  trap cleanup EXIT

  (cd accessops-ui && NEXT_PUBLIC_API_BASE="http://127.0.0.1:8000" npm run dev)
fi

echo "Done."
