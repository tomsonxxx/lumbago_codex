from __future__ import annotations

import sys
import traceback
from pathlib import Path
import os

sys.coinit_flags = 2

from dotenv import load_dotenv
from PyQt6 import QtCore, QtWidgets

from lumbago_app.ui.main_window import MainWindow
from lumbago_app.ui.theme import CYBER_QSS
from lumbago_app.core.config import app_data_dir


def main() -> int:
    load_dotenv()
    _install_exception_hooks()
    QtCore.QCoreApplication.setAttribute(QtCore.Qt.ApplicationAttribute.AA_UseSoftwareOpenGL)
    app = QtWidgets.QApplication(sys.argv)
    app.setStyleSheet(CYBER_QSS)
    app.aboutToQuit.connect(lambda: _write_log("app.log", "aboutToQuit"))
    try:
        if os.getenv("LUMBAGO_SAFE_MODE", "0") == "1":
            window = QtWidgets.QMainWindow()
            window.setWindowTitle("Lumbago Music AI (Safe Mode)")
            window.resize(1000, 700)
            window.show()
        else:
            window = MainWindow()
            window.show()
        smoke_seconds = _read_int_env("LUMBAGO_SMOKE_SECONDS", 0)
        if smoke_seconds > 0:
            QtCore.QTimer.singleShot(smoke_seconds * 1000, app.quit)
        QtCore.QTimer.singleShot(2000, lambda: _write_log("app.log", "alive 2s"))
        result = app.exec()
        _write_log("app.log", f"app.exec ended: {result}")
        return result
    except Exception:
        _log_crash()
        QtWidgets.QMessageBox.critical(
            None,
            "Błąd uruchomienia",
            "Wystąpił błąd podczas uruchamiania aplikacji. "
            "Szczegóły zapisano w pliku crash.log.",
        )
        return 1


def _log_crash() -> None:
    try:
        target = app_data_dir() / "crash.log"
    except Exception:
        target = Path.cwd() / ".lumbago_data" / "crash.log"
        target.parent.mkdir(parents=True, exist_ok=True)
    try:
        target.write_text(traceback.format_exc(), encoding="utf-8")
    except Exception:
        pass


def _install_exception_hooks() -> None:
    def _handle_exception(exc_type, exc_value, exc_traceback):
        try:
            text = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
            _write_log("crash.log", text)
        finally:
            sys.__excepthook__(exc_type, exc_value, exc_traceback)

    def _qt_message_handler(mode, context, message):
        _write_log("qt.log", f"{mode}: {message}")

    sys.excepthook = _handle_exception
    try:
        QtCore.qInstallMessageHandler(_qt_message_handler)
    except Exception:
        pass


def _write_log(filename: str, content: str) -> None:
    try:
        target = app_data_dir() / filename
    except Exception:
        target = Path.cwd() / ".lumbago_data" / filename
        target.parent.mkdir(parents=True, exist_ok=True)
    try:
        target.write_text(content, encoding="utf-8")
    except Exception:
        pass


def _read_int_env(name: str, default: int) -> int:
    value = os.getenv(name, "")
    try:
        parsed = int(value)
        return parsed if parsed >= 0 else default
    except ValueError:
        return default


if __name__ == "__main__":
    raise SystemExit(main())
