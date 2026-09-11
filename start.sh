#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

if [[ -f .venv/bin/activate ]]; then
  source .venv/bin/activate
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is optional for local development. Running backend and frontend directly."
else
  echo "Starting Docker services for PostgreSQL and Redis..."
  docker compose up -d postgres redis
fi

cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

cd ../frontend
npm run dev -- --host 0.0.0.0 --port 3000 &
FRONTEND_PID=$!

trap "kill $BACKEND_PID $FRONTEND_PID" EXIT
wait
