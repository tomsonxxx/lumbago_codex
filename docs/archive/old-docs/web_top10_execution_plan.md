# Plan wykonania punktów webowych (Top 10) — ARCHIWALNY / DEPRECATED

**Uwaga: Desktop-only focus.** Web MVP (FastAPI + React) jest legacy i nie jest rozwijany dla głównej aplikacji Lumbago Music AI (która jest PyQt6 desktop z full DJ new arch migration).

Ten dokument jest historyczny. Główne flow (DJ, library, analysis, tagger) są w desktop (`lumbago_app`).

Punkty webowe poniżej zachowane dla odniesienia (dotyczyły standalone ID3 lub dawnego web planu).

## Punkt 2: CI/CD Web

- Dostarczono workflow: `.github/workflows/web-ci.yml`.
- Workflow uruchamia się warunkowo po wykryciu kodu web (`web/`, `frontend/`, `package.json`).

## Punkt 3: Naprawa Web audio playback

- Zadanie: ustabilizować player (`HTMLAudioElement` lub Howler), dodać obsługę błędów i retry.
- Done:
  - Odtwarzanie play/pause/seek działa dla min. MP3 + WAV.
  - Brak zatrzymań UI przy błędzie ładowania pliku.
  - Test integracyjny dla podstawowego flow odtwarzania.

## Punkt 4: Naprawa filtra Key (Camelot)

- Zadanie: unifikacja mapowania Camelot ↔ klucz muzyczny i filtrowanie bez false negatives.
- Done:
  - Filtr znajduje `8A`, `8a`, `Am`, `A minor` zgodnie z mapowaniem.
  - Testy jednostkowe mapowań i przypadków brzegowych.

## Punkt 5: Implementacja `ImportWizardModal` (Web)

- Zadanie: modal 4-krokowy (źródło, skan, podgląd, import).
- Done:
  - Walidacja ścieżek i raport błędów.
  - Obsługa anulowania procesu.
  - Testy UI kroku 1→4.

## Punkt 6: Implementacja `DuplicateFinderModal` (Web)

- Zadanie: widok grup duplikatów + akcje keep/delete/merge.
- Done:
  - Wykrywanie hash + metadata + fingerprint.
  - Akcje na grupie i log zmian.
  - Test przepływu UI + test integracyjny API.

## Punkt 8: Uzupełnienie Web DB (`settings`, `cache`, `tag_history`)

- Zadanie: dodać tabele i migracje.
- Done:
  - Migracje wersjonowane (up/down).
  - Repozytorium danych z CRUD.
  - Testy migracji i kompatybilności wstecz.

## Punkt 9: Testy Web (unit + integration)

- Zadanie: minimalny próg jakości dla krytycznych przepływów.
- Done:
  - Unit: walidacja metadata, mapowanie key, parser importu.
  - Integration: import -> tag -> zapis -> odczyt.
  - Raport testów publikowany w CI.
