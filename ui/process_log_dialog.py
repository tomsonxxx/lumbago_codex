from __future__ import annotations

from pathlib import Path

from PyQt6 import QtCore, QtGui, QtWidgets

from core.process_log_pl import build_colored_log_html, format_log_line_html, legend_entries
from ui.widgets import apply_dialog_fade, dialog_icon_pixmap


class _SourceLegendWidget(QtWidgets.QFrame):
    """Niewielka legenda kolorów źródeł w rogu okna logu."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ProcessLogLegend")
        self.setStyleSheet(
            """
            QFrame#ProcessLogLegend {
                background: rgba(15, 23, 42, 0.88);
                border: 1px solid #334155;
                border-radius: 8px;
            }
            QLabel#LegendTitle {
                color: #94a3b8;
                font-size: 10px;
                font-weight: 600;
            }
            QLabel#LegendItem {
                color: #e2e8f0;
                font-size: 10px;
            }
            """
        )
        grid = QtWidgets.QGridLayout(self)
        grid.setContentsMargins(8, 6, 8, 6)
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(3)

        title = QtWidgets.QLabel("Legenda źródeł")
        title.setObjectName("LegendTitle")
        grid.addWidget(title, 0, 0, 1, 2)

        row = 1
        col = 0
        for _key, label, color in legend_entries():
            swatch = QtWidgets.QLabel()
            swatch.setFixedSize(10, 10)
            swatch.setStyleSheet(
                f"background:{color}; border-radius:2px; border:1px solid #475569;"
            )
            item = QtWidgets.QLabel(label)
            item.setObjectName("LegendItem")
            cell = QtWidgets.QHBoxLayout()
            cell.setSpacing(4)
            cell.setContentsMargins(0, 0, 0, 0)
            wrap = QtWidgets.QWidget()
            wrap.setLayout(cell)
            cell.addWidget(swatch)
            cell.addWidget(item)
            cell.addStretch(1)
            grid.addWidget(wrap, row, col)
            col += 1
            if col > 1:
                col = 0
                row += 1


class _ColoredLogView(QtWidgets.QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setLineWrapMode(QtWidgets.QTextEdit.LineWrapMode.NoWrap)
        self.setFont(QtGui.QFont("Consolas", 10))
        self.setPlaceholderText("Brak wpisów w logu procesów.")
        self.setStyleSheet("QTextEdit { background: #0b1220; color: #cbd5e1; }")


class ProcessLogDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Log procesów aplikacji")
        self.resize(980, 620)
        apply_dialog_fade(self)

        self._last_size = -1
        self._last_mtime_ns = -1
        self._last_raw_text = ""
        self._user_scrolled_up = False

        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(8)

        card = QtWidgets.QFrame()
        card.setObjectName("DialogCard")
        card_layout = QtWidgets.QVBoxLayout(card)
        card_layout.setContentsMargins(12, 12, 12, 12)
        card_layout.setSpacing(8)
        root.addWidget(card, 1)

        title_row = QtWidgets.QHBoxLayout()
        title_icon = QtWidgets.QLabel()
        title_icon.setPixmap(dialog_icon_pixmap(18))
        title = QtWidgets.QLabel("Log procesów")
        title.setObjectName("DialogTitle")
        hint = QtWidgets.QLabel("Kolory odpowiadają źródłom metadanych i procesom")
        hint.setObjectName("DialogHint")
        title_row.addWidget(title_icon)
        title_row.addWidget(title)
        title_row.addWidget(hint)
        title_row.addStretch(1)
        card_layout.addLayout(title_row)

        log_host = QtWidgets.QWidget()
        log_host_layout = QtWidgets.QVBoxLayout(log_host)
        log_host_layout.setContentsMargins(0, 0, 0, 0)
        self._view = _ColoredLogView(log_host)
        log_host_layout.addWidget(self._view)

        self._legend = _SourceLegendWidget(log_host)
        self._legend.setParent(self._view.viewport())
        self._legend.raise_()
        self._legend.adjustSize()
        self._reposition_legend()
        self._view.verticalScrollBar().valueChanged.connect(self._on_scroll_changed)
        self._view.installEventFilter(self)
        card_layout.addWidget(log_host, 1)

        button_row = QtWidgets.QHBoxLayout()
        self._auto_scroll = QtWidgets.QCheckBox("Auto-scroll (tylko gdy jesteś na końcu)")
        self._auto_scroll.setChecked(False)
        refresh_btn = QtWidgets.QPushButton("Odśwież")
        refresh_btn.clicked.connect(self._refresh_now)
        clear_btn = QtWidgets.QPushButton("Wyczyść log")
        clear_btn.clicked.connect(self._clear_log)
        close_btn = QtWidgets.QPushButton("Zamknij")
        close_btn.clicked.connect(self.accept)
        button_row.addWidget(self._auto_scroll)
        button_row.addStretch(1)
        button_row.addWidget(refresh_btn)
        button_row.addWidget(clear_btn)
        button_row.addWidget(close_btn)
        card_layout.addLayout(button_row)

        self._timer = QtCore.QTimer(self)
        self._timer.timeout.connect(self._refresh_now)
        self._timer.start(1200)
        self._refresh_now()

    def eventFilter(self, watched, event) -> bool:
        if watched is self._view and event.type() == QtCore.QEvent.Type.Resize:
            self._reposition_legend()
        return super().eventFilter(watched, event)

    def _reposition_legend(self) -> None:
        if not self._legend or not self._view:
            return
        margin = 8
        legend_size = self._legend.sizeHint()
        x = max(margin, self._view.viewport().width() - legend_size.width() - margin)
        y = margin
        self._legend.setGeometry(x, y, legend_size.width(), legend_size.height())

    def _log_path(self) -> Path:
        return Path.cwd() / ".lumbago_data" / "process.log"

    def _on_scroll_changed(self, value: int) -> None:
        sb = self._view.verticalScrollBar()
        self._user_scrolled_up = value < (sb.maximum() - 8)

    def _is_near_bottom(self) -> bool:
        sb = self._view.verticalScrollBar()
        return sb.maximum() <= 0 or sb.value() >= (sb.maximum() - 8)

    def _set_log_html(self, text: str, *, preserve_scroll: bool, scroll_pos: int) -> None:
        sb = self._view.verticalScrollBar()
        self._view.setHtml(build_colored_log_html(text))
        if preserve_scroll:
            sb.setValue(min(scroll_pos, sb.maximum()))
        elif self._auto_scroll.isChecked() and not self._user_scrolled_up:
            sb.setValue(sb.maximum())

    def _append_log_html(self, delta: str) -> None:
        if not delta:
            return
        cursor = self._view.textCursor()
        cursor.movePosition(QtGui.QTextCursor.MoveOperation.End)
        if self._view.toPlainText():
            cursor.insertHtml("<br>")
        html_chunk = "<br>".join(format_log_line_html(line) for line in delta.splitlines())
        cursor.insertHtml(html_chunk)
        self._view.setTextCursor(cursor)

    def _refresh_now(self, *, force_full: bool = False) -> None:
        path = self._log_path()
        if not path.exists():
            if self._last_raw_text:
                self._view.clear()
                self._last_raw_text = ""
            self._last_size = 0
            self._last_mtime_ns = 0
            return
        try:
            stat = path.stat()
        except Exception:
            return
        if (
            not force_full
            and stat.st_size == self._last_size
            and stat.st_mtime_ns == self._last_mtime_ns
        ):
            return

        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return

        self._last_size = stat.st_size
        self._last_mtime_ns = stat.st_mtime_ns

        if text == self._last_raw_text:
            return

        sb = self._view.verticalScrollBar()
        preserve_scroll = self._user_scrolled_up and not self._auto_scroll.isChecked()
        scroll_pos = sb.value()

        if not force_full and self._last_raw_text and text.startswith(self._last_raw_text):
            delta = text[len(self._last_raw_text) :]
            if delta:
                self._append_log_html(delta)
        else:
            self._set_log_html(text, preserve_scroll=preserve_scroll, scroll_pos=scroll_pos)

        self._last_raw_text = text

        if self._auto_scroll.isChecked() and (not preserve_scroll) and (
            not self._user_scrolled_up or self._is_near_bottom()
        ):
            sb.setValue(sb.maximum())
            self._user_scrolled_up = False

        self._reposition_legend()

    def _clear_log(self) -> None:
        path = self._log_path()
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("", encoding="utf-8")
        except Exception:
            return
        self._last_size = 0
        self._last_mtime_ns = 0
        self._last_raw_text = ""
        self._user_scrolled_up = False
        self._refresh_now(force_full=True)