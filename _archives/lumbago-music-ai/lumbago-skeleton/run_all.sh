#!/usr/bin/env bash
set -euo pipefail
echo "Starting Lumbago Music AI (dev) - run_all.sh"

# Start docker-compose dev if docker available
if command -v docker >/dev/null 2>&1 && command -v docker-compose >/dev/null 2>&1; then
  echo "Detected docker. Starting docker-compose.dev.yml..."
  docker-compose -f docker-compose.dev.yml up --build -d
  echo "Docker compose started. Frontend at http://localhost:5173, Backend at http://localhost:8000"
  exit 0
fi

echo "Docker not found. Running local dev servers (requires python/node)."

# Backend
cd backend
python -m venv .venv || true
source .venv/bin/activate
pip install -r requirements.txt
# Start worker in background (requires celery installed)
echo "Starting celery worker (in background)..."
celery -A backend.app.celery_app.celery worker --loglevel=info -Q ai &
# Start uvicorn
uvicorn backend.app.main:app --reload --port 8000 &
BACKEND_PID=$!

# Frontend
cd ../frontend
npm install
npm run dev &
FRONTEND_PID=$!

echo "Servers started. Backend PID=$BACKEND_PID, Frontend PID=$FRONTEND_PID"
echo "Press CTRL+C to stop."
wait
