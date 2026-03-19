from __future__ import annotations

import requests
from PyQt6 import QtWidgets, QtGui

from lumbago_app.core.config import load_settings, save_settings
from lumbago_app.ui.widgets import apply_dialog_fade, dialog_icon_pixmap


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

        title_row = QtWidgets.QHBoxLayout()
        title_icon = QtWidgets.QLabel()
        title_icon.setPixmap(dialog_icon_pixmap(18))
        title_icon.setFixedSize(20, 20)
        title = QtWidgets.QLabel(self.windowTitle())
        title.setObjectName("DialogTitle")
        title_row.addWidget(title_icon)
        title_row.addWidget(title)
        title_row.addStretch(1)
        layout.addLayout(title_row)

        form = QtWidgets.QFormLayout()

        self.acoustid_key = QtWidgets.QLineEdit()
        self.musicbrainz_app = QtWidgets.QLineEdit()
        self.discogs_token = QtWidgets.QLineEdit()
        self.cloud_provider = QtWidgets.QComboBox()
        self.cloud_provider.addItems(["", "openai", "gemini", "grok", "deepseek"])
        self.cloud_api_key = QtWidgets.QLineEdit()
        self.gemini_api_key = QtWidgets.QLineEdit()
        self.gemini_base_url = QtWidgets.QLineEdit()
        self.gemini_model = QtWidgets.QLineEdit()
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
            "Przykład: (?P<artist>.+) - (?P<title>.+)"
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
            self.gemini_api_key,
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
        form.addRow("Klucz Gemini API", self.gemini_api_key)
        form.addRow("Adres bazowy Gemini (URL)", self.gemini_base_url)
        form.addRow("Model Gemini", self.gemini_model)
        form.addRow("Klucz Grok API", self.grok_api_key)
        form.addRow("Adres bazowy Grok (URL)", self.grok_base_url)
        form.addRow("Model Grok", self.grok_model)
        form.addRow("Klucz DeepSeek API", self.deepseek_api_key)
        form.addRow("Adres bazowy DeepSeek (URL)", self.deepseek_base_url)
        form.addRow("Model DeepSeek", self.deepseek_model)
        form.addRow("Klucz OpenAI API", self.openai_api_key)
        form.addRow("Adres bazowy OpenAI (URL)", self.openai_base_url)
        form.addRow("Model OpenAI", self.openai_model)
        form.addRow("Wzorce nazw plików (regex, 1 na linię)", self.filename_patterns)
        form.addRow("Walidacja metadanych", self.validation_policy)
        form.addRow("Cache metadanych (TTL)", self.metadata_cache_ttl)

        layout.addLayout(form)

        test_row = QtWidgets.QGridLayout()
        self.test_acoustid_btn = QtWidgets.QPushButton("Test AcoustID")
        self.test_acoustid_btn.clicked.connect(self._test_acoustid)
        self.test_musicbrainz_btn = QtWidgets.QPushButton("Test MusicBrainz")
        self.test_musicbrainz_btn.clicked.connect(self._test_musicbrainz)
        self.test_discogs_btn = QtWidgets.QPushButton("Test Discogs")
        self.test_discogs_btn.clicked.connect(self._test_discogs)
        self.test_cloud_btn = QtWidgets.QPushButton("Test Cloud (provider)")
        self.test_cloud_btn.clicked.connect(self._test_cloud_provider)
        self.test_gemini_btn = QtWidgets.QPushButton("Test Gemini")
        self.test_gemini_btn.clicked.connect(self._test_gemini)
        self.test_openai_btn = QtWidgets.QPushButton("Test OpenAI")
        self.test_openai_btn.clicked.connect(self._test_openai)
        self.test_grok_btn = QtWidgets.QPushButton("Test Grok")
        self.test_grok_btn.clicked.connect(self._test_grok)
        self.test_deepseek_btn = QtWidgets.QPushButton("Test DeepSeek")
        self.test_deepseek_btn.clicked.connect(self._test_deepseek)
        test_row.addWidget(self.test_acoustid_btn, 0, 0)
        test_row.addWidget(self.test_musicbrainz_btn, 0, 1)
        test_row.addWidget(self.test_discogs_btn, 0, 2)
        test_row.addWidget(self.test_cloud_btn, 0, 3)
        test_row.addWidget(self.test_gemini_btn, 1, 0)
        test_row.addWidget(self.test_openai_btn, 1, 1)
        test_row.addWidget(self.test_grok_btn, 1, 2)
        test_row.addWidget(self.test_deepseek_btn, 1, 3)
        layout.addLayout(test_row)

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
        self.gemini_api_key.setText(settings.gemini_api_key or "")
        self.gemini_base_url.setText(settings.gemini_base_url or "")
        self.gemini_model.setText(settings.gemini_model or "")
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
                "GEMINI_API_KEY": self.gemini_api_key.text().strip(),
                "GEMINI_BASE_URL": self.gemini_base_url.text().strip(),
                "GEMINI_MODEL": self.gemini_model.text().strip(),
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

    def _show_test_result(self, title: str, ok: bool, detail: str = "") -> None:
        text = "Połączenie OK." if ok else "Test nieudany."
        if detail:
            text = f"{text}\n{detail}"
        if ok:
            QtWidgets.QMessageBox.information(self, title, text)
        else:
            QtWidgets.QMessageBox.warning(self, title, text)

    def _test_acoustid(self) -> None:
        api_key = self.acoustid_key.text().strip()
        if not api_key:
            self._show_test_result("AcoustID", False, "Brak klucza API.")
            return
        url = "https://api.acoustid.org/v2/lookup"
        params = {
            "client": api_key,
            "meta": "recordings",
            "duration": "1",
            "fingerprint": "test",
        }
        try:
            response = requests.get(url, params=params, timeout=12)
            data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
            status = data.get("status")
            if response.status_code == 200 and status in {"ok", "error"}:
                self._show_test_result("AcoustID", True, f"HTTP {response.status_code}, status: {status}")
                return
            self._show_test_result("AcoustID", False, f"HTTP {response.status_code}")
        except Exception as exc:
            self._show_test_result("AcoustID", False, str(exc))

    def _test_musicbrainz(self) -> None:
        app_name = self.musicbrainz_app.text().strip() or "LumbagoMusicAI"
        url = "https://musicbrainz.org/ws/2/recording"
        headers = {"User-Agent": f"{app_name}/1.0"}
        params = {"query": "recording:test", "fmt": "json", "limit": "1"}
        try:
            response = requests.get(url, headers=headers, params=params, timeout=12)
            if response.status_code == 200:
                self._show_test_result("MusicBrainz", True, "Zapytanie działa poprawnie.")
                return
            self._show_test_result("MusicBrainz", False, f"HTTP {response.status_code}")
        except Exception as exc:
            self._show_test_result("MusicBrainz", False, str(exc))

    def _test_discogs(self) -> None:
        token = self.discogs_token.text().strip()
        if not token:
            self._show_test_result("Discogs", False, "Brak tokenu.")
            return
        url = "https://api.discogs.com/database/search"
        headers = {
            "Authorization": f"Discogs token={token}",
            "User-Agent": "LumbagoMusicAI/1.0",
        }
        params = {"q": "test", "type": "release", "per_page": "1"}
        self._test_http_get("Discogs", url, headers=headers, params=params)

    def _test_cloud_provider(self) -> None:
        provider = self.cloud_provider.currentText().strip()
        if provider == "gemini":
            self._test_gemini()
            return
        if provider == "openai":
            self._test_openai()
            return
        if provider == "grok":
            self._test_grok()
            return
        if provider == "deepseek":
            self._test_deepseek()
            return
        self._show_test_result("Cloud AI", False, "Wybierz dostawcę chmurowego.")

    def _test_gemini(self) -> None:
        api_key = self.gemini_api_key.text().strip() or self.cloud_api_key.text().strip()
        base_url = self.gemini_base_url.text().strip() or "https://generativelanguage.googleapis.com/v1beta"
        if not api_key:
            self._show_test_result("Gemini", False, "Brak klucza API.")
            return
        url = f"{base_url.rstrip('/')}/models"
        headers = {"x-goog-api-key": api_key}
        self._test_http_get("Gemini", url, headers=headers)

    def _test_openai(self) -> None:
        api_key = self.openai_api_key.text().strip() or self.cloud_api_key.text().strip()
        base_url = self.openai_base_url.text().strip() or "https://api.openai.com/v1"
        if not api_key:
            self._show_test_result("OpenAI", False, "Brak klucza API.")
            return
        self._test_openai_like_api("OpenAI", base_url, api_key)

    def _test_grok(self) -> None:
        api_key = self.grok_api_key.text().strip() or self.cloud_api_key.text().strip()
        base_url = self.grok_base_url.text().strip() or "https://api.x.ai/v1"
        if not api_key:
            self._show_test_result("Grok", False, "Brak klucza API.")
            return
        self._test_openai_like_api("Grok", base_url, api_key)

    def _test_deepseek(self) -> None:
        api_key = self.deepseek_api_key.text().strip() or self.cloud_api_key.text().strip()
        base_url = self.deepseek_base_url.text().strip() or "https://api.deepseek.com/v1"
        if not api_key:
            self._show_test_result("DeepSeek", False, "Brak klucza API.")
            return
        self._test_openai_like_api("DeepSeek", base_url, api_key)

    def _test_openai_like_api(self, title: str, base_url: str, api_key: str) -> None:
        url = f"{base_url.rstrip('/')}/models"
        headers = {"Authorization": f"Bearer {api_key}"}
        self._test_http_get(title, url, headers=headers)

    def _test_http_get(
        self,
        title: str,
        url: str,
        headers: dict[str, str] | None = None,
        params: dict[str, str] | None = None,
    ) -> None:
        try:
            response = requests.get(url, headers=headers or {}, params=params or {}, timeout=12)
            if response.status_code == 200:
                self._show_test_result(title, True, "Połączenie i autoryzacja działają.")
                return
            detail = f"HTTP {response.status_code}"
            try:
                payload = response.json()
                error = payload.get("error")
                if isinstance(error, dict):
                    message = str(error.get("message", "")).strip()
                    detail = f"{detail}: {message}" if message else detail
                elif isinstance(error, str):
                    detail = f"{detail}: {error}"
            except Exception:
                pass
            self._show_test_result(title, False, detail)
        except Exception as exc:
            self._show_test_result(title, False, str(exc))



