Lumbago Music AI - Complete package (generated)

Start locally (dev):
  ./start_local.sh

Start with docker-compose (prod-like):
  ./start_docker.sh

Build images and package artifacts:
  ./build_and_package.sh

CI: see .github/workflows/ci.yml for pipeline details.


## Run everything (dev)
Preferowane: użyj docker-compose.dev.yml:
  docker-compose -f docker-compose.dev.yml up --build
Alternatywnie: użyj run_all.sh (uruchamia docker if present, otherwise local servers):
  ./run_all.sh


## Uruchamianie lokalne i Docker

- Lokalnie (skrypt):
  - `./scripts/run_local.sh` (Linux/macOS). Skrypt tworzy venv, instaluje dependencies, inicjalizuje DB i uruchamia backend oraz frontend w tle (nohup). Logi w ./logs/.
- Docker:
  - `./scripts/run_docker.sh` - zbuduje obrazy i uruchomi docker-compose.prod.yml

## Celery (AI workers)
- Aby uruchomić worker dla analizy AI, uruchom:
  - `celery -A backend.app.ai_service.celery worker --loglevel=info`
- Broker: domyślnie Redis `redis://localhost:6379/0` (można skonfigurować przez env vars CELERY_BROKER, CELERY_BACKEND)

## Workers & audio dependencies

- Dodałem zależności audio (librosa, numpy, soundfile, ffmpeg-python, pyacoustid) do backend/requirements.txt.
- Worker Dockerfile znajduje się w backend/Dockerfile.worker i instaluje potrzebne systemowe biblioteki (ffmpeg, libsndfile, libchromaprint).

## Docker-compose (prod) updates

- `docker-compose.prod.yml` zawiera usługi: redis, backend, worker, frontend.
- Worker uruchamia Celery i łączy się z Redis.

## Kubernetes manifests

- Katalog k8s/ zawiera manifesty dla: backend, frontend, redis, postgres oraz szablon secretów.
- Skrypt deploy_do_digitalocean.sh przygotowuje kubeconfig i aplikuje manifesty (wymaga doctl + kubectl).

## Co dalej

- Uzupełnij GHCR/registry informacje w manifestach (zamień REPLACE_OWNER).
- Skonfiguruj GitHub Actions secrets do pushowania obrazów do rejestru.
- Dla Essentia lub innych native libs możesz potrzebować dodatkowych zależności systemowych w Dockerfile.


## Auth & Playlists

- Registration, login, refresh tokens implemented (argon2 hashing). Use endpoints:
  - POST /auth/register {email,password,display_name}
  - POST /auth/login {email,password}
  - POST /auth/refresh {refresh_token}

- Playlists endpoints: GET /api/playlists, POST /api/playlists

- Alembic-like migrations (sqlite friendly) available in backend/alembic/versions


## Duplicate Finder

- Backend module: `backend/app/duplicate_finder.py` contains the logic for hash, tag, and fingerprint comparisons.
- Endpoint: POST /api/duplicates/find will return groups of duplicates. In the skeleton it falls back to a mocked dataset.

### UI suggestions (Duplicate Finder Modal)
- Show waveform previews side-by-side for each candidate pair.
- Provide quick actions: Keep / Delete / Merge Metadata / Open in Editor.
- Allow batch operations with undo safety (trash bin + 30-day retention).
- Allow similarity threshold slider (0.5 - 1.0) for user tuning.


## ETAP 1 — Library Browser (done)

- Enhanced backend filters for /api/tracks (q, bpm_min, bpm_max, key, missing_metadata).
- Frontend components added: LibraryLayout, EnhancedTrackList, TrackGrid, FilterPanel, TrackDetailPanel, DockPlayer.
- Frontend tests (vitest) skeleton added for EnhancedTrackList.

### UI Simulation notes
- TrackList supports pagination, sorting, and basic import/scan actions.
- FilterPanel should be connected to API params to perform server-side filtering.
- TrackDetailPanel displays waveform (use generate_waveform.py to create images) and metadata editor.

### Next steps
- Connect FilterPanel inputs to EnhancedTrackList queries via axios/react-query.
- Implement Track selection to show details in TrackDetailPanel and control DockPlayer.
- Add real artwork thumbnails and waveform previews.


## ETAP 1 - Dopracowana Przeglądarka Biblioteki (Library Browser)

Wprowadziłem następujące zmiany i sugestie UI:

- TrackList: sortowanie kolumn (kliknięcie nagłówka), prosty resizing zachowany przez CSS.
- TrackGrid: pokazuje artwork gdy dostępne (metadata.artwork_path), klikalne karty.
- FilterPanel: BPM min/max, Key select, Missing metadata checkbox, Apply button.
- TrackDetailPanel: pobiera szczegóły tracka i oferuje Edit/Analyze przyciski.
- DockPlayer: prosty kontroler audio.

### Sugestie UX podczas importu i kolejnych etapów:
- Dodaj podgląd waveform w TrackDetailPanel (mini-waveform) - generowany przez `scripts/generate_waveform.py`.
- Podczas filtrowania pokaż licznik pasujących utworów i możliwość zapisu filtra jako Smart Collection.
- Dodaj lazy-loading obrazków w TrackGrid i placeholder skeleton.



## ETAP 1 — Library Browser (What was added)

- Backend: `/api/tracks` supports q (search), bpm_min, bpm_max, key, missing_metadata, skip, limit, sort.
- Frontend: full layout: LeftSidebar, FilterPanel, TrackList, TrackGrid, TrackDetailPanel, DockPlayer, TopbarSearch.
- TrackList supports pagination and sorting; TrackGrid has hover actions; FilterPanel applies filters to list.

### UI Simulation & Behavior (how it should feel):
- Start: Library Browser opens with Topbar search focused.
- Use FilterPanel to set BPM range; click Apply — list refreshes with server-side filter.
- Toggle List/Grid — grid shows artworks and hover actions (Play, Tag).
- Click track — TrackDetailPanel fetches waveform via `/api/tracks/{id}` and displays image if present.
- DockPlayer shows currently selected track and simple controls.

### Tests
- Backend tests added: `backend/tests/test_tracks_api.py` (basic smoke tests for search/filter endpoints).



## ETAP2 — Import Wizard
- Backend: scanner.py + /api/import/scan
- Frontend: ImportWizard modal
- Testy: test_scanner.py
