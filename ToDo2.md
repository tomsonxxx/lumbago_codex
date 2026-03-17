# ToDo2 — Lumbago Music AI (Plan od podstaw, Windows UI)

## Legenda
- [ ] do zrobienia
- [x] zrobione
- [~] pominięte

## Priorytety
- P0 — krytyczne (MVP)
- P1 — bardzo ważne
- P2 — ważne
- P3 — mile widziane

## Estymacje (orientacyjne)
- S: 1–3h
- M: 4–8h
- L: 1–2 dni
- XL: 3–5 dni

---

# Etap 0 — Założenia i decyzje startowe (P0)
- [x] (P0, S) Potwierdzić docelową technologię UI na Windows (WinUI 3 vs Qt)
- [ ] (P0, S) Zdecydować o modelu integracji UI z logiką (lokalny API / IPC)
- [ ] (P0, S) Zdefiniować zakres MVP (moduły obowiązkowe na start)
- [x] (P0, S) Ustalić docelowy styl wizualny (kierunek, klimat, kontrast)

# Etap 1 — Audyt i konsolidacja wiedzy (P0)
- [x] (P0, S) Przegląd dokumentacji obecnego projektu
- [x] (P0, S) Przegląd Build.md i ToDo.md
- [x] (P0, M) Przegląd dokumentacji poprzednich projektów
- [x] (P0, S) Przegląd szkiców WinUI 3 (docs/winui3) i podglądów UI

# Etap 2 — Benchmark funkcji i wzorców UI (P0/P1)
- [x] (P0, M) Zmapować wzorce z aplikacji DJ i menedżerów biblioteki
- [x] (P1, M) Spisać listę wzorców do adaptacji (nawigacja, biblioteka, player)
- [x] (P1, M) Zidentyfikować „must‑have” interakcje (drag&drop, bulk actions) (v1)

# Etap 3 — Architektura informacji i nawigacja (P0)
- [x] (P0, M) Zdefiniować mapę widoków i przepływy użytkownika (v1)
- [x] (P0, M) Ustalić strukturę nawigacji (lewy panel, topbar, dock) (v1)
- [x] (P1, M) Określić stany widoków (puste, ładowanie, błędy) (v1)

# Etap 4 — Design system (P0/P1)
- [x] (P0, M) Paleta kolorów, typografia i skale odstępów (v1)
- [x] (P0, M) Zestaw komponentów bazowych (Button, Input, Card, Panel) (v1)
- [x] (P1, M) Style listy/siatki, tabele, chipy, tagi i suwaki (v1)
- [x] (P1, M) Zasady kontrastu i dostępności (v1)

# Etap 5 — Makiety kluczowych widoków (P0/P1)
- [x] (P0, M) Start / Dashboard (v1)
- [x] (P0, L) Biblioteka: lista + siatka + panel filtrów + panel szczegółów (v1)
- [x] (P0, M) Import / Skaner (v1)
- [x] (P1, M) Duplikaty (v1)
- [x] (P1, M) Konwerter XML (v1)
- [x] (P1, M) Ustawienia (API, zachowanie, cache) (v1)
- [x] (P1, M) Porównanie tagów (v1)
- [x] (P1, M) Smart Tagger / AI (v1)
- [x] (P1, M) Playlisty i smart playlisty (v1)
- [x] (P1, M) Globalny odtwarzacz (dock) (v1)

# Etap 6 — Prototyp interaktywny (P1)
- [ ] (P1, M) Prototyp klikany dla głównych flow
- [ ] (P1, S) Przegląd z Tobą i korekty

# Etap 7 — Implementacja UI (P0/P1)
- [ ] (P0, L) Szkielet aplikacji (shell, nawigacja, routing)
- [ ] (P0, L) Widok Biblioteki z listą, siatką i filtrami
- [ ] (P1, L) Widoki: Import, Duplikaty, Konwerter, Ustawienia
- [ ] (P1, L) Dialog Porównania Tagów i Smart Tagger
- [ ] (P1, L) Globalny odtwarzacz + pasek akcji

# Etap 8 — Integracja z logiką (P0/P1)
- [ ] (P0, M) Podłączenie danych: tracki, playlisty, tagi
- [ ] (P1, M) Akcje masowe i edycje w UI
- [ ] (P1, M) Integracja AI Taggera i kolejek

# Etap 9 — Testy i jakość (P1/P2)
- [ ] (P1, M) Testy UI kluczowych flow
- [ ] (P1, M) Testy dostępności
- [ ] (P2, M) Testy wydajności listy (duże biblioteki)

# Etap 10 — Dokumentacja i release (P1/P2)
- [ ] (P1, S) Aktualizacja dokumentacji projektu
- [ ] (P1, S) Build2.md — log zmian
- [ ] (P2, S) Checklist testu na czystym Windows

---

# Plan współpracy z Tobą (szybkie checkpointy)
- [x] (P0, S) Zatwierdzenie kierunku stylu i technologii UI
- [ ] (P0, S) Akceptacja mapy widoków i nawigacji
- [ ] (P1, S) Akceptacja makiet Biblioteki i Odtwarzacza
- [ ] (P1, S) Akceptacja całego zestawu makiet

---

# Plan projektowania UI (współpraca)
- [x] (P0, S) Warsztat stylu: paleta, typografia, efekty „neon glass” (v1)
- [x] (P0, M) Mapa widoków i przepływów: „Start → Biblioteka → Akcje” (v1)
- [x] (P0, M) Makieta Biblioteki (lista + siatka + filtry + detail) (v1)
- [ ] (P1, M) Makieta Importu i Duplikatów
- [x] (P1, M) Makieta Odtwarzacza (dock) + Quick Actions (v1)
- [x] (P1, M) Makieta Tag Compare i Smart Tagger (v1)
- [ ] (P1, S) Przegląd i korekty wspólne

---

# Notatki scalające (źródła)
- Build.md i ToDo.md: kompletna funkcjonalność i stan implementacji
- docs/winui3: szkice XAML dla nowego UI
- plany „plan_budowy_lumbago.md”: priorytet Biblioteki jako centrum
- makiety z lumbago_app/ui/assets/mockups i docs/winui3/previews
- docs/winui3/ui_plan.md: styl, mapa widoków i makieta Biblioteki (v1)

---

# Wzorce do adaptacji (wstępnie)
- Biblioteka jako centralny widok z listą utworów i kolumnami
- Panel boczny z playlistami/crates oraz szybkim przełączaniem widoków
- Filtry i wyszukiwanie jako stałe elementy pracy z biblioteką
- Odtwarzacz w formie docka z podstawowymi kontrolkami
- Dodatkowy panel boczny na kolejkę / podgląd / narzędzia (sideview)
- Smart playlisty / autoplaylisty oparte o reguły
- Podgląd i szybkie odtwarzanie z listy (preview)
