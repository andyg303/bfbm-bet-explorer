#!/usr/bin/env bash
# Quick-start without Docker (requires local Postgres + Node + Python)
# For one-command startup with zero dependencies, use: docker compose up --build
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Override DB_HOST for local dev (Docker Compose sets it to 'db')
export DB_HOST="${DB_HOST:-localhost}"

# Backend
echo "🚀 Starting backend..."
cd "$SCRIPT_DIR/backend"
python api/main.py &
BACKEND_PID=$!

# Frontend (install deps if needed)
echo "🚀 Starting frontend..."
cd "$SCRIPT_DIR/frontend"
[ -d node_modules ] || npm install
npx vite &
FRONTEND_PID=$!

echo ""
echo "✅  Backend  → http://localhost:8000"
echo "✅  Frontend → http://localhost:5173"
echo ""
echo "Press Ctrl+C to stop both."

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM
wait
