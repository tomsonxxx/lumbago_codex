"""Przeprojektowane Studio Analizy + AutoTagowania AI — Lumbago Music
================================================================

Układ:
  ┌──────────────────────────────────────────────────────────────────┐
  │  Pasek narzędzi: [Pipeline] [Provider] [Metadane] [▶ Uruchom]   │
  ├──────────────────┬───────────────────────────────────────────────┤
  │  Kolejka         │  Zakładki: AI Tagi | Analiza Audio | Log      │
  │  (lista z        │                                               │
  │   statusami)     │  FieldComparisonWidget — per-field diff       │
  │                  │  z paskami pewności i przyciskami ✓/✗         │
  ├──────────────────┴───────────────────────────────────────────────┤
  │  [████████░░] 8/12 utworów  "Analizuję: track.mp3"              │
  │  [✓ Akceptuj wszystko] [✗ Odrzuć wszystko] … [💾 Zastosuj]      │
  └──────────────────────────────────────────────────────────────────┘
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from PyQt6 import QtCore, QtGui, QtWidgets

from lumbago_app.core.config import load_settings
from lumbago_app.core.models import AnalysisResult, Track
from lumbago_app.data.repository import replace_track_tags, update_tracks
from lumbago_app.services.ai_tagger import CloudAiTagger, LocalAiTagger
from lumbago_app.services.metadata_enricher import AutoMetadataFiller
from lumbago_app.ui.widgets import apply_dialog_fade


# ──────────────────────────────────────────────────────────────────────────────
# Stałe
# ──────────────────────────────────────────────────────────────────────────────

FIELDS = ["bpm", "key", "genre", "mood", "energy"]
FIELD_LABELS = {"bpm": "BPM", "key": "Tonacja", "genre": "Gatunek", "mood": "Nastrój", "energy": "Energia"}


# ──────────────────────────────────────────────────────────────────────────────
# Model danych — stan jednego utworu w kolejce
# ──────────────────────────────────────────────────────────────────────────────

class TrackStatus(Enum):
    QUEUED  = "queued"
    RUNNING = "running"
    DONE    = "done"
    ERROR   = "error"
    SKIPPED = "skipped"


_STATUS_ICON: dict[TrackStatus, tuple[str, str]] = {
    TrackStatus.QUEUED:  ("○", "#888888"),
    TrackStatus.RUNNING: ("⟳", "#FFD700"),
    TrackStatus.DONE:    ("✓", "#00E676"),
    TrackStatus.ERROR:   ("✗", "#FF5252"),
    TrackStatus.SKIPPED: ("–", "#888888"),
}


@dataclass
class TrackAnalysisState:
    track: Track
    status: TrackStatus = TrackStatus.QUEUED
    audio_result: Any = None          # AudioFeatureResult | None
    ai_result: AnalysisResult | None = None
    error_msg: str = ""
    # per-field decyzja: True=akceptuj, False=odrzuć, None=niezdecydowany
    decisions: dict[str, bool | None] = field(default_factory=dict)


# ──────────────────────────────────────────────────────────────────────────────
# Model listy kolejki (lewa kolumna)
# ──────────────────────────────────────────────────────────────────────────────

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
            icon, _ = _STATUS_ICON[state.status]
            name = Path(state.track.path).stem[:48]
            return f"{icon}  {name}"
        if role == QtCore.Qt.ItemDataRole.ForegroundRole:
            _, color = _STATUS_ICON[state.status]
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


# ──────────────────────────────────────────────────────────────────────────────
# Widget: pasek pewności (kolorowy)
# ──────────────────────────────────────────────────────────────────────────────

class ConfidenceBar(QtWidgets.QWidget):
    """Kolorowy pasek pewności z procentem tekstowym."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._value = 0.0
        self.setFixedHeight(16)
        self.setMinimumWidth(80)

    def set_value(self, v: float) -> None:
        self._value = max(0.0, min(1.0, v))
        self.update()

    def paintEvent(self, _event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        painter.fillRect(0, 0, w, h, QtGui.QColor("#1a1a2e"))
        filled = int(w * self._value)
        if self._value >= 0.75:
            color = QtGui.QColor("#00E676")
        elif self._value >= 0.5:
            color = QtGui.QColor("#FFD700")
        else:
            color = QtGui.QColor("#FF5252")
        if filled > 0:
            painter.fillRect(0, 0, filled, h, color)
        painter.setPen(QtGui.QColor("white"))
        painter.setFont(QtGui.QFont("Consolas", 8))
        painter.drawText(
            0, 0, w, h,
            QtCore.Qt.AlignmentFlag.AlignCenter,
            f"{self._value:.0%}",
        )


# ──────────────────────────────────────────────────────────────────────────────
# Widget: tabela per-field (prawa kolumna, zakładka AI Tagi)
# ──────────────────────────────────────────────────────────────────────────────

class FieldComparisonWidget(QtWidgets.QWidget):
    """
    Tabela porównawcza pól:
      Pole | Obecna wartość | Propozycja AI | Pewność | [✓] [✗]
    """

    decisions_changed = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._state: TrackAnalysisState | None = None
        self._rows: dict[str, dict] = {}
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        # Nagłówek
        hdr = QtWidgets.QWidget()
        hdr.setObjectName("FieldComparisonHeader")
        hl = QtWidgets.QHBoxLayout(hdr)
        hl.setContentsMargins(6, 3, 6, 3)
        for text, stretch in [("Pole", 1), ("Obecna", 2), ("Propozycja AI", 2), ("Pewność", 2), ("", 1)]:
            lbl = QtWidgets.QLabel(f"<b>{text}</b>")
            lbl.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            hl.addWidget(lbl, stretch)
        layout.addWidget(hdr)

        sep = QtWidgets.QFrame()
        sep.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        sep.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
        layout.addWidget(sep)

        # Wiersze pól
        for fname in FIELDS:
            row_w = QtWidgets.QWidget()
            row_w.setObjectName("FieldRow")
            rl = QtWidgets.QHBoxLayout(row_w)
            rl.setContentsMargins(6, 4, 6, 4)
            rl.setSpacing(8)

            lbl_field = QtWidgets.QLabel(FIELD_LABELS[fname])
            lbl_field.setObjectName("FieldLabel")
            lbl_field.setFixedWidth(62)

            lbl_current = QtWidgets.QLabel("—")
            lbl_current.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            lbl_current.setObjectName("CurrentValue")

            lbl_proposed = QtWidgets.QLabel("—")
            lbl_proposed.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            lbl_proposed.setObjectName("ProposedValue")

            conf_bar = ConfidenceBar()

            btn_accept = QtWidgets.QPushButton("✓")
            btn_accept.setFixedSize(26, 26)
            btn_accept.setCheckable(True)
            btn_accept.setObjectName("AcceptBtn")
            btn_accept.setToolTip("Akceptuj to pole")

            btn_reject = QtWidgets.QPushButton("✗")
            btn_reject.setFixedSize(26, 26)
            btn_reject.setCheckable(True)
            btn_reject.setObjectName("RejectBtn")
            btn_reject.setToolTip("Odrzuć to pole")

            def _make_handlers(fn, ab, rb):
                def _on_accept():
                    if ab.isChecked():
                        rb.setChecked(False)
                    self._on_decision(fn)

                def _on_reject():
                    if rb.isChecked():
                        ab.setChecked(False)
                    self._on_decision(fn)

                ab.clicked.connect(_on_accept)
                rb.clicked.connect(_on_reject)

            _make_handlers(fname, btn_accept, btn_reject)

            rl.addWidget(lbl_field, 1)
            rl.addWidget(lbl_current, 2)
            rl.addWidget(lbl_proposed, 2)
            rl.addWidget(conf_bar, 2)
            rl.addWidget(btn_accept)
            rl.addWidget(btn_reject)

            layout.addWidget(row_w)
            self._rows[fname] = {
                "row_widget": row_w,
                "current": lbl_current,
                "proposed": lbl_proposed,
                "conf_bar": conf_bar,
                "accept": btn_accept,
                "reject": btn_reject,
            }

        layout.addStretch()

    def _on_decision(self, fname: str) -> None:
        if self._state is None:
            return
        row = self._rows[fname]
        if row["accept"].isChecked():
            self._state.decisions[fname] = True
        elif row["reject"].isChecked():
            self._state.decisions[fname] = False
        else:
            self._state.decisions[fname] = None
        self.decisions_changed.emit()

    def load_state(self, state: TrackAnalysisState | None) -> None:
        self._state = state
        if state is None:
            for row in self._rows.values():
                row["current"].setText("—")
                row["proposed"].setText("—")
                row["conf_bar"].set_value(0.0)
                row["accept"].setChecked(False)
                row["reject"].setChecked(False)
                row["row_widget"].setEnabled(False)
            return

        track = state.track
        result = state.ai_result

        current: dict[str, str] = {
            "bpm":    str(track.bpm) if track.bpm else "—",
            "key":    track.key or "—",
            "genre":  track.genre or "—",
            "mood":   track.mood or "—",
            "energy": f"{track.energy:.2f}" if track.energy is not None else "—",
        }

        proposed: dict[str, str] = {}
        if result:
            proposed = {
                "bpm":    str(result.bpm) if result.bpm else "—",
                "key":    result.key or "—",
                "genre":  result.genre or "—",
                "mood":   result.mood or "—",
                "energy": f"{result.energy:.2f}" if result.energy is not None else "—",
            }

        conf = (result.confidence or 0.0) if result else 0.0

        for fname, row in self._rows.items():
            has_result = result is not None
            row["row_widget"].setEnabled(has_result)
            row["current"].setText(current[fname])
            prop_val = proposed.get(fname, "—") if has_result else "—"
            row["proposed"].setText(prop_val)
            row["conf_bar"].set_value(conf)

            # Podświetl zmienione wartości
            if has_result and prop_val != "—" and prop_val != current[fname]:
                row["proposed"].setStyleSheet("color: #00E676; font-weight: bold;")
            else:
                row["proposed"].setStyleSheet("")

            # Przywróć decyzję
            dec = state.decisions.get(fname)
            row["accept"].setChecked(dec is True)
            row["reject"].setChecked(dec is False)

    def accept_all_confident(self, threshold: float = 0.6) -> None:
        """Zaznacz ✓ dla wszystkich pól których pewność >= threshold."""
        if self._state is None or self._state.ai_result is None:
            return
        conf = self._state.ai_result.confidence or 0.0
        if conf >= threshold:
            for fname, row in self._rows.items():
                if row["proposed"].text() != "—":
                    row["accept"].setChecked(True)
                    row["reject"].setChecked(False)
                    self._state.decisions[fname] = True
        self.decisions_changed.emit()

    def reject_all(self) -> None:
        if self._state is None:
            return
        for fname, row in self._rows.items():
            row["accept"].setChecked(False)
            row["reject"].setChecked(True)
            self._state.decisions[fname] = False
        self.decisions_changed.emit()


# ──────────────────────────────────────────────────────────────────────────────
# Widget: wyniki analizy audio (zakładka Analiza Audio)
# ──────────────────────────────────────────────────────────────────────────────

class AudioInfoPanel(QtWidgets.QWidget):
    """Wyniki AudioFeatureExtractor dla zaznaczonego utworu."""

    def __init__(self, parent=None):
        super().__init__(parent)
        fl = QtWidgets.QFormLayout(self)
        fl.setContentsMargins(12, 12, 12, 12)
        fl.setSpacing(8)

        def _bar():
            b = QtWidgets.QProgressBar()
            b.setRange(0, 100)
            b.setFixedHeight(13)
            b.setTextVisible(False)
            return b

        self._tempo_lbl     = QtWidgets.QLabel("—")
        self._bright_bar    = _bar()
        self._rough_bar     = _bar()
        self._spectral_lbl  = QtWidgets.QLabel("—")
        self._mfcc_lbl      = QtWidgets.QLabel("—")
        self._mfcc_lbl.setWordWrap(True)

        fl.addRow("Tempo (librosa):",   self._tempo_lbl)
        fl.addRow("Jasność tonu:",      self._bright_bar)
        fl.addRow("Szorstkość:",        self._rough_bar)
        fl.addRow("Centroid spektralny:", self._spectral_lbl)
        fl.addRow("MFCC top-5:",        self._mfcc_lbl)

    def load_result(self, result) -> None:
        if result is None:
            self._tempo_lbl.setText("—")
            self._bright_bar.setValue(0)
            self._rough_bar.setValue(0)
            self._spectral_lbl.setText("—")
            self._mfcc_lbl.setText("—")
            return
        self._tempo_lbl.setText(f"{result.tempo:.1f} BPM" if result.tempo else "—")
        self._bright_bar.setValue(int((result.brightness or 0.0) * 100))
        self._rough_bar.setValue(int((result.roughness or 0.0) * 100))
        self._spectral_lbl.setText(f"{result.spectral_centroid:.0f} Hz" if result.spectral_centroid else "—")
        try:
            mfcc = json.loads(result.mfcc_json or "[]")
            self._mfcc_lbl.setText(str([round(v, 2) for v in mfcc[:5]]))
        except Exception:
            self._mfcc_lbl.setText("—")


# ──────────────────────────────────────────────────────────────────────────────
# Główne okno dialogowe
# ──────────────────────────────────────────────────────────────────────────────

class AiTaggerDialog(QtWidgets.QDialog):
    """
    Studio Analizy i AutoTagowania AI.

    Przepływ pracy:
      1. Użytkownik wybiera kroki pipeline (audio / AI / metadane online)
      2. Klika ▶ Uruchom — worker analizuje każdy utwór kolejno
      3. Status i wyniki widać live na liście kolejki (lewa kolumna)
      4. Kliknięcie utworu na liście pokazuje szczegóły (prawa kolumna):
         - per-field diff: obecna vs proponowana wartość + pasek pewności
         - wyniki analizy audio (librosa)
         - log
      5. Użytkownik akceptuje/odrzuca pola per-utwór lub hurtowo
      6. Klika 💾 Zastosuj — zapisuje tylko zaakceptowane pola
    """

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
        self.setMinimumSize(1020, 640)
        apply_dialog_fade(self)

        self._tracks = tracks
        self._auto_fetch_default = auto_fetch
        self._auto_method_default = auto_method
        self._allow_auto_fetch = allow_auto_fetch
        self._force_cloud = force_cloud

        self._states: list[TrackAnalysisState] = [TrackAnalysisState(track=t) for t in tracks]
        self._queue_model = TrackQueueModel(self._states)
        self._worker: _PipelineWorker | None = None
        self._current_state: TrackAnalysisState | None = None

        self._build_ui()

    # ── Budowa UI ──────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 8)
        root.setSpacing(8)

        root.addWidget(self._build_toolbar())
        root.addWidget(self._build_main_area(), 1)
        root.addWidget(self._build_bottom_bar())

    def _build_toolbar(self) -> QtWidgets.QWidget:
        toolbar = QtWidgets.QFrame()
        toolbar.setObjectName("StudioToolbar")
        tl = QtWidgets.QHBoxLayout(toolbar)
        tl.setContentsMargins(10, 6, 10, 6)
        tl.setSpacing(10)

        tl.addWidget(QtWidgets.QLabel("<b>Pipeline:</b>"))
        self._chk_audio = QtWidgets.QCheckBox("Analiza audio")
        self._chk_audio.setChecked(True)
        self._chk_audio.setToolTip("Ekstrahuj BPM, jasność, MFCC i waveform przez librosa")
        self._chk_ai = QtWidgets.QCheckBox("AI tagowanie")
        self._chk_ai.setChecked(True)
        self._chk_ai.setToolTip("Uzupełnij brakujące tagi przez wybrany model AI")
        self._chk_meta = QtWidgets.QCheckBox("Metadane online")
        self._chk_meta.setChecked(self._auto_fetch_default)
        self._chk_meta.setToolTip("Pobierz metadane z AcoustID / MusicBrainz / Discogs")
        if not self._allow_auto_fetch:
            self._chk_meta.setChecked(False)
            self._chk_meta.setEnabled(False)

        tl.addWidget(self._chk_audio)
        tl.addWidget(self._chk_ai)
        tl.addWidget(self._chk_meta)
        tl.addWidget(_vsep())

        tl.addWidget(QtWidgets.QLabel("Provider:"))
        self._provider_combo = QtWidgets.QComboBox()
        self._provider_combo.addItems(["local", "openai", "gemini", "grok", "deepseek"])
        settings = load_settings()
        self._provider_combo.setCurrentText(settings.cloud_ai_provider or "local")
        self._provider_combo.setMinimumWidth(90)
        tl.addWidget(self._provider_combo)

        tl.addWidget(QtWidgets.QLabel("Metadane:"))
        self._method_combo = QtWidgets.QComboBox()
        self._method_combo.addItems(["Auto", "AcoustID + MusicBrainz", "MusicBrainz", "Discogs"])
        if self._auto_method_default:
            self._method_combo.setCurrentText(_auto_method_label(self._auto_method_default))
        self._method_combo.setMinimumWidth(150)
        tl.addWidget(self._method_combo)

        tl.addStretch()

        self._run_btn = QtWidgets.QPushButton("▶  Uruchom")
        self._run_btn.setObjectName("PrimaryBtn")
        self._run_btn.setFixedHeight(32)
        self._run_btn.clicked.connect(self._start_pipeline)

        self._stop_btn = QtWidgets.QPushButton("■  Stop")
        self._stop_btn.setObjectName("DangerBtn")
        self._stop_btn.setFixedHeight(32)
        self._stop_btn.setEnabled(False)
        self._stop_btn.clicked.connect(self._stop_pipeline)

        tl.addWidget(self._run_btn)
        tl.addWidget(self._stop_btn)
        return toolbar

    def _build_main_area(self) -> QtWidgets.QWidget:
        splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)

        # ── Lewa kolumna: kolejka ─────────────────────────────────────────────
        left = QtWidgets.QWidget()
        ll = QtWidgets.QVBoxLayout(left)
        ll.setContentsMargins(0, 0, 4, 0)
        ll.setSpacing(4)

        hdr = QtWidgets.QLabel(f"<b>Kolejka</b>  ({len(self._tracks)} utworów)")
        hdr.setObjectName("SectionTitle")
        ll.addWidget(hdr)

        self._queue_list = QtWidgets.QListView()
        self._queue_list.setModel(self._queue_model)
        self._queue_list.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        self._queue_list.setAlternatingRowColors(True)
        self._queue_list.selectionModel().currentChanged.connect(self._on_queue_selection)
        ll.addWidget(self._queue_list, 1)

        splitter.addWidget(left)

        # ── Prawa kolumna: szczegóły ──────────────────────────────────────────
        right = QtWidgets.QWidget()
        rl = QtWidgets.QVBoxLayout(right)
        rl.setContentsMargins(4, 0, 0, 0)
        rl.setSpacing(4)

        self._detail_title = QtWidgets.QLabel("← Wybierz utwór z listy")
        self._detail_title.setObjectName("DialogTitle")
        rl.addWidget(self._detail_title)

        self._tabs = QtWidgets.QTabWidget()

        # Zakładka 1: porównanie per-field
        self._field_comparison = FieldComparisonWidget()
        self._field_comparison.decisions_changed.connect(self._update_apply_btn)
        self._tabs.addTab(self._field_comparison, "AI Tagi")

        # Zakładka 2: analiza audio
        self._audio_panel = AudioInfoPanel()
        self._tabs.addTab(self._audio_panel, "Analiza Audio")

        # Zakładka 3: log
        self._log_view = QtWidgets.QPlainTextEdit()
        self._log_view.setReadOnly(True)
        self._log_view.setPlaceholderText("Log przetwarzania pojawi się tutaj…")
        self._log_view.setFont(QtGui.QFont("Consolas", 8))
        self._tabs.addTab(self._log_view, "Log")

        rl.addWidget(self._tabs, 1)

        # Przyciski per-utwór
        per_track = QtWidgets.QHBoxLayout()
        self._btn_accept_confident = QtWidgets.QPushButton("✓ Akceptuj pewne (≥60%)")
        self._btn_accept_confident.setToolTip("Zaznacz ✓ dla wszystkich pól z pewnością ≥ 60%")
        self._btn_accept_confident.clicked.connect(
            lambda: self._field_comparison.accept_all_confident(0.6)
        )
        self._btn_reject_track = QtWidgets.QPushButton("✗ Odrzuć wszystkie pola")
        self._btn_reject_track.clicked.connect(self._field_comparison.reject_all)
        per_track.addWidget(self._btn_accept_confident)
        per_track.addWidget(self._btn_reject_track)
        per_track.addStretch()
        rl.addLayout(per_track)

        splitter.addWidget(right)
        splitter.setSizes([290, 730])
        return splitter

    def _build_bottom_bar(self) -> QtWidgets.QWidget:
        bottom = QtWidgets.QFrame()
        bottom.setObjectName("StudioBottomBar")
        bl = QtWidgets.QVBoxLayout(bottom)
        bl.setContentsMargins(8, 6, 8, 6)
        bl.setSpacing(4)

        # Pasek postępu
        prog_row = QtWidgets.QHBoxLayout()
        self._progress_bar = QtWidgets.QProgressBar()
        self._progress_bar.setRange(0, max(1, len(self._tracks)))
        self._progress_bar.setValue(0)
        self._progress_bar.setFixedHeight(16)
        self._status_lbl = QtWidgets.QLabel("Gotowy do analizy.")
        self._status_lbl.setObjectName("DialogHint")
        prog_row.addWidget(self._progress_bar, 3)
        prog_row.addWidget(self._status_lbl, 2)
        bl.addLayout(prog_row)

        # Przyciski akcji
        act_row = QtWidgets.QHBoxLayout()
        self._accept_all_btn = QtWidgets.QPushButton("✓ Akceptuj wszystko")
        self._accept_all_btn.setEnabled(False)
        self._accept_all_btn.clicked.connect(self._accept_all_tracks)

        self._reject_all_btn = QtWidgets.QPushButton("✗ Odrzuć wszystko")
        self._reject_all_btn.setEnabled(False)
        self._reject_all_btn.clicked.connect(self._reject_all_tracks)

        self._apply_btn = QtWidgets.QPushButton("💾 Zastosuj zaakceptowane")
        self._apply_btn.setObjectName("PrimaryBtn")
        self._apply_btn.setEnabled(False)
        self._apply_btn.clicked.connect(self._apply_accepted)

        self._cancel_btn = QtWidgets.QPushButton("Anuluj")
        self._cancel_btn.clicked.connect(self.reject)

        act_row.addWidget(self._accept_all_btn)
        act_row.addWidget(self._reject_all_btn)
        act_row.addStretch()
        act_row.addWidget(self._apply_btn)
        act_row.addWidget(self._cancel_btn)
        bl.addLayout(act_row)
        return bottom

    # ── Sloty ─────────────────────────────────────────────────────────────────

    def _on_queue_selection(
        self, current: QtCore.QModelIndex, _previous: QtCore.QModelIndex
    ) -> None:
        state = self._queue_model.data(current, QtCore.Qt.ItemDataRole.UserRole)
        if not isinstance(state, TrackAnalysisState):
            return
        self._current_state = state
        self._detail_title.setText(Path(state.track.path).name)
        self._field_comparison.load_state(state)
        self._audio_panel.load_result(state.audio_result)

    def _start_pipeline(self) -> None:
        settings = load_settings()
        provider = self._provider_combo.currentText()
        method = _auto_method_id(self._method_combo.currentText(), settings)

        tagger = None
        if self._chk_ai.isChecked():
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
                if not key:
                    QtWidgets.QMessageBox.warning(
                        self, "Brak klucza API",
                        "Ustaw klucz API dla wybranego providera w Ustawieniach.",
                    )
                    return
                base_url, model = _provider_settings(provider, settings)
                tagger = CloudAiTagger(provider, key, base_url=base_url, model=model)

        auto_filler = None
        if self._chk_meta.isChecked():
            auto_filler = AutoMetadataFiller(
                settings.acoustid_api_key,
                settings.musicbrainz_app_name,
                settings.discogs_token,
                settings.validation_policy,
                settings.metadata_cache_ttl_days,
            )

        # Reset stanów
        for state in self._states:
            state.status = TrackStatus.QUEUED
            state.ai_result = None
            state.audio_result = None
            state.decisions.clear()
        self._queue_model.refresh_all()
        self._progress_bar.setRange(0, max(1, len(self._tracks)))
        self._progress_bar.setValue(0)
        self._log_view.clear()
        self._accept_all_btn.setEnabled(False)
        self._reject_all_btn.setEnabled(False)
        self._apply_btn.setEnabled(False)
        self._run_btn.setEnabled(False)
        self._stop_btn.setEnabled(True)

        self._worker = _PipelineWorker(
            states=self._states,
            tagger=tagger,
            auto_filler=auto_filler,
            method=method,
            do_audio=self._chk_audio.isChecked(),
        )
        self._worker.signals.track_started.connect(self._on_track_started)
        self._worker.signals.track_done.connect(self._on_track_done)
        self._worker.signals.finished.connect(self._on_finished)
        QtCore.QThreadPool.globalInstance().start(self._worker)

    def _stop_pipeline(self) -> None:
        if self._worker:
            self._worker.stop()
        self._stop_btn.setEnabled(False)
        self._status_lbl.setText("Zatrzymywanie…")

    def _on_track_started(self, row: int) -> None:
        state = self._states[row]
        state.status = TrackStatus.RUNNING
        self._queue_model.refresh_row(row)
        name = Path(state.track.path).name
        self._status_lbl.setText(f"Analizuję: {name}")
        self._log_view.appendPlainText(f"▶ {name}")

    def _on_track_done(self, row: int) -> None:
        state = self._states[row]
        self._queue_model.refresh_row(row)
        self._progress_bar.setValue(row + 1)

        # Odśwież szczegóły jeśli zaznaczony
        sel = self._queue_list.currentIndex()
        if sel.isValid() and sel.row() == row:
            self._field_comparison.load_state(state)
            self._audio_panel.load_result(state.audio_result)

        # Log
        if state.status == TrackStatus.DONE and state.ai_result:
            r = state.ai_result
            conf_str = f"{r.confidence:.0%}" if r.confidence is not None else "?"
            self._log_view.appendPlainText(
                f"  ✓ bpm={r.bpm}  key={r.key}  genre={r.genre}  "
                f"mood={r.mood}  energy={r.energy}  conf={conf_str}"
            )
        elif state.status == TrackStatus.ERROR:
            self._log_view.appendPlainText(f"  ✗ Błąd: {state.error_msg}")

    def _on_finished(self) -> None:
        self._run_btn.setEnabled(True)
        self._stop_btn.setEnabled(False)
        done   = sum(1 for s in self._states if s.status == TrackStatus.DONE)
        errors = sum(1 for s in self._states if s.status == TrackStatus.ERROR)
        self._status_lbl.setText(f"Gotowe: {done} OK, {errors} błędów")
        self._log_view.appendPlainText(f"\n── Zakończono: {done}/{len(self._states)} ──")
        self._accept_all_btn.setEnabled(done > 0)
        self._reject_all_btn.setEnabled(done > 0)
        self._update_apply_btn()

        # Automatycznie zaznacz pierwszy gotowy utwór
        if not self._queue_list.currentIndex().isValid():
            for i, state in enumerate(self._states):
                if state.status == TrackStatus.DONE:
                    self._queue_list.setCurrentIndex(self._queue_model.index(i))
                    break

    def _accept_all_tracks(self) -> None:
        for state in self._states:
            if not state.ai_result:
                continue
            for fname in FIELDS:
                if getattr(state.ai_result, fname, None) is not None:
                    state.decisions[fname] = True
        if self._current_state:
            self._field_comparison.load_state(self._current_state)
        self._update_apply_btn()

    def _reject_all_tracks(self) -> None:
        for state in self._states:
            for fname in FIELDS:
                state.decisions[fname] = False
        if self._current_state:
            self._field_comparison.load_state(self._current_state)
        self._update_apply_btn()

    def _update_apply_btn(self) -> None:
        has_accept = any(
            v is True
            for state in self._states
            for v in state.decisions.values()
        )
        self._apply_btn.setEnabled(has_accept)

    def _apply_accepted(self) -> None:
        settings = load_settings()
        provider = self._provider_combo.currentText()
        source = f"ai:{provider}"
        changed: list[Track] = []

        for state in self._states:
            if not state.ai_result:
                continue
            result = state.ai_result
            track = state.track
            tags: list[str] = []
            modified = False
            for fname in FIELDS:
                if state.decisions.get(fname) is not True:
                    continue
                val = getattr(result, fname, None)
                if val is None:
                    continue
                setattr(track, fname, val)
                tags.append(f"{fname}:{val}")
                modified = True
            if modified:
                replace_track_tags(track.path, tags, source=source, confidence=result.confidence)
                changed.append(track)

        if changed:
            update_tracks(changed)
            self._status_lbl.setText(f"Zapisano zmiany dla {len(changed)} utworów.")
            self.accept()
        else:
            self._status_lbl.setText("Brak zaakceptowanych zmian do zapisania.")

    # ── Wsteczna kompatybilność z main_window ─────────────────────────────────

    def _analyze(self) -> None:
        """Alias dla _start_pipeline — zachowuje stary interfejs."""
        self._start_pipeline()


# ──────────────────────────────────────────────────────────────────────────────
# Worker: pipeline w wątku tła
# ──────────────────────────────────────────────────────────────────────────────

class _WorkerSignals(QtCore.QObject):
    track_started = QtCore.pyqtSignal(int)
    track_done    = QtCore.pyqtSignal(int)
    finished      = QtCore.pyqtSignal()


class _PipelineWorker(QtCore.QRunnable):
    def __init__(
        self,
        states: list[TrackAnalysisState],
        tagger,
        auto_filler,
        method: str,
        do_audio: bool,
    ):
        super().__init__()
        self.states      = states
        self.tagger      = tagger
        self.auto_filler = auto_filler
        self.method      = method
        self.do_audio    = do_audio
        self.signals     = _WorkerSignals()
        self._stop       = False

    def stop(self) -> None:
        self._stop = True

    def run(self) -> None:
        extractor = None
        if self.do_audio:
            try:
                from lumbago_app.services.audio_features import AudioFeatureExtractor
                extractor = AudioFeatureExtractor()
            except Exception:
                pass

        for idx, state in enumerate(self.states):
            if self._stop:
                state.status = TrackStatus.SKIPPED
                self.signals.track_done.emit(idx)
                continue

            self.signals.track_started.emit(idx)
            try:
                # Krok 1: analiza audio (librosa)
                if extractor:
                    try:
                        state.audio_result = extractor.extract(Path(state.track.path))
                    except Exception:
                        state.audio_result = None

                # Krok 2: metadane online
                if self.auto_filler:
                    try:
                        self.auto_filler.fill_missing(state.track, self.method)
                    except Exception:
                        pass

                # Krok 3: AI tagowanie
                if self.tagger:
                    result = self.tagger.analyze(state.track)
                    state.ai_result = result
                    # Automatyczna akceptacja pól z wysoką pewnością
                    conf = result.confidence or 0.0
                    if conf >= 0.6:
                        for fname in FIELDS:
                            if getattr(result, fname, None) is not None:
                                state.decisions[fname] = True

                state.status = TrackStatus.DONE
            except Exception as exc:
                state.status = TrackStatus.ERROR
                state.error_msg = str(exc)

            self.signals.track_done.emit(idx)

        self.signals.finished.emit()


# ──────────────────────────────────────────────────────────────────────────────
# Pomocnicze
# ──────────────────────────────────────────────────────────────────────────────

def _vsep() -> QtWidgets.QFrame:
    sep = QtWidgets.QFrame()
    sep.setFrameShape(QtWidgets.QFrame.Shape.VLine)
    sep.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
    return sep


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
        return "Auto"
    if method == "acoustid":
        return "AcoustID + MusicBrainz"
    if method == "discogs":
        return "Discogs"
    return "MusicBrainz"


def _is_valid_key(value: str) -> bool:
    if re.match(r"^(1[0-2]|[1-9])[AB]$", value, re.IGNORECASE):
        return True
    return bool(re.match(r"^[A-G](#|b)?m?$", value, re.IGNORECASE))
