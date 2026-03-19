#!/usr/bin/env bash
set -euo pipefail
echo "Starting Lumbago Music AI (local dev)..."
cd backend
if [ ! -d ".venv" ]; then python3 -m venv .venv; fi
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
nohup uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload > backend.log 2>&1 &
sleep 1
cd ../frontend
if [ ! -d "node_modules" ]; then npm ci; fi
nohup npm run dev > frontend.log 2>&1 &
echo "Started. Frontend: http://localhost:5173 Backend: http://localhost:8000/health"
