from __future__ import annotations

from pathlib import Path
from typing import Any

from PyQt6 import QtCore, QtGui, QtWidgets

from lumbago_app.core.models import Track
from lumbago_app.ui.import_wizard import ScanWizardWorker, ImportWizardWorker, ImportOptions


class DropZone(QtWidgets.QFrame):
    """Strefa drag & drop z przerywaną ramką."""

    folder_dropped = QtCore.pyqtSignal(str)

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setMinimumHeight(180)
        self.setObjectName("Card")
        self._hovered = False
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)
        layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(12)

        self._icon_label = QtWidgets.QLabel("\U0001f4c2")
        self._icon_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self._icon_label.setStyleSheet("font-size: 42px; background: transparent; border: none;")
        layout.addWidget(self._icon_label)

        self._text_label = QtWidgets.QLabel("Przeciagnij folder tutaj")
        self._text_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self._text_label.setStyleSheet(
            "color: #94a3b8; font-size: 14px; font-weight: 600; background: transparent; border: none;"
        )
        layout.addWidget(self._text_label)

        self._hint_label = QtWidgets.QLabel("lub uzyj przycisku ponizej")
        self._hint_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self._hint_label.setStyleSheet(
            "color: #64748b; font-size: 11px; background: transparent; border: none;"
        )
        layout.addWidget(self._hint_label)

    def _update_border_style(self) -> None:
        color = "#00d4ff" if self._hovered else "rgba(0, 212, 255, 0.25)"
        width = "2px" if self._hovered else "2px"
        self.setStyleSheet(
            f"DropZone {{ background-color: #0d112a; border: {width} dashed {color}; border-radius: 16px; }}"
        )

    def showEvent(self, event: QtGui.QShowEvent) -> None:
        super().showEvent(event)
        self._update_border_style()

    def dragEnterEvent(self, event: QtGui.QDragEnterEvent) -> None:
        if event.mimeData() and event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.isLocalFile() and Path(url.toLocalFile()).is_dir():
                    event.acceptProposedAction()
                    self._hovered = True
                    self._update_border_style()
                    return
        event.ignore()

    def dragLeaveEvent(self, event: QtGui.QDragLeaveEvent) -> None:
        self._hovered = False
        self._update_border_style()
        super().dragLeaveEvent(event)

    def dropEvent(self, event: QtGui.QDropEvent) -> None:
        self._hovered = False
        self._update_border_style()
        if event.mimeData() and event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                path = url.toLocalFile()
                if Path(path).is_dir():
                    self.folder_dropped.emit(path)
                    event.acceptProposedAction()
                    return
        event.ignore()


class StepIndicator(QtWidgets.QWidget):
    """Wskaznik krokow - 3 kolka polaczone liniami."""

    _LABELS = ["Folder", "Opcje", "Import"]

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self._current = 0
        self.setFixedHeight(64)

    def set_step(self, step: int) -> None:
        self._current = step
        self.update()

    def paintEvent(self, event: QtGui.QPaintEvent) -> None:
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        n = len(self._LABELS)
        spacing = w / (n + 1)
        cy = h // 2 - 6
        radius = 14

        cyan = QtGui.QColor("#00d4ff")
        muted = QtGui.QColor("#1e2d45")
        text_active = QtGui.QColor("#e6f7ff")
        text_muted = QtGui.QColor("#64748b")
        bg = QtGui.QColor("#0a0d1a")

        # Linie laczace
        for i in range(n - 1):
            x1 = int(spacing * (i + 1)) + radius
            x2 = int(spacing * (i + 2)) - radius
            color = cyan if i < self._current else muted
            pen = QtGui.QPen(color, 2)
            painter.setPen(pen)
            painter.drawLine(x1, cy, x2, cy)

        # Kolka i etykiety
        for i in range(n):
            cx = int(spacing * (i + 1))
            active = i <= self._current
            fill = cyan if active else bg
            border = cyan if active else muted

            painter.setPen(QtGui.QPen(border, 2))
            painter.setBrush(QtGui.QBrush(fill))
            painter.drawEllipse(QtCore.QPoint(cx, cy), radius, radius)

            # Numer w kolku
            num_color = QtGui.QColor("#0a0d1a") if active else text_muted
            painter.setPen(num_color)
            font = painter.font()
            font.setWeight(QtGui.QFont.Weight.Bold)
            font.setPixelSize(12)
            painter.setFont(font)
            painter.drawText(
                QtCore.QRect(cx - radius, cy - radius, radius * 2, radius * 2),
                QtCore.Qt.AlignmentFlag.AlignCenter,
                str(i + 1),
            )

            # Etykieta pod kolkiem
            label_color = text_active if active else text_muted
            painter.setPen(label_color)
            font.setWeight(QtGui.QFont.Weight.Normal)
            font.setPixelSize(11)
            painter.setFont(font)
            painter.drawText(
                QtCore.QRect(cx - 50, cy + radius + 4, 100, 20),
                QtCore.Qt.AlignmentFlag.AlignCenter,
                self._LABELS[i],
            )

        painter.end()


class ImportPage(QtWidgets.QWidget):
    """Strona importu muzyki - inline widget do QStackedWidget."""

    import_finished = QtCore.pyqtSignal(list)  # list[Track]

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self._thread_pool = QtCore.QThreadPool.globalInstance()
        self._tracks: list[Track] = []
        self._errors: list[dict[str, Any]] = []
        self._scan_worker: ScanWizardWorker | None = None
        self._import_worker: ImportWizardWorker | None = None
        self._build_ui()

    # ── UI ───────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(24, 16, 24, 16)
        root.setSpacing(0)

        # Karta glowna
        card = QtWidgets.QFrame()
        card.setObjectName("Card")
        card_lay = QtWidgets.QVBoxLayout(card)
        card_lay.setContentsMargins(20, 16, 20, 20)
        card_lay.setSpacing(14)
        root.addWidget(card, 1)

        # Tytul
        title = QtWidgets.QLabel("Import muzyki")
        title.setObjectName("DialogTitle")
        card_lay.addWidget(title)

        # Wskaznik krokow
        self._step_indicator = StepIndicator()
        card_lay.addWidget(self._step_indicator)

        # Stack z krokami
        self._stack = QtWidgets.QStackedWidget()
        card_lay.addWidget(self._stack, 1)

        self._stack.addWidget(self._build_step_folder())
        self._stack.addWidget(self._build_step_options())
        self._stack.addWidget(self._build_step_progress())

        # Nawigacja
        nav = QtWidgets.QHBoxLayout()
        nav.setSpacing(8)
        nav.addStretch(1)

        self._btn_back = QtWidgets.QPushButton("Wstecz")
        self._btn_back.clicked.connect(self._go_back)
        nav.addWidget(self._btn_back)

        self._btn_next = QtWidgets.QPushButton("Dalej")
        self._btn_next.clicked.connect(self._go_next)
        nav.addWidget(self._btn_next)

        self._btn_import = QtWidgets.QPushButton("Importuj")
        self._btn_import.setObjectName("PrimaryAction")
        self._btn_import.clicked.connect(self._start_import)
        nav.addWidget(self._btn_import)

        card_lay.addLayout(nav)
        self._update_nav()

    # ── Krok 1: Folder ───────────────────────────────────────────────────

    def _build_step_folder(self) -> QtWidgets.QWidget:
        page = QtWidgets.QWidget()
        lay = QtWidgets.QVBoxLayout(page)
        lay.setContentsMargins(0, 8, 0, 0)
        lay.setSpacing(12)

        header = QtWidgets.QLabel("Wybierz folder z muzyka")
        header.setObjectName("SectionTitle")
        lay.addWidget(header)

        # Drop zone
        self._drop_zone = DropZone()
        self._drop_zone.folder_dropped.connect(self._on_folder_dropped)
        lay.addWidget(self._drop_zone, 1)

        # Sciezka + przegladaj
        row = QtWidgets.QHBoxLayout()
        row.setSpacing(8)
        self._folder_input = QtWidgets.QLineEdit()
        self._folder_input.setPlaceholderText("Sciezka do folderu z muzyka...")
        row.addWidget(self._folder_input, 1)

        browse_btn = QtWidgets.QPushButton("Przegladaj")
        browse_btn.clicked.connect(self._browse_folder)
        row.addWidget(browse_btn)
        lay.addLayout(row)

        return page

    # ── Krok 2: Opcje ────────────────────────────────────────────────────

    def _build_step_options(self) -> QtWidgets.QWidget:
        page = QtWidgets.QWidget()
        lay = QtWidgets.QVBoxLayout(page)
        lay.setContentsMargins(0, 8, 0, 0)
        lay.setSpacing(14)

        header = QtWidgets.QLabel("Opcje skanowania")
        header.setObjectName("SectionTitle")
        lay.addWidget(header)

        self._recursive_check = QtWidgets.QCheckBox("Skanowanie rekurencyjne (podfoldery)")
        self._recursive_check.setChecked(True)
        lay.addWidget(self._recursive_check)

        ext_label = QtWidgets.QLabel("Rozszerzenia plikow (oddzielone przecinkami)")
        ext_label.setStyleSheet("color: #94a3b8;")
        lay.addWidget(ext_label)

        self._ext_input = QtWidgets.QLineEdit()
        self._ext_input.setText(".mp3,.flac,.wav,.m4a,.ogg,.aac")
        self._ext_input.setPlaceholderText(".mp3,.flac,.wav,.m4a,.ogg,.aac")
        lay.addWidget(self._ext_input)

        self._bpm_check = QtWidgets.QCheckBox(
            "Wykryj BPM przez librosa dla plikow bez BPM (wolniejszy import)"
        )
        self._bpm_check.setToolTip(
            "Uzywa librosa.beat.beat_track() na pierwszych 60s kazdego pliku.\n"
            "Znacznie wydluza czas importu, ale uzupelnia BPM tam gdzie tagi go nie maja."
        )
        lay.addWidget(self._bpm_check)

        lay.addStretch(1)
        return page

    # ── Krok 3: Postep ───────────────────────────────────────────────────

    def _build_step_progress(self) -> QtWidgets.QWidget:
        page = QtWidgets.QWidget()
        lay = QtWidgets.QVBoxLayout(page)
        lay.setContentsMargins(0, 8, 0, 0)
        lay.setSpacing(14)

        header = QtWidgets.QLabel("Postep importu")
        header.setObjectName("SectionTitle")
        lay.addWidget(header)

        # Skanowanie
        scan_label = QtWidgets.QLabel("Skanowanie plikow:")
        scan_label.setStyleSheet("color: #94a3b8; font-size: 12px;")
        lay.addWidget(scan_label)

        self._scan_progress = QtWidgets.QProgressBar()
        self._scan_progress.setRange(0, 100)
        self._scan_progress.setTextVisible(True)
        self._scan_progress.setFormat("%v / %m plikow")
        lay.addWidget(self._scan_progress)

        self._scan_status = QtWidgets.QLabel("Oczekiwanie...")
        self._scan_status.setStyleSheet("color: #64748b; font-size: 11px;")
        lay.addWidget(self._scan_status)

        # Import
        import_label = QtWidgets.QLabel("Import do biblioteki:")
        import_label.setStyleSheet("color: #94a3b8; font-size: 12px;")
        lay.addWidget(import_label)

        self._import_progress = QtWidgets.QProgressBar()
        self._import_progress.setRange(0, 100)
        self._import_progress.setTextVisible(True)
        self._import_progress.setFormat("%v / %m utworow")
        lay.addWidget(self._import_progress)

        self._import_status = QtWidgets.QLabel("Oczekiwanie na skanowanie...")
        self._import_status.setStyleSheet("color: #64748b; font-size: 11px;")
        lay.addWidget(self._import_status)

        # Bledy
        self._error_label = QtWidgets.QLabel("")
        self._error_label.setStyleSheet("color: #ef4444; font-size: 11px;")
        self._error_label.hide()
        lay.addWidget(self._error_label)

        lay.addStretch(1)
        return page

    # ── Nawigacja ────────────────────────────────────────────────────────

    def _update_nav(self) -> None:
        idx = self._stack.currentIndex()
        self._step_indicator.set_step(idx)
        self._btn_back.setVisible(idx > 0)
        self._btn_next.setVisible(idx < 1)  # widoczny tylko na kroku 0
        self._btn_import.setVisible(idx == 1)  # widoczny na kroku 1 (opcje)
        if idx == 2:
            self._btn_back.setVisible(False)
            self._btn_next.setVisible(False)
            self._btn_import.setVisible(False)

    def _go_back(self) -> None:
        idx = self._stack.currentIndex()
        if idx > 0:
            self._stack.setCurrentIndex(idx - 1)
        self._update_nav()

    def _go_next(self) -> None:
        idx = self._stack.currentIndex()
        if idx == 0:
            folder = self._folder_input.text().strip()
            if not folder or not Path(folder).is_dir():
                QtWidgets.QMessageBox.warning(
                    self, "Import", "Wybierz prawidlowy folder z muzyka."
                )
                return
            self._stack.setCurrentIndex(1)
        self._update_nav()

    def _browse_folder(self) -> None:
        folder = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Wybierz folder z muzyka"
        )
        if folder:
            self._folder_input.setText(folder)

    def _on_folder_dropped(self, path: str) -> None:
        self._folder_input.setText(path)

    # ── Opcje ────────────────────────────────────────────────────────────

    def _build_options(self) -> ImportOptions | None:
        folder = self._folder_input.text().strip()
        if not folder:
            return None
        extensions = {
            e.strip().lower()
            for e in self._ext_input.text().split(",")
            if e.strip().startswith(".")
        }
        if not extensions:
            extensions = {".mp3", ".flac", ".wav", ".m4a", ".ogg", ".aac"}
        return ImportOptions(
            folder=Path(folder),
            recursive=self._recursive_check.isChecked(),
            extensions=extensions,
        )

    # ── Skanowanie ───────────────────────────────────────────────────────

    def _start_import(self) -> None:
        options = self._build_options()
        if not options:
            QtWidgets.QMessageBox.warning(
                self, "Import", "Najpierw wybierz folder."
            )
            return

        self._stack.setCurrentIndex(2)
        self._update_nav()

        self._tracks = []
        self._errors = []
        self._scan_progress.setValue(0)
        self._import_progress.setValue(0)
        self._scan_status.setText("Skanowanie w toku...")
        self._import_status.setText("Oczekiwanie na skanowanie...")
        self._error_label.hide()

        self._scan_worker = ScanWizardWorker(options)
        self._scan_worker.signals.progress.connect(self._on_scan_progress)
        self._scan_worker.signals.finished.connect(self._on_scan_finished)
        self._thread_pool.start(self._scan_worker)

    def _on_scan_progress(self, current: int, total: int) -> None:
        self._scan_progress.setMaximum(total or 1)
        self._scan_progress.setValue(current)
        self._scan_status.setText(f"Skanowanie: {current} / {total} plikow...")

    def _on_scan_finished(
        self, tracks: list[Track], errors: list[dict[str, Any]], canceled: bool
    ) -> None:
        self._tracks = tracks
        self._errors.extend(errors)
        self._scan_worker = None

        if canceled:
            self._scan_status.setText("Skanowanie anulowane.")
            self._scan_status.setStyleSheet("color: #ef4444; font-size: 11px;")
            return

        count = len(tracks)
        self._scan_status.setText(f"Znaleziono {count} utworow.")
        self._scan_status.setStyleSheet("color: #00d4ff; font-size: 11px;")
        self._scan_progress.setValue(self._scan_progress.maximum())

        if not tracks:
            self._import_status.setText("Brak plikow do zaimportowania.")
            return

        # Rozpocznij import
        self._import_status.setText("Import w toku...")
        self._import_progress.setRange(0, count)
        self._import_progress.setValue(0)

        detect_bpm = self._bpm_check.isChecked()
        self._import_worker = ImportWizardWorker(tracks, 200, detect_bpm=detect_bpm)
        self._import_worker.signals.progress.connect(self._on_import_progress)
        self._import_worker.signals.finished.connect(self._on_import_finished)
        self._thread_pool.start(self._import_worker)

    # ── Import ───────────────────────────────────────────────────────────

    def _on_import_progress(self, current: int, total: int) -> None:
        self._import_progress.setMaximum(total or 1)
        self._import_progress.setValue(current)
        self._import_status.setText(f"Importowanie: {current} / {total} utworow...")

    def _on_import_finished(
        self, errors: list[dict[str, Any]], canceled: bool
    ) -> None:
        self._errors.extend(errors)
        self._import_worker = None

        if canceled:
            self._import_status.setText("Import anulowany.")
            self._import_status.setStyleSheet("color: #ef4444; font-size: 11px;")
            return

        self._import_progress.setValue(self._import_progress.maximum())
        count = len(self._tracks)
        self._import_status.setText(f"Zaimportowano {count} utworow.")
        self._import_status.setStyleSheet("color: #00d4ff; font-size: 11px;")

        if self._errors:
            self._error_label.setText(f"Bledy: {len(self._errors)} plikow z problemami.")
            self._error_label.show()

        self.import_finished.emit(self._tracks)

    # ── Reset / cleanup ──────────────────────────────────────────────────

    def reset(self) -> None:
        """Resetuj strone do stanu poczatkowego."""
        if self._scan_worker:
            self._scan_worker.stop()
            self._scan_worker = None
        if self._import_worker:
            self._import_worker.stop()
            self._import_worker = None

        self._tracks = []
        self._errors = []
        self._folder_input.clear()
        self._scan_progress.setValue(0)
        self._import_progress.setValue(0)
        self._scan_status.setText("Oczekiwanie...")
        self._scan_status.setStyleSheet("color: #64748b; font-size: 11px;")
        self._import_status.setText("Oczekiwanie na skanowanie...")
        self._import_status.setStyleSheet("color: #64748b; font-size: 11px;")
        self._error_label.hide()
        self._stack.setCurrentIndex(0)
        self._update_nav()

    def stop_workers(self) -> None:
        """Zatrzymaj wszystkie workery w tle."""
        if self._scan_worker:
            self._scan_worker.stop()
        if self._import_worker:
            self._import_worker.stop()
