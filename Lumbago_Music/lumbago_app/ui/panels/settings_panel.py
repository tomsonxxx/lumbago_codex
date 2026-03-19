"""Lumbago Music AI — Panel ustawień."""

import logging
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTabWidget, QFormLayout,
    QLineEdit, QCheckBox, QComboBox, QLabel,
)

logger = logging.getLogger(__name__)


class SettingsPanel(QWidget):
    """Panel ustawień z zakładkami (AI, Import, UI, Integracje)."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        tabs = QTabWidget()

        tabs.addTab(self._build_ai_tab(), "✦ AI / LLM")
        tabs.addTab(self._build_import_tab(), "⬆ Import")
        tabs.addTab(self._build_ui_tab(), "🎨 Wygląd")
        tabs.addTab(self._build_integrations_tab(), "🔌 Integracje")

        layout.addWidget(tabs)

    def _build_ai_tab(self) -> QWidget:
        w = QWidget()
        form = QFormLayout(w)
        form.setSpacing(10)

        note = QLabel(
            "Klucze API przechowywane w pliku .env\n"
            "Dodaj klucz dla co najmniej jednego providera."
        )
        note.setStyleSheet("color: #808090; font-size: 11px;")
        form.addRow(note)

        self._openai_key = QLineEdit()
        self._openai_key.setEchoMode(QLineEdit.EchoMode.Password)
        self._openai_key.setPlaceholderText("sk-...")
        form.addRow("OpenAI API Key:", self._openai_key)

        self._anthropic_key = QLineEdit()
        self._anthropic_key.setEchoMode(QLineEdit.EchoMode.Password)
        self._anthropic_key.setPlaceholderText("sk-ant-...")
        form.addRow("Anthropic API Key:", self._anthropic_key)

        self._gemini_key = QLineEdit()
        self._gemini_key.setEchoMode(QLineEdit.EchoMode.Password)
        self._gemini_key.setPlaceholderText("AIza...")
        form.addRow("Gemini API Key:", self._gemini_key)

        return w

    def _build_import_tab(self) -> QWidget:
        w = QWidget()
        form = QFormLayout(w)
        form.setSpacing(10)

        self._watch_dirs = QLineEdit()
        self._watch_dirs.setPlaceholderText("C:\\Muzyka;D:\\DJ Sets")
        form.addRow("Monitorowane katalogi:", self._watch_dirs)

        self._import_recursive = QCheckBox("Skanuj rekurencyjnie")
        self._import_recursive.setChecked(True)
        form.addRow("", self._import_recursive)

        return w

    def _build_ui_tab(self) -> QWidget:
        w = QWidget()
        form = QFormLayout(w)
        form.setSpacing(10)

        self._theme_combo = QComboBox()
        self._theme_combo.addItems(["cyber_neon", "fluent_dark"])
        form.addRow("Motyw:", self._theme_combo)

        return w

    def _build_integrations_tab(self) -> QWidget:
        w = QWidget()
        form = QFormLayout(w)
        form.setSpacing(10)

        self._acoustid_key = QLineEdit()
        form.addRow("AcoustID API Key:", self._acoustid_key)

        self._discogs_token = QLineEdit()
        self._discogs_token.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("Discogs Token:", self._discogs_token)

        self._lastfm_key = QLineEdit()
        form.addRow("Last.fm API Key:", self._lastfm_key)

        return w
