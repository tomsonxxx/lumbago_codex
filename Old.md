# Old.md

## Usunięta pozycja: `inteligentny_tagger_id3_src2`
- Oryginalna rola: duplikat frontendu.
- Co przeniesiono: nic nowego (duplikat 1:1).
- Dokąd przeniesiono: n/a.
- Dowód: `docs/legacy_feature_matrix.md`.

## Usunięta pozycja: `inteligentny_tagger_id3`
- Oryginalna rola: niekompletna wersja pośrednia.
- Co przeniesiono: nic (placeholdery).
- Dokąd przeniesiono: n/a.
- Dowód: `docs/legacy_feature_matrix.md`.

## Usunięta pozycja: `Id3Tager`
- Oryginalna rola: starszy webowy projekt AI taggera.
- Co przeniesiono: smart merge, batch consistency, rozszerzony kontrakt tagów.
- Dokąd przeniesiono: `lumbago_app/core`, `lumbago_app/data`, `lumbago_app/ui`.
- Dowód: `tests/test_ai_tagger_merge.py`, `tests/test_tag_history.py`.

## Usunięta pozycja: `lumbagov3_extracted`, `_archives`
- Oryginalna rola: historyczne snapshoty.
- Co przeniesiono: brak funkcji runtime.
- Dokąd przeniesiono: n/a.
- Dowód: `docs/legacy_feature_matrix.md`.

## Usunięte artefakty
- `build/`, `dist/`, `output/`, `tmp/`, `__pycache__/`, `.pytest_cache/`.
