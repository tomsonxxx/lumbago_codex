# DJ Player — przewodnik (hotcue, memory, sync)

> Dokumentacja wersji desktopowej PyQt6. Ostatnia aktualizacja: 2026-06-14.

## Uruchomienie

1. Otwórz główne okno aplikacji.
2. Kliknij **DJ Player**.
3. Domyślny tryb: **Odtwarzacz** (single MVP). Przełącznik **Konsola DJ** (dual deck A/B) jest w tym samym oknie.

### Smoke test

```powershell
$env:LUMBAGO_SAFE_MODE=1; $env:LUMBAGO_SMOKE_SECONDS=3; python main.py
```

---

## Tryby okna

| Tryb | Opis |
|------|------|
| **Odtwarzacz (single)** | Jeden deck, duża waveform, transport PLAY/CUE/STOP, drag z biblioteki |
| **Konsola DJ (dual)** | Dwa decki A/B, hotcue 8 padów/deck, mixer, sync, memory S/R |
| **Compact (pilot)** | Zwinięty widok z animowanym wskaźnikiem obrotu przy odtwarzaniu |

### FILE vs STREAM

- **FILE** — drag&drop, `load_track`, zapis tagów, rename.
- **STREAM** — play/pause/seek/stop/cue, waveform playhead, hotcue jump.

---

## Hotcue

Hotcue to zapisana pozycja w utworze (ms). Służy do skoku (jump) lub ustawienia punktu startu.

### Zachowanie w UI

| Akcja | Efekt |
|-------|-------|
| Klik pad (pusty) | Ustaw hotcue na bieżącej pozycji playhead |
| Klik pad (zapisany) | Skok do zapisanego czasu |
| Shift + klik na waveform | Ustaw hotcue (dual) |
| Double-click waveform | Ustaw **main CUE** + seek (single) |

### Limity

- Dual deck: do **8** hotcue (indeksy 0–7)
- Single Odtwarzacz: do **4** padów
- Kolory z palety `BOOTH_COLORS`

### Persystencja

Hotcue dla utworów z `id` w bazie trafiają do tabeli cue points i są odtwarzane przy ponownym załadowaniu.

**Kod:** `ui/dj/hotcue_manager.py`, `ui/dj/views/hotcue_grid.py`

---

## Memory (S / R)

Sesyjny snapshot stanu decku (nie przetrwa restartu aplikacji).

- **S (Save)** — zapisuje snapshot
- **R (Recall)** — przywraca snapshot

### Zapisywane pola

`track_path`, `main_cue_ms`, `loop_in_ms`, `loop_out_ms`, `hotcues`, `pitch`, `trim`, `keylock`

### Recall

1. Reload pliku jeśli inny niż aktualny.
2. Przywraca hotcue, loop, cue, pitch/trim/keylock.
3. Wznawia odtwarzanie jeśli deck grał przed recall.

**Kod:** `ui/dj/views/memory_controls.py`, `DeckController.save_memory()` / `recall_memory()`

---

## Sync

Synchronizacja tempa i fazy decku docelowego z deckiem źródłowym (Rekordbox-style).

1. Załaduj utwory na A i B.
2. Kliknij **SYNC** na decku docelowym.

Technicznie: `rate = bpm_inny / bpm_mój`, seek do pozycji partnera. Wymaga znanych BPM. Tylko dual — single nie ma sync.

**Kod:** `DeckController.do_sync()`

---

## Waveform — color coding

| Kolor | Znaczenie |
|-------|-----------|
| Czerwony | Kick / bass |
| Żółty | Hi-hat / perkusja |
| Zielony | Wokale / środek |
| Niebieski | Breakdown / cicho |

---

## Testy

```bash
python -m pytest -q -k "dj or hotcue or playback or ui_smoke or e2e"
```

Ręczna checklista: `crew/CHECKLIST_reczny_test_nowy_DJ_Player.md`