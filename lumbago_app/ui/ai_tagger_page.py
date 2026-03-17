from __future__ import annotations

import re
from typing import Any

from PyQt6 import QtCore, QtGui, QtWidgets

from lumbago_app.core.config import load_settings
from lumbago_app.core.models import AnalysisResult, Track
from lumbago_app.data.repository import replace_track_tags, update_tracks
from lumbago_app.services.ai_tagger import CloudAiTagger, LocalAiTagger

# ---------------------------------------------------------------------------
# Stale kolorow tematu
# ---------------------------------------------------------------------------
_BG = "#0a0d1a"
_CYAN = "#00d4ff"
_PURPLE = "#8b5cf6"
_PINK = "#ec4899"
_TEXT = "#e6f7ff"
_TEXT_DIM = "#94a3b8"

_STATUS_WAITING = "\u23f3 Oczekuje"
_STATUS_PROCESSING = "\U0001f504 Przetwarzanie"
_STATUS_SUCCESS = "\u2705 Sukces"
_STATUS_ERROR = "\u274c B\u0142\u0105d"

_PROVIDERS = ["lokalny", "openai", "gemini", "grok", "deepseek"]

_STYLESHEET = f"""
QWidget#AiTaggerPage {{
    background: {_BG};
}}
QFrame#Card {{
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 10px;
}}
QLabel {{
    color: {_TEXT};
    font-size: 13px;
}}
QLabel#SectionTitle {{
    color: {_CYAN};
    font-size: 15px;
    font-weight: 700;
    padding: 2px 0;
}}
QLabel.dim {{
    color: {_TEXT_DIM};
    font-size: 12px;
}}
QTableWidget {{
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 6px;
    color: {_TEXT};
    gridline-color: rgba(255,255,255,0.06);
    font-size: 12px;
    selection-background-color: rgba(0,212,255,0.15);
}}
QTableWidget::item {{
    padding: 4px 6px;
}}
QHeaderView::section {{
    background: rgba(255,255,255,0.06);
    color: {_CYAN};
    border: none;
    padding: 6px;
    font-weight: 600;
    font-size: 12px;
}}
QComboBox {{
    background: rgba(255,255,255,0.06);
    color: {_TEXT};
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 13px;
    min-width: 120px;
}}
QComboBox:hover {{
    border-color: {_CYAN};
}}
QComboBox::drop-down {{
    border: none;
    width: 24px;
}}
QComboBox QAbstractItemView {{
    background: #141829;
    color: {_TEXT};
    border: 1px solid rgba(255,255,255,0.12);
    selection-background-color: rgba(0,212,255,0.2);
}}
QPushButton#PrimaryAction {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 {_CYAN}, stop:1 {_PURPLE});
    color: #fff;
    border: none;
    border-radius: 6px;
    padding: 8px 18px;
    font-size: 13px;
    font-weight: 600;
}}
QPushButton#PrimaryAction:hover {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 {_PURPLE}, stop:1 {_PINK});
}}
QPushButton#PrimaryAction:disabled {{
    background: rgba(255,255,255,0.08);
    color: {_TEXT_DIM};
}}
QPushButton {{
    background: rgba(255,255,255,0.06);
    color: {_TEXT};
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 6px;
    padding: 7px 14px;
    font-size: 13px;
}}
QPushButton:hover {{
    border-color: {_CYAN};
    background: rgba(255,255,255,0.09);
}}
QProgressBar {{
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 6px;
    height: 18px;
    text-align: center;
    color: {_TEXT};
    font-size: 11px;
}}
QProgressBar::chunk {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 {_CYAN}, stop:1 {_PURPLE});
    border-radius: 5px;
}}
QScrollBar:vertical {{
    background: transparent;
    width: 8px;
}}
QScrollBar::handle:vertical {{
    background: rgba(255,255,255,0.12);
    border-radius: 4px;
    min-height: 30px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
"""


# ---------------------------------------------------------------------------
# Pomocnicze
# ---------------------------------------------------------------------------

def _provider_api_key(provider: str, settings) -> str | None:
    if provider == "openai":
        return settings.openai_api_key or settings.cloud_ai_api_key
    if provider == "grok":
        return settings.grok_api_key or settings.cloud_ai_api_key
    if provider == "deepseek":
        return settings.deepseek_api_key or settings.cloud_ai_api_key
    if provider == "gemini":
        return settings.cloud_ai_api_key
    return None


def _provider_settings(provider: str, settings) -> tuple[str | None, str | None]:
    if provider == "openai":
        return settings.openai_base_url, settings.openai_model
    if provider == "grok":
        return settings.grok_base_url, settings.grok_model
    if provider == "deepseek":
        return settings.deepseek_base_url, settings.deepseek_model
    return None, None


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
        if not re.match(r"^(1[0-2]|[1-9])[AB]$", key, re.IGNORECASE) and not re.match(
            r"^[A-G](#|b)?m?$", key, re.IGNORECASE
        ):
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


# ---------------------------------------------------------------------------
# Worker sygnaly i QRunnable
# ---------------------------------------------------------------------------

class _TaggerSignals(QtCore.QObject):
    progress = QtCore.pyqtSignal(int, int)
    track_done = QtCore.pyqtSignal(int, object)  # (row_index, AnalysisResult)
    finished = QtCore.pyqtSignal()
    error = QtCore.pyqtSignal(int, str)  # (row_index, error_message)


class _TaggerWorker(QtCore.QRunnable):
    def __init__(self, tracks: list[Track], tagger: Any):
        super().__init__()
        self.tracks = tracks
        self.tagger = tagger
        self.signals = _TaggerSignals()
        self._stop = False

    def stop(self) -> None:
        self._stop = True

    def run(self) -> None:
        total = len(self.tracks)
        for idx, track in enumerate(self.tracks):
            if self._stop:
                break
            try:
                result = self.tagger.analyze(track)
                self.signals.track_done.emit(idx, result)
            except Exception as exc:
                self.signals.error.emit(idx, str(exc))
            self.signals.progress.emit(idx + 1, total)
        self.signals.finished.emit()


# ---------------------------------------------------------------------------
# Widgety pomocnicze
# ---------------------------------------------------------------------------

def _make_card() -> QtWidgets.QFrame:
    frame = QtWidgets.QFrame()
    frame.setObjectName("Card")
    return frame


def _section_label(text: str) -> QtWidgets.QLabel:
    lbl = QtWidgets.QLabel(text)
    lbl.setObjectName("SectionTitle")
    return lbl


def _dim_label(text: str) -> QtWidgets.QLabel:
    lbl = QtWidgets.QLabel(text)
    lbl.setProperty("class", "dim")
    lbl.setStyleSheet(f"color: {_TEXT_DIM}; font-size: 12px;")
    return lbl


def _primary_button(text: str) -> QtWidgets.QPushButton:
    btn = QtWidgets.QPushButton(text)
    btn.setObjectName("PrimaryAction")
    return btn


# ---------------------------------------------------------------------------
# Glowny widget strony AI Tagger
# ---------------------------------------------------------------------------

class AiTaggerPage(QtWidgets.QWidget):
    """Strona AI Tagger do osadzenia w QStackedWidget."""

    tags_applied = QtCore.pyqtSignal()

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("AiTaggerPage")
        self.setStyleSheet(_STYLESHEET)

        self._tracks: list[Track] = []
        self._results: dict[int, AnalysisResult] = {}  # row -> result
        self._original_data: dict[int, dict[str, Any]] = {}  # row -> oryginalne tagi
        self._worker: _TaggerWorker | None = None
        self._selected_row: int = -1

        self._build_ui()

    # ---- budowanie UI --------------------------------------------------

    def _build_ui(self) -> None:
        root = QtWidgets.QHBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(14)

        # --- Lewa kolumna (60%) ---
        left = QtWidgets.QVBoxLayout()
        left.setSpacing(10)

        # Tytul sekcji
        left.addWidget(_section_label("Kolejka utworow"))

        # Wiersz batch-action
        batch_row = QtWidgets.QHBoxLayout()
        self._btn_start = _primary_button("Rozpocznij analiz\u0119")
        self._btn_stop = QtWidgets.QPushButton("Zatrzymaj")
        self._btn_select_all = QtWidgets.QPushButton("Zaznacz wszystkie")
        self._btn_deselect_all = QtWidgets.QPushButton("Odznacz wszystkie")
        self._btn_stop.setEnabled(False)
        batch_row.addWidget(self._btn_start)
        batch_row.addWidget(self._btn_stop)
        batch_row.addStretch(1)
        batch_row.addWidget(self._btn_select_all)
        batch_row.addWidget(self._btn_deselect_all)
        left.addLayout(batch_row)

        # Tabela
        self._table = QtWidgets.QTableWidget(0, 7)
        self._table.setHorizontalHeaderLabels(
            ["Tytu\u0142", "Artysta", "BPM", "Tonacja", "Nastr\u00f3j", "Gatunek", "Status"]
        )
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(
            QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows
        )
        self._table.setSelectionMode(
            QtWidgets.QAbstractItemView.SelectionMode.SingleSelection
        )
        self._table.setEditTriggers(
            QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers
        )
        header = self._table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Interactive)
        header.setSectionsMovable(True)
        left.addWidget(self._table, 1)

        # --- Prawa kolumna (40%) ---
        right = QtWidgets.QVBoxLayout()
        right.setSpacing(12)

        # Karta dostawcy
        provider_card = _make_card()
        pc_lay = QtWidgets.QVBoxLayout(provider_card)
        pc_lay.setContentsMargins(14, 12, 14, 12)
        pc_lay.setSpacing(8)
        pc_lay.addWidget(_section_label("Dostawca AI"))
        self._provider_combo = QtWidgets.QComboBox()
        self._provider_combo.addItems(_PROVIDERS)
        pc_lay.addWidget(self._provider_combo)
        self._provider_info = _dim_label("Wybierz dostawc\u0119 analizy tag\u00f3w")
        pc_lay.addWidget(self._provider_info)
        right.addWidget(provider_card)

        # Karta postepu
        progress_card = _make_card()
        pg_lay = QtWidgets.QVBoxLayout(progress_card)
        pg_lay.setContentsMargins(14, 12, 14, 12)
        pg_lay.setSpacing(8)
        pg_lay.addWidget(_section_label("Post\u0119p"))
        self._progress_bar = QtWidgets.QProgressBar()
        self._progress_bar.setRange(0, 1)
        self._progress_bar.setValue(0)
        self._progress_bar.setTextVisible(True)
        pg_lay.addWidget(self._progress_bar)
        self._progress_label = _dim_label("0/0 przetworzonych")
        pg_lay.addWidget(self._progress_label)
        right.addWidget(progress_card)

        # Karta szczeg. zaznaczonego
        detail_card = _make_card()
        dc_lay = QtWidgets.QVBoxLayout(detail_card)
        dc_lay.setContentsMargins(14, 12, 14, 12)
        dc_lay.setSpacing(6)
        dc_lay.addWidget(_section_label("Szczeg\u00f3\u0142y utworu"))

        self._detail_title = QtWidgets.QLabel("\u2014")
        self._detail_title.setWordWrap(True)
        dc_lay.addWidget(self._detail_title)

        # Oryginalne vs AI
        compare_grid = QtWidgets.QGridLayout()
        compare_grid.setSpacing(4)
        compare_grid.addWidget(
            _dim_label(""), 0, 0
        )
        orig_hdr = _dim_label("Oryginalne")
        orig_hdr.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        compare_grid.addWidget(orig_hdr, 0, 1)
        ai_hdr = _dim_label("AI")
        ai_hdr.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        compare_grid.addWidget(ai_hdr, 0, 2)

        self._compare_fields: dict[str, tuple[QtWidgets.QLabel, QtWidgets.QLabel]] = {}
        field_names = [
            ("BPM", "bpm"),
            ("Tonacja", "key"),
            ("Nastr\u00f3j", "mood"),
            ("Gatunek", "genre"),
            ("Energia", "energy"),
        ]
        for row_i, (display_name, field_key) in enumerate(field_names, start=1):
            lbl_name = _dim_label(display_name)
            lbl_orig = QtWidgets.QLabel("\u2014")
            lbl_orig.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            lbl_ai = QtWidgets.QLabel("\u2014")
            lbl_ai.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            lbl_ai.setStyleSheet(f"color: {_CYAN};")
            compare_grid.addWidget(lbl_name, row_i, 0)
            compare_grid.addWidget(lbl_orig, row_i, 1)
            compare_grid.addWidget(lbl_ai, row_i, 2)
            self._compare_fields[field_key] = (lbl_orig, lbl_ai)

        dc_lay.addLayout(compare_grid)
        right.addWidget(detail_card, 1)

        # Przyciski akcji
        action_card = _make_card()
        ac_lay = QtWidgets.QVBoxLayout(action_card)
        ac_lay.setContentsMargins(14, 12, 14, 12)
        ac_lay.setSpacing(8)
        self._btn_apply = _primary_button("Zastosuj tagi")
        self._btn_reject = QtWidgets.QPushButton("Odrzu\u0107")
        self._btn_apply_all = _primary_button("Zastosuj wszystkie")
        ac_lay.addWidget(self._btn_apply)
        ac_lay.addWidget(self._btn_reject)
        ac_lay.addWidget(self._btn_apply_all)
        self._btn_apply.setEnabled(False)
        self._btn_reject.setEnabled(False)
        self._btn_apply_all.setEnabled(False)
        right.addWidget(action_card)

        right.addStretch(0)

        # Proporcje 60/40
        left_w = QtWidgets.QWidget()
        left_w.setLayout(left)
        right_w = QtWidgets.QWidget()
        right_w.setLayout(right)

        root.addWidget(left_w, 6)
        root.addWidget(right_w, 4)

        # Polaczenia sygnalow
        self._btn_start.clicked.connect(self._start_analysis)
        self._btn_stop.clicked.connect(self._stop_analysis)
        self._btn_select_all.clicked.connect(self._select_all_rows)
        self._btn_deselect_all.clicked.connect(self._deselect_all_rows)
        self._btn_apply.clicked.connect(self._apply_selected)
        self._btn_reject.clicked.connect(self._reject_selected)
        self._btn_apply_all.clicked.connect(self._apply_all)
        self._table.currentCellChanged.connect(self._on_row_changed)

    # ---- publiczne API ------------------------------------------------

    def set_tracks(self, tracks: list[Track]) -> None:
        """Ustawia liste utworow do otagowania."""
        self._tracks = list(tracks)
        self._results.clear()
        self._original_data.clear()
        self._selected_row = -1
        self._populate_table()
        self._update_detail(-1)
        self._progress_bar.setRange(0, max(len(tracks), 1))
        self._progress_bar.setValue(0)
        self._progress_label.setText(f"0/{len(tracks)} przetworzonych")
        self._btn_apply_all.setEnabled(False)

    # ---- wypelnianie tabeli -------------------------------------------

    def _populate_table(self) -> None:
        self._table.setRowCount(0)
        for idx, track in enumerate(self._tracks):
            row = self._table.rowCount()
            self._table.insertRow(row)
            self._table.setItem(row, 0, QtWidgets.QTableWidgetItem(track.title or ""))
            self._table.setItem(row, 1, QtWidgets.QTableWidgetItem(track.artist or ""))
            self._table.setItem(row, 2, QtWidgets.QTableWidgetItem(str(track.bpm or "")))
            self._table.setItem(row, 3, QtWidgets.QTableWidgetItem(track.key or ""))
            self._table.setItem(row, 4, QtWidgets.QTableWidgetItem(track.mood or ""))
            self._table.setItem(row, 5, QtWidgets.QTableWidgetItem(track.genre or ""))
            self._table.setItem(row, 6, QtWidgets.QTableWidgetItem(_STATUS_WAITING))
            # Zapamietaj oryginalne dane
            self._original_data[idx] = {
                "bpm": track.bpm,
                "key": track.key,
                "mood": track.mood,
                "genre": track.genre,
                "energy": track.energy,
            }

    # ---- analiza ------------------------------------------------------

    def _start_analysis(self) -> None:
        if not self._tracks:
            return

        provider = self._provider_combo.currentText()
        settings = load_settings()

        if provider == "lokalny":
            tagger: Any = LocalAiTagger()
            self._provider_info.setText("Analiza lokalna (heurystyka)")
        else:
            key = _provider_api_key(provider, settings)
            base_url, model = _provider_settings(provider, settings)
            if not key:
                QtWidgets.QMessageBox.warning(
                    self,
                    "Brak klucza API",
                    f"Ustaw klucz API dla dostawcy \u201e{provider}\u201d w Ustawieniach.",
                )
                return
            tagger = CloudAiTagger(provider, key, base_url=base_url, model=model)
            self._provider_info.setText(f"Dostawca: {provider}")

        # Ustaw statusy na Oczekuje
        for row in range(self._table.rowCount()):
            self._table.item(row, 6).setText(_STATUS_WAITING)

        self._results.clear()
        self._progress_bar.setRange(0, len(self._tracks))
        self._progress_bar.setValue(0)
        self._progress_label.setText(f"0/{len(self._tracks)} przetworzonych")

        self._btn_start.setEnabled(False)
        self._btn_stop.setEnabled(True)
        self._btn_apply_all.setEnabled(False)

        self._worker = _TaggerWorker(self._tracks, tagger)
        self._worker.signals.progress.connect(self._on_progress)
        self._worker.signals.track_done.connect(self._on_track_done)
        self._worker.signals.error.connect(self._on_track_error)
        self._worker.signals.finished.connect(self._on_finished)

        # Oznacz pierwszy jako Przetwarzanie
        if self._table.rowCount() > 0:
            self._table.item(0, 6).setText(_STATUS_PROCESSING)

        QtCore.QThreadPool.globalInstance().start(self._worker)

    def _stop_analysis(self) -> None:
        if self._worker:
            self._worker.stop()
        self._btn_stop.setEnabled(False)
        self._btn_start.setEnabled(True)

    def _on_progress(self, current: int, total: int) -> None:
        self._progress_bar.setValue(current)
        self._progress_label.setText(f"{current}/{total} przetworzonych")
        # Oznacz nastepny jako Przetwarzanie
        if current < total and current < self._table.rowCount():
            self._table.item(current, 6).setText(_STATUS_PROCESSING)

    def _on_track_done(self, row: int, result: AnalysisResult) -> None:
        self._results[row] = result
        if row < self._table.rowCount():
            self._table.item(row, 6).setText(_STATUS_SUCCESS)
            # Aktualizuj kolumny tabeli wartosciami AI
            self._table.item(row, 2).setText(str(result.bpm or ""))
            self._table.item(row, 3).setText(result.key or "")
            self._table.item(row, 4).setText(result.mood or "")
            self._table.item(row, 5).setText(result.genre or "")
        # Odswiez panel szcz. jesli ten wiersz jest zaznaczony
        if row == self._selected_row:
            self._update_detail(row)

    def _on_track_error(self, row: int, msg: str) -> None:
        if row < self._table.rowCount():
            self._table.item(row, 6).setText(_STATUS_ERROR)

    def _on_finished(self) -> None:
        self._btn_start.setEnabled(True)
        self._btn_stop.setEnabled(False)
        self._btn_apply_all.setEnabled(bool(self._results))
        self._worker = None

    # ---- szczegoly zaznaczonego wiersza --------------------------------

    def _on_row_changed(self, row: int, _col: int, _prev_row: int, _prev_col: int) -> None:
        self._selected_row = row
        self._update_detail(row)
        has_result = row >= 0 and row in self._results
        self._btn_apply.setEnabled(has_result)
        self._btn_reject.setEnabled(has_result)

    def _update_detail(self, row: int) -> None:
        if row < 0 or row >= len(self._tracks):
            self._detail_title.setText("\u2014")
            for lbl_orig, lbl_ai in self._compare_fields.values():
                lbl_orig.setText("\u2014")
                lbl_ai.setText("\u2014")
            return

        track = self._tracks[row]
        self._detail_title.setText(
            f"{track.title or 'Bez tytu\u0142u'} \u2014 {track.artist or 'Nieznany artysta'}"
        )

        orig = self._original_data.get(row, {})
        result = self._results.get(row)

        for field_key, (lbl_orig, lbl_ai) in self._compare_fields.items():
            orig_val = orig.get(field_key)
            lbl_orig.setText(str(orig_val) if orig_val is not None else "\u2014")
            if result:
                ai_val = getattr(result, field_key, None)
                lbl_ai.setText(str(ai_val) if ai_val is not None else "\u2014")
            else:
                lbl_ai.setText("\u2014")

    # ---- zaznaczanie wierszy ------------------------------------------

    def _select_all_rows(self) -> None:
        self._table.selectAll()

    def _deselect_all_rows(self) -> None:
        self._table.clearSelection()

    # ---- akcje na tagach ----------------------------------------------

    def _apply_selected(self) -> None:
        row = self._selected_row
        if row < 0 or row not in self._results:
            return
        self._apply_result_to_track(row)
        self.tags_applied.emit()

    def _reject_selected(self) -> None:
        row = self._selected_row
        if row < 0 or row not in self._results:
            return
        # Przywroc oryginalne wartosci w tabeli
        orig = self._original_data.get(row, {})
        self._table.item(row, 2).setText(str(orig.get("bpm", "") or ""))
        self._table.item(row, 3).setText(str(orig.get("key", "") or ""))
        self._table.item(row, 4).setText(str(orig.get("mood", "") or ""))
        self._table.item(row, 5).setText(str(orig.get("genre", "") or ""))
        del self._results[row]
        self._update_detail(row)
        self._btn_apply.setEnabled(False)
        self._btn_reject.setEnabled(False)

    def _apply_all(self) -> None:
        settings = load_settings()
        applied: list[Track] = []
        for row, result in list(self._results.items()):
            if _below_confidence(result, settings.validation_policy):
                continue
            self._apply_result_to_track(row, settings=settings, batch=True)
            applied.append(self._tracks[row])
        if applied:
            update_tracks(applied)
            self.tags_applied.emit()
        self._btn_apply_all.setEnabled(False)

    def _apply_result_to_track(
        self,
        row: int,
        *,
        settings: Any | None = None,
        batch: bool = False,
    ) -> None:
        if settings is None:
            settings = load_settings()
        result = self._results.get(row)
        if not result:
            return
        result = _sanitize_ai_result(result, settings.validation_policy)
        track = self._tracks[row]

        provider = self._provider_combo.currentText()
        source = f"ai:{provider}"

        track.bpm = result.bpm or track.bpm
        track.key = result.key or track.key
        track.mood = result.mood or track.mood
        track.energy = result.energy or track.energy
        track.genre = result.genre or track.genre

        replace_track_tags(
            track.path,
            _build_ai_tags(result),
            source=source,
            confidence=result.confidence,
        )

        if not batch:
            update_tracks([track])
