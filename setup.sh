#!/usr/bin/env bash
# BidSense one-shot setup + launch (macOS/Linux).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"

echo "[1/4] Backend dependencies..."
cd "$ROOT/backend"
python3 -m pip install -r requirements.txt --quiet
if [ ! -f .env ]; then
  cp .env.example .env
  echo "  Created backend/.env from example (no keys needed for the cached demo)."
fi

echo "[2/4] Frontend dependencies..."
cd "$ROOT/frontend"
npm install --silent

echo "[3/4] Starting backend on http://localhost:8000 (background)..."
cd "$ROOT/backend"
python3 -m uvicorn main:app --port 8000 &
BACKEND_PID=$!
trap "kill $BACKEND_PID 2>/dev/null || true" EXIT

echo "[4/4] Starting frontend on http://localhost:3000 ..."
echo "  Demo documents are in demo-assets/ - drag one onto the dropzone."
cd "$ROOT/frontend"
npm run dev
