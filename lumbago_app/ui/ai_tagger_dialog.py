from __future__ import annotations

from PyQt6 import QtCore, QtWidgets

from lumbago_app.core.config import load_settings
from lumbago_app.core.models import AnalysisResult, Track
import re
from lumbago_app.data.repository import replace_track_tags, update_tracks
from lumbago_app.services.ai_tagger import BatchAiQueueWorker, CloudAiTagger, LocalAiTagger
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

        # --- Batch queue panel ---
        queue_frame = QtWidgets.QFrame()
        queue_frame.setObjectName("DialogCard")
        queue_layout = QtWidgets.QVBoxLayout(queue_frame)
        queue_layout.setContentsMargins(10, 8, 10, 8)
        queue_layout.setSpacing(6)

        queue_hdr = QtWidgets.QHBoxLayout()
        queue_lbl = QtWidgets.QLabel("Kolejka wsadowa (BatchAI)")
        queue_lbl.setObjectName("SectionTitle")
        self._batch_toggle_btn = QtWidgets.QPushButton("▼ Rozwiń")
        self._batch_toggle_btn.setFixedWidth(90)
        queue_hdr.addWidget(queue_lbl)
        queue_hdr.addStretch()
        queue_hdr.addWidget(self._batch_toggle_btn)
        queue_layout.addLayout(queue_hdr)

        self._batch_panel = QtWidgets.QWidget()
        bp = QtWidgets.QVBoxLayout(self._batch_panel)
        bp.setContentsMargins(0, 0, 0, 0)
        bp.setSpacing(4)

        self._batch_progress = QtWidgets.QProgressBar()
        self._batch_progress.setRange(0, max(1, len(self._tracks)))
        self._batch_progress.setValue(0)
        self._batch_progress.setFixedHeight(14)
        bp.addWidget(self._batch_progress)

        self._batch_log = QtWidgets.QPlainTextEdit()
        self._batch_log.setReadOnly(True)
        self._batch_log.setMaximumHeight(90)
        self._batch_log.setPlaceholderText("Log kolejki wsadowej…")
        bp.addWidget(self._batch_log)

        batch_row = QtWidgets.QHBoxLayout()
        self._batch_start_btn = QtWidgets.QPushButton("Uruchom kolejkę")
        self._batch_start_btn.setToolTip("Przetwórz wszystkie załadowane ścieżki przez BatchAiQueueWorker")
        self._batch_start_btn.clicked.connect(self._run_batch_queue)
        self._batch_stop_btn = QtWidgets.QPushButton("Zatrzymaj")
        self._batch_stop_btn.setEnabled(False)
        batch_row.addWidget(self._batch_start_btn)
        batch_row.addWidget(self._batch_stop_btn)
        batch_row.addStretch()
        bp.addLayout(batch_row)

        self._batch_panel.setVisible(False)
        queue_layout.addWidget(self._batch_panel)
        self._batch_toggle_btn.clicked.connect(self._toggle_batch_panel)
        layout.addWidget(queue_frame)
        self._batch_worker: BatchAiQueueWorker | None = None
        self._batch_done_count = 0
        # -------------------------

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

    def _toggle_batch_panel(self) -> None:
        visible = not self._batch_panel.isVisible()
        self._batch_panel.setVisible(visible)
        self._batch_toggle_btn.setText("▲ Zwiń" if visible else "▼ Rozwiń")

    def _run_batch_queue(self) -> None:
        if not self._tracks:
            return
        settings = load_settings()
        provider = settings.cloud_ai_provider or "local"
        if provider == "local":
            tagger = LocalAiTagger()
        else:
            key = (
                settings.cloud_ai_api_key
                or settings.gemini_api_key
                or settings.openai_api_key
                or settings.grok_api_key
                or settings.deepseek_api_key
            )
            base_url, model = _provider_settings(provider, settings)
            if not key:
                self._batch_log.appendPlainText("Brak klucza API — skonfiguruj w Ustawieniach.")
                return
            tagger = CloudAiTagger(provider, key, base_url=base_url, model=model)

        self._batch_worker = BatchAiQueueWorker(self)
        for idx, track in enumerate(self._tracks):
            self._batch_worker.enqueue(track.path, priority=idx)

        self._batch_stop_btn.setEnabled(True)
        self._batch_start_btn.setEnabled(False)
        self._batch_done_count = 0
        self._batch_progress.setRange(0, len(self._tracks))
        self._batch_progress.setValue(0)
        self._batch_log.clear()

        self._batch_worker.track_progress.connect(self._on_batch_field)
        self._batch_worker.track_done.connect(self._on_batch_track_done)
        self._batch_worker.batch_done.connect(self._on_batch_finished)
        self._batch_stop_btn.clicked.connect(self._batch_worker.stop)

        self._batch_log.appendPlainText(f"Kolejka: {len(self._tracks)} utworów | provider: {provider}")
        self._batch_worker.process(tagger)

    def _on_batch_field(self, path: str, field: str, value: str, confidence: float) -> None:
        short = path.split("\\")[-1] if "\\" in path else path.split("/")[-1]
        bar = "█" * int(confidence * 10)
        self._batch_log.appendPlainText(f"  {short} | {field}: {value} [{bar} {confidence:.0%}]")

    def _on_batch_track_done(self, path: str) -> None:
        self._batch_done_count += 1
        self._batch_progress.setValue(self._batch_done_count)

    def _on_batch_finished(self) -> None:
        self._batch_stop_btn.setEnabled(False)
        self._batch_start_btn.setEnabled(True)
        self._batch_log.appendPlainText(f"Gotowe — przetworzono {self._batch_done_count} utworów.")

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
            key = (
                settings.cloud_ai_api_key
                or settings.gemini_api_key
                or settings.openai_api_key
                or settings.grok_api_key
                or settings.deepseek_api_key
            )
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
            if _below_confidence(result, settings.validation_policy, provider):
                continue
            result = _sanitize_ai_result(result, settings.validation_policy)
            track.bpm = result.bpm or track.bpm
            track.key = result.key or track.key
            track.mood = result.mood or track.mood
            track.energy = result.energy or track.energy
            track.genre = result.genre or track.genre
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
            return
        self.status_label.setText("Brak zmian do zapisania. Sprawdź pewność/politykę walidacji.")
        QtWidgets.QMessageBox.information(
            self,
            "AutoTagowanie AI",
            "Nie zastosowano zmian. Dla trybu lokalnego ustaw walidację na lenient "
            "lub użyj dostawcy chmurowego.",
        )

    def _set_all_actions(self, label: str) -> None:
        for row_idx in range(self.table.rowCount()):
            action = self.table.cellWidget(row_idx, 9)
            if isinstance(action, QtWidgets.QComboBox):
                action.setCurrentText(label)


def _build_ai_tags(result: AnalysisResult) -> list[str]:
    tags: list[str] = []
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
    if result.description:
        tags.append(f"description:{result.description}")
    return tags


def _provider_settings(provider: str, settings) -> tuple[str | None, str | None]:
    if provider == "gemini":
        return settings.gemini_base_url, settings.gemini_model
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


def _below_confidence(result: AnalysisResult, policy: str | None, provider: str | None = None) -> bool:
    if result.confidence is None:
        return False
    if (provider or "").lower() == "local":
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

    return AnalysisResult(
        bpm=bpm,
        key=key,
        mood=result.mood,
        energy=energy,
        genre=result.genre,
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
        self.signals.finished.emit(results)



