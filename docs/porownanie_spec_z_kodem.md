# Porównanie: specyfikacja z `lumbagov3_extracted/1.md` vs obecny kod

## Kontekst

Nie udało się automatycznie odczytać podanego linku `chatgpt.com/shared/...`, ponieważ strona zwraca ekran ochronny `Just a moment...` (Cloudflare). W repozytorium znajduje się jednak lokalna, rozbudowana specyfikacja produktu w pliku `lumbagov3_extracted/1.md`, więc to ją potraktowałem jako materiał referencyjny do porównania.

## TL;DR

Obecny kod **nie jest implementacją 1:1 opisanej architektury webowej**, ale zawiera już sporą część **funkcji domenowych**. Największa rozbieżność dotyczy **architektury**:

- spec opisuje **SPA React + FastAPI + PostgreSQL + Redis + Celery + S3/MinIO**, 
- repo implementuje dziś **desktopową aplikację PyQt6 + lokalne SQLite + bez warstwy REST/auth/websocket**.

Innymi słowy: **zgadza się kierunek produktu i wiele funkcji DJ-skich**, ale **warstwa techniczna i deploymentowa są zupełnie inne**.

## 1. Co jest zgodne funkcjonalnie

### 1.1 Zarządzanie biblioteką muzyczną
Spec zakłada inteligentny menedżer biblioteki DJ-skiej z obsługą tracków, playlist i odtwarzania. Obecna aplikacja również realizuje ten obszar: ma bibliotekę tracków, playlisty, widok listy/siatki, panel szczegółów i lokalny player.

**Wniosek:** domena produktu jest zgodna, mimo różnicy technologicznej.

### 1.2 AI tagging i uzupełnianie metadanych
Spec przewiduje analizę AI. W obecnym kodzie działa zarówno lokalny tagger heurystyczny, jak i cloud AI dla wielu providerów (`openai`, `gemini`, a także endpointy kompatybilne z OpenAI dla innych dostawców). Dodatkowo są ustawienia dla AcoustID, MusicBrainz i Discogs.

**Wniosek:** ten obszar jest już relatywnie blisko wizji produktu, choć w formie lokalnej/desktopowej, a nie jobowej i webowej.

### 1.3 Wykrywanie duplikatów
Spec wymienia 3 metody wykrywania duplikatów. W repo są implementacje po hashach, tagach i fingerprintach, a także osobne UI do skanowania i operacji na grupach duplikatów.

**Wniosek:** to jeden z najlepiej pokrytych obszarów względem specyfikacji.

### 1.4 Playlisty i workflow DJ-ski
Spec zakłada CRUD playlist, zarządzanie utworami i odtwarzanie. W obecnym kodzie są playlisty zwykłe i smart, dodawanie utworów do playlist, zmiana kolejności oraz eksport playlisty do VirtualDJ XML.

**Wniosek:** funkcjonalnie repo wspiera istotną część workflow DJ-skiego.

### 1.5 XML / Rekordbox / VirtualDJ
Spec podkreśla konwersję Rekordbox ↔ VirtualDJ. W repo znajduje się parser/import i testy dla XML Rekordbox oraz VirtualDJ.

**Wniosek:** ten element produktu jest faktycznie obecny.

## 2. Najważniejsze rozbieżności architektoniczne

### 2.1 Web app vs desktop app
Spec jasno mówi o aplikacji **webowej SPA (React + FastAPI)**. Obecny projekt jest opisany i uruchamiany jako **desktopowa aplikacja Python/Windows z PyQt6**.

**Skutek praktyczny:** bieżący kod nie jest backendem/frontendem dla przeglądarki, tylko samodzielną aplikacją desktopową.

### 2.2 PostgreSQL + users + ownership vs lokalne SQLite
Spec zakłada model wieloużytkownikowy: tabela `users`, rekordy `tracks` i `playlists` powiązane z właścicielem, joby AI itd. Obecna baza ma lokalne tabele `tracks`, `tags`, `playlists`, `playlist_tracks`, `settings`, `change_log`, `metadata_cache`, ale **bez użytkowników, ról i owner_id**.

**Skutek praktyczny:** obecny model danych wspiera pojedynczą lokalną bibliotekę, a nie system kont i dostępu wieloużytkownikowego.

### 2.3 Brak REST API
Spec definiuje konkretne endpointy `/api/auth/*`, `/api/tracks/*`, `/api/playlists/*`, `/api/ai/*`, `/api/export/*`. W obecnym repo nie ma takiej warstwy HTTP dla głównej aplikacji desktopowej; operacje odbywają się bezpośrednio przez GUI i repozytorium danych.

**Skutek praktyczny:** nie da się dziś potraktować repo jako implementacji kontraktu API opisanego w specyfikacji.

### 2.4 Brak WebSocket / Redis / Celery / S3-MinIO
Spec zakłada real-time collaboration, Redis pub/sub, Celery do jobów i obiektowy storage. W obecnym kodzie nie ma tej infrastruktury w głównej aplikacji desktopowej.

**Skutek praktyczny:** brak asynchronicznej, skalowalnej architektury usługowej i brak funkcji chmurowych ze specyfikacji.

## 3. Funkcje z wizji produktu, których teraz nie widać lub są tylko częściowo obecne

### 3.1 Autoryzacja i konta użytkowników
Spec zakłada rejestrację, logowanie, JWT i endpoint `me`. W obecnym kodzie nie ma systemu logowania użytkowników.

### 3.2 Cloud sync / collaboration
Spec wymienia cloud sync, backup biblioteki i real-time collaboration przez WebSocket. W obecnym desktopowym kodzie widać lokalne dane, ale nie widać synchronizacji między użytkownikami czy współpracy na żywo.

### 3.3 Job system dla AI i exportu
Spec przewiduje osobne joby AI i eksportu z trackingiem statusu/progresu. Obecny kod wywołuje analizę lokalnie lub przez bezpośrednie requesty HTTP do providerów AI, bez kolejki typu Celery.

### 3.4 Generowanie muzyki i eksport jako usługi backendowe
Spec zakłada szersze moduły typu `ai.generate`, eksporty i pobieranie wyników. Tego kontraktu usługowego w obecnej implementacji nie ma.

## 4. Obszary, gdzie obecny kod jest bardziej „desktop-MVP” niż „platforma SaaS”

Tak naprawdę obecny stan repo można traktować jako:

- **bogaty desktopowy MVP / produkt single-user**,
- z dużą liczbą funkcji domenowych,
- ale **bez przejścia do architektury webowej i wieloużytkownikowej** opisanej w `1.md`.

To ważne, bo oznacza, że przy dalszym rozwoju są dwie sensowne ścieżki:

1. **Kontynuacja desktopu** — rozwijanie PyQt6/SQLite i lokalnych funkcji.
2. **Migracja do platformy webowej** — potraktowanie obecnych modułów domenowych jako prototypu logiki biznesowej i przeniesienie ich do backendu FastAPI + nowego frontendu React.

## 5. Co można realnie reutilizować przy migracji do specyfikacji webowej

Najbardziej wartościowe do ponownego użycia są:

- modele domenowe tracków i playlist,
- logika tagowania heurystycznego,
- integracje z providerami metadanych,
- logika fingerprint/duplicate detection,
- parsery XML Rekordbox / VirtualDJ,
- część walidacji i testów domenowych.

Najmniej reutilizowalne będą:

- sam interfejs PyQt6,
- desktopowe flow okien/dialogów,
- bezpośrednie zależności UI ↔ repozytorium,
- założenia o lokalnym SQLite jako głównym storage.

## 6. Moja ocena zgodności

### Zgodność produktowa / domenowa: **średnia do wysokiej**
Repo już umie dużo z obszaru DJ music managera: biblioteka, playlisty, duplikaty, XML, player, AI tagging.

### Zgodność architektoniczna: **niska**
Największa luka to różnica między:

- **docelową platformą web/cloud**, a
- **obecną aplikacją desktop/local-first**.

### Zgodność z checklistą wdrożeniową z `1.md`: **częściowa**
Zrealizowane są przede wszystkim funkcje domenowe, ale nie warstwa backendowa, auth, storage, websockety i job orchestration.

## 7. Rekomendacja

Jeżeli link, który podałeś, rzeczywiście odpowiada wizji z `lumbagov3_extracted/1.md`, to moja rekomendacja jest taka:

- **nie traktować obecnego repo jako „prawie gotowego web appa”**,
- tylko jako **mocny desktopowy proof-of-concept / MVP domenowe**,
- z którego warto wyodrębnić logikę biznesową do przyszłego backendu.

Najrozsądniejszy następny krok techniczny to przygotowanie mapy migracji:

1. wydzielenie warstwy domenowej niezależnej od PyQt,
2. zaprojektowanie API kontraktów `tracks / playlists / ai / export`,
3. migracja danych z lokalnego SQLite do modelu PostgreSQL z `users`,
4. dopiero potem budowa frontendu React.
