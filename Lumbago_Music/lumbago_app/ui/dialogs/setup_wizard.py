"""Lumbago Music AI — Kreator pierwszego uruchomienia."""

import logging
from PyQt6.QtWidgets import (
    QWizard, QWizardPage, QVBoxLayout, QLabel,
    QLineEdit, QFormLayout, QCheckBox,
)

logger = logging.getLogger(__name__)


class SetupWizard(QWizard):
    """
    Kreator pierwszego uruchomienia.
    Prowadzi przez konfigurację bazy, kluczy AI i katalogów muzycznych.
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Konfiguracja Lumbago Music AI")
        self.setWizardStyle(QWizard.WizardStyle.ModernStyle)
        self.addPage(WelcomePage())
        self.addPage(AIKeysPage())
        self.addPage(LibraryPage())
        self.addPage(FinishPage())


class WelcomePage(QWizardPage):
    def __init__(self) -> None:
        super().__init__()
        self.setTitle("Witaj w Lumbago Music AI")
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(
            "Ten kreator pomoże skonfigurować:\n\n"
            "1. Klucze API dla AI tagowania\n"
            "2. Katalogi biblioteki muzycznej\n"
            "3. Preferencje UI\n\n"
            "Możesz przejść do konfiguracji w dowolnym momencie z menu Ustawienia."
        ))


class AIKeysPage(QWizardPage):
    def __init__(self) -> None:
        super().__init__()
        self.setTitle("Klucze API dla AI")
        self.setSubTitle("Dodaj co najmniej jeden klucz API aby używać AI taggera.")
        form = QFormLayout(self)
        self._openai = QLineEdit()
        self._openai.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("OpenAI API Key:", self._openai)
        self._gemini = QLineEdit()
        self._gemini.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("Gemini API Key (darmowy):", self._gemini)


class LibraryPage(QWizardPage):
    def __init__(self) -> None:
        super().__init__()
        self.setTitle("Katalogi biblioteki muzycznej")
        form = QFormLayout(self)
        self._dir = QLineEdit()
        self._dir.setPlaceholderText("C:\\Muzyka")
        form.addRow("Główny katalog:", self._dir)
        self._auto_import = QCheckBox("Automatycznie importuj nowe pliki (watchdog)")
        self._auto_import.setChecked(True)
        form.addRow("", self._auto_import)


class FinishPage(QWizardPage):
    def __init__(self) -> None:
        super().__init__()
        self.setTitle("Konfiguracja zakończona")
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(
            "Lumbago Music AI jest gotowy do użycia!\n\n"
            "Kliknij 'Zakończ' aby uruchomić aplikację."
        ))
