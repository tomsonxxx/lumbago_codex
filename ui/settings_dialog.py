from __future__ import annotations

import requests
from PyQt6 import QtWidgets, QtGui

from core.config import (
    default_musicbrainz_user_agent,
    load_settings,
    normalize_musicbrainz_user_agent,
    save_settings,
)
from ui.widgets import apply_dialog_fade, dialog_icon_pixmap


class SettingsDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ustawienia / Klucze API")
        self.setMinimumWidth(520)
        apply_dialog_fade(self)
        self._syncing_validation_controls = False
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

        self.musicbrainz_app = QtWidgets.QLineEdit()
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
        self.overwrite_existing_tags = QtWidgets.QCheckBox("Nadpisuj istniejące tagi")
        self.overwrite_existing_tags.setToolTip(
            "Włącza agresywne nadpisywanie lokalnych tagów lepszymi danymi z internetu."
        )
        self.validation_policy = QtWidgets.QComboBox()
        self.validation_policy.addItems(["strict", "balanced", "lenient", "aggressive"])
        self.metadata_cache_ttl = QtWidgets.QSpinBox()
        self.metadata_cache_ttl.setRange(0, 365)
        self.metadata_cache_ttl.setSuffix(" dni")
        self.autotag_parallel_workers = QtWidgets.QSpinBox()
        self.autotag_parallel_workers.setRange(1, 16)
        self.provider_parallel_workers = QtWidgets.QSpinBox()
        self.provider_parallel_workers.setRange(2, 12)

        for field in [
            self.cloud_api_key,
            self.gemini_api_key,
            self.grok_api_key,
            self.deepseek_api_key,
            self.openai_api_key,
        ]:
            field.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)

        form.addRow("Nazwa aplikacji MusicBrainz", self.musicbrainz_app)
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
        form.addRow("", self.overwrite_existing_tags)
        form.addRow("Walidacja metadanych", self.validation_policy)
        form.addRow("Cache metadanych (TTL)", self.metadata_cache_ttl)
        form.addRow("Równoległe pliki (autotag)", self.autotag_parallel_workers)
        form.addRow("Równoległe źródła (API)", self.provider_parallel_workers)

        layout.addLayout(form)

        self.overwrite_existing_tags.toggled.connect(self._on_overwrite_existing_tags_toggled)
        self.validation_policy.currentTextChanged.connect(self._on_validation_policy_changed)

        test_row = QtWidgets.QGridLayout()
        self.test_musicbrainz_btn = QtWidgets.QPushButton("Test MusicBrainz")
        self.test_musicbrainz_btn.clicked.connect(self._test_musicbrainz)
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
        test_row.addWidget(self.test_musicbrainz_btn, 0, 0)
        test_row.addWidget(self.test_cloud_btn, 0, 1)
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
        self.musicbrainz_app.setText(settings.musicbrainz_app_name or default_musicbrainz_user_agent())
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
        policy = settings.validation_policy or "aggressive"
        self._set_validation_policy(policy)
        self.metadata_cache_ttl.setValue(settings.metadata_cache_ttl_days)
        self.autotag_parallel_workers.setValue(settings.autotag_parallel_workers)
        self.provider_parallel_workers.setValue(settings.provider_parallel_workers)

    def _save(self):
        musicbrainz_user_agent = normalize_musicbrainz_user_agent(self.musicbrainz_app.text())
        save_settings(
            {
                "MUSICBRAINZ_APP_NAME": musicbrainz_user_agent,
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
                "VALIDATION_POLICY": self.validation_policy.currentText().strip() or "aggressive",
                "METADATA_CACHE_TTL_DAYS": str(self.metadata_cache_ttl.value()),
                "AUTOTAG_PARALLEL_WORKERS": str(self.autotag_parallel_workers.value()),
                "PROVIDER_PARALLEL_WORKERS": str(self.provider_parallel_workers.value()),
            }
        )
        self.accept()

    def _on_overwrite_existing_tags_toggled(self, checked: bool) -> None:
        if self._syncing_validation_controls:
            return
        desired_policy = "aggressive" if checked else "balanced"
        if checked and self.validation_policy.currentText() != desired_policy:
            self._set_validation_policy(desired_policy)
        elif not checked and self.validation_policy.currentText() == "aggressive":
            self._set_validation_policy(desired_policy)

    def _on_validation_policy_changed(self, policy: str) -> None:
        if self._syncing_validation_controls:
            return
        should_overwrite = policy == "aggressive"
        if self.overwrite_existing_tags.isChecked() != should_overwrite:
            self._syncing_validation_controls = True
            try:
                self.overwrite_existing_tags.setChecked(should_overwrite)
            finally:
                self._syncing_validation_controls = False

    def _set_validation_policy(self, policy: str) -> None:
        self._syncing_validation_controls = True
        try:
            self.validation_policy.setCurrentText(policy)
            self.overwrite_existing_tags.setChecked(policy == "aggressive")
        finally:
            self._syncing_validation_controls = False

    def _show_test_result(self, title: str, ok: bool, detail: str = "") -> None:
        text = "Połączenie OK." if ok else "Test nieudany."
        if detail:
            text = f"{text}\n{detail}"
        if ok:
            QtWidgets.QMessageBox.information(self, title, text)
        else:
            QtWidgets.QMessageBox.warning(self, title, text)

    def _test_musicbrainz(self) -> None:
        app_name = normalize_musicbrainz_user_agent(self.musicbrainz_app.text())
        url = "https://musicbrainz.org/ws/2/recording"
        headers = {"User-Agent": app_name}
        params = {"query": "recording:test", "fmt": "json", "limit": "1"}
        try:
            response = requests.get(url, headers=headers, params=params, timeout=12)
            if response.status_code == 200:
                self._show_test_result("MusicBrainz", True, "Zapytanie działa poprawnie.")
                return
            self._show_test_result("MusicBrainz", False, f"HTTP {response.status_code}")
        except Exception as exc:
            self._show_test_result("MusicBrainz", False, str(exc))

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


class ApiKeyCheckDialog(QtWidgets.QDialog):
    """Standalone dialog that validates all configured API keys at once."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Sprawdzanie kluczy API")
        self.setMinimumWidth(560)
        apply_dialog_fade(self)
        self._results: dict[str, QtWidgets.QLabel] = {}
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        card = QtWidgets.QFrame()
        card.setObjectName("DialogCard")
        card_layout = QtWidgets.QVBoxLayout(card)
        card_layout.setContentsMargins(16, 14, 16, 16)
        card_layout.setSpacing(8)
        layout.addWidget(card)

        title_row = QtWidgets.QHBoxLayout()
        title_icon = QtWidgets.QLabel()
        title_icon.setPixmap(dialog_icon_pixmap(18))
        title_icon.setFixedSize(20, 20)
        title = QtWidgets.QLabel("Sprawdzanie kluczy API")
        title.setObjectName("DialogTitle")
        title_row.addWidget(title_icon)
        title_row.addWidget(title)
        title_row.addStretch(1)
        card_layout.addLayout(title_row)

        desc = QtWidgets.QLabel("Kliknij <b>Testuj wszystko</b> aby zweryfikować poprawność wszystkich skonfigurowanych kluczy API.")
        desc.setWordWrap(True)
        card_layout.addWidget(desc)

        self._grid = QtWidgets.QGridLayout()
        self._grid.setSpacing(6)
        services = [
            ("MusicBrainz", "musicbrainz"),
            ("Gemini", "gemini"),
            ("OpenAI", "openai"),
            ("Grok", "grok"),
            ("DeepSeek", "deepseek"),
        ]
        for row, (label, key) in enumerate(services):
            name_lbl = QtWidgets.QLabel(f"<b>{label}</b>")
            status_lbl = QtWidgets.QLabel("—")
            status_lbl.setMinimumWidth(350)
            self._results[key] = status_lbl
            self._grid.addWidget(name_lbl, row, 0)
            self._grid.addWidget(status_lbl, row, 1)
        card_layout.addLayout(self._grid)

        btn_row = QtWidgets.QHBoxLayout()
        self._test_all_btn = QtWidgets.QPushButton("Testuj wszystko")
        self._test_all_btn.setObjectName("PrimaryBtn")
        self._test_all_btn.clicked.connect(self._run_all_tests)
        close_btn = QtWidgets.QPushButton("Zamknij")
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(self._test_all_btn)
        btn_row.addStretch(1)
        btn_row.addWidget(close_btn)
        card_layout.addLayout(btn_row)

    def _set_status(self, key: str, ok: bool, detail: str) -> None:
        label = self._results.get(key)
        if label is None:
            return
        if ok:
            label.setText(f'<span style="color:#00E676;">OK</span> — {detail}')
        else:
            label.setText(f'<span style="color:#FF5252;">BŁĄD</span> — {detail}')

    def _set_pending(self, key: str) -> None:
        label = self._results.get(key)
        if label is not None:
            label.setText('<span style="color:#FFD700;">Testowanie...</span>')

    def _set_skipped(self, key: str) -> None:
        label = self._results.get(key)
        if label is not None:
            label.setText('<span style="color:#888;">Brak klucza — pominięto</span>')

    def _run_all_tests(self) -> None:
        self._test_all_btn.setEnabled(False)
        settings = load_settings()
        QtWidgets.QApplication.processEvents()

        # MusicBrainz
        self._set_pending("musicbrainz")
        QtWidgets.QApplication.processEvents()
        self._test_musicbrainz(settings.musicbrainz_app_name or "LumbagoMusicAI")

        # Cloud providers
        provider_configs = {
            "gemini": (settings.gemini_api_key, settings.gemini_base_url or "https://generativelanguage.googleapis.com/v1beta"),
            "openai": (settings.openai_api_key, settings.openai_base_url or "https://api.openai.com/v1"),
            "grok": (settings.grok_api_key, settings.grok_base_url or "https://api.x.ai/v1"),
            "deepseek": (settings.deepseek_api_key, settings.deepseek_base_url or "https://api.deepseek.com/v1"),
        }
        for provider, (api_key, base_url) in provider_configs.items():
            if not api_key:
                self._set_skipped(provider)
                continue
            self._set_pending(provider)
            QtWidgets.QApplication.processEvents()
            if provider == "gemini":
                self._test_gemini_api(api_key, base_url)
            else:
                self._test_openai_like(provider, api_key, base_url)

        self._test_all_btn.setEnabled(True)

    def _test_musicbrainz(self, app_name: str) -> None:
        try:
            resp = requests.get(
                "https://musicbrainz.org/ws/2/recording",
                headers={"User-Agent": f"{app_name}/1.0"},
                params={"query": "recording:test", "fmt": "json", "limit": "1"},
                timeout=12,
            )
            if resp.status_code == 200:
                self._set_status("musicbrainz", True, "Zapytanie działa poprawnie")
            else:
                self._set_status("musicbrainz", False, f"HTTP {resp.status_code}")
        except Exception as exc:
            self._set_status("musicbrainz", False, str(exc))

    def _test_gemini_api(self, api_key: str, base_url: str) -> None:
        try:
            resp = requests.get(
                f"{base_url.rstrip('/')}/models",
                headers={"x-goog-api-key": api_key},
                timeout=12,
            )
            if resp.status_code == 200:
                self._set_status("gemini", True, "Połączenie i autoryzacja działają")
            else:
                self._set_status("gemini", False, self._extract_http_error(resp))
        except Exception as exc:
            self._set_status("gemini", False, str(exc))

    def _test_openai_like(self, provider: str, api_key: str, base_url: str) -> None:
        try:
            resp = requests.get(
                f"{base_url.rstrip('/')}/models",
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=12,
            )
            if resp.status_code == 200:
                self._set_status(provider, True, "Połączenie i autoryzacja działają")
            else:
                self._set_status(provider, False, self._extract_http_error(resp))
        except Exception as exc:
            self._set_status(provider, False, str(exc))

    @staticmethod
    def _extract_http_error(resp: requests.Response) -> str:
        detail = f"HTTP {resp.status_code}"
        try:
            payload = resp.json()
            error = payload.get("error")
            if isinstance(error, dict):
                msg = str(error.get("message", "")).strip()
                if msg:
                    detail = f"{detail}: {msg}"
            elif isinstance(error, str) and error:
                detail = f"{detail}: {error}"
        except Exception:
            pass
        return detail

