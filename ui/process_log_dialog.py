from __future__ import annotations

from pathlib import Path

from PyQt6 import QtCore, QtGui, QtWidgets

from ui.widgets import apply_dialog_fade, dialog_icon_pixmap


class ProcessLogDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Log procesów aplikacji")
        self.resize(980, 620)
        apply_dialog_fade(self)

        self._last_size = -1
        self._last_mtime_ns = -1
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
        hint = QtWidgets.QLabel("Autotagowanie, rozpoznawanie i status przetwarzania")
        hint.setObjectName("DialogHint")
        title_row.addWidget(title_icon)
        title_row.addWidget(title)
        title_row.addWidget(hint)
        title_row.addStretch(1)
        card_layout.addLayout(title_row)

        self._view = QtWidgets.QPlainTextEdit()
        self._view.setReadOnly(True)
        self._view.setLineWrapMode(QtWidgets.QPlainTextEdit.LineWrapMode.NoWrap)
        self._view.setFont(QtGui.QFont("Consolas", 10))
        self._view.setPlaceholderText("Brak wpisów w logu procesów.")
        self._view.verticalScrollBar().valueChanged.connect(self._on_scroll_changed)
        card_layout.addWidget(self._view, 1)

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

    def _log_path(self) -> Path:
        return Path.cwd() / ".lumbago_data" / "process.log"

    def _on_scroll_changed(self, value: int) -> None:
        sb = self._view.verticalScrollBar()
        self._user_scrolled_up = value < (sb.maximum() - 8)

    def _is_near_bottom(self) -> bool:
        sb = self._view.verticalScrollBar()
        return sb.maximum() <= 0 or sb.value() >= (sb.maximum() - 8)

    def _refresh_now(self, *, force_full: bool = False) -> None:
        path = self._log_path()
        if not path.exists():
            if self._view.toPlainText():
                self._view.clear()
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

        old_text = self._view.toPlainText()
        if text == old_text:
            return

        sb = self._view.verticalScrollBar()
        preserve_scroll = self._user_scrolled_up and not self._auto_scroll.isChecked()
        scroll_pos = sb.value()

        if not force_full and old_text and text.startswith(old_text):
            delta = text[len(old_text) :]
            if delta:
                cursor = self._view.textCursor()
                cursor.movePosition(QtGui.QTextCursor.MoveOperation.End)
                cursor.insertText(delta)
                self._view.setTextCursor(cursor)
        else:
            self._view.setPlainText(text)
            if preserve_scroll:
                sb.setValue(min(scroll_pos, sb.maximum()))
            elif self._auto_scroll.isChecked() and not self._user_scrolled_up:
                sb.setValue(sb.maximum())

        if self._auto_scroll.isChecked() and (not preserve_scroll) and (not self._user_scrolled_up or self._is_near_bottom()):
            sb.setValue(sb.maximum())
            self._user_scrolled_up = False

    def _clear_log(self) -> None:
        path = self._log_path()
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("", encoding="utf-8")
        except Exception:
            return
        self._last_size = 0
        self._last_mtime_ns = 0
        self._user_scrolled_up = False
        self._refresh_now(force_full=True)