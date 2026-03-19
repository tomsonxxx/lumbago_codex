"""
Lumbago Music AI — Punkt wejścia UI
=====================================
Inicjalizuje QApplication, ładuje motyw i uruchamia MainWindow.
"""

import logging
import os
import sys
from typing import Sequence

logger = logging.getLogger(__name__)


def run_app(argv: Sequence[str]) -> int:
    """
    Uruchamia aplikację PyQt6.

    Args:
        argv: Argumenty wiersza poleceń (sys.argv).

    Returns:
        Kod wyjścia.
    """
    # Import PyQt6 — tutaj aby błąd był czytelny
    try:
        from PyQt6.QtWidgets import QApplication, QMessageBox
        from PyQt6.QtCore import Qt, QCoreApplication
        from PyQt6.QtGui import QFont, QIcon, QPalette, QColor
    except ImportError as exc:
        print(f"BŁĄD: PyQt6 nie jest zainstalowane: {exc}", file=sys.stderr)
        return 1

    # Atrybuty przed stworzeniem QApplication
    QCoreApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)

    app = QApplication(list(argv))
    app.setApplicationName("Lumbago Music AI")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("LumbagoMusic")

    # Załaduj motyw
    _apply_theme(app)

    # Czcionka domyślna
    font = QFont("Segoe UI Variable", 10)
    font.setHintingPreference(QFont.HintingPreference.PreferFullHinting)
    app.setFont(font)

    # Tryb Safe Mode — nie ładuj okna głównego
    if os.environ.get("LUMBAGO_SAFE_MODE") == "1":
        logger.warning("SAFE MODE — uruchamianie w trybie diagnostycznym")
        _run_safe_mode_dialog(app)
        return 0

    # Główne okno
    try:
        from lumbago_app.ui.main_window import MainWindow
        window = MainWindow()
        window.show()
        logger.info("Główne okno wyświetlone")
        return app.exec()
    except Exception as exc:
        logger.critical("Nie można otworzyć okna głównego: %s", exc, exc_info=True)
        QMessageBox.critical(
            None,
            "Błąd krytyczny",
            f"Nie można uruchomić Lumbago Music:\n{exc}\n\n"
            "Sprawdź plik lumbago.log w katalogu logs/",
        )
        return 1


def _apply_theme(app: object) -> None:
    """Ładuje i aplikuje wybrany motyw QSS."""
    try:
        from lumbago_app.core.config import get_settings
        from lumbago_app.ui.themes import THEMES

        settings = get_settings()
        theme_name = settings.DEFAULT_THEME
        qss = THEMES.get(theme_name, THEMES.get("cyber_neon", ""))

        if qss:
            app.setStyleSheet(qss)  # type: ignore[union-attr]
            logger.debug("Motyw '%s' załadowany", theme_name)
        else:
            logger.warning("Nieznany motyw: %s", theme_name)
    except Exception as exc:
        logger.warning("Błąd ładowania motywu: %s", exc)


def _run_safe_mode_dialog(app: object) -> None:
    """Wyświetla prosty dialog w trybie Safe Mode."""
    from PyQt6.QtWidgets import QMessageBox
    msg = QMessageBox()
    msg.setWindowTitle("Lumbago Music AI — Safe Mode")
    msg.setText("Aplikacja uruchomiona w trybie Safe Mode.\n\nBaza danych i konfiguracja dostępne.")
    msg.setIcon(QMessageBox.Icon.Warning)
    msg.exec()


def main() -> None:
    """Punkt wejścia skryptu (project.scripts)."""
    from lumbago_app.core.logging_setup import configure_logging
    configure_logging()
    sys.exit(run_app(sys.argv))


if __name__ == "__main__":
    main()
