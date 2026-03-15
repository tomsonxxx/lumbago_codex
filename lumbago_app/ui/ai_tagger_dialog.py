from __future__ import annotations

from PyQt6 import QtCore, QtWidgets

from lumbago_app.core.config import load_settings
from lumbago_app.core.models import AnalysisResult, Track
import re
from lumbago_app.data.repository import replace_track_tags, update_tracks
from lumbago_app.services.ai_tagger import CloudAiTagger, LocalAiTagger
from lumbago_app.services.metadata_enricher import AutoMetadataFiller


class AiTaggerDialog(QtWidgets.QDialog):
    def __init__(self, tracks: list[Track], parent=None, auto_fetch: bool = False, auto_method: str | None = None):
        super().__init__(parent)
        self.setWindowTitle("Tagger AI")
        self.setMinimumSize(760, 460)
        self._tracks = tracks
        self._auto_fetch_default = auto_fetch
        self._auto_method_default = auto_method
        self._results: dict[str, AnalysisResult] = {}
        self._build_ui()
        self._analyze()

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        self.provider_label = QtWidgets.QLabel("")
        layout.addWidget(self.provider_label)

        self.table = QtWidgets.QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(
            ["Tytuł", "Artysta", "BPM", "Tonacja", "Nastrój", "Energia", "Akcja"]
        )
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table, 1)

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

    def _analyze(self):
        self.table.setRowCount(0)
        settings = load_settings()
        provider = settings.cloud_ai_provider or "local"
        self.provider_label.setText(f"Provider: {provider}")

        if provider == "local":
            tagger = LocalAiTagger()
        else:
            key = settings.cloud_ai_api_key or settings.openai_api_key or settings.grok_api_key or settings.deepseek_api_key
            base_url, model = _provider_settings(provider, settings)
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
            for track, result in results:
                self._results[track.path] = result
                row = self.table.rowCount()
                self.table.insertRow(row)
                self.table.setItem(row, 0, QtWidgets.QTableWidgetItem(track.title or ""))
                self.table.setItem(row, 1, QtWidgets.QTableWidgetItem(track.artist or ""))
                self.table.setItem(row, 2, QtWidgets.QTableWidgetItem(str(result.bpm or "")))
                self.table.setItem(row, 3, QtWidgets.QTableWidgetItem(result.key or ""))
                self.table.setItem(row, 4, QtWidgets.QTableWidgetItem(result.mood or ""))
                self.table.setItem(row, 5, QtWidgets.QTableWidgetItem(str(result.energy or "")))
                action = QtWidgets.QComboBox()
                action.addItems(["Akceptuj", "Odrzuć"])
                action.setToolTip("Akceptuj lub odrzuć propozycję")
                self.table.setCellWidget(row, 6, action)

        self._worker.signals.progress.connect(on_progress)
        self._worker.signals.finished.connect(on_finished)
        QtCore.QThreadPool.globalInstance().start(self._worker)

    def _apply_all(self):
        accepted_tracks: list[Track] = []
        settings = load_settings()
        provider = settings.cloud_ai_provider or "local"
        source = f"ai:{provider}"
        for row_idx, track in enumerate(self._tracks):
            action = self.table.cellWidget(row_idx, 6)
            if isinstance(action, QtWidgets.QComboBox) and action.currentText() != "Akceptuj":
                continue
            result = self._results.get(track.path)
            if not result:
                continue
            if _below_confidence(result, settings.validation_policy):
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

    def _set_all_actions(self, label: str) -> None:
        for row_idx in range(self.table.rowCount()):
            action = self.table.cellWidget(row_idx, 6)
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
