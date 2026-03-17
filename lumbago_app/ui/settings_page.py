from __future__ import annotations

import os
import shutil

from PyQt6 import QtWidgets, QtCore, QtGui

from lumbago_app.core.config import load_settings, save_settings


# ---------------------------------------------------------------------------
# Stałe kolorów
# ---------------------------------------------------------------------------
_BG = "#0a0d1a"
_CYAN = "#00d4ff"
_PURPLE = "#8b5cf6"
_TEXT = "#e6f7ff"
_TEXT_DIM = "#94a3b8"

_NAV_STYLE = f"""
QPushButton[objectName="NavItem"],
QPushButton[objectName="NavItemActive"] {{
    border: none;
    border-radius: 6px;
    padding: 10px 14px;
    text-align: left;
    font-size: 13px;
    color: {_TEXT_DIM};
    background: transparent;
}}
QPushButton[objectName="NavItem"]:hover {{
    background: rgba(0, 212, 255, 0.08);
    color: {_TEXT};
}}
QPushButton[objectName="NavItemActive"] {{
    background: rgba(0, 212, 255, 0.15);
    color: {_CYAN};
    border-left: 3px solid {_CYAN};
}}
"""

_CONTENT_STYLE = f"""
QFrame[objectName="Card"] {{
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 8px;
}}
QLabel[objectName="SectionTitle"] {{
    font-size: 14px;
    font-weight: 600;
    color: {_CYAN};
    padding-bottom: 2px;
}}
QLabel {{
    color: {_TEXT};
    font-size: 12px;
}}
QLineEdit, QTextEdit, QComboBox, QSpinBox {{
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 5px;
    color: {_TEXT};
    padding: 6px 8px;
    font-size: 12px;
}}
QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QSpinBox:focus {{
    border-color: {_CYAN};
}}
QComboBox::drop-down {{
    border: none;
    padding-right: 6px;
}}
QComboBox QAbstractItemView {{
    background: #111528;
    color: {_TEXT};
    selection-background-color: rgba(0, 212, 255, 0.2);
    border: 1px solid rgba(255,255,255,0.1);
}}
QPushButton {{
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 5px;
    color: {_TEXT};
    padding: 6px 14px;
    font-size: 12px;
}}
QPushButton:hover {{
    background: rgba(0, 212, 255, 0.12);
    border-color: {_CYAN};
}}
QPushButton[objectName="PrimaryAction"] {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {_CYAN}, stop:1 {_PURPLE});
    color: #0a0d1a;
    font-weight: 600;
    border: none;
    padding: 8px 28px;
    border-radius: 6px;
}}
QPushButton[objectName="PrimaryAction"]:hover {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #33ddff, stop:1 #a77dff);
}}
"""


class SettingsPage(QtWidgets.QWidget):
    """Strona ustawień do osadzenia w QStackedWidget (inline, nie dialog)."""

    settings_saved = QtCore.pyqtSignal()

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setStyleSheet(f"SettingsPage {{ background: {_BG}; }}")
        self._build_ui()
        self._load()

    # ------------------------------------------------------------------
    # Budowanie UI
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        root = QtWidgets.QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Lewy panel nawigacyjny ────────────────────────────────────
        nav_frame = QtWidgets.QFrame()
        nav_frame.setFixedWidth(200)
        nav_frame.setStyleSheet(
            f"background: rgba(255,255,255,0.02); border-right: 1px solid rgba(255,255,255,0.06);"
        )
        nav_layout = QtWidgets.QVBoxLayout(nav_frame)
        nav_layout.setContentsMargins(10, 18, 10, 18)
        nav_layout.setSpacing(4)
        nav_frame.setStyleSheet(_NAV_STYLE + nav_frame.styleSheet())

        self._nav_buttons: list[QtWidgets.QPushButton] = []
        nav_items = ["Ogólne", "AI Cloud", "Zaawansowane", "Diagnostyki"]
        for idx, label in enumerate(nav_items):
            btn = QtWidgets.QPushButton(label)
            btn.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
            btn.clicked.connect(lambda checked, i=idx: self._switch_section(i))
            nav_layout.addWidget(btn)
            self._nav_buttons.append(btn)

        nav_layout.addStretch(1)
        root.addWidget(nav_frame)

        # ── Prawy panel treści ────────────────────────────────────────
        right = QtWidgets.QWidget()
        right.setStyleSheet(_CONTENT_STYLE)
        right_layout = QtWidgets.QVBoxLayout(right)
        right_layout.setContentsMargins(24, 18, 24, 18)
        right_layout.setSpacing(16)

        self._content_stack = QtWidgets.QStackedWidget()
        right_layout.addWidget(self._content_stack, 1)

        self._build_general_section()
        self._build_ai_cloud_section()
        self._build_advanced_section()
        self._build_diagnostics_section()

        # ── Dolny pasek przycisków ────────────────────────────────────
        btn_row = QtWidgets.QHBoxLayout()
        btn_row.setSpacing(10)
        btn_row.addStretch(1)

        restore_btn = QtWidgets.QPushButton("Przywróć domyślne")
        restore_btn.clicked.connect(self._restore_defaults)
        btn_row.addWidget(restore_btn)

        save_btn = QtWidgets.QPushButton("Zapisz")
        save_btn.setObjectName("PrimaryAction")
        save_btn.clicked.connect(self._save)
        btn_row.addWidget(save_btn)

        right_layout.addLayout(btn_row)
        root.addWidget(right, 1)

        # Domyślnie pierwsza sekcja
        self._switch_section(0)

    def _switch_section(self, index: int) -> None:
        self._content_stack.setCurrentIndex(index)
        for i, btn in enumerate(self._nav_buttons):
            btn.setObjectName("NavItemActive" if i == index else "NavItem")
            # Wymuś odświeżenie stylu
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    # ------------------------------------------------------------------
    # Sekcja: Ogólne
    # ------------------------------------------------------------------

    def _build_general_section(self) -> None:
        page = QtWidgets.QWidget()
        scroll = self._scrollable(page)

        layout = QtWidgets.QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        title = QtWidgets.QLabel("Ogólne")
        title.setObjectName("SectionTitle")
        layout.addWidget(title)

        card = self._card()
        form = QtWidgets.QFormLayout(card)
        form.setContentsMargins(16, 14, 16, 14)
        form.setSpacing(10)

        self.validation_policy = QtWidgets.QComboBox()
        self.validation_policy.addItems(["strict", "balanced", "lenient"])
        form.addRow("Polityka walidacji:", self.validation_policy)

        self.metadata_cache_ttl = QtWidgets.QSpinBox()
        self.metadata_cache_ttl.setRange(0, 365)
        self.metadata_cache_ttl.setSuffix(" dni")
        form.addRow("Cache metadanych (TTL):", self.metadata_cache_ttl)

        self.filename_patterns = QtWidgets.QTextEdit()
        self.filename_patterns.setPlaceholderText(
            "Wzorce regex, jeden na linię\n"
            "Przykład: (?P<artist>.+) - (?P<title>.+)"
        )
        self.filename_patterns.setMaximumHeight(120)
        form.addRow("Wzorce nazw plików:", self.filename_patterns)

        self.ui_theme = QtWidgets.QComboBox()
        self.ui_theme.addItems(["cyber", "minimal_dark"])
        self.ui_theme.setToolTip("Zmiana motywu wymaga restartu aplikacji")
        form.addRow("Motyw UI:", self.ui_theme)

        layout.addWidget(card)
        layout.addStretch(1)

        self._content_stack.addWidget(scroll)

    # ------------------------------------------------------------------
    # Sekcja: AI Cloud
    # ------------------------------------------------------------------

    def _build_ai_cloud_section(self) -> None:
        page = QtWidgets.QWidget()
        scroll = self._scrollable(page)

        layout = QtWidgets.QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        title = QtWidgets.QLabel("AI Cloud")
        title.setObjectName("SectionTitle")
        layout.addWidget(title)

        # ── Wybór dostawcy ────────────────────────────────────────────
        provider_card = self._card()
        pc_lay = QtWidgets.QVBoxLayout(provider_card)
        pc_lay.setContentsMargins(16, 14, 16, 14)
        pc_lay.setSpacing(8)

        pc_title = QtWidgets.QLabel("Aktywny dostawca")
        pc_title.setObjectName("SectionTitle")
        pc_lay.addWidget(pc_title)

        self.cloud_provider = QtWidgets.QComboBox()
        self.cloud_provider.addItems(["", "openai", "gemini", "grok", "deepseek"])
        self.cloud_provider.setToolTip("Wybierz dostawcę AI do tagowania w chmurze")
        self.cloud_provider.currentTextChanged.connect(self._on_provider_changed)
        pc_lay.addWidget(self.cloud_provider)

        self._provider_status = QtWidgets.QLabel("")
        self._provider_status.setWordWrap(True)
        pc_lay.addWidget(self._provider_status)

        layout.addWidget(provider_card)

        # ── Klucze per dostawca ───────────────────────────────────────
        providers_info: list[tuple[str, str, str, str, str]] = [
            ("openai", "OpenAI", "sk-...", "gpt-4.1-mini", "OPENAI_API_KEY"),
            ("gemini", "Gemini", "AIza...", "gemini-2.5-flash", "GEMINI_API_KEY"),
            ("grok", "Grok (xAI)", "xai-...", "grok-2-latest", "GROK_API_KEY"),
            ("deepseek", "DeepSeek", "sk-...", "deepseek-chat", "DEEPSEEK_API_KEY"),
        ]

        self._ai_key_fields: dict[str, QtWidgets.QLineEdit] = {}
        self._ai_model_fields: dict[str, QtWidgets.QLineEdit] = {}
        self._ai_env_labels: dict[str, QtWidgets.QLabel] = {}

        for provider_id, display_name, key_ph, model_ph, env_var in providers_info:
            card = self._card()
            card_lay = QtWidgets.QVBoxLayout(card)
            card_lay.setContentsMargins(16, 14, 16, 14)
            card_lay.setSpacing(8)

            lbl = QtWidgets.QLabel(display_name)
            lbl.setObjectName("SectionTitle")
            card_lay.addWidget(lbl)

            # Klucz API + przycisk test
            key_row = QtWidgets.QHBoxLayout()
            key_field = QtWidgets.QLineEdit()
            key_field.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
            key_field.setPlaceholderText(key_ph)
            key_row.addWidget(key_field, 1)

            test_btn = QtWidgets.QPushButton("Testuj")
            test_btn.setFixedWidth(70)
            test_btn.clicked.connect(
                lambda checked, pid=provider_id: self._run_provider_test(pid)
            )
            key_row.addWidget(test_btn)
            card_lay.addLayout(key_row)

            self._ai_key_fields[provider_id] = key_field

            # Model
            model_field = QtWidgets.QLineEdit()
            model_field.setPlaceholderText(model_ph)
            card_lay.addWidget(model_field)
            self._ai_model_fields[provider_id] = model_field

            # Env var detection
            env_lbl = self._env_label(env_var)
            card_lay.addWidget(env_lbl)
            self._ai_env_labels[provider_id] = env_lbl

            layout.addWidget(card)

        layout.addStretch(1)
        self._content_stack.addWidget(scroll)

    # ------------------------------------------------------------------
    # Sekcja: Zaawansowane
    # ------------------------------------------------------------------

    def _build_advanced_section(self) -> None:
        page = QtWidgets.QWidget()
        scroll = self._scrollable(page)

        layout = QtWidgets.QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        title = QtWidgets.QLabel("Zaawansowane")
        title.setObjectName("SectionTitle")
        layout.addWidget(title)

        # ── Adresy bazowe ─────────────────────────────────────────────
        urls_card = self._card()
        urls_form = QtWidgets.QFormLayout(urls_card)
        urls_form.setContentsMargins(16, 14, 16, 14)
        urls_form.setSpacing(10)

        url_title = QtWidgets.QLabel("Adresy bazowe API")
        url_title.setObjectName("SectionTitle")
        urls_form.addRow(url_title)

        self.openai_base_url = QtWidgets.QLineEdit()
        self.openai_base_url.setPlaceholderText("https://api.openai.com/v1")
        urls_form.addRow("OpenAI:", self.openai_base_url)

        self.grok_base_url = QtWidgets.QLineEdit()
        self.grok_base_url.setPlaceholderText("https://api.x.ai/v1")
        urls_form.addRow("Grok:", self.grok_base_url)

        self.deepseek_base_url = QtWidgets.QLineEdit()
        self.deepseek_base_url.setPlaceholderText("https://api.deepseek.com/v1")
        urls_form.addRow("DeepSeek:", self.deepseek_base_url)

        layout.addWidget(urls_card)

        # ── Klucze zewnętrzne ─────────────────────────────────────────
        ext_card = self._card()
        ext_form = QtWidgets.QFormLayout(ext_card)
        ext_form.setContentsMargins(16, 14, 16, 14)
        ext_form.setSpacing(10)

        ext_title = QtWidgets.QLabel("Klucze zewnętrzne")
        ext_title.setObjectName("SectionTitle")
        ext_form.addRow(ext_title)

        self.acoustid_key = QtWidgets.QLineEdit()
        self.acoustid_key.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
        self.acoustid_key.setPlaceholderText("Klucz API AcoustID")
        ext_form.addRow("AcoustID:", self.acoustid_key)

        self.musicbrainz_app = QtWidgets.QLineEdit()
        self.musicbrainz_app.setPlaceholderText("Nazwa aplikacji MusicBrainz")
        ext_form.addRow("MusicBrainz:", self.musicbrainz_app)

        self.discogs_token = QtWidgets.QLineEdit()
        self.discogs_token.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
        self.discogs_token.setPlaceholderText("Token Discogs")
        ext_form.addRow("Discogs:", self.discogs_token)

        layout.addWidget(ext_card)
        layout.addStretch(1)

        self._content_stack.addWidget(scroll)

    # ------------------------------------------------------------------
    # Sekcja: Diagnostyki
    # ------------------------------------------------------------------

    def _build_diagnostics_section(self) -> None:
        page = QtWidgets.QWidget()
        scroll = self._scrollable(page)

        layout = QtWidgets.QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        title = QtWidgets.QLabel("Diagnostyki")
        title.setObjectName("SectionTitle")
        layout.addWidget(title)

        card = self._card()
        card_lay = QtWidgets.QVBoxLayout(card)
        card_lay.setContentsMargins(16, 14, 16, 14)
        card_lay.setSpacing(10)

        self.diag_text = QtWidgets.QTextEdit()
        self.diag_text.setReadOnly(True)
        self.diag_text.setPlaceholderText("Kliknij 'Odśwież' aby sprawdzić status systemu")
        self.diag_text.setMinimumHeight(280)
        self.diag_text.setStyleSheet(
            f"font-family: 'Consolas', 'Courier New', monospace; font-size: 12px; color: {_TEXT};"
        )
        card_lay.addWidget(self.diag_text, 1)

        refresh_btn = QtWidgets.QPushButton("Odśwież diagnostykę")
        refresh_btn.clicked.connect(self._refresh_diagnostics)
        card_lay.addWidget(refresh_btn)

        layout.addWidget(card)
        layout.addStretch(1)

        self._content_stack.addWidget(scroll)

    # ------------------------------------------------------------------
    # Pomocnicze metody budowania UI
    # ------------------------------------------------------------------

    @staticmethod
    def _card() -> QtWidgets.QFrame:
        frame = QtWidgets.QFrame()
        frame.setObjectName("Card")
        return frame

    @staticmethod
    def _scrollable(inner: QtWidgets.QWidget) -> QtWidgets.QScrollArea:
        scroll = QtWidgets.QScrollArea()
        scroll.setWidget(inner)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        return scroll

    @staticmethod
    def _env_label(env_var: str) -> QtWidgets.QLabel:
        value = os.getenv(env_var)
        if value:
            text = f"Wykryto {env_var} w zmiennych środowiskowych"
            color = "#4ade80"
        else:
            text = f"{env_var} nie ustawiona"
            color = "#64748b"
        lbl = QtWidgets.QLabel(text)
        lbl.setStyleSheet(f"color: {color}; font-size: 11px;")
        return lbl

    # ------------------------------------------------------------------
    # Logika dostawcy AI
    # ------------------------------------------------------------------

    def _on_provider_changed(self, provider: str) -> None:
        if not provider:
            self._provider_status.setText("")
            return
        field = self._ai_key_fields.get(provider)
        has_key = bool(field and field.text().strip())
        env_map = {
            "openai": "OPENAI_API_KEY",
            "grok": "GROK_API_KEY",
            "deepseek": "DEEPSEEK_API_KEY",
            "gemini": "GEMINI_API_KEY",
        }
        has_env = bool(os.getenv(env_map.get(provider, "")))
        if has_key:
            self._provider_status.setText(f"Klucz {provider} skonfigurowany")
            self._provider_status.setStyleSheet("color: #4ade80; font-size: 11px;")
        elif has_env:
            self._provider_status.setText(f"Klucz {provider} wykryty w środowisku")
            self._provider_status.setStyleSheet("color: #4ade80; font-size: 11px;")
        else:
            self._provider_status.setText(f"Brak klucza dla {provider}")
            self._provider_status.setStyleSheet("color: #f59e0b; font-size: 11px;")

    def _run_provider_test(self, provider: str) -> None:
        from lumbago_app.services.ai_tagger import CloudAiTagger

        field = self._ai_key_fields.get(provider)
        api_key = field.text().strip() if field else ""
        if not api_key:
            QtWidgets.QMessageBox.warning(
                self, f"Test {provider}", "Podaj klucz API."
            )
            return

        url_map = {
            "openai": self.openai_base_url,
            "grok": self.grok_base_url,
            "deepseek": self.deepseek_base_url,
        }
        model_field = self._ai_model_fields.get(provider)
        url_field = url_map.get(provider)

        base_url = url_field.text().strip() if url_field else None
        model = model_field.text().strip() if model_field else None

        ok, msg = CloudAiTagger.test_connection(
            provider, api_key, base_url or None, model or None
        )
        if ok:
            QtWidgets.QMessageBox.information(self, f"Test {provider}", msg)
        else:
            QtWidgets.QMessageBox.warning(self, f"Test {provider}", msg)

    # ------------------------------------------------------------------
    # Diagnostyki
    # ------------------------------------------------------------------

    def _refresh_diagnostics(self) -> None:
        from lumbago_app.core.config import app_data_dir, cache_dir

        lines: list[str] = []

        def _check_tool(name: str) -> str:
            path = shutil.which(name)
            return f"OK  {path}" if path else "BRAK  Nie znaleziono w PATH"

        lines.append(f"fpcalc:   {_check_tool('fpcalc')}")
        lines.append(f"ffmpeg:   {_check_tool('ffmpeg')}")
        lines.append("")

        data_dir = app_data_dir()
        db_path = data_dir / "lumbago.db"
        if db_path.exists():
            size_mb = db_path.stat().st_size / 1024 / 1024
            lines.append(f"Baza danych:  {db_path}")
            lines.append(f"  Rozmiar: {size_mb:.2f} MB")
        else:
            lines.append("Baza danych:  Nie istnieje")
        lines.append("")

        cache = cache_dir()
        try:
            cache_size = sum(
                f.stat().st_size for f in cache.rglob("*") if f.is_file()
            )
            lines.append(f"Cache:  {cache}")
            lines.append(f"  Rozmiar: {cache_size / 1024 / 1024:.2f} MB")
        except Exception:
            lines.append(f"Cache:  {cache}  (brak dostępu)")

        lines.append("")
        try:
            import librosa

            lines.append(f"librosa:  OK  {librosa.__version__}")
        except ImportError:
            lines.append("librosa:  BRAK  Nie zainstalowana (BPM/key detection niedostępne)")

        self.diag_text.setPlainText("\n".join(lines))

    # ------------------------------------------------------------------
    # Ładowanie / zapisywanie
    # ------------------------------------------------------------------

    def _load(self) -> None:
        settings = load_settings()

        self.validation_policy.setCurrentText(settings.validation_policy or "balanced")
        self.metadata_cache_ttl.setValue(settings.metadata_cache_ttl_days)
        self.filename_patterns.setPlainText(
            "\n".join(settings.filename_patterns or [])
        )
        self.ui_theme.setCurrentText(settings.ui_theme or "cyber")

        self.cloud_provider.setCurrentText(settings.cloud_ai_provider or "")

        # Klucze per dostawca
        key_mapping: dict[str, str | None] = {
            "openai": settings.openai_api_key,
            "gemini": settings.cloud_ai_api_key,
            "grok": settings.grok_api_key,
            "deepseek": settings.deepseek_api_key,
        }
        for provider_id, value in key_mapping.items():
            field = self._ai_key_fields.get(provider_id)
            if field:
                field.setText(value or "")

        model_mapping: dict[str, str | None] = {
            "openai": settings.openai_model,
            "gemini": None,
            "grok": settings.grok_model,
            "deepseek": settings.deepseek_model,
        }
        for provider_id, value in model_mapping.items():
            field = self._ai_model_fields.get(provider_id)
            if field:
                field.setText(value or "")

        self.openai_base_url.setText(settings.openai_base_url or "")
        self.grok_base_url.setText(settings.grok_base_url or "")
        self.deepseek_base_url.setText(settings.deepseek_base_url or "")

        self.acoustid_key.setText(settings.acoustid_api_key or "")
        self.musicbrainz_app.setText(settings.musicbrainz_app_name or "")
        self.discogs_token.setText(settings.discogs_token or "")

    def _save(self) -> None:
        values: dict[str, str] = {
            "VALIDATION_POLICY": self.validation_policy.currentText().strip(),
            "METADATA_CACHE_TTL_DAYS": str(self.metadata_cache_ttl.value()),
            "FILENAME_PATTERNS": self.filename_patterns.toPlainText().strip(),
            "UI_THEME": self.ui_theme.currentText().strip(),
            "CLOUD_AI_PROVIDER": self.cloud_provider.currentText().strip(),
            "OPENAI_API_KEY": self._ai_key_fields["openai"].text().strip(),
            "CLOUD_AI_API_KEY": self._ai_key_fields["gemini"].text().strip(),
            "GROK_API_KEY": self._ai_key_fields["grok"].text().strip(),
            "DEEPSEEK_API_KEY": self._ai_key_fields["deepseek"].text().strip(),
            "OPENAI_MODEL": self._ai_model_fields["openai"].text().strip(),
            "GROK_MODEL": self._ai_model_fields["grok"].text().strip(),
            "DEEPSEEK_MODEL": self._ai_model_fields["deepseek"].text().strip(),
            "OPENAI_BASE_URL": self.openai_base_url.text().strip(),
            "GROK_BASE_URL": self.grok_base_url.text().strip(),
            "DEEPSEEK_BASE_URL": self.deepseek_base_url.text().strip(),
            "ACOUSTID_API_KEY": self.acoustid_key.text().strip(),
            "MUSICBRAINZ_APP_NAME": self.musicbrainz_app.text().strip(),
            "DISCOGS_TOKEN": self.discogs_token.text().strip(),
        }
        save_settings(values)
        self.settings_saved.emit()

    def _restore_defaults(self) -> None:
        confirm = QtWidgets.QMessageBox.question(
            self,
            "Przywróć domyślne",
            "Czy na pewno chcesz przywrócić ustawienia domyślne?\n"
            "Klucze API nie zostaną usunięte.",
            QtWidgets.QMessageBox.StandardButton.Yes
            | QtWidgets.QMessageBox.StandardButton.No,
        )
        if confirm != QtWidgets.QMessageBox.StandardButton.Yes:
            return

        self.validation_policy.setCurrentText("balanced")
        self.metadata_cache_ttl.setValue(30)
        self.filename_patterns.setPlainText("")
        self.ui_theme.setCurrentText("cyber")
        self.cloud_provider.setCurrentText("")
        self.openai_base_url.setText("https://api.openai.com/v1")
        self.grok_base_url.setText("https://api.x.ai/v1")
        self.deepseek_base_url.setText("https://api.deepseek.com/v1")
        self._ai_model_fields["openai"].setText("gpt-4.1-mini")
        self._ai_model_fields["grok"].setText("grok-2-latest")
        self._ai_model_fields["deepseek"].setText("deepseek-chat")
        self._ai_model_fields["gemini"].setText("gemini-2.5-flash")
