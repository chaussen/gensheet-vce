#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"

cleanup() {
  echo ""
  echo "==> Shutting down..."
  kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
  wait "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
}
trap cleanup INT TERM

echo "==> Starting backend on http://localhost:8000"
cd "$ROOT" && "$ROOT/venv/bin/uvicorn" backend.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

echo "==> Starting frontend on http://localhost:5173"
cd "$ROOT/frontend" && npm run dev &
FRONTEND_PID=$!

echo "==> Press Ctrl+C to stop both servers."
wait "$BACKEND_PID" "$FRONTEND_PID"
