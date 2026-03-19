# Decyzja IPC (WinUI 3 ↔ Python)

Data: 2026-03-19
Status: zatwierdzone do MVP

## Wybrany model

- Model IPC: lokalne HTTP na `127.0.0.1` (FastAPI w procesie Python).

## Dlaczego

- Najniższy koszt wdrożenia i debugowania.
- Prosta integracja z testami CI oraz przyszłym web bridge.
- Czytelna separacja: UI (WinUI) i logika domenowa (Python).

## Zakres MVP

- WinUI 3 jako klient.
- Python uruchamia lokalny serwer API.
- Autoryzacja lokalna tokenem sesyjnym w pamięci procesu.
- Brak ekspozycji na sieć zewnętrzną (bind tylko `127.0.0.1`).

## Konsekwencje

- Named Pipes i COM odkładamy po MVP.
- Definicja kontraktu API musi być utrzymana wersyjnie.
- Wydajność i bezpieczeństwo kontrolowane przez limity endpointów i walidację payloadów.

## Kryteria Done

- Szkielet endpointów health + metadata/tag + duplicates.
- Klient WinUI korzysta z jednego adaptera HTTP.
- Test integracyjny: start backendu, handshake, pojedyncza operacja tagowania.
