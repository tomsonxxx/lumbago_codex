
# **Plan Budowy Systemu Lumbago Music AI**
## **Dokumentacja Scalona v2.1**

---

# **1. Status Obecny (MVP Client-Side - Zrealizowane)**

### 🟢 Faza 1: Przeglądarka Biblioteki & UI V3
*   ✅ **Neon UI (Cyberpunk):** Przebudowa layoutu na ciemny motyw z akcentami Cyan/Magenta.
*   ✅ **Start Screen:** Nowy ekran powitalny z siatką akcji i animacjami.
*   ✅ **Sidebar V2:** Zastąpiono stary pasek boczny nowym, spójnym ze stylem Neon.
*   ✅ **Widok Biblioteki:**
    *   3-kolumnowy layout (Lista + Prawy Panel Inspektora).
    *   Aktywny utwór ("Active Track") z dużą okładką i wizualizacją.
*   ✅ **Organizacja:** Sortowanie po wszystkich polach, filtrowanie (Rok, Gatunek, Status).

### 🟢 Faza 2: Import & Skaner
*   ✅ **System Importu:** Drag & Drop, Folder Scan, URL Import.
*   ✅ **Direct Access (File System API):** Edycja plików bezpośrednio na dysku użytkownika.
*   ✅ **Odczyt Tagów:** Obsługa ID3 (MP3), MP4 Atoms (M4A), Vorbis (FLAC).

### 🟢 Faza 3: Smart Tagger AI
*   ✅ **Integracja:** Bezpośrednie połączenie z **Gemini 3.0 Pro** (Client-side API).
*   ✅ **Search Grounding:** Użycie Google Search Tool do weryfikacji metadanych.
*   ✅ **Wydajność:** Przetwarzanie wsadowe (Batch) z kolejką równoległą.

### 🟢 Faza 4: Narzędzia DJ-skie
*   ✅ **Wyszukiwarka Duplikatów:** Analiza po nazwie, metadanych i rozmiarze.
*   ✅ **Konwerter XML:** Import baz danych Rekordbox i VirtualDJ.
*   ✅ **Odtwarzacz:** Globalny Dock Player z wizualizacją Web Audio API.
*   ✅ **Playlisty:** Lokalne playlisty + eksport do `.m3u8`.

---

# **2. Plan Rozwoju: Faza "Fullstack" (Architektura Docelowa)**

Poniższe kroki transformują aplikację z narzędzia lokalnego w system chmurowy z backendem.

### 🚧 Krok 1: Backend Setup (Python/FastAPI)
- [ ] Uruchomienie serwera FastAPI (patrz: `lumbago-skeleton/backend`).
- [ ] Konfiguracja bazy danych PostgreSQL i migracji Alembic.
- [ ] System kolejek Celery + Redis (do ciężkich zadań w tle).

### 🚧 Krok 2: Uwierzytelnianie i Użytkownicy
- [ ] Rejestracja i logowanie (JWT Auth).
- [ ] Role użytkowników (Free/Pro).
- [ ] Synchronizacja ustawień między urządzeniami.

### 🚧 Krok 3: Przeniesienie Logiki na Serwer (Hybrid Mode)
- [ ] **Cloud Storage (S3/MinIO):** Upload plików dla użytkowników chmurowych (backup biblioteki).
- [ ] **Zaawansowana Analiza Audio (Server-side):**
    *   Użycie bibliotek `librosa` / `essentia` na backendzie do precyzyjnego wykrywania BPM i Tonacji (zamiast polegania na tagach).
    *   Generowanie pełnych waveformów (PNG/JSON) i przechowywanie w bazie.
    *   Audio Fingerprinting (Chromaprint) do perfekcyjnego wykrywania duplikatów audio.

### 🚧 Krok 4: Kolaboracja i Real-time
- [ ] WebSocket server (Powiadomienia o postępie zadań AI).
- [ ] Współdzielenie playlist między użytkownikami.

---

# **3. Czeklista ToDo (Usprawnienia Obecnej Wersji Client-Side)**

Zanim przejdziemy do backendu, należy dopracować obecną wersję przeglądarkową.

### 🛠️ UX & Fixes
- [ ] **Smart Playlists (UI):** Dodać interfejs do edycji reguł inteligentnych playlist (obecnie tylko tworzenie).
- [ ] **Wydajność Grid:** Wirtualizacja listy (Virtual Scrolling) dla bibliotek > 1000 utworów.

### 🎵 Audio Engine (Client-side)
- [ ] **Lokalna analiza BPM:** Zbadanie możliwości użycia `essentia.js` (WebAssembly) do wykrywania BPM bezpośrednio w przeglądarce, jako fallback dla AI/Tagów.
- [ ] **Edycja Audio:** Proste przycinanie ciszy (trimming) przy użyciu `ffmpeg.wasm`.

---

### **Instrukcja dla Agenta:**
Przy kolejnych zadaniach sprawdzaj sekcję **"3. Czeklista ToDo"** dla usprawnień bieżących, lub **"2. Plan Rozwoju"** jeśli użytkownik poprosi o funkcje backendowe (logowanie, chmura).
