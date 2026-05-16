# RECOVERY — Konsolidacja repozytorium 2026-05-16

## Commit przed konsolidacją
```
1f5047c8 chore(vercel): skip all deployments — web app removed
```
Aby cofnąć całą konsolidację:
```
git reset --hard 1f5047c8
```
Aby odtworzyć pojedynczy plik:
```
git checkout 1f5047c8 -- <ścieżka>
```

---

## MAPA PRZENIESIONYCH PLIKÓW (lumbago_app/ → root)

| Stara ścieżka | Nowa ścieżka |
|---|---|
| lumbago_app/main.py | main.py |
| lumbago_app/__init__.py | (usunięty) |
| lumbago_app/core/__init__.py | core/__init__.py |
| lumbago_app/core/analysis_cache.py | core/analysis_cache.py |
| lumbago_app/core/audio.py | core/audio.py |
| lumbago_app/core/backup.py | core/backup.py |
| lumbago_app/core/config.py | core/config.py |
| lumbago_app/core/models.py | core/models.py |
| lumbago_app/core/renamer.py | core/renamer.py |
| lumbago_app/core/services.py | core/services.py |
| lumbago_app/core/waveform.py | core/waveform.py |
| lumbago_app/data/__init__.py | data/__init__.py |
| lumbago_app/data/db.py | data/db.py |
| lumbago_app/data/repository.py | data/repository.py |
| lumbago_app/data/schema.py | data/schema.py |
| lumbago_app/services/__init__.py | services/__init__.py |
| lumbago_app/services/ai_tagger.py | services/ai_tagger.py |
| lumbago_app/services/ai_tagger_merge.py | services/ai_tagger_merge.py |
| lumbago_app/services/analysis_engine.py | services/analysis_engine.py |
| lumbago_app/services/autotag_rewrite.py | services/autotag_rewrite.py |
| lumbago_app/services/beatgrid.py | services/beatgrid.py |
| lumbago_app/services/fuzzy_dedup.py | services/fuzzy_dedup.py |
| lumbago_app/services/key_detection.py | services/key_detection.py |
| lumbago_app/services/loudness.py | services/loudness.py |
| lumbago_app/services/metadata_enricher.py | services/metadata_enricher.py |
| lumbago_app/services/metadata_pipeline_v2.py | services/metadata_pipeline_v2.py |
| lumbago_app/services/metadata_providers.py | services/metadata_providers.py |
| lumbago_app/services/metadata_writeback.py | services/metadata_writeback.py |
| lumbago_app/services/recognition_pipeline_v2.py | services/recognition_pipeline_v2.py |
| lumbago_app/services/recognizer.py | services/recognizer.py |
| lumbago_app/services/xml_converter.py | services/xml_converter.py |
| lumbago_app/ui/__init__.py | ui/__init__.py |
| lumbago_app/ui/ai_tagger_dialog.py | ui/ai_tagger_dialog.py |
| lumbago_app/ui/bulk_edit_dialog.py | ui/bulk_edit_dialog.py |
| lumbago_app/ui/change_history_dialog.py | ui/change_history_dialog.py |
| lumbago_app/ui/duplicates_dialog.py | ui/duplicates_dialog.py |
| lumbago_app/ui/health_dashboard.py | ui/health_dashboard.py |
| lumbago_app/ui/import_wizard.py | ui/import_wizard.py |
| lumbago_app/ui/library_widget.py | ui/library_widget.py |
| lumbago_app/ui/main_window.py | ui/main_window.py |
| lumbago_app/ui/models.py | ui/models.py |
| lumbago_app/ui/player_widget.py | ui/player_widget.py |
| lumbago_app/ui/playlist_dialog.py | ui/playlist_dialog.py |
| lumbago_app/ui/playlist_order_dialog.py | ui/playlist_order_dialog.py |
| lumbago_app/ui/process_log_dialog.py | ui/process_log_dialog.py |
| lumbago_app/ui/recognition_queue.py | ui/recognition_queue.py |
| lumbago_app/ui/renamer_dialog.py | ui/renamer_dialog.py |
| lumbago_app/ui/settings_dialog.py | ui/settings_dialog.py |
| lumbago_app/ui/tag_compare_dialog.py | ui/tag_compare_dialog.py |
| lumbago_app/ui/theme.py | ui/theme.py |
| lumbago_app/ui/widgets.py | ui/widgets.py |
| lumbago_app/ui/xml_converter_dialog.py | ui/xml_converter_dialog.py |
| lumbago_app/ui/xml_import_dialog.py | ui/xml_import_dialog.py |

---

## USUNIĘTE PLIKI ŚLEDZONE PRZEZ GIT

### Prototyp WinUI 3 (winui/ — 32 pliki C#)
- winui/LumbagoWinUI.sln
- winui/LumbagoWinUI/App.xaml + App.xaml.cs
- winui/LumbagoWinUI/MainWindow.xaml + MainWindow.xaml.cs
- winui/LumbagoWinUI/LumbagoWinUI.csproj
- winui/LumbagoWinUI/Assets/.gitkeep
- winui/LumbagoWinUI/Models/*.cs (4 pliki)
- winui/LumbagoWinUI/Pages/*.xaml + *.xaml.cs (12 plików)
- winui/LumbagoWinUI/Services/*.cs (2 pliki)
- winui/LumbagoWinUI/Themes/Theme.xaml
- winui/LumbagoWinUI/app.manifest

### Dokumentacja przestarzała (docs/)
- docs/winui3/ (cały podkatalog — 20+ plików XAML, PNG, MD)
- docs/web_top10_execution_plan.md
- docs/legacy_feature_matrix.md
- docs/porownanie_spec_z_kodem.md
- docs/clean_windows_test.md

### Pozostałe usunięte
- Claude/Spolszczenie/TODO.md
- Claude/Spolszczenie/pl-PL.json
- package.json (root)
- package-lock.json (root)
- memory.md
- AGENTS.md
- vercel.json
- tests/test_web_backend_api.py
- tests/test_web_tag_edit_flow.py

---

## ZACHOWANE (bez zmian)
- tests/ (wszystkie poza 2 web testami)
- migrations/
- scripts/
- assets/
- tools/
- docs/user_guide.md
- docs/HISTORY.md
- docs/analysis-tagging-audit.md
- .github/workflows/desktop-ci.yml
- requirements.txt
- alembic.ini
- pyproject.toml (zaktualizowany)
- pyinstaller.spec (zaktualizowany)
- CLAUDE.md (przepisany)
