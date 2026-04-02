from __future__ import annotations

import json
import math
import re
from copy import deepcopy
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from PyQt6 import QtCore, QtGui, QtWidgets

from lumbago_app.core.config import load_settings
from lumbago_app.core.models import AnalysisResult, Track
from lumbago_app.core.services import enrich_track_with_analysis
from lumbago_app.core.audio import write_tags
from lumbago_app.data.repository import replace_track_tags, update_tracks
from lumbago_app.services.ai_tagger import CloudAiTagger, LocalAiTagger
from lumbago_app.services.ai_tagger_merge import _merge_analysis_into_track
from lumbago_app.services.key_detection import detect_key
from lumbago_app.services.metadata_enricher import AutoMetadataFiller, MetadataFillReport, available_metadata_methods
from lumbago_app.ui.widgets import apply_dialog_fade

FIELDS = [
    "title", "artist", "album", "albumartist", "year", "genre",
    "tracknumber", "discnumber", "composer",
    "bpm", "key", "mood", "energy",
    "comment", "lyrics", "isrc", "publisher", "grouping", "copyright", "remixer",
]
AI_FIELDS = {"genre", "bpm", "key", "mood", "energy"}
FIELD_LABELS = {
    "title": "Tytuł",
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
    "mood": "Nastrój",
    "energy": "Energia",
    "comment": "Komentarz",
    "lyrics": "Tekst",
    "isrc": "ISRC",
    "publisher": "Wydawca",
    "grouping": "Grupa",
    "copyright": "Prawa autorskie",
    "remixer": "Remikser",
}
METHOD_ORDER = ["offline", "online", "mix"]


class TrackStatus(Enum):
    QUEUED = "queued"
    RUNNING = "running"
    DONE = "done"
    ERROR = "error"
    SKIPPED = "skipped"


STATUS_ICON: dict[TrackStatus, tuple[str, str]] = {
    TrackStatus.QUEUED: ("○", "#888888"),
    TrackStatus.RUNNING: ("⟳", "#FFD700"),
    TrackStatus.DONE: ("✓", "#00E676"),
    TrackStatus.ERROR: ("✗", "#FF5252"),
    TrackStatus.SKIPPED: ("–", "#888888"),
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
        return bool(normalized) and normalized not in {"-", "—", "unknown", "n/a", "none", "null"}
    return True


def _format_value(field_name: str, value: Any) -> str:
    if not _has_value(value):
        return "—"
    if field_name == "energy":
        return f"{float(value):.2f}"
    if field_name == "bpm":
        return f"{float(value):.1f}"
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
    if field_name in AI_FIELDS and state.ai_result is not None:
        return float(state.ai_result.confidence or 0.0)
    return 1.0 if field_name in _changed_fields(state.track, state.proposed_track) else 0.0


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
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        header = QtWidgets.QWidget()
        header_layout = QtWidgets.QHBoxLayout(header)
        header_layout.setContentsMargins(6, 3, 6, 3)
        for text, stretch in [("Pole", 1), ("Obecne", 2), ("Propozycja", 2), ("Pewność", 2), ("", 1)]:
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
            label_current = QtWidgets.QLabel("—")
            label_current.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            label_proposed = QtWidgets.QLabel("—")
            label_proposed.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            confidence = ConfidenceBar()
            accept = QtWidgets.QPushButton("Tak")
            accept.setCheckable(True)
            accept.setFixedSize(42, 26)
            accept.setToolTip("Akceptuj zmianę dla tego pola")
            reject = QtWidgets.QPushButton("Nie")
            reject.setCheckable(True)
            reject.setFixedSize(42, 26)
            reject.setToolTip("Odrzuć zmianę dla tego pola")

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
                current = proposed = "—"
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
            row["row_widget"].setEnabled(changed)
            row["accept"].setEnabled(changed)
            row["reject"].setEnabled(changed)
            row["accept"].setChecked(decision is True)
            row["reject"].setChecked(decision is False)
            row["proposed"].setStyleSheet("color: #00E676; font-weight: bold;" if changed else "")

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


class AudioInfoPanel(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QtWidgets.QFormLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        def _bar() -> QtWidgets.QProgressBar:
            bar = QtWidgets.QProgressBar()
            bar.setRange(0, 100)
            bar.setTextVisible(False)
            return bar

        self._tempo = QtWidgets.QLabel("—")
        self._brightness = _bar()
        self._roughness = _bar()
        self._spectral = QtWidgets.QLabel("—")
        self._mfcc = QtWidgets.QLabel("—")
        self._mfcc.setWordWrap(True)
        layout.addRow("Tempo:", self._tempo)
        layout.addRow("Jasność:", self._brightness)
        layout.addRow("Szorstkość:", self._roughness)
        layout.addRow("Centroid spektralny:", self._spectral)
        layout.addRow("MFCC top-5:", self._mfcc)

    def load_result(self, result: Any) -> None:
        if result is None:
            self._tempo.setText("—")
            self._brightness.setValue(0)
            self._roughness.setValue(0)
            self._spectral.setText("—")
            self._mfcc.setText("—")
            return
        tempo = _safe_tempo(result)
        self._tempo.setText(f"{tempo:.1f} BPM" if tempo is not None else "—")
        self._brightness.setValue(int((getattr(result, "brightness", 0.0) or 0.0) * 100))
        self._roughness.setValue(int((getattr(result, "roughness", 0.0) or 0.0) * 100))
        spectral = getattr(result, "spectral_centroid", None)
        self._spectral.setText(f"{float(spectral):.0f} Hz" if spectral else "—")
        try:
            mfcc = json.loads(getattr(result, "mfcc_json", "") or "[]")
        except Exception:
            mfcc = []
        self._mfcc.setText(str([round(float(value), 2) for value in mfcc[:5]]) if mfcc else "—")


class MetadataSourcesPanel(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self._summary = QtWidgets.QLabel("Brak danych o źródłach.")
        self._summary.setWordWrap(True)
        layout.addWidget(self._summary)
        self._table = QtWidgets.QTableWidget(0, 4)
        self._table.setHorizontalHeaderLabels(["Źródło", "Status", "Pola", "Szczegóły"])
        self._table.verticalHeader().setVisible(False)
        self._table.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        self._table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self._table, 1)

    def load_report(self, report: MetadataFillReport | None) -> None:
        self._table.setRowCount(0)
        if report is None:
            self._summary.setText("Brak raportu źródeł dla zaznaczonego utworu.")
            return
        self._summary.setText(f"Metoda: {report.method}. {report.summary}")
        for source in report.sources:
            row = self._table.rowCount()
            self._table.insertRow(row)
            self._table.setItem(row, 0, QtWidgets.QTableWidgetItem(source.label))
            self._table.setItem(row, 1, QtWidgets.QTableWidgetItem(source.status))
            self._table.setItem(row, 2, QtWidgets.QTableWidgetItem(", ".join(source.fields) if source.fields else "—"))
            self._table.setItem(row, 3, QtWidgets.QTableWidgetItem(source.detail or "—"))


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
        layout.addWidget(QtWidgets.QLabel("<b>Pipeline:</b>"))

        self._chk_audio = QtWidgets.QCheckBox("Analiza audio")
        self._chk_audio.setChecked(True)
        self._chk_audio.setToolTip("Wylicza tempo, energię i tonację z pliku audio.")
        self._chk_ai = QtWidgets.QCheckBox("Autotagowanie AI")
        self._chk_ai.setChecked(True)
        self._chk_ai.setToolTip("Uzupełnia pola AI na podstawie bieżących metadanych i analizy audio.")
        self._chk_meta = QtWidgets.QCheckBox("Metadane zewnętrzne")
        self._chk_meta.setChecked(self._auto_fetch_default)
        self._chk_meta.setToolTip("Łączy metody lokalne i online, np. tagi pliku, AcoustID, MusicBrainz i Discogs.")
        if not self._allow_auto_fetch:
            self._chk_meta.setChecked(False)
            self._chk_meta.setEnabled(False)
        layout.addWidget(self._chk_audio)
        layout.addWidget(self._chk_ai)
        layout.addWidget(self._chk_meta)
        layout.addWidget(_vsep())

        layout.addWidget(QtWidgets.QLabel("Provider AI:"))
        self._provider_combo = QtWidgets.QComboBox()
        self._provider_combo.addItems(["local", "openai", "gemini", "grok", "deepseek"])
        settings = load_settings()
        default_provider = settings.cloud_ai_provider or "local"
        self._provider_combo.setCurrentText("openai" if self._force_cloud and default_provider == "local" else default_provider)
        layout.addWidget(self._provider_combo)

        layout.addWidget(QtWidgets.QLabel("Metoda metadanych:"))
        self._method_combo = QtWidgets.QComboBox()
        methods = available_metadata_methods()
        for method_id in METHOD_ORDER:
            label = methods.get(method_id)
            if label:
                self._method_combo.addItem(label, method_id)
        if self._auto_method_default:
            index = self._method_combo.findData(self._auto_method_default)
            if index >= 0:
                self._method_combo.setCurrentIndex(index)
        self._method_combo.setMinimumWidth(220)
        layout.addWidget(self._method_combo)
        layout.addStretch()

        self._run_btn = QtWidgets.QPushButton("Start analizy")
        self._run_btn.setObjectName("PrimaryBtn")
        self._run_btn.clicked.connect(self._start_pipeline)
        self._stop_btn = QtWidgets.QPushButton("Zatrzymaj")
        self._stop_btn.setObjectName("DangerBtn")
        self._stop_btn.setEnabled(False)
        self._stop_btn.clicked.connect(self._stop_pipeline)
        layout.addWidget(self._run_btn)
        layout.addWidget(self._stop_btn)
        return toolbar

    def _build_main_area(self) -> QtWidgets.QWidget:
        splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)
        left = QtWidgets.QWidget()
        left_layout = QtWidgets.QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 4, 0)
        left_layout.addWidget(QtWidgets.QLabel(f"<b>Kolejka</b> ({len(self._tracks)} utworów)"))
        self._queue_list = QtWidgets.QListView()
        self._queue_list.setModel(self._queue_model)
        self._queue_list.selectionModel().currentChanged.connect(self._on_queue_selection)
        left_layout.addWidget(self._queue_list, 1)
        splitter.addWidget(left)

        right = QtWidgets.QWidget()
        right_layout = QtWidgets.QVBoxLayout(right)
        right_layout.setContentsMargins(4, 0, 0, 0)
        self._detail_title = QtWidgets.QLabel("Wybierz utwór z kolejki")
        self._detail_title.setObjectName("DialogTitle")
        right_layout.addWidget(self._detail_title)
        self._tabs = QtWidgets.QTabWidget()
        self._field_comparison = FieldComparisonWidget()
        self._field_comparison.decisions_changed.connect(self._update_apply_btn)
        self._audio_panel = AudioInfoPanel()
        self._sources_panel = MetadataSourcesPanel()
        self._log_view = QtWidgets.QPlainTextEdit()
        self._log_view.setReadOnly(True)
        self._log_view.setPlaceholderText("Tutaj pojawi się log przetwarzania.")
        self._log_view.setFont(QtGui.QFont("Consolas", 9))
        self._tabs.addTab(self._field_comparison, "Propozycje")
        self._tabs.addTab(self._audio_panel, "Analiza audio")
        self._tabs.addTab(self._sources_panel, "Źródła")
        self._tabs.addTab(self._log_view, "Log")
        right_layout.addWidget(self._tabs, 1)
        buttons = QtWidgets.QHBoxLayout()
        self._btn_accept_confident = QtWidgets.QPushButton("Akceptuj pewne pola")
        self._btn_accept_confident.clicked.connect(lambda: self._field_comparison.accept_all_confident(0.6))
        self._btn_reject_track = QtWidgets.QPushButton("Odrzuć pola utworu")
        self._btn_reject_track.clicked.connect(self._field_comparison.reject_all)
        buttons.addWidget(self._btn_accept_confident)
        buttons.addWidget(self._btn_reject_track)
        buttons.addStretch()
        right_layout.addLayout(buttons)
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
        actions = QtWidgets.QHBoxLayout()
        self._accept_all_btn = QtWidgets.QPushButton("Akceptuj wszystko")
        self._accept_all_btn.setEnabled(False)
        self._accept_all_btn.clicked.connect(self._accept_all_tracks)
        self._reject_all_btn = QtWidgets.QPushButton("Odrzuć wszystko")
        self._reject_all_btn.setEnabled(False)
        self._reject_all_btn.clicked.connect(self._reject_all_tracks)
        self._apply_btn = QtWidgets.QPushButton("Zastosuj zaakceptowane")
        self._apply_btn.setObjectName("PrimaryBtn")
        self._apply_btn.setEnabled(False)
        self._apply_btn.clicked.connect(self._apply_accepted)
        self._cancel_btn = QtWidgets.QPushButton("Anuluj")
        self._cancel_btn.clicked.connect(self.reject)
        actions.addWidget(self._accept_all_btn)
        actions.addWidget(self._reject_all_btn)
        actions.addStretch()
        actions.addWidget(self._apply_btn)
        actions.addWidget(self._cancel_btn)
        layout.addLayout(actions)
        return bottom

    def _on_queue_selection(self, current: QtCore.QModelIndex, _previous: QtCore.QModelIndex) -> None:
        state = self._queue_model.data(current, QtCore.Qt.ItemDataRole.UserRole)
        if not isinstance(state, TrackAnalysisState):
            return
        self._current_state = state
        self._detail_title.setText(Path(state.track.path).name)
        self._field_comparison.load_state(state)
        self._audio_panel.load_result(state.audio_result)
        self._sources_panel.load_report(state.metadata_report)

    def _start_pipeline(self) -> None:
        settings = load_settings()
        provider = self._provider_combo.currentText()
        method = self._method_combo.currentData() or "auto"
        tagger = None
        if self._chk_ai.isChecked():
            if provider == "local":
                tagger = LocalAiTagger()
            else:
                api_key, base_url, model = _resolve_provider_config(provider, settings)
                if not api_key:
                    QtWidgets.QMessageBox.warning(self, "Brak klucza API", f"Ustaw klucz API dla providera '{provider}' w ustawieniach.")
                    return
                tagger = CloudAiTagger(provider, api_key, base_url=base_url, model=model)
        auto_filler = None
        if self._chk_meta.isChecked():
            auto_filler = AutoMetadataFiller(
                settings.acoustid_api_key,
                settings.musicbrainz_app_name,
                settings.discogs_token,
                settings.validation_policy,
                settings.metadata_cache_ttl_days,
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
        self._accept_all_btn.setEnabled(False)
        self._reject_all_btn.setEnabled(False)
        self._apply_btn.setEnabled(False)
        self._run_btn.setEnabled(False)
        self._stop_btn.setEnabled(True)
        self._status_lbl.setText("Uruchamianie analizy...")
        self._worker = _PipelineWorker(self._states, tagger, auto_filler, method, self._chk_audio.isChecked())
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
        self._status_lbl.setText(f"Analizuję: {name}")
        self._log_view.appendPlainText(f"> {name}")

    def _on_track_done(self, row: int) -> None:
        state = self._states[row]
        self._queue_model.refresh_row(row)
        self._progress_bar.setValue(row + 1)
        if self._queue_list.currentIndex().isValid() and self._queue_list.currentIndex().row() == row:
            self._field_comparison.load_state(state)
            self._audio_panel.load_result(state.audio_result)
            self._sources_panel.load_report(state.metadata_report)
        if state.status == TrackStatus.DONE:
            changed = _changed_fields(state.track, state.proposed_track)
            self._log_view.appendPlainText(f"  zmienione pola: {', '.join(changed) if changed else 'brak'}")
            if state.metadata_report is not None:
                self._log_view.appendPlainText(f"  źródła: {state.metadata_report.summary}")
            if state.ai_result is not None:
                self._log_view.appendPlainText(
                    f"  AI: bpm={state.ai_result.bpm} key={state.ai_result.key} "
                    f"genre={state.ai_result.genre} mood={state.ai_result.mood} energy={state.ai_result.energy} "
                    f"conf={float(state.ai_result.confidence or 0.0):.0%}"
                )
        elif state.status == TrackStatus.ERROR:
            self._log_view.appendPlainText(f"  błąd: {state.error_msg}")

    def _on_finished(self) -> None:
        self._run_btn.setEnabled(True)
        self._stop_btn.setEnabled(False)
        done = sum(1 for state in self._states if state.status == TrackStatus.DONE)
        errors = sum(1 for state in self._states if state.status == TrackStatus.ERROR)
        self._status_lbl.setText(f"Gotowe: {done} OK, {errors} błędów")
        self._log_view.appendPlainText(f"\n-- Zakończono: {done}/{len(self._states)} --")
        self._accept_all_btn.setEnabled(done > 0)
        self._reject_all_btn.setEnabled(done > 0)
        self._update_apply_btn()
        if not self._queue_list.currentIndex().isValid():
            for row, state in enumerate(self._states):
                if state.status == TrackStatus.DONE:
                    self._queue_list.setCurrentIndex(self._queue_model.index(row))
                    break

    def _accept_all_tracks(self) -> None:
        for state in self._states:
            for field_name in _changed_fields(state.track, state.proposed_track):
                state.decisions[field_name] = True
        if self._current_state is not None:
            self._field_comparison.load_state(self._current_state)
        self._update_apply_btn()

    def _reject_all_tracks(self) -> None:
        for state in self._states:
            for field_name in _changed_fields(state.track, state.proposed_track):
                state.decisions[field_name] = False
        if self._current_state is not None:
            self._field_comparison.load_state(self._current_state)
        self._update_apply_btn()

    def _update_apply_btn(self) -> None:
        self._apply_btn.setEnabled(any(value is True for state in self._states for value in state.decisions.values()))

    def _apply_accepted(self) -> None:
        source = f"ai:{self._provider_combo.currentText()}"
        changed_tracks: list[Track] = []
        write_errors: list[str] = []
        for state in self._states:
            db_tags: list[str] = []
            file_tags: dict[str, str] = {}
            for field_name in FIELDS:
                if state.decisions.get(field_name) is not True:
                    continue
                old_value = getattr(state.track, field_name, None)
                new_value = getattr(state.proposed_track, field_name, None)
                if _format_value(field_name, old_value) == _format_value(field_name, new_value):
                    continue
                setattr(state.track, field_name, new_value)
                db_tags.append(f"{field_name}:{new_value}")
                file_tags[field_name] = str(new_value) if new_value is not None else ""
            if db_tags:
                replace_track_tags(state.track.path, db_tags, source=source, confidence=state.ai_result.confidence if state.ai_result else None)
                try:
                    write_tags(Path(state.track.path), file_tags)
                except Exception as exc:
                    write_errors.append(f"{Path(state.track.path).name}: {exc}")
                changed_tracks.append(state.track)
        if changed_tracks:
            update_tracks(changed_tracks)
            msg = f"Zapisano zmiany dla {len(changed_tracks)} utworów (baza + pliki audio)."
            if write_errors:
                msg += f"\nBłędy zapisu tagów: {len(write_errors)}"
                for err in write_errors[:5]:
                    msg += f"\n  {err}"
            self._status_lbl.setText(msg)
            self.accept()
        else:
            self._status_lbl.setText("Brak zaakceptowanych zmian do zapisania.")

    def _analyze(self) -> None:
        self._start_pipeline()


class _WorkerSignals(QtCore.QObject):
    track_started = QtCore.pyqtSignal(int)
    track_done = QtCore.pyqtSignal(int)
    finished = QtCore.pyqtSignal()


class _PipelineWorker(QtCore.QRunnable):
    def __init__(self, states: list[TrackAnalysisState], tagger, auto_filler, method: str, do_audio: bool):
        super().__init__()
        self.states = states
        self.tagger = tagger
        self.auto_filler = auto_filler
        self.method = method
        self.do_audio = do_audio
        self.signals = _WorkerSignals()
        self._stop = False

    def stop(self) -> None:
        self._stop = True

    def run(self) -> None:
        extractor = None
        if self.do_audio:
            try:
                from lumbago_app.services.audio_features import AudioFeatureExtractor

                extractor = AudioFeatureExtractor()
            except Exception:
                extractor = None
        for idx, state in enumerate(self.states):
            if self._stop:
                state.status = TrackStatus.SKIPPED
                self.signals.track_done.emit(idx)
                continue
            self.signals.track_started.emit(idx)
            try:
                working = deepcopy(state.track)
                state.decisions.clear()
                state.metadata_report = None
                state.ai_result = None
                state.audio_result = None
                state.error_msg = ""
                if extractor is not None:
                    try:
                        state.audio_result = extractor.extract(Path(working.path))
                    except Exception:
                        state.audio_result = None
                    detected_key = detect_key(Path(working.path))
                    enrich_track_with_analysis(
                        working,
                        detected_bpm=_safe_tempo(state.audio_result),
                        detected_key=detected_key if detected_key and not working.key else None,
                        detected_energy=_audio_energy(state.audio_result),
                    )
                    if state.audio_result is not None:
                        try:
                            from lumbago_app.core.models import AudioFeatures
                            from lumbago_app.data.repository import upsert_audio_features
                            af = AudioFeatures(
                                track_id=0,
                                mfcc_json=getattr(state.audio_result, "mfcc_json", "[]") or "[]",
                                tempo=getattr(state.audio_result, "tempo", None),
                                spectral_centroid=getattr(state.audio_result, "spectral_centroid", None),
                                spectral_rolloff=getattr(state.audio_result, "spectral_rolloff", None),
                                brightness=getattr(state.audio_result, "brightness", None),
                                roughness=getattr(state.audio_result, "roughness", None),
                                zero_crossing_rate=getattr(state.audio_result, "zero_crossing_rate", None),
                                chroma_json=getattr(state.audio_result, "chroma_json", None),
                                danceability=getattr(state.audio_result, "danceability", None),
                                valence=getattr(state.audio_result, "valence", None),
                            )
                            upsert_audio_features(working.path, af)
                        except Exception:
                            pass
                if self.auto_filler is not None:
                    state.metadata_report = self.auto_filler.fill_missing_with_report(working, self.method)
                if self.tagger is not None:
                    state.ai_result = self.tagger.analyze(working)
                    _merge_analysis_into_track(working, state.ai_result)
                    if float(state.ai_result.confidence or 0.0) >= 0.6:
                        for field_name in AI_FIELDS:
                            if _format_value(field_name, getattr(state.track, field_name, None)) != _format_value(field_name, getattr(working, field_name, None)):
                                state.decisions[field_name] = True
                state.proposed_track = working
                state.status = TrackStatus.DONE
            except Exception as exc:
                state.status = TrackStatus.ERROR
                state.error_msg = str(exc)
                state.proposed_track = deepcopy(state.track)
            self.signals.track_done.emit(idx)
        self.signals.finished.emit()


def _vsep() -> QtWidgets.QFrame:
    separator = QtWidgets.QFrame()
    separator.setFrameShape(QtWidgets.QFrame.Shape.VLine)
    separator.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
    return separator


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
