# Old.md

## Usunięta pozycja: `inteligentny_tagger_id3_src2`
- Oryginalna rola: kopia robocza frontendu ID3 taggera.
- Co przeniesiono: nic nowego, katalog był duplikatem 1:1 `inteligentny_tagger_id3_src`.
- Dokąd przeniesiono: n/a.
- Dowód (test/plik): porównanie hash 49/49 plików identycznych; matryca `docs/legacy_feature_matrix.md`.

## Usunięta pozycja: `inteligentny_tagger_id3`
- Oryginalna rola: niekompletna wersja pośrednia.
- Co przeniesiono: nic, zawierała placeholdery (`[full_path_of_file_1]`, `[full_path_of_file_2]`).
- Dokąd przeniesiono: n/a.
- Dowód (test/plik): analiza katalogu i matryca `docs/legacy_feature_matrix.md`.

## Usunięta pozycja: `Id3Tager`
- Oryginalna rola: starszy webowy projekt AI taggera.
- Co przeniesiono:
  - inteligentne merge AI (ochrona przed słabymi nadpisaniami),
  - batch consistency dla spójności artysta/album,
  - rozszerzony kontrakt tagów (m.in. track/disc/album artist/composer/comments/isrc/danceability).
- Dokąd przeniesiono:
  - `lumbago_app/ui/ai_tagger_dialog.py`,
  - `lumbago_app/core/models.py`,
  - `lumbago_app/data/schema.py`,
  - `lumbago_app/data/repository.py`,
  - `lumbago_app/ui/main_window.py`.
- Dowód (test/plik):
  - `tests/test_ai_tagger_merge.py`,
  - `tests/test_tag_history.py`,
  - `pytest -q tests` -> 18 passed.

## Usunięta pozycja: `lumbagov3_extracted`
- Oryginalna rola: wyekstrahowana historyczna wersja web v3.
- Co przeniesiono: brak nowych funkcji krytycznych ponad to, co już dodano z `Id3Tager`/`src`.
- Dokąd przeniesiono: n/a.
- Dowód (test/plik): matryca `docs/legacy_feature_matrix.md`.

## Usunięta pozycja: `_archives`
- Oryginalna rola: historyczne archiwa i snapshoty.
- Co przeniesiono: brak elementów runtime.
- Dokąd przeniesiono: n/a.
- Dowód (test/plik): matryca `docs/legacy_feature_matrix.md`.

## Usunięta pozycja: artefakty i cache
- Oryginalna rola: dane tymczasowe build/test/runtime.
- Co przeniesiono: n/a.
- Dokąd przeniesiono: n/a.
- Usunięte:
  - `build/`, `dist/`, `output/`, `tmp/`,
  - `**/__pycache__/`, `.pytest_cache/`.
- Dowód (test/plik):
  - zielony test po czyszczeniu: `pytest -q tests`,
  - CI: `.github/workflows/desktop-ci.yml`.
