"""
InterTager Dialog — pełna analiza, wyszukiwanie i tagowanie jednym kliknięciem.
Port mechanizmu z inteligentny-tagger-id3 (aiService.ts) na PyQt6.
"""
from __future__ import annotations

from pathlib import Path

from PyQt6 import QtCore, QtGui, QtWidgets

from lumbago_app.core.config import cache_dir, load_settings
from lumbago_app.core.models import Track
from lumbago_app.data.repository import update_track
from lumbago_app.services.inter_tager import (
    analyze_track,
    apply_merged_to_track,
    smart_merge,
)
from lumbago_app.ui.widgets import apply_dialog_fade, dialog_icon_pixmap


# Kolumny tabeli wyników
_COLS = [
    ("", 24),           # 0: checkbox
    ("Plik", 180),      # 1: filename
    ("Tytuł AI", 160),  # 2
    ("Artysta AI", 140),# 3
    ("Album AI", 140),  # 4
    ("Rok", 50),        # 5
    ("Gatunek", 90),    # 6
    ("BPM", 55),        # 7
    ("Tonacja", 65),    # 8
    ("Nastrój", 90),    # 9
    ("Status", 90),     # 10
]

_STATE_COLORS = {
    "pending":    "#64748b",
    "processing": "#f59e0b",
    "ok":         "#4ade80",
    "error":      "#f87171",
}


class InterTagerDialog(QtWidgets.QDialog):
    tags_applied = QtCore.pyqtSignal()

    def __init__(self, tracks: list[Track], parent=None):
        super().__init__(parent)
        self.setWindowTitle("InterTager — pełne tagowanie AI")
        self.setMinimumSize(960, 560)
        apply_dialog_fade(self)
        self._tracks = tracks
        self._results: dict[str, dict] = {}   # path → merged dict
        self._worker: _InterTagerWorker | None = None
        self._build_ui()
        self._update_provider_label()

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        outer = QtWidgets.QVBoxLayout(self)
        outer.setContentsMargins(16, 16, 16, 16)
        outer.setSpacing(12)

        card = QtWidgets.QFrame()
        card.setObjectName("DialogCard")
        layout = QtWidgets.QVBoxLayout(card)
        layout.setContentsMargins(16, 14, 16, 16)
        layout.setSpacing(10)
        outer.addWidget(card)

        # Nagłówek
        title_row = QtWidgets.QHBoxLayout()
        icon_lbl = QtWidgets.QLabel()
        icon_lbl.setPixmap(dialog_icon_pixmap(18))
        icon_lbl.setFixedSize(20, 20)
        title_lbl = QtWidgets.QLabel(self.windowTitle())
        title_lbl.setObjectName("DialogTitle")
        title_row.addWidget(icon_lbl)
        title_row.addWidget(title_lbl)
        title_row.addStretch(1)
        layout.addLayout(title_row)

        # Info o providerze
        self.provider_lbl = QtWidgets.QLabel("")
        self.provider_lbl.setObjectName("DialogHint")
        layout.addWidget(self.provider_lbl)

        # Opcje
        opts = QtWidgets.QHBoxLayout()
        self.batch_check = QtWidgets.QCheckBox("Tryb wsadowy (szybszy, do 10 plików na zapytanie)")
        self.batch_check.setChecked(True)
        self.batch_check.setToolTip(
            "Wysyła wiele plików w jednym zapytaniu do AI.\n"
            "Szybszy i tańszy, ale może być mniej dokładny dla każdego pliku osobno."
        )
        self.cover_check = QtWidgets.QCheckBox("Pobieraj i osadzaj okładki")
        self.cover_check.setChecked(True)
        self.cover_check.setToolTip("Pobiera okładkę albumu z URL zwróconego przez AI i osadza w pliku.")
        opts.addWidget(self.batch_check)
        opts.addSpacing(20)
        opts.addWidget(self.cover_check)
        opts.addStretch(1)
        layout.addLayout(opts)

        # Tabela
        self.table = QtWidgets.QTableWidget(0, len(_COLS))
        self.table.setHorizontalHeaderLabels([c[0] for c in _COLS])
        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Interactive)
        hdr.setStretchLastSection(True)
        for i, (_, w) in enumerate(_COLS):
            self.table.setColumnWidth(i, w)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table, 1)

        self._populate_table()

        # Pasek statusu
        self.status_lbl = QtWidgets.QLabel(f"Załadowano {len(self._tracks)} utworów. Kliknij 'Analizuj'.")
        self.status_lbl.setObjectName("DialogHint")
        layout.addWidget(self.status_lbl)

        # Przyciski dolne
        btn_row = QtWidgets.QHBoxLayout()
        self.analyze_btn = QtWidgets.QPushButton("Analizuj")
        self.analyze_btn.setToolTip("Uruchom analizę AI i pobierz tagi dla wszystkich utworów")
        self.analyze_btn.clicked.connect(self._start_analysis)

        self.select_all_btn = QtWidgets.QPushButton("Zaznacz wszystko")
        self.select_all_btn.clicked.connect(lambda: self._set_all_checks(True))
        self.deselect_btn = QtWidgets.QPushButton("Odznacz wszystko")
        self.deselect_btn.clicked.connect(lambda: self._set_all_checks(False))

        self.apply_btn = QtWidgets.QPushButton("Zastosuj zaznaczone")
        self.apply_btn.setToolTip("Zapisz tagi do plików audio i do bazy danych")
        self.apply_btn.setEnabled(False)
        self.apply_btn.clicked.connect(self._apply_selected)

        self.cancel_btn = QtWidgets.QPushButton("Anuluj")
        self.cancel_btn.clicked.connect(self._on_cancel)

        btn_row.addWidget(self.analyze_btn)
        btn_row.addWidget(self.select_all_btn)
        btn_row.addWidget(self.deselect_btn)
        btn_row.addStretch(1)
        btn_row.addWidget(self.apply_btn)
        btn_row.addWidget(self.cancel_btn)
        layout.addLayout(btn_row)

    def _populate_table(self):
        self.table.setRowCount(0)
        for track in self._tracks:
            row = self.table.rowCount()
            self.table.insertRow(row)

            # Checkbox
            chk = QtWidgets.QCheckBox()
            chk.setChecked(True)
            chk_widget = QtWidgets.QWidget()
            chk_lay = QtWidgets.QHBoxLayout(chk_widget)
            chk_lay.addWidget(chk)
            chk_lay.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            chk_lay.setContentsMargins(0, 0, 0, 0)
            self.table.setCellWidget(row, 0, chk_widget)

            filename = Path(track.path).name
            self.table.setItem(row, 1, QtWidgets.QTableWidgetItem(filename))
            self.table.setItem(row, 2, QtWidgets.QTableWidgetItem(""))
            self.table.setItem(row, 3, QtWidgets.QTableWidgetItem(""))
            self.table.setItem(row, 4, QtWidgets.QTableWidgetItem(""))
            self.table.setItem(row, 5, QtWidgets.QTableWidgetItem(""))
            self.table.setItem(row, 6, QtWidgets.QTableWidgetItem(""))
            self.table.setItem(row, 7, QtWidgets.QTableWidgetItem(""))
            self.table.setItem(row, 8, QtWidgets.QTableWidgetItem(""))
            self.table.setItem(row, 9, QtWidgets.QTableWidgetItem(""))
            status_item = QtWidgets.QTableWidgetItem("oczekuje")
            status_item.setForeground(QtGui.QColor(_STATE_COLORS["pending"]))
            self.table.setItem(row, 10, status_item)
            self.table.setRowData(row, track)  # type: ignore[attr-defined]

    # fallback — store track via UserRole on item 1
    def _set_track_row(self, row: int, track: Track):
        item = self.table.item(row, 1)
        if item:
            item.setData(QtCore.Qt.ItemDataRole.UserRole, track)

    def _get_track_row(self, row: int) -> Track | None:
        item = self.table.item(row, 1)
        if item:
            return item.data(QtCore.Qt.ItemDataRole.UserRole)
        return None

    def _update_provider_label(self):
        settings = load_settings()
        provider = settings.cloud_ai_provider or "local"
        self.provider_lbl.setText(
            f"Dostawca: {provider} | Pliki: {len(self._tracks)} | "
            "Pełna analiza: tytuł, artysta, album, rok, gatunek, BPM, tonacja, nastrój, okładka"
        )

    # ── Zaznaczanie ───────────────────────────────────────────────────────────

    def _set_all_checks(self, state: bool):
        for row in range(self.table.rowCount()):
            w = self.table.cellWidget(row, 0)
            if w:
                chk = w.findChild(QtWidgets.QCheckBox)
                if chk:
                    chk.setChecked(state)

    def _is_row_checked(self, row: int) -> bool:
        w = self.table.cellWidget(row, 0)
        if w:
            chk = w.findChild(QtWidgets.QCheckBox)
            if chk:
                return chk.isChecked()
        return False

    # ── Analiza ───────────────────────────────────────────────────────────────

    def _start_analysis(self):
        settings = load_settings()
        provider = settings.cloud_ai_provider or ""
        if not provider:
            QtWidgets.QMessageBox.warning(
                self, "Brak dostawcy",
                "Ustaw dostawcę Cloud AI w Ustawieniach (OpenAI / Gemini / Grok / DeepSeek)."
            )
            return
        api_key = _get_api_key(provider, settings)
        if not api_key:
            QtWidgets.QMessageBox.warning(
                self, "Brak klucza API",
                f"Ustaw klucz API dla {provider} w Ustawieniach."
            )
            return
        base_url, model = _get_provider_settings(provider, settings)

        self.analyze_btn.setEnabled(False)
        self.apply_btn.setEnabled(False)
        self._results.clear()

        # Reset statusów
        for row in range(self.table.rowCount()):
            self._set_row_status(row, "pending", "oczekuje")

        batch = self.batch_check.isChecked()
        self._worker = _InterTagerWorker(
            self._tracks, provider, api_key, base_url, model, batch_mode=batch
        )
        self._worker.signals.row_started.connect(self._on_row_started)
        self._worker.signals.row_done.connect(self._on_row_done)
        self._worker.signals.row_error.connect(self._on_row_error)
        self._worker.signals.finished.connect(self._on_finished)
        QtCore.QThreadPool.globalInstance().start(self._worker)

        self.status_lbl.setText("Analizuję...")

    def _on_row_started(self, row: int):
        self._set_row_status(row, "processing", "analizuję…")

    def _on_row_done(self, row: int, merged: dict):
        self._results[self._tracks[row].path] = merged
        # Uzupełnij kolumny wynikami
        self.table.item(row, 2).setText(str(merged.get("title") or ""))
        self.table.item(row, 3).setText(str(merged.get("artist") or ""))
        self.table.item(row, 4).setText(str(merged.get("album") or ""))
        self.table.item(row, 5).setText(str(merged.get("year") or ""))
        self.table.item(row, 6).setText(str(merged.get("genre") or ""))
        bpm = merged.get("bpm")
        self.table.item(row, 7).setText(f"{float(bpm):.0f}" if bpm else "")
        self.table.item(row, 8).setText(str(merged.get("key") or ""))
        self.table.item(row, 9).setText(str(merged.get("mood") or ""))
        self._set_row_status(row, "ok", "OK")

    def _on_row_error(self, row: int, error: str):
        self._set_row_status(row, "error", f"błąd")
        item = self.table.item(row, 10)
        if item:
            item.setToolTip(error)

    def _on_finished(self, total: int, errors: int):
        self.analyze_btn.setEnabled(True)
        ok = total - errors
        self.apply_btn.setEnabled(ok > 0)
        self.status_lbl.setText(
            f"Analiza zakończona: {ok}/{total} OK"
            + (f", {errors} błędów" if errors else "")
            + ". Sprawdź wyniki i kliknij 'Zastosuj zaznaczone'."
        )

    def _set_row_status(self, row: int, state: str, text: str):
        item = self.table.item(row, 10)
        if item:
            item.setText(text)
            item.setForeground(QtGui.QColor(_STATE_COLORS.get(state, "#fff")))

    # ── Zastosowanie ──────────────────────────────────────────────────────────

    def _apply_selected(self):
        cover_dir = cache_dir() / "covers"
        cover_dir.mkdir(parents=True, exist_ok=True)
        download_covers = self.cover_check.isChecked()

        applied = 0
        for row, track in enumerate(self._tracks):
            if not self._is_row_checked(row):
                continue
            merged = self._results.get(track.path)
            if not merged:
                continue
            try:
                apply_merged_to_track(
                    track,
                    merged,
                    cover_dir=cover_dir if download_covers else None,
                )
                update_track(track)
                self._set_row_status(row, "ok", "zapisano ✓")
                applied += 1
            except Exception as exc:
                self._set_row_status(row, "error", "zapis błąd")
                item = self.table.item(row, 10)
                if item:
                    item.setToolTip(str(exc))

        self.status_lbl.setText(f"Zastosowano tagi dla {applied} utworów.")
        self.tags_applied.emit()

        if applied > 0:
            QtWidgets.QMessageBox.information(
                self, "InterTager",
                f"Zapisano tagi dla {applied} utworów.\n"
                "Zmiany widoczne po odświeżeniu biblioteki."
            )
            self.accept()

    def _on_cancel(self):
        if self._worker:
            self._worker.stop()
        self.reject()


# ── Worker ────────────────────────────────────────────────────────────────────

class _Signals(QtCore.QObject):
    row_started = QtCore.pyqtSignal(int)
    row_done    = QtCore.pyqtSignal(int, dict)
    row_error   = QtCore.pyqtSignal(int, str)
    finished    = QtCore.pyqtSignal(int, int)   # total, errors


class _InterTagerWorker(QtCore.QRunnable):
    BATCH_SIZE = 8  # pliki na jedno zapytanie w trybie wsadowym

    def __init__(
        self,
        tracks: list[Track],
        provider: str,
        api_key: str,
        base_url: str | None,
        model: str | None,
        batch_mode: bool = True,
    ):
        super().__init__()
        self.tracks = tracks
        self.provider = provider
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.batch_mode = batch_mode
        self.signals = _Signals()
        self._stop = False

    def stop(self):
        self._stop = True

    def run(self):
        errors = 0
        total = len(self.tracks)

        if self.batch_mode:
            errors = self._run_batch()
        else:
            errors = self._run_single()

        self.signals.finished.emit(total, errors)

    def _run_single(self) -> int:
        errors = 0
        for idx, track in enumerate(self.tracks):
            if self._stop:
                break
            self.signals.row_started.emit(idx)
            try:
                raw = analyze_track(
                    track, self.provider, self.api_key, self.base_url, self.model
                )
                merged = smart_merge(track, raw)
                self.signals.row_done.emit(idx, merged)
            except Exception as exc:
                errors += 1
                self.signals.row_error.emit(idx, str(exc))
        return errors

    def _run_batch(self) -> int:
        from lumbago_app.services.inter_tager import analyze_batch

        errors = 0
        idx_map = {Path(t.path).name: i for i, t in enumerate(self.tracks)}

        # Podziel na chunki
        for chunk_start in range(0, len(self.tracks), self.BATCH_SIZE):
            if self._stop:
                break
            chunk = self.tracks[chunk_start:chunk_start + self.BATCH_SIZE]

            # Oznacz jako "przetwarzane"
            for i, t in enumerate(chunk):
                self.signals.row_started.emit(chunk_start + i)

            try:
                results = analyze_batch(
                    chunk, self.provider, self.api_key, self.base_url, self.model
                )
                # Mapuj wyniki z powrotem
                result_map = {r.get("_filename", ""): r for r in results}
                for i, track in enumerate(chunk):
                    fname = Path(track.path).name
                    merged = result_map.get(fname)
                    if merged:
                        self.signals.row_done.emit(chunk_start + i, merged)
                    else:
                        # Fallback: single dla tego tracka
                        try:
                            from lumbago_app.services.inter_tager import analyze_track, smart_merge
                            raw = analyze_track(
                                track, self.provider, self.api_key, self.base_url, self.model
                            )
                            merged2 = smart_merge(track, raw)
                            self.signals.row_done.emit(chunk_start + i, merged2)
                        except Exception as exc2:
                            errors += 1
                            self.signals.row_error.emit(chunk_start + i, str(exc2))
            except Exception as exc:
                # Batch failed — fallback to single for each
                for i, track in enumerate(chunk):
                    if self._stop:
                        break
                    try:
                        from lumbago_app.services.inter_tager import analyze_track, smart_merge
                        raw = analyze_track(
                            track, self.provider, self.api_key, self.base_url, self.model
                        )
                        merged = smart_merge(track, raw)
                        self.signals.row_done.emit(chunk_start + i, merged)
                    except Exception as exc2:
                        errors += 1
                        self.signals.row_error.emit(chunk_start + i, str(exc2))
        return errors


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_api_key(provider: str, settings) -> str | None:
    if provider == "openai":
        return settings.openai_api_key or settings.cloud_ai_api_key
    if provider == "grok":
        return settings.grok_api_key or settings.cloud_ai_api_key
    if provider == "deepseek":
        return settings.deepseek_api_key or settings.cloud_ai_api_key
    if provider == "gemini":
        return settings.cloud_ai_api_key
    return settings.cloud_ai_api_key


def _get_provider_settings(provider: str, settings) -> tuple[str | None, str | None]:
    if provider == "openai":
        return settings.openai_base_url or None, settings.openai_model or None
    if provider == "grok":
        return settings.grok_base_url or None, settings.grok_model or None
    if provider == "deepseek":
        return settings.deepseek_base_url or None, settings.deepseek_model or None
    return None, None
