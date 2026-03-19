from __future__ import annotations

from PyQt6 import QtCore, QtWidgets

from lumbago_app.core.config import load_settings
from lumbago_app.core.models import AnalysisResult, Track
import re
from lumbago_app.data.repository import replace_track_tags, update_tracks
from lumbago_app.services.ai_tagger import CloudAiTagger, LocalAiTagger
from lumbago_app.services.metadata_enricher import AutoMetadataFiller
from lumbago_app.ui.widgets import apply_dialog_fade, dialog_icon_pixmap


class AiTaggerDialog(QtWidgets.QDialog):
    def __init__(
        self,
        tracks: list[Track],
        parent=None,
        auto_fetch: bool = False,
        auto_method: str | None = None,
        allow_auto_fetch: bool = True,
        force_cloud: bool = False,
    ):
        super().__init__(parent)
        self.setWindowTitle("AutoTagowanie AI")
        self.setMinimumSize(760, 460)
        apply_dialog_fade(self)
        self._tracks = tracks
        self._auto_fetch_default = auto_fetch
        self._auto_method_default = auto_method
        self._allow_auto_fetch = allow_auto_fetch
        self._force_cloud = force_cloud
        self._results: dict[str, AnalysisResult] = {}
        self._worker = None
        self._build_ui()

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        card = QtWidgets.QFrame()
        card.setObjectName("DialogCard")
        card_layout = QtWidgets.QVBoxLayout(card)
        card_layout.setContentsMargins(16, 14, 16, 16)
        card_layout.setSpacing(10)
        layout.addWidget(card)
        layout = card_layout

        title_row = QtWidgets.QHBoxLayout()
        title_icon = QtWidgets.QLabel()
        title_icon.setPixmap(dialog_icon_pixmap(18))
        title_icon.setFixedSize(20, 20)
        title = QtWidgets.QLabel(self.windowTitle())
        title.setObjectName("DialogTitle")
        title_row.addWidget(title_icon)
        title_row.addWidget(title)
        title_row.addStretch(1)
        layout.addLayout(title_row)

        self.provider_label = QtWidgets.QLabel("")
        layout.addWidget(self.provider_label)

        self.table = QtWidgets.QTableWidget(0, 10)
        self.table.setHorizontalHeaderLabels(
            ["Tytuł", "Artysta", "BPM", "Tonacja", "Gatunek", "Nastrój", "Energia", "Pewność", "Status", "Akcja"]
        )
        self.table.setAlternatingRowColors(True)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Interactive)
        header.setSectionsMovable(True)
        header.setStretchLastSection(True)
        header.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        header.customContextMenuRequested.connect(self._show_column_menu)
        layout.addWidget(self.table, 1)

        self.status_label = QtWidgets.QLabel("")
        self.status_label.setObjectName("DialogHint")
        layout.addWidget(self.status_label)

        options = QtWidgets.QHBoxLayout()
        self.auto_fetch = QtWidgets.QCheckBox("Auto‑uzupełniaj brakujące tagi z internetu")
        self.auto_fetch.setChecked(self._auto_fetch_default)
        self.auto_method = QtWidgets.QComboBox()
        self.auto_method.addItems(
            [
                "Auto (priorytety)",
                "AcoustID + MusicBrainz",
                "MusicBrainz (wyszukiwanie)",
                "Discogs (wyszukiwanie)",
            ]
        )
        if self._auto_method_default:
            self.auto_method.setCurrentText(_auto_method_label(self._auto_method_default))
        options.addWidget(self.auto_fetch)
        options.addWidget(self.auto_method)
        options.addStretch(1)
        if not self._allow_auto_fetch:
            self.auto_fetch.setChecked(False)
            self.auto_fetch.setEnabled(False)
            self.auto_method.setEnabled(False)
            self.auto_method.setVisible(False)

        self.analyze_btn = QtWidgets.QPushButton("Analizuj")
        self.analyze_btn.setToolTip("Uruchom analizę AI dla zaznaczonych utworów")
        self.analyze_btn.clicked.connect(self._analyze)
        options.addWidget(self.analyze_btn)
        layout.addLayout(options)

        row = QtWidgets.QHBoxLayout()
        self.accept_all_btn = QtWidgets.QPushButton("Akceptuj wszystko")
        self.accept_all_btn.setToolTip("Ustaw akcję Akceptuj dla wszystkich")
        self.accept_all_btn.clicked.connect(lambda: self._set_all_actions("Akceptuj"))
        self.reject_all_btn = QtWidgets.QPushButton("Odrzuć wszystko")
        self.reject_all_btn.setToolTip("Ustaw akcję Odrzuć dla wszystkich")
        self.reject_all_btn.clicked.connect(lambda: self._set_all_actions("Odrzuć"))
        self.apply_all = QtWidgets.QPushButton("Zastosuj wszystko")
        self.apply_all.setToolTip("Zapisz wynik tagowania dla utworów z akcją Akceptuj")
        self.apply_all.clicked.connect(self._apply_all)
        self.cancel_btn = QtWidgets.QPushButton("Anuluj")
        self.cancel_btn.setToolTip("Zamknij bez zapisywania")
        self.cancel_btn.clicked.connect(self.reject)
        row.addStretch(1)
        row.addWidget(self.accept_all_btn)
        row.addWidget(self.reject_all_btn)
        row.addWidget(self.apply_all)
        row.addWidget(self.cancel_btn)
        layout.addLayout(row)
        self._set_actions_enabled(False)
        self.status_label.setText("Kliknij Analizuj, aby pobrać propozycje tagów.")

    def _set_actions_enabled(self, enabled: bool) -> None:
        self.accept_all_btn.setEnabled(enabled)
        self.reject_all_btn.setEnabled(enabled)
        self.apply_all.setEnabled(enabled)

    def _analyze(self):
        self.table.setRowCount(0)
        self._results.clear()
        self._set_actions_enabled(False)
        self.status_label.setText("Trwa analiza AI...")
        settings = load_settings()
        provider = settings.cloud_ai_provider or "local"
        mode_label = "tryb API" if self._force_cloud else "tryb mieszany"
        self.provider_label.setText(f"Dostawca: {provider} • {mode_label}")

        if self._force_cloud and provider == "local":
            QtWidgets.QMessageBox.warning(
                self,
                "Brak providera chmurowego",
                "Ustaw dostawcę Cloud AI (OpenAI/Grok/DeepSeek/Gemini) w Ustawieniach.",
            )
            return

        if provider == "local":
            tagger = LocalAiTagger()
        else:
            key = settings.cloud_ai_api_key or settings.openai_api_key or settings.grok_api_key or settings.deepseek_api_key
            base_url, model = _provider_settings(provider, settings)
            if not key:
                QtWidgets.QMessageBox.warning(
                    self,
                    "Brak klucza API",
                    "Ustaw klucz API dla wybranego providera w Ustawieniach.",
                )
                return
            tagger = CloudAiTagger(provider, key, base_url=base_url, model=model)

        method = _auto_method_id(self.auto_method.currentText(), settings)
        auto_enabled = self.auto_fetch.isChecked()
        auto_filler = AutoMetadataFiller(
            settings.acoustid_api_key,
            settings.musicbrainz_app_name,
            settings.discogs_token,
            settings.validation_policy,
            settings.metadata_cache_ttl_days,
        )

        self._worker = AiTaggerWorker(self._tracks, tagger, auto_filler, auto_enabled, method)
        progress = QtWidgets.QProgressDialog("Analiza AI...", "Anuluj", 0, len(self._tracks), self)
        progress.setWindowTitle("Tagger AI")
        progress.setMinimumDuration(0)

        def on_progress(current: int, total: int):
            progress.setMaximum(total)
            progress.setValue(current)
            if progress.wasCanceled():
                self._worker.stop()

        def on_finished(results: list[tuple[Track, AnalysisResult]]):
            progress.close()
            error_messages = []
            for track, result in results:
                self._results[track.path] = result
                row = self.table.rowCount()
                self.table.insertRow(row)
                self.table.setItem(row, 0, QtWidgets.QTableWidgetItem(track.title or ""))
                self.table.setItem(row, 1, QtWidgets.QTableWidgetItem(track.artist or ""))
                self.table.setItem(row, 2, QtWidgets.QTableWidgetItem(str(result.bpm or "")))
                self.table.setItem(row, 3, QtWidgets.QTableWidgetItem(result.key or ""))
                self.table.setItem(row, 4, QtWidgets.QTableWidgetItem(result.genre or ""))
                self.table.setItem(row, 5, QtWidgets.QTableWidgetItem(result.mood or ""))
                self.table.setItem(row, 6, QtWidgets.QTableWidgetItem(str(result.energy or "")))
                self.table.setItem(row, 7, QtWidgets.QTableWidgetItem(str(result.confidence or "")))
                self.table.setItem(row, 8, QtWidgets.QTableWidgetItem(result.description or ""))
                action = QtWidgets.QComboBox()
                action.addItems(["Akceptuj", "Odrzuć"])
                action.setToolTip("Akceptuj lub odrzuć propozycję")
                self.table.setCellWidget(row, 9, action)
                if result.description and "Cloud AI" in result.description:
                    error_messages.append(result.description)
            self._set_actions_enabled(bool(results))
            if error_messages:
                message = error_messages[0]
                self.status_label.setText(f"Problem z API: {message}")
                QtWidgets.QMessageBox.warning(
                    self,
                    "Problem z API",
                    f"{message}\nSprawdź ustawienia providera, modelu i limitów rozliczeń.",
                )
            else:
                self.status_label.setText("Analiza zakończona. Sprawdź wyniki i wybierz akcje.")

        self._worker.signals.progress.connect(on_progress)
        self._worker.signals.finished.connect(on_finished)
        QtCore.QThreadPool.globalInstance().start(self._worker)

    def _show_column_menu(self, pos):
        menu = QtWidgets.QMenu(self)
        show_all = menu.addAction("Pokaż wszystkie")
        hide_all = menu.addAction("Ukryj wszystkie")
        menu.addSeparator()
        actions = []
        for col in range(self.table.columnCount()):
            name = self.table.horizontalHeaderItem(col).text()
            action = QtWidgets.QAction(name, menu)
            action.setCheckable(True)
            action.setChecked(not self.table.isColumnHidden(col))
            actions.append((action, col))
            menu.addAction(action)
        chosen = menu.exec(self.table.horizontalHeader().mapToGlobal(pos))
        if chosen == show_all:
            for _, col in actions:
                self.table.setColumnHidden(col, False)
            return
        if chosen == hide_all:
            for _, col in actions:
                self.table.setColumnHidden(col, True)
            return
        for action, col in actions:
            if chosen == action:
                self.table.setColumnHidden(col, not action.isChecked())
                break

    def _apply_all(self):
        accepted_tracks: list[Track] = []
        settings = load_settings()
        provider = settings.cloud_ai_provider or "local"
        source = f"ai:{provider}"
        for row_idx, track in enumerate(self._tracks):
            action = self.table.cellWidget(row_idx, 9)
            if isinstance(action, QtWidgets.QComboBox) and action.currentText() != "Akceptuj":
                continue
            result = self._results.get(track.path)
            if not result:
                continue
            if _below_confidence(result, settings.validation_policy):
                continue
            result = _sanitize_ai_result(result, settings.validation_policy)
            _merge_analysis_into_track(track, result)
            accepted_tracks.append(track)
            replace_track_tags(
                track.path,
                _build_ai_tags(result),
                source=source,
                confidence=result.confidence,
            )
        if accepted_tracks:
            update_tracks(accepted_tracks)
        self.accept()

    def _set_all_actions(self, label: str) -> None:
        for row_idx in range(self.table.rowCount()):
            action = self.table.cellWidget(row_idx, 9)
            if isinstance(action, QtWidgets.QComboBox):
                action.setCurrentText(label)


def _build_ai_tags(result: AnalysisResult) -> list[str]:
    tags: list[str] = []
    if result.title:
        tags.append(f"title:{result.title}")
    if result.artist:
        tags.append(f"artist:{result.artist}")
    if result.album:
        tags.append(f"album:{result.album}")
    if result.year:
        tags.append(f"year:{result.year}")
    if result.genre:
        tags.append(f"genre:{result.genre}")
    if result.mood:
        tags.append(f"mood:{result.mood}")
    if result.key:
        tags.append(f"key:{result.key}")
    if result.bpm is not None:
        tags.append(f"bpm:{result.bpm}")
    if result.energy is not None:
        tags.append(f"energy:{result.energy}")
    if result.danceability is not None:
        tags.append(f"danceability:{result.danceability}")
    if result.track_number:
        tags.append(f"track_number:{result.track_number}")
    if result.disc_number:
        tags.append(f"disc_number:{result.disc_number}")
    if result.album_artist:
        tags.append(f"album_artist:{result.album_artist}")
    if result.composer:
        tags.append(f"composer:{result.composer}")
    if result.original_artist:
        tags.append(f"original_artist:{result.original_artist}")
    if result.comments:
        tags.append(f"comments:{result.comments}")
    if result.isrc:
        tags.append(f"isrc:{result.isrc}")
    if result.record_label:
        tags.append(f"record_label:{result.record_label}")
    if result.description:
        tags.append(f"description:{result.description}")
    return tags


def _provider_settings(provider: str, settings) -> tuple[str | None, str | None]:
    if provider == "openai":
        return settings.openai_base_url, settings.openai_model
    if provider == "grok":
        return settings.grok_base_url, settings.grok_model
    if provider == "deepseek":
        return settings.deepseek_base_url, settings.deepseek_model
    return None, None


def _auto_method_id(label: str, settings) -> str:
    if "Auto" in label:
        return "auto"
    if "AcoustID" in label:
        return "acoustid" if settings.acoustid_api_key else "musicbrainz"
    if "Discogs" in label:
        return "discogs" if settings.discogs_token else "musicbrainz"
    return "musicbrainz"


def _auto_method_label(method: str) -> str:
    if method == "auto":
        return "Auto (priorytety)"
    if method == "acoustid":
        return "AcoustID + MusicBrainz"
    if method == "discogs":
        return "Discogs (wyszukiwanie)"
    return "MusicBrainz (wyszukiwanie)"


def _below_confidence(result: AnalysisResult, policy: str | None) -> bool:
    if result.confidence is None:
        return False
    threshold = 0.6
    if policy == "strict":
        threshold = 0.8
    elif policy == "lenient":
        threshold = 0.4
    return result.confidence < threshold


def _sanitize_ai_result(result: AnalysisResult, policy: str | None) -> AnalysisResult:
    bpm_min, bpm_max = (60.0, 200.0)
    if policy == "lenient":
        bpm_min, bpm_max = (40.0, 220.0)
    elif policy == "balanced":
        bpm_min, bpm_max = (50.0, 210.0)

    bpm = result.bpm
    if bpm is not None and (bpm < bpm_min or bpm > bpm_max):
        bpm = None

    key = result.key
    if key:
        key = key.strip()
        if not _is_valid_key(key):
            key = None

    energy = result.energy
    if energy is not None and (energy < 0.0 or energy > 1.0):
        energy = None
    danceability = result.danceability
    if danceability is not None and (danceability < 0.0 or danceability > 1.0):
        danceability = None

    return AnalysisResult(
        title=result.title,
        artist=result.artist,
        album=result.album,
        year=result.year,
        bpm=bpm,
        key=key,
        mood=result.mood,
        energy=energy,
        danceability=danceability,
        genre=result.genre,
        track_number=result.track_number,
        disc_number=result.disc_number,
        album_artist=result.album_artist,
        composer=result.composer,
        copyright=result.copyright,
        encoded_by=result.encoded_by,
        original_artist=result.original_artist,
        comments=result.comments,
        album_cover_url=result.album_cover_url,
        isrc=result.isrc,
        release_type=result.release_type,
        record_label=result.record_label,
        description=result.description,
        confidence=result.confidence,
    )


def _is_valid_key(value: str) -> bool:
    camelot = re.match(r"^(1[0-2]|[1-9])[AB]$", value, re.IGNORECASE)
    if camelot:
        return True
    musical = re.match(r"^[A-G](#|b)?m?$", value, re.IGNORECASE)
    return bool(musical)


class AiTaggerSignals(QtCore.QObject):
    progress = QtCore.pyqtSignal(int, int)
    finished = QtCore.pyqtSignal(list)


class AiTaggerWorker(QtCore.QRunnable):
    def __init__(
        self,
        tracks: list[Track],
        tagger,
        auto_filler: AutoMetadataFiller,
        auto_enabled: bool,
        method: str,
    ):
        super().__init__()
        self.tracks = tracks
        self.tagger = tagger
        self.auto_filler = auto_filler
        self.auto_enabled = auto_enabled
        self.method = method
        self.signals = AiTaggerSignals()
        self._stop = False

    def stop(self):
        self._stop = True

    def run(self):
        results: list[tuple[Track, AnalysisResult]] = []
        total = len(self.tracks)
        for idx, track in enumerate(self.tracks, 1):
            if self._stop:
                break
            if self.auto_enabled:
                try:
                    self.auto_filler.fill_missing(track, self.method)
                except Exception:
                    pass
            result = self.tagger.analyze(track)
            results.append((track, result))
            self.signals.progress.emit(idx, total)
        results = _harmonize_batch_results(results)
        self.signals.finished.emit(results)


def _merge_analysis_into_track(track: Track, result: AnalysisResult) -> None:
    _set_if_better(track, "title", result.title)
    _set_if_better(track, "artist", result.artist)
    _set_if_better(track, "album", result.album)
    _set_if_better(track, "year", result.year)
    _set_if_better(track, "genre", result.genre)
    _set_if_better(track, "key", result.key)
    _set_if_better(track, "mood", result.mood)
    _set_if_better(track, "track_number", result.track_number)
    _set_if_better(track, "disc_number", result.disc_number)
    _set_if_better(track, "album_artist", result.album_artist)
    _set_if_better(track, "composer", result.composer)
    _set_if_better(track, "copyright", result.copyright)
    _set_if_better(track, "encoded_by", result.encoded_by)
    _set_if_better(track, "original_artist", result.original_artist)
    _set_if_better(track, "comments", result.comments)
    _set_if_better(track, "isrc", result.isrc)
    _set_if_better(track, "release_type", result.release_type)
    _set_if_better(track, "record_label", result.record_label)
    if result.bpm is not None:
        track.bpm = result.bpm
    if result.energy is not None:
        track.energy = result.energy
    if result.danceability is not None:
        track.danceability = result.danceability


def _set_if_better(track: Track, field: str, candidate: str | None) -> None:
    if not candidate:
        return
    current = getattr(track, field, None)
    if current and _is_weak_text(candidate):
        return
    setattr(track, field, candidate)


def _is_weak_text(value: str) -> bool:
    lowered = value.lower().strip()
    return lowered in {"unknown", "n/a", "none", "undefined", "various artists", "brak danych"}


def _harmonize_batch_results(
    results: list[tuple[Track, AnalysisResult]],
) -> list[tuple[Track, AnalysisResult]]:
    groups: dict[tuple[str, str], list[int]] = {}
    for idx, (track, _) in enumerate(results):
        artist = (track.artist or "").strip().lower()
        album = (track.album or "").strip().lower()
        if artist and album:
            groups.setdefault((artist, album), []).append(idx)

    for indexes in groups.values():
        if len(indexes) < 2:
            continue
        common_artist = _majority_text([results[i][1].artist for i in indexes])
        common_album = _majority_text([results[i][1].album for i in indexes])
        common_album_artist = _majority_text([results[i][1].album_artist for i in indexes])
        for i in indexes:
            track, analysis = results[i]
            if common_artist and not _is_weak_text(common_artist):
                analysis.artist = common_artist
            if common_album and not _is_weak_text(common_album):
                analysis.album = common_album
            if common_album_artist and not _is_weak_text(common_album_artist):
                analysis.album_artist = common_album_artist
            results[i] = (track, analysis)
    return results


def _majority_text(values: list[str | None]) -> str | None:
    counts: dict[str, int] = {}
    for value in values:
        if not value:
            continue
        cleaned = value.strip()
        if not cleaned or _is_weak_text(cleaned):
            continue
        counts[cleaned] = counts.get(cleaned, 0) + 1
    if not counts:
        return None
    return max(counts.items(), key=lambda pair: pair[1])[0]



