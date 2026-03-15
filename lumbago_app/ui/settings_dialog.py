from __future__ import annotations

from PyQt6 import QtWidgets

from lumbago_app.core.config import load_settings, save_settings
from lumbago_app.ui.widgets import apply_dialog_fade


class SettingsDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ustawienia / Klucze API")
        self.setMinimumWidth(520)
        apply_dialog_fade(self)
        self._build_ui()
        self._load()

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        card = QtWidgets.QFrame()
        card.setObjectName("DialogCard")
        card_layout = QtWidgets.QVBoxLayout(card)
        card_layout.setContentsMargins(16, 14, 16, 16)
        card_layout.setSpacing(10)
        layout.addWidget(card)
        layout = card_layout

        title = QtWidgets.QLabel(self.windowTitle())
        title.setObjectName("DialogTitle")
        layout.addWidget(title)
        form = QtWidgets.QFormLayout()

        self.acoustid_key = QtWidgets.QLineEdit()
        self.musicbrainz_app = QtWidgets.QLineEdit()
        self.discogs_token = QtWidgets.QLineEdit()
        self.cloud_provider = QtWidgets.QComboBox()
        self.cloud_provider.addItems(["", "openai", "gemini", "grok", "deepseek"])
        self.cloud_api_key = QtWidgets.QLineEdit()
        self.grok_api_key = QtWidgets.QLineEdit()
        self.deepseek_api_key = QtWidgets.QLineEdit()
        self.openai_api_key = QtWidgets.QLineEdit()
        self.openai_base_url = QtWidgets.QLineEdit()
        self.openai_model = QtWidgets.QLineEdit()
        self.grok_base_url = QtWidgets.QLineEdit()
        self.grok_model = QtWidgets.QLineEdit()
        self.deepseek_base_url = QtWidgets.QLineEdit()
        self.deepseek_model = QtWidgets.QLineEdit()
        self.filename_patterns = QtWidgets.QTextEdit()
        self.filename_patterns.setPlaceholderText(
            "PrzykĹ‚ad: (?P<artist>.+) - (?P<title>.+)"
        )
        self.validation_policy = QtWidgets.QComboBox()
        self.validation_policy.addItems(["strict", "balanced", "lenient"])
        self.metadata_cache_ttl = QtWidgets.QSpinBox()
        self.metadata_cache_ttl.setRange(0, 365)
        self.metadata_cache_ttl.setSuffix(" dni")

        for field in [
            self.acoustid_key,
            self.discogs_token,
            self.cloud_api_key,
            self.grok_api_key,
            self.deepseek_api_key,
            self.openai_api_key,
        ]:
            field.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)

        form.addRow("Klucz API AcoustID", self.acoustid_key)
        form.addRow("Nazwa aplikacji MusicBrainz", self.musicbrainz_app)
        form.addRow("Token Discogs", self.discogs_token)
        form.addRow("Dostawca AI (chmura)", self.cloud_provider)
        form.addRow("Klucz AI (chmura)", self.cloud_api_key)
        form.addRow("Klucz Grok API", self.grok_api_key)
        form.addRow("Adres bazowy Grok (URL)", self.grok_base_url)
        form.addRow("Model Grok", self.grok_model)
        form.addRow("Klucz DeepSeek API", self.deepseek_api_key)
        form.addRow("Adres bazowy DeepSeek (URL)", self.deepseek_base_url)
        form.addRow("Model DeepSeek", self.deepseek_model)
        form.addRow("Klucz OpenAI API", self.openai_api_key)
        form.addRow("Adres bazowy OpenAI (URL)", self.openai_base_url)
        form.addRow("Model OpenAI", self.openai_model)
        form.addRow("Wzorce nazw plikĂłw (regex, 1 na liniÄ™)", self.filename_patterns)
        form.addRow("Walidacja metadanych", self.validation_policy)
        form.addRow("Cache metadanych (TTL)", self.metadata_cache_ttl)

        layout.addLayout(form)

        btn_row = QtWidgets.QHBoxLayout()
        btn_row.addStretch(1)
        save_btn = QtWidgets.QPushButton("Zapisz")
        save_btn.clicked.connect(self._save)
        cancel_btn = QtWidgets.QPushButton("Anuluj")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(save_btn)
        btn_row.addWidget(cancel_btn)
        layout.addLayout(btn_row)

    def _load(self):
        settings = load_settings()
        self.acoustid_key.setText(settings.acoustid_api_key or "")
        self.musicbrainz_app.setText(settings.musicbrainz_app_name or "")
        self.discogs_token.setText(settings.discogs_token or "")
        self.cloud_provider.setCurrentText(settings.cloud_ai_provider or "")
        self.cloud_api_key.setText(settings.cloud_ai_api_key or "")
        self.grok_api_key.setText(settings.grok_api_key or "")
        self.grok_base_url.setText(settings.grok_base_url or "")
        self.grok_model.setText(settings.grok_model or "")
        self.deepseek_api_key.setText(settings.deepseek_api_key or "")
        self.deepseek_base_url.setText(settings.deepseek_base_url or "")
        self.deepseek_model.setText(settings.deepseek_model or "")
        self.openai_api_key.setText(settings.openai_api_key or "")
        self.openai_base_url.setText(settings.openai_base_url or "")
        self.openai_model.setText(settings.openai_model or "")
        self.filename_patterns.setPlainText("\n".join(settings.filename_patterns or []))
        self.validation_policy.setCurrentText(settings.validation_policy or "balanced")
        self.metadata_cache_ttl.setValue(settings.metadata_cache_ttl_days)

    def _save(self):
        save_settings(
            {
                "ACOUSTID_API_KEY": self.acoustid_key.text().strip(),
                "MUSICBRAINZ_APP_NAME": self.musicbrainz_app.text().strip(),
                "DISCOGS_TOKEN": self.discogs_token.text().strip(),
                "CLOUD_AI_PROVIDER": self.cloud_provider.currentText().strip(),
                "CLOUD_AI_API_KEY": self.cloud_api_key.text().strip(),
                "GROK_API_KEY": self.grok_api_key.text().strip(),
                "GROK_BASE_URL": self.grok_base_url.text().strip(),
                "GROK_MODEL": self.grok_model.text().strip(),
                "DEEPSEEK_API_KEY": self.deepseek_api_key.text().strip(),
                "DEEPSEEK_BASE_URL": self.deepseek_base_url.text().strip(),
                "DEEPSEEK_MODEL": self.deepseek_model.text().strip(),
                "OPENAI_API_KEY": self.openai_api_key.text().strip(),
                "OPENAI_BASE_URL": self.openai_base_url.text().strip(),
                "OPENAI_MODEL": self.openai_model.text().strip(),
                "FILENAME_PATTERNS": self.filename_patterns.toPlainText().strip(),
                "VALIDATION_POLICY": self.validation_policy.currentText().strip(),
                "METADATA_CACHE_TTL_DAYS": str(self.metadata_cache_ttl.value()),
            }
        )
        self.accept()

