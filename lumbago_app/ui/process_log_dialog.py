from __future__ import annotations

from pathlib import Path

from PyQt6 import QtCore, QtGui, QtWidgets

from lumbago_app.ui.widgets import apply_dialog_fade, dialog_icon_pixmap


class ProcessLogDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Log procesow aplikacji")
        self.resize(980, 620)
        apply_dialog_fade(self)

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
        title = QtWidgets.QLabel("Log procesow")
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
        self._view.setFont(QtGui.QFont("Consolas", 10))
        self._view.setPlaceholderText("Brak wpisow logu procesow.")
        card_layout.addWidget(self._view, 1)

        button_row = QtWidgets.QHBoxLayout()
        self._auto_scroll = QtWidgets.QCheckBox("Auto-scroll")
        self._auto_scroll.setChecked(True)
        refresh_btn = QtWidgets.QPushButton("Odswiez")
        refresh_btn.clicked.connect(self._refresh_now)
        clear_btn = QtWidgets.QPushButton("Wyczysc log")
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
        self._timer.start(900)
        self._refresh_now()

    def _log_path(self) -> Path:
        return Path.cwd() / ".lumbago_data" / "process.log"

    def _refresh_now(self) -> None:
        path = self._log_path()
        if not path.exists():
            self._view.setPlainText("")
            return
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return
        self._view.setPlainText(text)
        if self._auto_scroll.isChecked():
            sb = self._view.verticalScrollBar()
            sb.setValue(sb.maximum())

    def _clear_log(self) -> None:
        path = self._log_path()
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("", encoding="utf-8")
        except Exception:
            return
        self._refresh_now()
