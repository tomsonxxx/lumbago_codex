from __future__ import annotations

from PyQt6 import QtWidgets, QtGui

from lumbago_app.core.config import load_settings, save_settings
from lumbago_app.ui.widgets import apply_dialog_fade, dialog_icon_pixmap


class SettingsDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ustawienia / Klucze API")
        self.setMinimumWidth(560)
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

        self.tabs = QtWidgets.QTabWidget()
        layout.addWidget(self.tabs, 1)

        self._build_metadata_tab()
        self._build_ai_tab()
        self._build_advanced_tab()
        self._build_diagnostics_tab()

        btn_row = QtWidgets.QHBoxLayout()
        btn_row.addStretch(1)
        save_btn = QtWidgets.QPushButton("Zapisz")
        save_btn.clicked.connect(self._save)
        cancel_btn = QtWidgets.QPushButton("Anuluj")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(save_btn)
        btn_row.addWidget(cancel_btn)
        layout.addLayout(btn_row)

    def _build_metadata_tab(self):
        tab = QtWidgets.QWidget()
        form = QtWidgets.QFormLayout(tab)
        form.setContentsMargins(12, 12, 12, 12)
        form.setSpacing(8)

        self.acoustid_key = QtWidgets.QLineEdit()
        self.acoustid_key.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
        acoustid_row = self._key_row(self.acoustid_key, self._test_acoustid)
        form.addRow("Klucz API AcoustID", acoustid_row)

        self.musicbrainz_app = QtWidgets.QLineEdit()
        form.addRow("Nazwa aplikacji MusicBrainz", self.musicbrainz_app)

        self.discogs_token = QtWidgets.QLineEdit()
        self.discogs_token.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
        discogs_row = self._key_row(self.discogs_token, self._test_discogs)
        form.addRow("Token Discogs", discogs_row)

        self.validation_policy = QtWidgets.QComboBox()
        self.validation_policy.addItems(["strict", "balanced", "lenient"])
        form.addRow("Walidacja metadanych", self.validation_policy)

        self.metadata_cache_ttl = QtWidgets.QSpinBox()
        self.metadata_cache_ttl.setRange(0, 365)
        self.metadata_cache_ttl.setSuffix(" dni")
        form.addRow("Cache metadanych (TTL)", self.metadata_cache_ttl)

        self.tabs.addTab(tab, "Metadane")

    def _build_ai_tab(self):
        tab = QtWidgets.QWidget()
        form = QtWidgets.QFormLayout(tab)
        form.setContentsMargins(12, 12, 12, 12)
        form.setSpacing(8)

        self.cloud_provider = QtWidgets.QComboBox()
        self.cloud_provider.addItems(["", "openai", "gemini", "grok", "deepseek"])
        form.addRow("Dostawca AI (chmura)", self.cloud_provider)

        self.cloud_api_key = QtWidgets.QLineEdit()
        self.cloud_api_key.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
        form.addRow("Klucz AI (aktywny dostawca)", self.cloud_api_key)

        self.openai_api_key = QtWidgets.QLineEdit()
        self.openai_api_key.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
        openai_row = self._key_row(self.openai_api_key, lambda: self._test_openai_compatible("openai"))
        form.addRow("Klucz OpenAI API", openai_row)

        self.openai_model = QtWidgets.QLineEdit()
        form.addRow("Model OpenAI", self.openai_model)

        self.grok_api_key = QtWidgets.QLineEdit()
        self.grok_api_key.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
        grok_row = self._key_row(self.grok_api_key, lambda: self._test_openai_compatible("grok"))
        form.addRow("Klucz Grok API", grok_row)

        self.grok_model = QtWidgets.QLineEdit()
        form.addRow("Model Grok", self.grok_model)

        self.deepseek_api_key = QtWidgets.QLineEdit()
        self.deepseek_api_key.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
        deepseek_row = self._key_row(self.deepseek_api_key, lambda: self._test_openai_compatible("deepseek"))
        form.addRow("Klucz DeepSeek API", deepseek_row)

        self.deepseek_model = QtWidgets.QLineEdit()
        form.addRow("Model DeepSeek", self.deepseek_model)

        self.tabs.addTab(tab, "AI Cloud")

    def _build_advanced_tab(self):
        tab = QtWidgets.QWidget()
        form = QtWidgets.QFormLayout(tab)
        form.setContentsMargins(12, 12, 12, 12)
        form.setSpacing(8)

        self.openai_base_url = QtWidgets.QLineEdit()
        form.addRow("Adres bazowy OpenAI (URL)", self.openai_base_url)

        self.grok_base_url = QtWidgets.QLineEdit()
        form.addRow("Adres bazowy Grok (URL)", self.grok_base_url)

        self.deepseek_base_url = QtWidgets.QLineEdit()
        form.addRow("Adres bazowy DeepSeek (URL)", self.deepseek_base_url)

        self.filename_patterns = QtWidgets.QTextEdit()
        self.filename_patterns.setPlaceholderText("Przykład: (?P<artist>.+) - (?P<title>.+)")
        self.filename_patterns.setMaximumHeight(100)
        form.addRow("Wzorce nazw plików (regex, 1 na linię)", self.filename_patterns)

        self.ui_theme = QtWidgets.QComboBox()
        self.ui_theme.addItems(["cyber", "minimal_dark"])
        self.ui_theme.setToolTip("Zmiana motywu wymaga restartu aplikacji")
        form.addRow("Motyw UI", self.ui_theme)

        self.tabs.addTab(tab, "Zaawansowane")

    def _build_diagnostics_tab(self):
        tab = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(tab)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        self.diag_text = QtWidgets.QTextEdit()
        self.diag_text.setReadOnly(True)
        self.diag_text.setPlaceholderText("Kliknij 'Odśwież' aby sprawdzić status")
        layout.addWidget(self.diag_text, 1)

        btn_row = QtWidgets.QHBoxLayout()
        refresh_btn = QtWidgets.QPushButton("Odśwież diagnostykę")
        refresh_btn.clicked.connect(self._refresh_diagnostics)
        vacuum_btn = QtWidgets.QPushButton("Vacuum bazy danych")
        vacuum_btn.setToolTip("Zmniejsz rozmiar bazy po usunięciach")
        vacuum_btn.clicked.connect(self._run_vacuum)
        restore_btn = QtWidgets.QPushButton("Przywróć kopię zapasową…")
        restore_btn.clicked.connect(self._open_restore_dialog)
        btn_row.addWidget(refresh_btn)
        btn_row.addWidget(vacuum_btn)
        btn_row.addStretch(1)
        btn_row.addWidget(restore_btn)
        layout.addLayout(btn_row)

        self.tabs.addTab(tab, "Diagnostyki")

    def _refresh_diagnostics(self):
        import shutil
        from lumbago_app.core.config import app_data_dir, cache_dir
        lines = []

        def _check_tool(name):
            path = shutil.which(name)
            return f"✓ {path}" if path else "✗ Nie znaleziono w PATH"

        lines.append(f"fpcalc:  {_check_tool('fpcalc')}")
        lines.append(f"ffmpeg:  {_check_tool('ffmpeg')}")
        lines.append("")
        data_dir = app_data_dir()
        db_path = data_dir / "lumbago.db"
        if db_path.exists():
            size_mb = db_path.stat().st_size / 1024 / 1024
            lines.append(f"Baza danych:  {db_path}\n  Rozmiar: {size_mb:.2f} MB")
        else:
            lines.append("Baza danych:  Nie istnieje")
        lines.append("")
        cache = cache_dir()
        cache_size = sum(f.stat().st_size for f in cache.rglob("*") if f.is_file())
        lines.append(f"Cache:  {cache}\n  Rozmiar: {cache_size / 1024 / 1024:.2f} MB")
        backups_dir = data_dir / "backups"
        backups = sorted(backups_dir.glob("*.zip")) if backups_dir.exists() else []
        lines.append(f"\nKopie zapasowe:  {len(backups)} plików w {backups_dir}")

        try:
            import librosa
            lines.append(f"\nlibrosa:  ✓ {librosa.__version__}")
        except ImportError:
            lines.append("\nlibrosa:  ✗ Nie zainstalowana (BPM/key detection niedostępne)")

        self.diag_text.setPlainText("\n".join(lines))

    def _run_vacuum(self):
        try:
            from lumbago_app.data.repository import vacuum_database
            vacuum_database()
            QtWidgets.QMessageBox.information(self, "Vacuum", "VACUUM zakończony pomyślnie.")
            self._refresh_diagnostics()
        except Exception as exc:
            QtWidgets.QMessageBox.critical(self, "Vacuum", f"Błąd: {exc}")

    def _open_restore_dialog(self):
        from lumbago_app.core.backup import list_backups, restore_backup
        files = list_backups()
        if not files:
            QtWidgets.QMessageBox.information(self, "Przywróć backup", "Brak kopii zapasowych.")
            return
        items = [f.name for f in files]
        chosen, ok = QtWidgets.QInputDialog.getItem(
            self, "Przywróć kopię zapasową",
            "Wybierz kopię do przywrócenia (wymaga restartu):", items, 0, False
        )
        if not ok or not chosen:
            return
        idx = items.index(chosen)
        confirm = QtWidgets.QMessageBox.question(
            self, "Przywróć backup",
            f"Przywrócić kopię:\n{chosen}\n\nBieżące dane zostaną zastąpione. Kontynuować?",
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
        )
        if confirm != QtWidgets.QMessageBox.StandardButton.Yes:
            return
        try:
            restore_backup(files[idx])
            QtWidgets.QMessageBox.information(
                self, "Przywróć backup",
                "Kopia przywrócona. Uruchom ponownie aplikację aby zmiany były widoczne."
            )
        except Exception as exc:
            QtWidgets.QMessageBox.critical(self, "Przywróć backup", f"Błąd: {exc}")

    def _key_row(self, field: QtWidgets.QLineEdit, test_fn) -> QtWidgets.QWidget:
        widget = QtWidgets.QWidget()
        row = QtWidgets.QHBoxLayout(widget)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(6)
        row.addWidget(field, 1)
        btn = QtWidgets.QPushButton("Testuj")
        btn.setFixedWidth(64)
        btn.setToolTip("Sprawdź poprawność klucza API")
        btn.clicked.connect(test_fn)
        row.addWidget(btn)
        return widget

    def _test_acoustid(self):
        key = self.acoustid_key.text().strip()
        if not key:
            QtWidgets.QMessageBox.warning(self, "Test AcoustID", "Podaj klucz API.")
            return
        try:
            import requests
            resp = requests.get(
                "https://api.acoustid.org/v2/lookup",
                params={"client": key, "meta": "recordings", "duration": "1", "fingerprint": "test"},
                timeout=10,
            )
            if resp.status_code in (200, 400):
                QtWidgets.QMessageBox.information(self, "Test AcoustID", "Klucz działa poprawnie.")
            else:
                QtWidgets.QMessageBox.warning(self, "Test AcoustID", f"Odpowiedź: {resp.status_code}")
        except Exception as exc:
            QtWidgets.QMessageBox.critical(self, "Test AcoustID", f"Błąd połączenia: {exc}")

    def _test_discogs(self):
        token = self.discogs_token.text().strip()
        if not token:
            QtWidgets.QMessageBox.warning(self, "Test Discogs", "Podaj token.")
            return
        try:
            import requests
            resp = requests.get(
                "https://api.discogs.com/oauth/identity",
                headers={"Authorization": f"Discogs token={token}"},
                timeout=10,
            )
            if resp.status_code == 200:
                QtWidgets.QMessageBox.information(self, "Test Discogs", "Token działa poprawnie.")
            else:
                QtWidgets.QMessageBox.warning(self, "Test Discogs", f"Odpowiedź: {resp.status_code}")
        except Exception as exc:
            QtWidgets.QMessageBox.critical(self, "Test Discogs", f"Błąd połączenia: {exc}")

    def _test_openai_compatible(self, provider: str):
        key_map = {"openai": self.openai_api_key, "grok": self.grok_api_key, "deepseek": self.deepseek_api_key}
        url_map = {
            "openai": self.openai_base_url.text().strip() or "https://api.openai.com/v1",
            "grok": self.grok_base_url.text().strip(),
            "deepseek": self.deepseek_base_url.text().strip(),
        }
        key = key_map[provider].text().strip()
        base_url = url_map[provider]
        if not key:
            QtWidgets.QMessageBox.warning(self, f"Test {provider}", "Podaj klucz API.")
            return
        if not base_url:
            QtWidgets.QMessageBox.warning(self, f"Test {provider}", "Podaj adres bazowy URL.")
            return
        try:
            import requests
            resp = requests.get(
                f"{base_url.rstrip('/')}/models",
                headers={"Authorization": f"Bearer {key}"},
                timeout=10,
            )
            if resp.status_code == 200:
                QtWidgets.QMessageBox.information(self, f"Test {provider}", "Klucz działa poprawnie.")
            else:
                QtWidgets.QMessageBox.warning(self, f"Test {provider}", f"Odpowiedź: {resp.status_code}")
        except Exception as exc:
            QtWidgets.QMessageBox.critical(self, f"Test {provider}", f"Błąd połączenia: {exc}")

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
        self.ui_theme.setCurrentText(settings.ui_theme or "cyber")

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
                "UI_THEME": self.ui_theme.currentText().strip(),
            }
        )
        self.accept()
