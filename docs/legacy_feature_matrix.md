# legacy_feature_matrix

| Funkcja | Stary plik / źródło | Status w `lumbago_app` | Decyzja | Docelowy moduł |
|---|---|---|---|---|
| AI merge bez nadpisywania `Unknown` | `Id3Tager/services/aiService.ts` | Dodane | przenieść | `lumbago_app/ui/ai_tagger_dialog.py` |
| Spójność wsadowa artist/album | `Id3Tager/services/aiService.ts` | Dodane | przenieść | `lumbago_app/ui/ai_tagger_dialog.py` |
| Rozszerzone pola tagów | `Id3Tager/types.ts` | Dodane | przenieść | `lumbago_app/core/models.py`, `lumbago_app/data/*`, `lumbago_app/ui/main_window.py` |
| Pipeline metadata AcoustID -> MB -> Discogs | legacy web | Utrzymane | zachować | `lumbago_app/services/metadata_enricher.py` |
| Safe delete duplikatów | legacy web | Ulepszone | przenieść | `lumbago_app/ui/duplicates_dialog.py` |
| `tag_history` + cache DB | dokumentacja v5 | Dodane | przenieść | `lumbago_app/data/schema.py`, `migrations/versions/0002_track_metadata_and_tag_history.py` |
| `inteligentny_tagger_id3_src2` | legacy | Duplikat 1:1 | usunąć | n/a |
| `inteligentny_tagger_id3` | legacy | Placeholder | usunąć | n/a |
| `Id3Tager`, `lumbagov3_extracted`, `_archives` | legacy | Funkcje krytyczne wyciągnięte | usunąć | n/a |
