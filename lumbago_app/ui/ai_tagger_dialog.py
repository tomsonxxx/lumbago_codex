from __future__ import annotations

import math
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from copy import deepcopy
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from PyQt6 import QtCore, QtGui, QtWidgets

from lumbago_app.core.config import load_settings
from lumbago_app.core.analysis_cache import load_analysis_cache, save_analysis_cache
from lumbago_app.core.models import AnalysisResult, Track
from lumbago_app.core.services import enrich_track_with_analysis
from lumbago_app.services.ai_tagger import CloudAiTagger, DatabaseTagger, MultiAiTagger, preflight_provider
from lumbago_app.services.ai_tagger_merge import _merge_analysis_into_track
from lumbago_app.services.key_detection import detect_key
from lumbago_app.services.metadata_enricher import AutoMetadataFiller, MetadataFillReport
from lumbago_app.services.metadata_writeback import PendingTrackWrite, apply_track_writes
from lumbago_app.ui.widgets import apply_dialog_fade

FIELDS = [
    "title", "bpm", "key", "artist", "album", "genre", "year", "composer",
    "comment", "lyrics", "publisher",
    "albumartist", "tracknumber", "discnumber",
    "rating", "mood", "energy",
    "isrc", "grouping", "copyright", "remixer",
]
AI_FIELDS = {"genre", "bpm", "key", "mood", "energy", "rating", "year"}
AUDIO_DERIVED_FIELDS = {"bpm", "key", "energy", "mood"}
FIELD_LABELS = {
    "title": "TytuĹ‚",
    "artist": "Artysta",
    "album": "Album",
    "albumartist": "Artysta albumu",
    "year": "Rok",
    "genre": "Gatunek",
    "tracknumber": "Nr utworu",
    "discnumber": "Nr dysku",
    "composer": "Kompozytor",
    "bpm": "BPM",
    "key": "Tonacja",
    "rating": "Ocena",
    "mood": "NastrĂłj",
    "energy": "Energia",
    "comment": "Komentarz",
    "lyrics": "Tekst",
    "isrc": "ISRC",
    "publisher": "Wydawca",
    "grouping": "Grupa",
    "copyright": "Prawa autorskie",
    "remixer": "Remikser",
}
METHOD_LABELS = {
    "online": "Online",
    "offline": "Offline",
    "mix": "Mix",
}
PROFILE_PRESETS: dict[str, dict[str, Any]] = {
    "Szybki": {
        "audio": True,
        "ai": True,
        "meta": False,
        "method": "offline",
        "audio_duration": 30,
        "workers": 4,
        "source_workers": 4,
        "api_workers": 2,
        "accept_threshold": 0.7,
    },
    "Zbalansowany": {
        "audio": True,
        "ai": True,
        "meta": True,
        "method": "mix",
        "audio_duration": 45,
        "workers": 6,
        "source_workers": 6,
        "api_workers": 3,
        "accept_threshold": 0.6,
    },
    "Dokladny": {
        "audio": True,
        "ai": True,
        "meta": True,
        "method": "online",
        "audio_duration": 120,
        "workers": 8,
        "source_workers": 8,
        "api_workers": 4,
        "accept_threshold": 0.55,
    },
}


class TrackStatus(Enum):
    QUEUED = "queued"
    RUNNING = "running"
    DONE = "done"
    ERROR = "error"
    SKIPPED = "skipped"


STATUS_ICON: dict[TrackStatus, tuple[str, str]] = {
    TrackStatus.QUEUED: ("â—‹", "#888888"),
    TrackStatus.RUNNING: ("âźł", "#FFD700"),
    TrackStatus.DONE: ("âś“", "#00E676"),
    TrackStatus.ERROR: ("âś—", "#FF5252"),
    TrackStatus.SKIPPED: ("â€“", "#888888"),
}


@dataclass
class TrackAnalysisState:
    track: Track
    proposed_track: Track
    status: TrackStatus = TrackStatus.QUEUED
    audio_result: Any = None
    ai_result: AnalysisResult | None = None
    metadata_report: MetadataFillReport | None = None
    error_msg: str = ""
    decisions: dict[str, bool | None] = field(default_factory=dict)


def _has_value(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        normalized = value.strip().lower()
        return bool(normalized) and normalized not in {"-", "—", "–", "unknown", "n/a", "none", "null", "\\"}
    return True


def _to_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _to_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _format_value(field_name: str, value: Any) -> str:
    if not _has_value(value):
        return "â€”"
    if field_name == "energy":
        return f"{float(value):.2f}"
    if field_name == "bpm":
        return f"{float(value):.1f}"
    if field_name == "rating":
        try:
            return str(int(value))
        except Exception:
            return str(value)
    return str(value)


def _safe_tempo(result: Any) -> float | None:
    try:
        tempo = float(getattr(result, "tempo", None))
    except (TypeError, ValueError):
        return None
    return tempo if math.isfinite(tempo) and tempo > 0 else None


def _audio_energy(result: Any) -> float | None:
    if result is None:
        return None
    brightness = float(getattr(result, "brightness", 0.0) or 0.0)
    roughness = float(getattr(result, "roughness", 0.0) or 0.0)
    energy = max(0.0, min(1.0, (brightness * 0.65) + (roughness * 0.35)))
    return energy if energy > 0 else None


def _changed_fields(original: Track, proposed: Track) -> list[str]:
    return [name for name in FIELDS if _format_value(name, getattr(original, name, None)) != _format_value(name, getattr(proposed, name, None))]


def _field_confidence(state: TrackAnalysisState, field_name: str) -> float:
    if field_name not in _changed_fields(state.track, state.proposed_track):
        return 0.0
    if field_name in AI_FIELDS:
        ai_value = getattr(state.ai_result, field_name, None) if state.ai_result is not None else None
        if _has_value(ai_value):
            confidence = float(state.ai_result.confidence or 0.0)
            if confidence > 0:
                return confidence
            return 0.75
        if field_name in AUDIO_DERIVED_FIELDS and state.audio_result is not None:
            return 0.7
    if state.metadata_report is not None and field_name in state.metadata_report.changed_fields:
        return 1.0
    return 1.0


def _default_accept_fields(state: TrackAnalysisState) -> set[str]:
    accepted: set[str] = set()
    changed = set(_changed_fields(state.track, state.proposed_track))
    if state.metadata_report is not None:
        accepted.update(field for field in state.metadata_report.changed_fields if field in changed)
    for field_name in changed:
        if _field_confidence(state, field_name) >= 0.6:
            accepted.add(field_name)
    return accepted


class TrackQueueModel(QtCore.QAbstractListModel):
    def __init__(self, states: list[TrackAnalysisState], parent=None):
        super().__init__(parent)
        self._states = states

    def rowCount(self, parent=QtCore.QModelIndex()) -> int:
        return len(self._states)

    def data(self, index: QtCore.QModelIndex, role=QtCore.Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or index.row() >= len(self._states):
            return None
        state = self._states[index.row()]
        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            icon, _ = STATUS_ICON[state.status]
            return f"{icon}  {Path(state.track.path).name}"
        if role == QtCore.Qt.ItemDataRole.ForegroundRole:
            _, color = STATUS_ICON[state.status]
            return QtGui.QColor(color)
        if role == QtCore.Qt.ItemDataRole.UserRole:
            return state
        return None

    def refresh_row(self, row: int) -> None:
        idx = self.index(row)
        self.dataChanged.emit(idx, idx)

    def refresh_all(self) -> None:
        if self._states:
            self.dataChanged.emit(self.index(0), self.index(len(self._states) - 1))


class ConfidenceBar(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._value = 0.0
        self.setFixedHeight(16)
        self.setMinimumWidth(80)

    def set_value(self, value: float) -> None:
        self._value = max(0.0, min(1.0, value))
        self.update()

    def paintEvent(self, _event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        width = self.width()
        height = self.height()
        painter.fillRect(0, 0, width, height, QtGui.QColor("#1a1a2e"))
        filled = int(width * self._value)
        color = QtGui.QColor("#00E676" if self._value >= 0.75 else "#FFD700" if self._value >= 0.5 else "#FF5252")
        if filled > 0:
            painter.fillRect(0, 0, filled, height, color)
        painter.setPen(QtGui.QColor("white"))
        painter.drawText(0, 0, width, height, QtCore.Qt.AlignmentFlag.AlignCenter, f"{self._value:.0%}")


class FieldComparisonWidget(QtWidgets.QWidget):
    decisions_changed = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._state: TrackAnalysisState | None = None
        self._rows: dict[str, dict[str, Any]] = {}
        self._show_changed_only = False
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        header = QtWidgets.QWidget()
        header_layout = QtWidgets.QHBoxLayout(header)
        header_layout.setContentsMargins(6, 3, 6, 3)
        for text, stretch in [("Pole", 1), ("Obecne", 2), ("Propozycja", 2), ("PewnoĹ›Ä‡", 2), ("", 1)]:
            label = QtWidgets.QLabel(f"<b>{text}</b>")
            label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            header_layout.addWidget(label, stretch)
        layout.addWidget(header)
        for field_name in FIELDS:
            row_widget = QtWidgets.QWidget()
            row_layout = QtWidgets.QHBoxLayout(row_widget)
            row_layout.setContentsMargins(6, 4, 6, 4)
            row_layout.setSpacing(8)
            label_field = QtWidgets.QLabel(FIELD_LABELS[field_name])
            label_field.setFixedWidth(72)
            label_current = QtWidgets.QLabel("â€”")
            label_current.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            label_proposed = QtWidgets.QLabel("â€”")
            label_proposed.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            confidence = ConfidenceBar()
            accept = QtWidgets.QPushButton("Tak")
            accept.setCheckable(True)
            accept.setFixedSize(42, 26)
            accept.setToolTip("Akceptuj zmianÄ™ dla tego pola")
            reject = QtWidgets.QPushButton("Nie")
            reject.setCheckable(True)
            reject.setFixedSize(42, 26)
            reject.setToolTip("OdrzuÄ‡ zmianÄ™ dla tego pola")

            def _bind(name: str, yes: QtWidgets.QPushButton, no: QtWidgets.QPushButton):
                def _on_yes():
                    if yes.isChecked():
                        no.setChecked(False)
                    self._on_decision(name)

                def _on_no():
                    if no.isChecked():
                        yes.setChecked(False)
                    self._on_decision(name)

                yes.clicked.connect(_on_yes)
                no.clicked.connect(_on_no)

            _bind(field_name, accept, reject)
            row_layout.addWidget(label_field, 1)
            row_layout.addWidget(label_current, 2)
            row_layout.addWidget(label_proposed, 2)
            row_layout.addWidget(confidence, 2)
            row_layout.addWidget(accept)
            row_layout.addWidget(reject)
            layout.addWidget(row_widget)
            self._rows[field_name] = {"row_widget": row_widget, "current": label_current, "proposed": label_proposed, "conf": confidence, "accept": accept, "reject": reject}
        layout.addStretch()

    def _on_decision(self, field_name: str) -> None:
        if self._state is None:
            return
        row = self._rows[field_name]
        if row["accept"].isChecked():
            self._state.decisions[field_name] = True
        elif row["reject"].isChecked():
            self._state.decisions[field_name] = False
        else:
            self._state.decisions[field_name] = None
        self.decisions_changed.emit()

    def load_state(self, state: TrackAnalysisState | None) -> None:
        self._state = state
        for field_name, row in self._rows.items():
            if state is None:
                current = proposed = "â€”"
                changed = False
                confidence = 0.0
                decision = None
            else:
                current = _format_value(field_name, getattr(state.track, field_name, None))
                proposed = _format_value(field_name, getattr(state.proposed_track, field_name, None))
                changed = current != proposed
                confidence = _field_confidence(state, field_name)
                decision = state.decisions.get(field_name)
                if not changed:
                    state.decisions.pop(field_name, None)
            row["current"].setText(current)
            row["proposed"].setText(proposed)
            row["current"].setToolTip(current)
            row["proposed"].setToolTip(proposed)
            row["conf"].set_value(confidence)
            row["row_widget"].setVisible(changed or not self._show_changed_only)
            row["row_widget"].setEnabled(changed)
            row["accept"].setEnabled(changed)
            row["reject"].setEnabled(changed)
            row["accept"].setChecked(decision is True)
            row["reject"].setChecked(decision is False)
            row["proposed"].setStyleSheet("color: #00E676; font-weight: bold;" if changed else "")

    def set_show_changed_only(self, enabled: bool) -> None:
        self._show_changed_only = bool(enabled)
        self.load_state(self._state)

    def accept_all_confident(self, threshold: float = 0.6) -> None:
        if self._state is None:
            return
        for field_name in _changed_fields(self._state.track, self._state.proposed_track):
            if _field_confidence(self._state, field_name) < threshold:
                continue
            row = self._rows[field_name]
            row["accept"].setChecked(True)
            row["reject"].setChecked(False)
            self._state.decisions[field_name] = True
        self.decisions_changed.emit()

    def reject_all(self) -> None:
        if self._state is None:
            return
        for field_name in _changed_fields(self._state.track, self._state.proposed_track):
            row = self._rows[field_name]
            row["accept"].setChecked(False)
            row["reject"].setChecked(True)
            self._state.decisions[field_name] = False
        self.decisions_changed.emit()


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
        self.setWindowTitle("Studio Analizy i AutoTagowania AI")
        self.setMinimumSize(1100, 700)
        apply_dialog_fade(self)
        self._tracks = tracks
        self._auto_fetch_default = auto_fetch
        self._auto_method_default = auto_method
        self._allow_auto_fetch = allow_auto_fetch
        self._force_cloud = force_cloud
        self._states = [TrackAnalysisState(track=track, proposed_track=deepcopy(track)) for track in tracks]
        self._queue_model = TrackQueueModel(self._states)
        self._current_state: TrackAnalysisState | None = None
        self._worker: _PipelineWorker | None = None
        self._last_run_providers: list[str] = []
        self._build_ui()

    def _build_ui(self) -> None:
        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 8)
        root.setSpacing(8)
        root.addWidget(self._build_toolbar())
        root.addWidget(self._build_main_area(), 1)
        root.addWidget(self._build_bottom_bar())

    def _build_toolbar(self) -> QtWidgets.QWidget:
        toolbar = QtWidgets.QFrame()
        layout = QtWidgets.QHBoxLayout(toolbar)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(10)
        layout.addWidget(QtWidgets.QLabel("Metoda analizy:"))
        self._method_combo = QtWidgets.QComboBox()
        for method_id in ("online", "offline", "mix"):
            self._method_combo.addItem(METHOD_LABELS[method_id], method_id)
        if self._auto_method_default in {"online", "offline", "mix"}:
            index = self._method_combo.findData(self._auto_method_default)
            if index >= 0:
                self._method_combo.setCurrentIndex(index)
        layout.addWidget(self._method_combo)

        self._options_btn = QtWidgets.QToolButton()
        self._options_btn.setText("Opcje")
        self._options_btn.setPopupMode(QtWidgets.QToolButton.ToolButtonPopupMode.InstantPopup)
        self._options_btn.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextOnly)
        self._options_menu = QtWidgets.QMenu(self._options_btn)
        self._options_btn.setMenu(self._options_menu)
        self._build_options_menu()
        layout.addWidget(self._options_btn)
        layout.addStretch()

        self._run_btn = QtWidgets.QPushButton("Start analizy")
        self._run_btn.setObjectName("PrimaryBtn")
        self._run_btn.clicked.connect(self._start_pipeline)
        self._stop_btn = QtWidgets.QPushButton("Stop")
        self._stop_btn.setObjectName("DangerBtn")
        self._stop_btn.setEnabled(False)
        self._stop_btn.clicked.connect(self._stop_pipeline)
        self._apply_btn = QtWidgets.QPushButton("Zastosuj zmiany")
        self._apply_btn.setObjectName("PrimaryBtn")
        self._apply_btn.setEnabled(False)
        self._apply_btn.clicked.connect(self._apply_accepted)
        layout.addWidget(self._run_btn)
        layout.addWidget(self._stop_btn)
        layout.addWidget(self._apply_btn)
        default_profile = "Szybki" if len(self._tracks) >= 300 else "Zbalansowany"
        self._apply_profile(default_profile)
        return toolbar

    def _build_main_area(self) -> QtWidgets.QWidget:
        splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)
        left = QtWidgets.QWidget()
        left_layout = QtWidgets.QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 4, 0)
        left_layout.addWidget(QtWidgets.QLabel(f"<b>Kolejka</b> ({len(self._tracks)} utworĂłw)"))
        self._queue_list = QtWidgets.QListView()
        self._queue_list.setModel(self._queue_model)
        self._queue_list.selectionModel().currentChanged.connect(self._on_queue_selection)
        left_layout.addWidget(self._queue_list, 1)
        splitter.addWidget(left)

        right = QtWidgets.QWidget()
        right_layout = QtWidgets.QVBoxLayout(right)
        right_layout.setContentsMargins(4, 0, 0, 0)
        self._detail_title = QtWidgets.QLabel("Wybierz utwĂłr z kolejki")
        self._detail_title.setObjectName("DialogTitle")
        right_layout.addWidget(self._detail_title)
        self._field_comparison = FieldComparisonWidget()
        self._field_comparison.decisions_changed.connect(self._update_apply_btn)
        self._log_view = QtWidgets.QPlainTextEdit()
        self._log_view.setReadOnly(True)
        self._log_view.setPlaceholderText("Tutaj pojawi siÄ™ log przetwarzania.")
        self._log_view.setFont(QtGui.QFont("Consolas", 9))
        self._field_comparison.set_show_changed_only(True)
        right_layout.addWidget(self._field_comparison, 3)
        right_layout.addWidget(QtWidgets.QLabel("<b>Log analizy</b>"))
        right_layout.addWidget(self._log_view, 2)
        splitter.addWidget(right)
        splitter.setSizes([320, 780])
        return splitter

    def _build_bottom_bar(self) -> QtWidgets.QWidget:
        bottom = QtWidgets.QFrame()
        layout = QtWidgets.QVBoxLayout(bottom)
        progress_row = QtWidgets.QHBoxLayout()
        self._progress_bar = QtWidgets.QProgressBar()
        self._progress_bar.setRange(0, max(1, len(self._tracks)))
        self._progress_bar.setValue(0)
        self._status_lbl = QtWidgets.QLabel("Gotowy do analizy.")
        progress_row.addWidget(self._progress_bar, 3)
        progress_row.addWidget(self._status_lbl, 2)
        layout.addLayout(progress_row)
        return bottom

    def _on_queue_selection(self, current: QtCore.QModelIndex, _previous: QtCore.QModelIndex) -> None:
        state = self._queue_model.data(current, QtCore.Qt.ItemDataRole.UserRole)
        if not isinstance(state, TrackAnalysisState):
            return
        self._current_state = state
        self._detail_title.setText(Path(state.track.path).name)
        self._field_comparison.load_state(state)

    def _apply_profile(self, profile_name: str) -> None:
        preset = PROFILE_PRESETS.get(profile_name)
        if not preset:
            return
        self._action_audio.setChecked(bool(preset["audio"]))
        self._action_ai.setChecked(bool(preset["ai"]))
        if self._allow_auto_fetch:
            self._action_meta.setChecked(bool(preset["meta"]))
        method_idx = self._method_combo.findData(preset["method"])
        if method_idx >= 0:
            self._method_combo.setCurrentIndex(method_idx)
        self._audio_duration.setValue(int(preset["audio_duration"]))
        self._workers_spin.setValue(int(preset["workers"]))
        self._source_workers_spin.setValue(int(preset.get("source_workers", 6)))
        self._api_workers_spin.setValue(int(preset.get("api_workers", 3)))
        self._accept_threshold.setValue(float(preset["accept_threshold"]))

    def _start_pipeline(self) -> None:
        settings = load_settings()
        method = self._method_combo.currentData() or "mix"
        tagger = None
        selected_providers = self._selected_providers()
        self._last_run_providers = selected_providers[:]
        if self._action_ai.isChecked():
            if not selected_providers:
                QtWidgets.QMessageBox.warning(self, "Brak API", "Wybierz co najmniej jedno API w menu Opcje.")
                return
            taggers: list[Any] = []
            # DatabaseTagger always runs first — AcoustID if key set, else MB text search
            _acoustid = None
            if settings.acoustid_api_key:
                from lumbago_app.services.recognizer import AcoustIdRecognizer
                _acoustid = AcoustIdRecognizer(settings.acoustid_api_key)
            taggers.append(DatabaseTagger(acoustid=_acoustid))
            for provider in selected_providers:
                api_key, base_url, model = _resolve_provider_config(provider, settings)
                if not api_key:
                    QtWidgets.QMessageBox.warning(self, "Brak klucza API", f"Ustaw klucz API dla providera '{provider}' w ustawieniach.")
                    return
                ok, detail = preflight_provider(provider, api_key, base_url, timeout=8)
                if not ok:
                    QtWidgets.QMessageBox.warning(
                        self,
                        "Błąd API",
                        f"Provider '{provider}' nie przeszedł testu połączenia.\nSzczegóły: {detail}",
                    )
                    return
                taggers.append(
                    CloudAiTagger(
                        provider,
                        api_key,
                        base_url=base_url,
                        model=model,
                        timeout=20,
                        retries=1,
                    )
                )
            tagger = MultiAiTagger(taggers, max_workers=int(self._api_workers_spin.value()))
        auto_filler = None
        if self._action_meta.isChecked():
            auto_filler = AutoMetadataFiller(
                settings.musicbrainz_app_name,
                settings.validation_policy,
                settings.metadata_cache_ttl_days,
                source_workers=int(self._source_workers_spin.value()),
            )
        for state in self._states:
            state.status = TrackStatus.QUEUED
            state.audio_result = None
            state.ai_result = None
            state.metadata_report = None
            state.error_msg = ""
            state.decisions.clear()
            state.proposed_track = deepcopy(state.track)
        self._queue_model.refresh_all()
        self._progress_bar.setValue(0)
        self._log_view.clear()
        self._apply_btn.setEnabled(False)
        self._run_btn.setEnabled(False)
        self._stop_btn.setEnabled(True)
        self._status_lbl.setText("Uruchamianie analizy...")
        audio_duration = int(self._audio_duration.value())
        if len(self._states) >= 250 and audio_duration > 30:
            audio_duration = 30
            self._log_view.appendPlainText(
                "  optymalizacja: skrócono czas analizy audio do 30s dla dużej paczki plików"
            )
        self._worker = _PipelineWorker(
            self._states,
            tagger,
            auto_filler,
            method,
            self._action_audio.isChecked(),
            audio_duration_s=audio_duration,
            max_workers=int(self._workers_spin.value()),
            accept_threshold=float(self._accept_threshold.value()),
        )
        self._worker.signals.track_started.connect(self._on_track_started)
        self._worker.signals.track_done.connect(self._on_track_done)
        self._worker.signals.finished.connect(self._on_finished)
        QtCore.QThreadPool.globalInstance().start(self._worker)

    def _stop_pipeline(self) -> None:
        if self._worker is not None:
            self._worker.stop()
        self._stop_btn.setEnabled(False)
        self._status_lbl.setText("Zatrzymywanie...")

    def _on_track_started(self, row: int) -> None:
        state = self._states[row]
        state.status = TrackStatus.RUNNING
        self._queue_model.refresh_row(row)
        name = Path(state.track.path).name
        self._status_lbl.setText(f"AnalizujÄ™: {name}")
        self._log_view.appendPlainText(f"> {name}")

    def _on_track_done(self, row: int) -> None:
        state = self._states[row]
        self._queue_model.refresh_row(row)
        finished = sum(1 for item in self._states if item.status in {TrackStatus.DONE, TrackStatus.ERROR, TrackStatus.SKIPPED})
        self._progress_bar.setValue(finished)
        if self._queue_list.currentIndex().isValid() and self._queue_list.currentIndex().row() == row:
            self._field_comparison.load_state(state)
            self._append_track_report_to_log(state)
        if state.status == TrackStatus.DONE:
            self._append_track_report_to_log(state)
        elif state.status == TrackStatus.ERROR:
            self._log_view.appendPlainText(f"  bĹ‚Ä…d: {state.error_msg}")

    def _on_finished(self) -> None:
        self._run_btn.setEnabled(True)
        self._stop_btn.setEnabled(False)
        done = sum(1 for state in self._states if state.status == TrackStatus.DONE)
        errors = sum(1 for state in self._states if state.status == TrackStatus.ERROR)
        self._status_lbl.setText(f"Gotowe: {done} OK, {errors} bĹ‚Ä™dĂłw")
        self._log_view.appendPlainText(f"\n-- ZakoĹ„czono: {done}/{len(self._states)} --")
        total_changed = 0
        metadata_fields = 0
        ai_fields = 0
        audio_fields = 0
        for state in self._states:
            changed = set(_changed_fields(state.track, state.proposed_track))
            total_changed += len(changed)
            metadata_changed = set(state.metadata_report.changed_fields) if state.metadata_report else set()
            metadata_fields += len(changed & metadata_changed)
            ai_from_result = set()
            if state.ai_result is not None:
                for field_name in AI_FIELDS:
                    if _has_value(getattr(state.ai_result, field_name, None)):
                        ai_from_result.add(field_name)
            ai_fields += len(changed & ai_from_result)
            audio_fields += len(changed & (AUDIO_DERIVED_FIELDS - ai_from_result))
        if total_changed > 0:
            self._log_view.appendPlainText(
                f"  Podsumowanie zmian: metadata={metadata_fields} ({metadata_fields/total_changed:.0%}), "
                f"AI={ai_fields} ({ai_fields/total_changed:.0%}), audio={audio_fields} ({audio_fields/total_changed:.0%})"
            )
        self._update_apply_btn()
        if not self._queue_list.currentIndex().isValid():
            for row, state in enumerate(self._states):
                if state.status == TrackStatus.DONE:
                    self._queue_list.setCurrentIndex(self._queue_model.index(row))
                    break

    def _update_apply_btn(self) -> None:
        self._apply_btn.setEnabled(any(value is True for state in self._states for value in state.decisions.values()))

    def _apply_accepted(self) -> None:
        providers = self._last_run_providers or self._selected_providers()
        source = "ai:" + ("+".join(providers) if providers else "manual")
        pending_writes: list[PendingTrackWrite] = []
        for state in self._states:
            file_tags: dict[str, str] = {}
            old_values: dict[str, str | None] = {}
            for field_name in FIELDS:
                if state.decisions.get(field_name) is not True:
                    continue
                old_value = getattr(state.track, field_name, None)
                new_value = getattr(state.proposed_track, field_name, None)
                if _format_value(field_name, old_value) == _format_value(field_name, new_value):
                    continue
                old_values[field_name] = None if old_value is None else str(old_value)
                setattr(state.track, field_name, new_value)
                file_tags[field_name] = str(new_value) if new_value is not None else ""
            if file_tags:
                pending_writes.append(
                    PendingTrackWrite(
                        track=state.track,
                        fields=file_tags,
                        source=source,
                        confidence=state.ai_result.confidence if state.ai_result else None,
                        change_log_source=source,
                        old_values=old_values,
                    )
                )
        if pending_writes:
            result = apply_track_writes(
                pending_writes,
                max_workers=int(self._workers_spin.value()),
                update_mode="bulk",
            )
            msg = f"Zapisano zmiany dla {result.track_count} utworow (baza + pliki audio)."
            if result.file_write_errors:
                msg += f"\nBledy zapisu tagow: {len(result.file_write_errors)}"
                for err in result.file_write_errors[:5]:
                    msg += f"\n  {err}"
            self._status_lbl.setText(msg)
            self.accept()
        else:
            self._status_lbl.setText("Brak zaakceptowanych zmian do zapisania.")

    def _build_options_menu(self) -> None:
        self._action_audio = self._options_menu.addAction("Analiza audio")
        self._action_audio.setCheckable(True)
        self._action_audio.setChecked(True)
        self._action_ai = self._options_menu.addAction("Analiza AI")
        self._action_ai.setCheckable(True)
        self._action_ai.setChecked(True)
        self._action_meta = self._options_menu.addAction("Wzbogacanie metadanych")
        self._action_meta.setCheckable(True)
        self._action_meta.setChecked(self._auto_fetch_default)
        if not self._allow_auto_fetch:
            self._action_meta.setChecked(False)
            self._action_meta.setEnabled(False)
        self._options_menu.addSeparator()

        providers_menu = self._options_menu.addMenu("API AI")
        self._provider_actions: dict[str, QtGui.QAction] = {}
        settings = load_settings()
        default_provider = settings.cloud_ai_provider or "openai"
        for provider in ["openai", "gemini", "grok", "deepseek"]:
            action = providers_menu.addAction(provider)
            action.setCheckable(True)
            action.setChecked(provider == default_provider)
            self._provider_actions[provider] = action
        if self._force_cloud:
            self._provider_actions["openai"].setChecked(True)

        self._options_menu.addSeparator()
        form_widget = QtWidgets.QWidget()
        form_layout = QtWidgets.QFormLayout(form_widget)
        form_layout.setContentsMargins(8, 8, 8, 8)
        form_layout.setSpacing(6)

        self._audio_duration = QtWidgets.QSpinBox()
        self._audio_duration.setRange(15, 180)
        self._audio_duration.setSingleStep(15)
        self._audio_duration.setValue(45)
        form_layout.addRow("Audio (s)", self._audio_duration)

        self._workers_spin = QtWidgets.QSpinBox()
        self._workers_spin.setRange(1, 16)
        self._workers_spin.setValue(6)
        form_layout.addRow("Pliki równolegle", self._workers_spin)

        self._source_workers_spin = QtWidgets.QSpinBox()
        self._source_workers_spin.setRange(1, 16)
        self._source_workers_spin.setValue(6)
        form_layout.addRow("Źródła równolegle", self._source_workers_spin)

        self._api_workers_spin = QtWidgets.QSpinBox()
        self._api_workers_spin.setRange(1, 8)
        self._api_workers_spin.setValue(3)
        form_layout.addRow("API równolegle", self._api_workers_spin)

        self._accept_threshold = QtWidgets.QDoubleSpinBox()
        self._accept_threshold.setRange(0.5, 0.95)
        self._accept_threshold.setSingleStep(0.05)
        self._accept_threshold.setValue(0.6)
        form_layout.addRow("Próg akceptacji", self._accept_threshold)

        widget_action = QtWidgets.QWidgetAction(self._options_menu)
        widget_action.setDefaultWidget(form_widget)
        self._options_menu.addAction(widget_action)

    def _selected_providers(self) -> list[str]:
        providers = [name for name, action in self._provider_actions.items() if action.isChecked()]
        if not providers and "openai" in self._provider_actions:
            self._provider_actions["openai"].setChecked(True)
            providers.append("openai")
        return providers

    def _append_track_report_to_log(self, state: TrackAnalysisState) -> None:
        changed = _changed_fields(state.track, state.proposed_track)
        self._log_view.appendPlainText(f"  zmienione pola: {', '.join(changed) if changed else 'brak'}")
        if state.metadata_report is not None:
            self._log_view.appendPlainText(f"  źródła: {state.metadata_report.summary}")
        if state.ai_result is not None:
            ai_line = (
                f"  AI: bpm={state.ai_result.bpm} key={state.ai_result.key} "
                f"genre={state.ai_result.genre} mood={state.ai_result.mood} energy={state.ai_result.energy} "
                f"conf={float(state.ai_result.confidence or 0.0):.0%}"
            )
            if state.ai_result.description:
                ai_line += f" [{state.ai_result.description}]"
            self._log_view.appendPlainText(ai_line)


class _WorkerSignals(QtCore.QObject):
    track_started = QtCore.pyqtSignal(int)
    track_done = QtCore.pyqtSignal(int)
    finished = QtCore.pyqtSignal()


class _PipelineWorker(QtCore.QRunnable):
    def __init__(
        self,
        states: list[TrackAnalysisState],
        tagger,
        auto_filler,
        method: str,
        do_audio: bool,
        *,
        audio_duration_s: int = 45,
        max_workers: int = 1,
        accept_threshold: float = 0.6,
    ):
        super().__init__()
        self.states = states
        self.tagger = tagger
        self.auto_filler = auto_filler
        self.method = method
        self.do_audio = do_audio
        self.audio_duration_s = max(15, int(audio_duration_s))
        self.max_workers = max(1, min(16, int(max_workers)))
        self.accept_threshold = max(0.5, min(0.95, float(accept_threshold)))
        self.signals = _WorkerSignals()
        self._stop = False

    def stop(self) -> None:
        self._stop = True

    def run(self) -> None:
        if isinstance(self.tagger, CloudAiTagger):
            self._run_cloud_chunked()
            return
        if self.max_workers <= 1:
            for idx, _ in enumerate(self.states):
                if self._stop:
                    self.states[idx].status = TrackStatus.SKIPPED
                    self.signals.track_done.emit(idx)
                    continue
                self.signals.track_started.emit(idx)
                self._process_track(idx)
                self.signals.track_done.emit(idx)
            self.signals.finished.emit()
            return

        pending_indexes = [idx for idx, _ in enumerate(self.states)]
        for idx in pending_indexes:
            self.signals.track_started.emit(idx)
        with ThreadPoolExecutor(max_workers=self.max_workers) as pool:
            future_map = {pool.submit(self._process_track, idx): idx for idx in pending_indexes}
            for future in as_completed(future_map):
                idx = future_map[future]
                try:
                    future.result()
                except Exception as exc:
                    state = self.states[idx]
                    state.status = TrackStatus.ERROR
                    state.error_msg = str(exc)
                    state.proposed_track = deepcopy(state.track)
                self.signals.track_done.emit(idx)
        self.signals.finished.emit()

    def _run_cloud_chunked(self) -> None:
        chunk_size = 20
        total = len(self.states)
        for start in range(0, total, chunk_size):
            end = min(total, start + chunk_size)
            for idx in range(start, end):
                if self._stop:
                    self.states[idx].status = TrackStatus.SKIPPED
                    self.signals.track_done.emit(idx)
                    continue
                self.signals.track_started.emit(idx)
                self._process_track(idx)
                if self.states[idx].status == TrackStatus.ERROR:
                    self.states[idx].error_msg = self.states[idx].error_msg or "Błąd AI"
                self.signals.track_done.emit(idx)
            # Mandatory cooldown between chunks to reduce API pressure / 429.
            if end < total:
                QtCore.QThread.msleep(3500)
        self.signals.finished.emit()

    def _process_track(self, idx: int) -> None:
        state = self.states[idx]
        try:
            working = deepcopy(state.track)
            path_obj = Path(working.path)
            state.decisions.clear()
            state.metadata_report = None
            state.ai_result = None
            state.audio_result = None
            state.error_msg = ""
            if self.auto_filler is not None:
                state.metadata_report = self.auto_filler.fill_missing_with_report(working, self.method)
            ai_input = deepcopy(working)
            if self.do_audio:
                state.audio_result = self._load_or_extract_audio(path_obj, working)
                detected_key = None if working.key else self._load_or_detect_key(path_obj)
                enrich_track_with_analysis(
                    working,
                    detected_bpm=_safe_tempo(state.audio_result),
                    detected_key=detected_key,
                    detected_energy=_audio_energy(state.audio_result),
                )
                self._persist_audio_features(working.path, state.audio_result)
            if self.tagger is not None:
                state.ai_result = self._load_cached_ai_result(path_obj)
                if state.ai_result is None:
                    state.ai_result = self.tagger.analyze(ai_input)
                    self._save_cached_ai_result(path_obj, state.ai_result)
                _merge_analysis_into_track(working, state.ai_result)
            state.proposed_track = working
            for field_name in _default_accept_fields(state):
                if _field_confidence(state, field_name) >= self.accept_threshold:
                    state.decisions[field_name] = True
            state.status = TrackStatus.DONE
        except Exception as exc:
            state.status = TrackStatus.ERROR
            state.error_msg = str(exc)
            state.proposed_track = deepcopy(state.track)

    def _load_or_extract_audio(self, path_obj: Path, working: Track):
        needs_audio_features = working.bpm is None or working.energy is None
        if not needs_audio_features:
            return None
        payload = load_analysis_cache(path_obj) or {}
        sig = self._audio_signature(path_obj)
        if (
            payload.get("signature") == sig
            and payload.get("audio_duration_s") == self.audio_duration_s
            and isinstance(payload.get("audio_result"), dict)
        ):
            return self._audio_result_from_cache(path_obj, payload.get("audio_result", {}))

        try:
            from lumbago_app.services.audio_features import AudioFeatureExtractor

            extractor = AudioFeatureExtractor()
            result = extractor.extract(path_obj, duration_s=self.audio_duration_s)
            save_analysis_cache(
                path_obj,
                {
                    "signature": sig,
                    "audio_duration_s": self.audio_duration_s,
                    "audio_result": self._audio_result_to_cache(result),
                },
            )
            return result
        except Exception:
            return None

    def _load_or_detect_key(self, path_obj: Path) -> str | None:
        payload = load_analysis_cache(path_obj) or {}
        sig = self._audio_signature(path_obj)
        if payload.get("signature") == sig and _has_value(payload.get("detected_key")):
            return str(payload.get("detected_key"))
        detected = detect_key(path_obj)
        merged = dict(payload)
        merged["signature"] = sig
        merged["detected_key"] = detected
        save_analysis_cache(path_obj, merged)
        return detected
    def _persist_audio_features(self, track_path: str, audio_result: Any) -> None:
        if audio_result is None:
            return
        try:
            from lumbago_app.core.models import AudioFeatures
            from lumbago_app.data.repository import upsert_audio_features

            af = AudioFeatures(
                track_id=0,
                mfcc_json=getattr(audio_result, "mfcc_json", "[]") or "[]",
                tempo=getattr(audio_result, "tempo", None),
                spectral_centroid=getattr(audio_result, "spectral_centroid", None),
                spectral_rolloff=getattr(audio_result, "spectral_rolloff", None),
                brightness=getattr(audio_result, "brightness", None),
                roughness=getattr(audio_result, "roughness", None),
                zero_crossing_rate=getattr(audio_result, "zero_crossing_rate", None),
                chroma_json=getattr(audio_result, "chroma_json", None),
                danceability=getattr(audio_result, "danceability", None),
                valence=getattr(audio_result, "valence", None),
            )
            upsert_audio_features(track_path, af)
        except Exception:
            return
    @staticmethod
    def _audio_signature(path_obj: Path) -> str:
        try:
            stat = path_obj.stat()
            return f"{path_obj}:{stat.st_size}:{int(stat.st_mtime)}"
        except Exception:
            return str(path_obj)

    @staticmethod
    def _audio_result_to_cache(result: Any) -> dict[str, Any]:
        return {
            "tempo": getattr(result, "tempo", None),
            "mfcc_json": getattr(result, "mfcc_json", "[]"),
            "spectral_centroid": getattr(result, "spectral_centroid", None),
            "spectral_rolloff": getattr(result, "spectral_rolloff", None),
            "brightness": getattr(result, "brightness", None),
            "roughness": getattr(result, "roughness", None),
            "waveform_blob": (
                getattr(result, "waveform_blob", b"").hex()
                if isinstance(getattr(result, "waveform_blob", None), (bytes, bytearray))
                else ""
            ),
        }

    @staticmethod
    def _audio_result_from_cache(path_obj: Path, payload: dict[str, Any]):
        class _CachedAudioResult:
            pass

        cached = _CachedAudioResult()
        cached.path = path_obj
        cached.tempo = payload.get("tempo")
        cached.mfcc_json = payload.get("mfcc_json") or "[]"
        cached.spectral_centroid = payload.get("spectral_centroid")
        cached.spectral_rolloff = payload.get("spectral_rolloff")
        cached.brightness = payload.get("brightness")
        cached.roughness = payload.get("roughness")
        waveform_hex = payload.get("waveform_blob") or ""
        cached.waveform_blob = bytes.fromhex(waveform_hex) if isinstance(waveform_hex, str) and waveform_hex else b""
        return cached

    def _ai_tagger_key(self) -> str | None:
        fn = getattr(self.tagger, "cache_key", None)
        return fn() if callable(fn) else None

    def _load_cached_ai_result(self, path_obj: Path) -> AnalysisResult | None:
        payload = load_analysis_cache(path_obj) or {}
        ai_data = payload.get("ai_result")
        if not isinstance(ai_data, dict):
            return None
        if payload.get("ai_signature") != self._audio_signature(path_obj):
            return None
        tagger_key = self._ai_tagger_key()
        if tagger_key is not None and payload.get("ai_tagger_key") != tagger_key:
            return None
        try:
            known = set(AnalysisResult.__dataclass_fields__)
            return AnalysisResult(**{k: v for k, v in ai_data.items() if k in known})
        except Exception:
            return None

    def _save_cached_ai_result(self, path_obj: Path, result: AnalysisResult) -> None:
        if not result.confidence:
            return
        try:
            payload = load_analysis_cache(path_obj) or {}
            payload["ai_signature"] = self._audio_signature(path_obj)
            tagger_key = self._ai_tagger_key()
            if tagger_key is not None:
                payload["ai_tagger_key"] = tagger_key
            payload["ai_result"] = {f: getattr(result, f) for f in result.__dataclass_fields__}
            save_analysis_cache(path_obj, payload)
        except Exception:
            pass


def _resolve_provider_config(provider: str, settings) -> tuple[str | None, str | None, str | None]:
    """Return (api_key, base_url, model) resolved specifically for the selected provider."""
    if provider == "gemini":
        key = settings.gemini_api_key or settings.cloud_ai_api_key
        return key, settings.gemini_base_url, settings.gemini_model
    if provider == "openai":
        key = settings.openai_api_key or settings.cloud_ai_api_key
        return key, settings.openai_base_url, settings.openai_model
    if provider == "grok":
        key = settings.grok_api_key or settings.cloud_ai_api_key
        return key, settings.grok_base_url, settings.grok_model
    if provider == "deepseek":
        key = settings.deepseek_api_key or settings.cloud_ai_api_key
        return key, settings.deepseek_base_url, settings.deepseek_model
    return None, None, None


def _is_valid_key(value: str) -> bool:
    if re.match(r"^(1[0-2]|[1-9])[AB]$", value, re.IGNORECASE):
        return True
    return bool(re.match(r"^[A-G](#|b)?m?$", value, re.IGNORECASE))
