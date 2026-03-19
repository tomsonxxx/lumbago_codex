"""
Lumbago Music AI — GUI Launcher
=================================
Okno startowe z checkboxami trybów diagnostycznych.
Uruchamia main.py z odpowiednimi flagami środowiskowymi.
"""

import sys
import os
import subprocess
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def _try_pyqt6() -> bool:
    try:
        import PyQt6  # noqa: F401
        return True
    except ImportError:
        return False


if _try_pyqt6():
    from PyQt6.QtWidgets import (
        QApplication, QDialog, QVBoxLayout, QHBoxLayout,
        QCheckBox, QPushButton, QLabel, QGroupBox, QFrame,
        QSpacerItem, QSizePolicy,
    )
    from PyQt6.QtCore import Qt, QProcess
    from PyQt6.QtGui import QFont, QColor, QPalette
else:
    # Fallback: uruchom bez GUI
    def main() -> int:
        """Uruchamia main.py bezpośrednio bez launchera."""
        script = Path(__file__).parent / "main.py"
        result = subprocess.run([sys.executable, str(script)] + sys.argv[1:])
        return result.returncode

    if __name__ == "__main__":
        sys.exit(main())
    raise SystemExit(0)


_STYLESHEET = """
QDialog {
    background-color: #0d0d0f;
    color: #e0e0e0;
}
QLabel#title {
    color: #00f5ff;
    font-size: 20px;
    font-weight: bold;
    letter-spacing: 2px;
}
QLabel#subtitle {
    color: #888888;
    font-size: 11px;
}
QGroupBox {
    border: 1px solid #1e3a3a;
    border-radius: 6px;
    margin-top: 10px;
    padding-top: 8px;
    color: #00f5ff;
    font-weight: bold;
    font-size: 11px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 4px;
}
QCheckBox {
    color: #c0c0c0;
    spacing: 8px;
    font-size: 12px;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid #00f5ff44;
    border-radius: 3px;
    background: #0a0a0c;
}
QCheckBox::indicator:checked {
    background: #00f5ff;
    border: 1px solid #00f5ff;
}
QCheckBox::indicator:hover {
    border: 1px solid #00f5ff;
}
QPushButton#launch {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #004f4f, stop:1 #007070);
    color: #00f5ff;
    border: 1px solid #00f5ff55;
    border-radius: 6px;
    padding: 10px 30px;
    font-size: 13px;
    font-weight: bold;
    letter-spacing: 1px;
}
QPushButton#launch:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #006060, stop:1 #008080);
    border: 1px solid #00f5ff99;
}
QPushButton#launch:pressed {
    background: #003030;
}
QPushButton#cancel {
    background: transparent;
    color: #666666;
    border: 1px solid #333333;
    border-radius: 6px;
    padding: 10px 20px;
    font-size: 12px;
}
QPushButton#cancel:hover {
    color: #999999;
    border: 1px solid #555555;
}
QFrame#separator {
    background: #1e1e2e;
}
"""


class LauncherDialog(QDialog):
    """Okno launchera z opcjami diagnostycznymi."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Lumbago Music AI — Launcher")
        self.setFixedSize(420, 380)
        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.WindowCloseButtonHint
        )
        self.setStyleSheet(_STYLESHEET)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(24, 20, 24, 20)

        # --- Nagłówek ---
        title = QLabel("LUMBAGO MUSIC AI")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel("DJ Library Manager v1.0.0")
        subtitle.setObjectName("subtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)

        # --- Separator ---
        sep = QFrame()
        sep.setObjectName("separator")
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFixedHeight(1)
        layout.addWidget(sep)

        # --- Opcje diagnostyczne ---
        group = QGroupBox("Tryby uruchomienia")
        group_layout = QVBoxLayout(group)
        group_layout.setSpacing(8)

        self.cb_safe = QCheckBox(
            "Safe Mode — wyłącz wtyczki i zewnętrzne serwisy"
        )
        self.cb_multimedia = QCheckBox(
            "Disable Multimedia — bez odtwarzania audio (stabilność)"
        )
        self.cb_verbose = QCheckBox(
            "Verbose Logging — szczegółowe logi (DEBUG)"
        )
        self.cb_reset_db = QCheckBox(
            "Reset Database — wyczyść i zainicjuj bazę od nowa"
        )

        # Zaznacz verbose jeśli env ustawiony
        if os.environ.get("LUMBAGO_VERBOSE") == "1":
            self.cb_verbose.setChecked(True)

        # Reset DB — pomarańczowe ostrzeżenie
        self.cb_reset_db.setStyleSheet(
            "QCheckBox { color: #ff8c00; }"
            "QCheckBox::indicator:checked { background: #ff8c00; border: 1px solid #ff8c00; }"
        )

        group_layout.addWidget(self.cb_safe)
        group_layout.addWidget(self.cb_multimedia)
        group_layout.addWidget(self.cb_verbose)
        group_layout.addWidget(self.cb_reset_db)
        layout.addWidget(group)

        layout.addSpacerItem(
            QSpacerItem(0, 8, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        )

        # --- Przyciski ---
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        btn_cancel = QPushButton("Anuluj")
        btn_cancel.setObjectName("cancel")
        btn_cancel.clicked.connect(self.reject)

        btn_launch = QPushButton("▶  URUCHOM")
        btn_launch.setObjectName("launch")
        btn_launch.setDefault(True)
        btn_launch.clicked.connect(self._launch)

        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_launch, stretch=1)
        layout.addLayout(btn_layout)

    def _launch(self) -> None:
        """Zbiera opcje i uruchamia main.py z odpowiednimi flagami."""
        env = os.environ.copy()

        if self.cb_safe.isChecked():
            env["LUMBAGO_SAFE_MODE"] = "1"
        if self.cb_multimedia.isChecked():
            env["LUMBAGO_DISABLE_MULTIMEDIA"] = "1"
        if self.cb_verbose.isChecked():
            env["LUMBAGO_VERBOSE"] = "1"
        if self.cb_reset_db.isChecked():
            env["LUMBAGO_RESET_DB"] = "1"

        script = Path(__file__).parent / "main.py"
        try:
            subprocess.Popen(
                [sys.executable, str(script)],
                env=env,
                cwd=str(Path(__file__).parent),
            )
            self.accept()
        except Exception as exc:
            logger.error("Nie można uruchomić aplikacji: %s", exc)
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(
                self,
                "Błąd uruchomienia",
                f"Nie można uruchomić main.py:\n{exc}",
            )


def main() -> int:
    """Punkt wejścia launchera."""
    app = QApplication(sys.argv)
    app.setApplicationName("Lumbago Music AI")
    app.setApplicationVersion("1.0.0")

    # Ciemna paleta bazowa
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor("#0d0d0f"))
    palette.setColor(QPalette.ColorRole.WindowText, QColor("#e0e0e0"))
    palette.setColor(QPalette.ColorRole.Base, QColor("#0a0a0c"))
    app.setPalette(palette)

    dialog = LauncherDialog()
    result = dialog.exec()
    return 0 if result == QDialog.DialogCode.Accepted else 1


if __name__ == "__main__":
    sys.exit(main())
