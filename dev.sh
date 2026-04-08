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

# Kill any stale process holding port 8000
if lsof -ti:8000 >/dev/null 2>&1; then
  echo "==> Port 8000 already in use — killing stale process..."
  kill "$(lsof -ti:8000)" 2>/dev/null || true
  sleep 1
fi

echo "==> Starting backend on http://localhost:8000"
cd "$ROOT" && "$ROOT/venv/bin/uvicorn" backend.main:app \
  --host 0.0.0.0 --port 8000 --reload \
  --log-level info \
  2>&1 | sed -u 's/^/[backend] /' &
BACKEND_PID=$!

# Wait until backend accepts connections (up to 10 s)
echo -n "==> Waiting for backend"
for i in $(seq 1 20); do
  if curl -sf http://localhost:8000/docs >/dev/null 2>&1; then
    echo " ready"
    break
  fi
  echo -n "."
  sleep 0.5
  if [ "$i" -eq 20 ]; then
    echo ""
    echo "==> ERROR: Backend did not start in 10 s — scroll up for [backend] error lines"
  fi
done

echo "==> Starting frontend on http://localhost:5173"
cd "$ROOT/frontend" && npm run dev 2>&1 | sed -u 's/^/[frontend] /' &
FRONTEND_PID=$!

echo "==> Press Ctrl+C to stop both servers."
wait "$BACKEND_PID" "$FRONTEND_PID"
