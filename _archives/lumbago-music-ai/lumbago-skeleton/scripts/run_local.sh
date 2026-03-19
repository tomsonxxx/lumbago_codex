#!/usr/bin/env bash
set -e
mkdir -p logs
echo "Setting up local environment for Lumbago Music AI (skeleton)"

# Backend
echo "-> Backend: creating venv and installing requirements"
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
echo "-> Initializing DB (sqlite)"
python -c "from app.init_db import init_db; init_db()" || true

# Start backend (in background)
echo "-> Starting backend uvicorn on :8000 (nohup)"
nohup uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 > ../logs/backend.log 2>&1 &
sleep 1

# Frontend
echo "-> Frontend: installing npm deps (if needed)"
cd ../frontend
npm ci
echo "-> Starting frontend dev server (vite) on :5173 (nohup)"
nohup npm run dev > ../logs/frontend.log 2>&1 &
sleep 1

echo "Done. Backend: http://localhost:8000/health  Frontend: http://localhost:5173"
