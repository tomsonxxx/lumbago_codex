# legacy_feature_matrix

| Funkcja | Stary plik / źródło | Status w `lumbago_app` | Decyzja | Docelowy moduł |
|---|---|---|---|---|
| AI merge bez nadpisywania wartościami typu `Unknown` | `Id3Tager/services/aiService.ts` | Dodane | przenieść | `lumbago_app/ui/ai_tagger_dialog.py` (`_merge_analysis_into_track`, `_is_weak_text`) |
| Spójność wsadowa artist/album | `Id3Tager/services/aiService.ts` (`smartBatchAnalyze`) | Dodane | przenieść | `lumbago_app/ui/ai_tagger_dialog.py` (`_harmonize_batch_results`) |
| Rozszerzony kontrakt tagów (track/disc/albumArtist/composer/comments/isrc/danceability) | `Id3Tager/types.ts` | Dodane | przenieść | `lumbago_app/core/models.py`, `lumbago_app/data/schema.py`, `lumbago_app/data/repository.py`, `lumbago_app/ui/main_window.py` |
| Pipeline metadata: AcoustID -> MusicBrainz -> Discogs | `inteligentny_tagger_id3_src/services/*` (koncepcja), stare flow web | Już obecne + utrzymane | zachować | `lumbago_app/services/metadata_enricher.py` |
| Bezpieczne usuwanie duplikatów | starsze flow duplikatów w web (`Delete/Merge`) | Ulepszone | przenieść | `lumbago_app/ui/duplicates_dialog.py` (przenoszenie do trash zamiast `unlink`) |
| Historia zmian tagów (`tag_history`) | wymagania dokumentacji v5 | Dodane | przenieść | `lumbago_app/data/schema.py`, `lumbago_app/data/repository.py`, `migrations/versions/0002_track_metadata_and_tag_history.py` |
| Cache metadanych w DB | wymagania dokumentacji v5 | Już obecne + migracja | zachować | `lumbago_app/data/schema.py`, `lumbago_app/data/repository.py`, `migrations/versions/0002_track_metadata_and_tag_history.py` |
| `inteligentny_tagger_id3_src2` | katalog legacy | 1:1 duplikat `src` | pominąć i usunąć | n/a |
| `inteligentny_tagger_id3` | katalog legacy | placeholder (`[full_path_of_file_*]`) | pominąć i usunąć | n/a |
| `Id3Tager` i `lumbagov3_extracted` jako osobne stare projekty web | katalogi legacy | funkcje krytyczne wyciągnięte | pominąć i usunąć | n/a |
| `_archives` jako źródła historyczne | katalog legacy | nie jest aktywnym kodem runtime | pominąć i usunąć | n/a |
