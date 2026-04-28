# Lumbago Music AI — Chronologiczna, szczegółowa lista krok‑po‑kroku (dla agenta AI)

**Źródła dołączone:** Pełna dokumentacja projektu (MAX) i Rozszerzona dokumentacja techniczna.

> Ten dokument jest gotowy do wklejenia dla agenta AI. Zawiera: chronologiczny plan budowy systemu, szczegółowe instrukcje implementacyjne (frontend, backend, AI workers), implementację UI i modali zgodnie z najnowszymi plikami, checklisty testów oraz sugestie usprawnień. Każdy krok ma konkretne akcje, pliki do stworzenia, komendy i oczekiwane wyniki.

---

## Przed startem — założenia środowiskowe (prerequisites)
- System operacyjny: Linux / macOS.
- Docker, docker-compose, Node 18+, Python 3.11+, PostgreSQL, Redis, MinIO.
- Repo: root folder `lumbago/`.

---

# Faza 0 — Scaffold projektu (2 dni)
### 0.1 — Utwórz repo i strukturę katalogów
```
/backend
/frontend
/docs
/deploy
/.github/workflows
```

### 0.2 — Dodaj docker-compose

### 0.3 — Backend skeleton (FastAPI)

### 0.4 — Frontend skeleton (React + TS)

---

# Faza 1 — Core Auth + Tracks (5 dni)

### 1.1 — DB migrations (Alebmic)

### 1.2 — Implementacja JWT auth (register/login/refresh/logout)

### 1.3 — Upload audio do S3 (MinIO)

### 1.4 — Endpointy listowania i pobierania

---

# Faza 2 — Playlists + Views + Player (5 dni)

### 2.1 — CRUD playlist

### 2.2 — Widoki list/grid + komponenty UI

### 2.3 — PlayerDock + local queue

### 2.4 — Quick actions

---

# Faza 3 — Realtime WebSocket (3 dni)

### 3.1 — Backend WebSocket manager

### 3.2 — Frontend WebSocket hook

---

# Faza 4 — Workers, AI Jobs, Export (7 dni)

### 4.1 — Konfiguracja Celery

### 4.2 — AI job pipeline (enqueue → worker → upload)

### 4.3 — Export/Encoding (ffmpeg)

### 4.4 — Retry & idempotency

---

# Faza 5 — Modale, UX, dostępność (4 dni)

### 5.1 — System modali

### 5.2 — Tooltips & aria-labels

### 5.3 — UX polish

---

# Faza 6 — Testy, CI/CD, monitoring (6 dni)

### 6.1 — Unit + integration tests

### 6.2 — End‑to‑end tests (Cypress)

### 6.3 — GitHub Actions (lint, tests, build)

### 6.4 — Prometheus + Grafana + Sentry

---

# Faza 7 — Deployment & hardening

- S3 w chmurze
- CDN dla statyków
- Kubernetes & autoscaling
- Secrets manager

---

# Komendy — backend
```
pip install fastapi uvicorn sqlalchemy alembic psycopg2-binary pydantic passlib[bcrypt] python-jose boto3 celery redis
uvicorn app.main:app --reload
celery -A app.tasks.celery worker --loglevel=info
```

# Komendy — frontend
```
pnpm install
pnpm dev
```

---

# Checklist jakościowa
- [ ] Healthcheck OK
- [ ] Auth działa w pełnym flow
- [ ] Upload 3 plików OK
- [ ] Odtwarzanie działa
- [ ] AI job kończy się poprawnie
- [ ] WebSocket event widoczny w UI
- [ ] Export działa
- [ ] Testy unit/integration/E2E przechodzą
- [ ] CI pipeline zielony

---

# Sugestie usprawnień
- Dodać progress bars
- Zapisać preferencje UI użytkownika
- Dodać presety filtrów
- Implementować dostępność WCAG
- Mobilna wersja paneli

---

# Finalne artefakty do repo
- `/backend/app/*`
- `/frontend/src/*`
- `/docs/*.pdf`
- `/deploy/docker-compose.yml`
