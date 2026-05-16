from __future__ import annotations

import requests
from PyQt6 import QtCore, QtGui, QtWidgets

from core.config import (
    default_musicbrainz_user_agent,
    load_settings,
    normalize_musicbrainz_user_agent,
    save_settings,
)
from ui.widgets import apply_dialog_fade, dialog_icon_pixmap


def _open_url(url: str) -> None:
    QtGui.QDesktopServices.openUrl(QtCore.QUrl(url))


def _link_button(label: str, url: str) -> QtWidgets.QPushButton:
    btn = QtWidgets.QPushButton(label)
    btn.setObjectName("LinkBtn")
    btn.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
    btn.setFlat(True)
    btn.setToolTip(url)
    btn.clicked.connect(lambda: _open_url(url))
    return btn


def _section_label(text: str) -> QtWidgets.QLabel:
    lbl = QtWidgets.QLabel(text)
    lbl.setObjectName("SectionLabel")
    return lbl


def _password_field(placeholder: str = "") -> QtWidgets.QLineEdit:
    field = QtWidgets.QLineEdit()
    field.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
    if placeholder:
        field.setPlaceholderText(placeholder)
    return field


def _make_scroll_widget() -> tuple[QtWidgets.QScrollArea, QtWidgets.QVBoxLayout]:
    """Returns (scroll_area, inner_layout) — add widgets to inner_layout."""
    inner = QtWidgets.QWidget()
    inner.setObjectName("ScrollInner")
    layout = QtWidgets.QVBoxLayout(inner)
    layout.setContentsMargins(0, 4, 4, 4)
    layout.setSpacing(0)

    scroll = QtWidgets.QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
    scroll.setWidget(inner)
    return scroll, layout


def _group(title: str) -> tuple[QtWidgets.QGroupBox, QtWidgets.QFormLayout]:
    box = QtWidgets.QGroupBox(title)
    box.setObjectName("SettingsGroup")
    form = QtWidgets.QFormLayout(box)
    form.setContentsMargins(12, 14, 12, 12)
    form.setSpacing(8)
    form.setLabelAlignment(QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter)
    return box, form


def _key_row(
    form: QtWidgets.QFormLayout,
    label: str,
    field: QtWidgets.QLineEdit,
    link_label: str,
    url: str,
    hint: str = "",
) -> None:
    """Add a form row with a password/text field and an 'Uzyskaj klucz →' link."""
    row_widget = QtWidgets.QWidget()
    row_layout = QtWidgets.QHBoxLayout(row_widget)
    row_layout.setContentsMargins(0, 0, 0, 0)
    row_layout.setSpacing(6)
    row_layout.addWidget(field, 1)
    row_layout.addWidget(_link_button(link_label, url))
    if hint:
        field.setToolTip(hint)
    form.addRow(label, row_widget)


class SettingsDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ustawienia / Klucze API")
        self.setMinimumSize(620, 520)
        self.setSizeGripEnabled(True)
        apply_dialog_fade(self)
        self._syncing_validation_controls = False
        self._build_ui()
        self._load()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(10)

        # Title row
        title_row = QtWidgets.QHBoxLayout()
        icon_lbl = QtWidgets.QLabel()
        icon_lbl.setPixmap(dialog_icon_pixmap(18))
        icon_lbl.setFixedSize(22, 22)
        title_lbl = QtWidgets.QLabel(self.windowTitle())
        title_lbl.setObjectName("DialogTitle")
        title_row.addWidget(icon_lbl)
        title_row.addWidget(title_lbl)
        title_row.addStretch(1)
        root.addLayout(title_row)

        # Tabs
        self._tabs = QtWidgets.QTabWidget()
        self._tabs.setDocumentMode(True)
        root.addWidget(self._tabs, 1)

        self._tabs.addTab(self._build_tab_metadata(), "Metadata")
        self._tabs.addTab(self._build_tab_ai(), "Cloud AI")
        self._tabs.addTab(self._build_tab_tagging(), "Tagowanie")
        self._tabs.addTab(self._build_tab_performance(), "Wydajność")

        # Bottom buttons
        btn_row = QtWidgets.QHBoxLayout()
        btn_row.addStretch(1)
        save_btn = QtWidgets.QPushButton("Zapisz")
        save_btn.setObjectName("PrimaryBtn")
        save_btn.clicked.connect(self._save)
        cancel_btn = QtWidgets.QPushButton("Anuluj")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(save_btn)
        btn_row.addWidget(cancel_btn)
        root.addLayout(btn_row)

    # ---- Tab: Metadata -----------------------------------------------

    def _build_tab_metadata(self) -> QtWidgets.QWidget:
        scroll, layout = _make_scroll_widget()

        # MusicBrainz
        mb_box, mb_form = _group("MusicBrainz")
        self.musicbrainz_app = QtWidgets.QLineEdit()
        self.musicbrainz_app.setToolTip(
            "User-Agent wysyłany do MusicBrainz API.\n"
            "Format: NazwaAplikacji/wersja (kontakt@email.com)"
        )
        mb_row = QtWidgets.QWidget()
        mb_row_layout = QtWidgets.QHBoxLayout(mb_row)
        mb_row_layout.setContentsMargins(0, 0, 0, 0)
        mb_row_layout.setSpacing(6)
        mb_row_layout.addWidget(self.musicbrainz_app, 1)
        mb_row_layout.addWidget(
            _link_button("Rejestracja →", "https://musicbrainz.org/register")
        )
        mb_form.addRow("Nazwa aplikacji / User-Agent", mb_row)

        self.test_musicbrainz_btn = QtWidgets.QPushButton("Test połączenia")
        self.test_musicbrainz_btn.clicked.connect(self._test_musicbrainz)
        mb_form.addRow("", self.test_musicbrainz_btn)
        layout.addWidget(mb_box)

        # AcoustID
        ac_box, ac_form = _group("AcoustID  (rozpoznawanie nagrań z odcisku palca)")
        self.acoustid_api_key = _password_field("ak_xxxxxxxxxxxxxxxxxxxxxxxx")
        _key_row(
            ac_form,
            "Klucz API",
            self.acoustid_api_key,
            "Uzyskaj klucz →",
            "https://acoustid.org/api-key",
            "Wymagany do rozpoznawania plików audio po odcisku palca (fpcalc).",
        )
        layout.addWidget(ac_box)

        # Discogs
        dc_box, dc_form = _group("Discogs  (metadane winyli / wydawnictw)")
        self.discogs_token = _password_field("token tutaj")
        _key_row(
            dc_form,
            "Token osobisty",
            self.discogs_token,
            "Utwórz token →",
            "https://www.discogs.com/settings/developers",
            "Discogs Personal Access Token. Nie wymaga OAuth dla odczytu.",
        )
        layout.addWidget(dc_box)

        layout.addStretch(1)
        return scroll

    # ---- Tab: Cloud AI -----------------------------------------------

    def _build_tab_ai(self) -> QtWidgets.QWidget:
        scroll, layout = _make_scroll_widget()

        # Active provider
        prov_box, prov_form = _group("Aktywny dostawca AI")
        self.cloud_provider = QtWidgets.QComboBox()
        self.cloud_provider.addItems(["", "gemini", "openai", "grok", "deepseek"])
        self.cloud_provider.setToolTip(
            "Dostawca używany domyślnie przez Smart Tagger i inne funkcje AI.\n"
            "Każdy dostawca ma osobne pole klucza poniżej."
        )
        prov_form.addRow("Aktywny dostawca", self.cloud_provider)
        layout.addWidget(prov_box)

        # Gemini
        gem_box, gem_form = _group("Google Gemini")
        self.gemini_api_key = _password_field("AIzaSy…")
        _key_row(
            gem_form,
            "Klucz API",
            self.gemini_api_key,
            "Google AI Studio →",
            "https://aistudio.google.com/app/apikey",
        )
        self.gemini_base_url = QtWidgets.QLineEdit()
        self.gemini_base_url.setPlaceholderText("https://generativelanguage.googleapis.com/v1beta")
        gem_form.addRow("Base URL", self.gemini_base_url)
        self.gemini_model = QtWidgets.QLineEdit()
        self.gemini_model.setPlaceholderText("gemini-2.0-flash")
        gem_form.addRow("Model", self.gemini_model)
        self.test_gemini_btn = QtWidgets.QPushButton("Test Gemini")
        self.test_gemini_btn.clicked.connect(self._test_gemini)
        gem_form.addRow("", self.test_gemini_btn)
        layout.addWidget(gem_box)

        # OpenAI
        oai_box, oai_form = _group("OpenAI")
        self.openai_api_key = _password_field("sk-proj-…")
        _key_row(
            oai_form,
            "Klucz API",
            self.openai_api_key,
            "platform.openai.com →",
            "https://platform.openai.com/api-keys",
        )
        self.openai_base_url = QtWidgets.QLineEdit()
        self.openai_base_url.setPlaceholderText("https://api.openai.com/v1")
        oai_form.addRow("Base URL", self.openai_base_url)
        self.openai_model = QtWidgets.QLineEdit()
        self.openai_model.setPlaceholderText("gpt-4.1-mini")
        oai_form.addRow("Model", self.openai_model)
        self.test_openai_btn = QtWidgets.QPushButton("Test OpenAI")
        self.test_openai_btn.clicked.connect(self._test_openai)
        oai_form.addRow("", self.test_openai_btn)
        layout.addWidget(oai_box)

        # Grok
        grok_box, grok_form = _group("xAI Grok")
        self.grok_api_key = _password_field("xai-…")
        _key_row(
            grok_form,
            "Klucz API",
            self.grok_api_key,
            "console.x.ai →",
            "https://console.x.ai/",
        )
        self.grok_base_url = QtWidgets.QLineEdit()
        self.grok_base_url.setPlaceholderText("https://api.x.ai/v1")
        grok_form.addRow("Base URL", self.grok_base_url)
        self.grok_model = QtWidgets.QLineEdit()
        self.grok_model.setPlaceholderText("grok-2-latest")
        grok_form.addRow("Model", self.grok_model)
        self.test_grok_btn = QtWidgets.QPushButton("Test Grok")
        self.test_grok_btn.clicked.connect(self._test_grok)
        grok_form.addRow("", self.test_grok_btn)
        layout.addWidget(grok_box)

        # DeepSeek
        ds_box, ds_form = _group("DeepSeek")
        self.deepseek_api_key = _password_field("sk-…")
        _key_row(
            ds_form,
            "Klucz API",
            self.deepseek_api_key,
            "platform.deepseek.com →",
            "https://platform.deepseek.com/api_keys",
        )
        self.deepseek_base_url = QtWidgets.QLineEdit()
        self.deepseek_base_url.setPlaceholderText("https://api.deepseek.com/v1")
        ds_form.addRow("Base URL", self.deepseek_base_url)
        self.deepseek_model = QtWidgets.QLineEdit()
        self.deepseek_model.setPlaceholderText("deepseek-chat")
        ds_form.addRow("Model", self.deepseek_model)
        self.test_deepseek_btn = QtWidgets.QPushButton("Test DeepSeek")
        self.test_deepseek_btn.clicked.connect(self._test_deepseek)
        ds_form.addRow("", self.test_deepseek_btn)
        layout.addWidget(ds_box)

        # Generic "cloud_api_key" fallback
        gen_box, gen_form = _group("Klucz ogólny (fallback dla aktywnego dostawcy)")
        self.cloud_api_key = _password_field("Używany gdy brak klucza dedykowanego")
        gen_form.addRow("Klucz API (ogólny)", self.cloud_api_key)
        layout.addWidget(gen_box)

        layout.addStretch(1)
        return scroll

    # ---- Tab: Tagowanie ----------------------------------------------

    def _build_tab_tagging(self) -> QtWidgets.QWidget:
        scroll, layout = _make_scroll_widget()

        pat_box, pat_form = _group("Wzorce nazw plików (regex)")
        self.filename_patterns = QtWidgets.QTextEdit()
        self.filename_patterns.setPlaceholderText(
            "Jeden wzorzec na linię. Przykład:\n"
            "(?P<artist>.+) - (?P<title>.+)\n"
            "(?P<artist>.+) — (?P<title>.+) \\[(?P<year>\\d{4})\\]"
        )
        self.filename_patterns.setMinimumHeight(100)
        pat_form.addRow("Wzorce (1/linię)", self.filename_patterns)
        layout.addWidget(pat_box)

        pol_box, pol_form = _group("Polityka walidacji metadanych")
        self.validation_policy = QtWidgets.QComboBox()
        self.validation_policy.addItems(["strict", "balanced", "lenient", "aggressive"])
        self.validation_policy.setToolTip(
            "strict — odrzuca wątpliwe dopasowania\n"
            "balanced — umiarkowana tolerancja\n"
            "lenient — przyjmuje więcej wyników\n"
            "aggressive — nadpisuje wszystko najlepszą znalezioną wartością"
        )
        pol_form.addRow("Polityka", self.validation_policy)

        self.overwrite_existing_tags = QtWidgets.QCheckBox(
            "Nadpisuj istniejące tagi (tryb aggressive)"
        )
        self.overwrite_existing_tags.setToolTip(
            "Odpowiednik polityki 'aggressive' — agresywne nadpisywanie\n"
            "lokalnych tagów lepszymi danymi z internetu."
        )
        pol_form.addRow("", self.overwrite_existing_tags)
        layout.addWidget(pol_box)

        self.overwrite_existing_tags.toggled.connect(self._on_overwrite_existing_tags_toggled)
        self.validation_policy.currentTextChanged.connect(self._on_validation_policy_changed)

        layout.addStretch(1)
        return scroll

    # ---- Tab: Wydajność ----------------------------------------------

    def _build_tab_performance(self) -> QtWidgets.QWidget:
        scroll, layout = _make_scroll_widget()

        par_box, par_form = _group("Równoległość")
        self.autotag_parallel_workers = QtWidgets.QSpinBox()
        self.autotag_parallel_workers.setRange(1, 16)
        self.autotag_parallel_workers.setToolTip(
            "Ile plików jest tagowanych jednocześnie (Smart Tagger)."
        )
        par_form.addRow("Równoległe pliki (autotag)", self.autotag_parallel_workers)

        self.provider_parallel_workers = QtWidgets.QSpinBox()
        self.provider_parallel_workers.setRange(2, 12)
        self.provider_parallel_workers.setToolTip(
            "Ile źródeł metadanych (MusicBrainz, Discogs…) jest odpytywanych równolegle."
        )
        par_form.addRow("Równoległe źródła (API)", self.provider_parallel_workers)
        layout.addWidget(par_box)

        cache_box, cache_form = _group("Cache metadanych")
        self.metadata_cache_ttl = QtWidgets.QSpinBox()
        self.metadata_cache_ttl.setRange(0, 365)
        self.metadata_cache_ttl.setSuffix("  dni")
        self.metadata_cache_ttl.setToolTip(
            "Jak długo przechowywać wyniki zapytań do zewnętrznych API.\n"
            "0 = wyłącz cache."
        )
        cache_form.addRow("Czas życia cache (TTL)", self.metadata_cache_ttl)
        layout.addWidget(cache_box)

        layout.addStretch(1)
        return scroll

    # ------------------------------------------------------------------
    # Load / Save
    # ------------------------------------------------------------------

    def _load(self) -> None:
        s = load_settings()
        self.musicbrainz_app.setText(s.musicbrainz_app_name or default_musicbrainz_user_agent())
        self.acoustid_api_key.setText(s.acoustid_api_key or "")
        self.discogs_token.setText(s.discogs_token or "")

        self.cloud_provider.setCurrentText(s.cloud_ai_provider or "")
        self.cloud_api_key.setText(s.cloud_ai_api_key or "")

        self.gemini_api_key.setText(s.gemini_api_key or "")
        self.gemini_base_url.setText(s.gemini_base_url or "")
        self.gemini_model.setText(s.gemini_model or "")

        self.openai_api_key.setText(s.openai_api_key or "")
        self.openai_base_url.setText(s.openai_base_url or "")
        self.openai_model.setText(s.openai_model or "")

        self.grok_api_key.setText(s.grok_api_key or "")
        self.grok_base_url.setText(s.grok_base_url or "")
        self.grok_model.setText(s.grok_model or "")

        self.deepseek_api_key.setText(s.deepseek_api_key or "")
        self.deepseek_base_url.setText(s.deepseek_base_url or "")
        self.deepseek_model.setText(s.deepseek_model or "")

        self.filename_patterns.setPlainText("\n".join(s.filename_patterns or []))
        self._set_validation_policy(s.validation_policy or "aggressive")
        self.metadata_cache_ttl.setValue(s.metadata_cache_ttl_days)
        self.autotag_parallel_workers.setValue(s.autotag_parallel_workers)
        self.provider_parallel_workers.setValue(s.provider_parallel_workers)

    def _save(self) -> None:
        save_settings(
            {
                "MUSICBRAINZ_APP_NAME": normalize_musicbrainz_user_agent(
                    self.musicbrainz_app.text()
                ),
                "ACOUSTID_API_KEY": self.acoustid_api_key.text().strip(),
                "DISCOGS_TOKEN": self.discogs_token.text().strip(),
                "CLOUD_AI_PROVIDER": self.cloud_provider.currentText().strip(),
                "CLOUD_AI_API_KEY": self.cloud_api_key.text().strip(),
                "GEMINI_API_KEY": self.gemini_api_key.text().strip(),
                "GEMINI_BASE_URL": self.gemini_base_url.text().strip(),
                "GEMINI_MODEL": self.gemini_model.text().strip(),
                "OPENAI_API_KEY": self.openai_api_key.text().strip(),
                "OPENAI_BASE_URL": self.openai_base_url.text().strip(),
                "OPENAI_MODEL": self.openai_model.text().strip(),
                "GROK_API_KEY": self.grok_api_key.text().strip(),
                "GROK_BASE_URL": self.grok_base_url.text().strip(),
                "GROK_MODEL": self.grok_model.text().strip(),
                "DEEPSEEK_API_KEY": self.deepseek_api_key.text().strip(),
                "DEEPSEEK_BASE_URL": self.deepseek_base_url.text().strip(),
                "DEEPSEEK_MODEL": self.deepseek_model.text().strip(),
                "FILENAME_PATTERNS": self.filename_patterns.toPlainText().strip(),
                "VALIDATION_POLICY": self.validation_policy.currentText().strip() or "aggressive",
                "METADATA_CACHE_TTL_DAYS": str(self.metadata_cache_ttl.value()),
                "AUTOTAG_PARALLEL_WORKERS": str(self.autotag_parallel_workers.value()),
                "PROVIDER_PARALLEL_WORKERS": str(self.provider_parallel_workers.value()),
            }
        )
        self.accept()

    # ------------------------------------------------------------------
    # Validation policy sync
    # ------------------------------------------------------------------

    def _on_overwrite_existing_tags_toggled(self, checked: bool) -> None:
        if self._syncing_validation_controls:
            return
        desired = "aggressive" if checked else "balanced"
        current = self.validation_policy.currentText()
        if checked and current != desired:
            self._set_validation_policy(desired)
        elif not checked and current == "aggressive":
            self._set_validation_policy(desired)

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

    # ------------------------------------------------------------------
    # API tests
    # ------------------------------------------------------------------

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
        try:
            resp = requests.get(
                "https://musicbrainz.org/ws/2/recording",
                headers={"User-Agent": app_name},
                params={"query": "recording:test", "fmt": "json", "limit": "1"},
                timeout=12,
            )
            if resp.status_code == 200:
                self._show_test_result("MusicBrainz", True, "Zapytanie działa poprawnie.")
            else:
                self._show_test_result("MusicBrainz", False, f"HTTP {resp.status_code}")
        except Exception as exc:
            self._show_test_result("MusicBrainz", False, str(exc))

    def _test_gemini(self) -> None:
        api_key = self.gemini_api_key.text().strip() or self.cloud_api_key.text().strip()
        base_url = (
            self.gemini_base_url.text().strip()
            or "https://generativelanguage.googleapis.com/v1beta"
        )
        if not api_key:
            self._show_test_result("Gemini", False, "Brak klucza API.")
            return
        self._test_http_get("Gemini", f"{base_url.rstrip('/')}/models", {"x-goog-api-key": api_key})

    def _test_openai(self) -> None:
        api_key = self.openai_api_key.text().strip() or self.cloud_api_key.text().strip()
        base_url = self.openai_base_url.text().strip() or "https://api.openai.com/v1"
        if not api_key:
            self._show_test_result("OpenAI", False, "Brak klucza API.")
            return
        self._test_http_get("OpenAI", f"{base_url.rstrip('/')}/models", {"Authorization": f"Bearer {api_key}"})

    def _test_grok(self) -> None:
        api_key = self.grok_api_key.text().strip() or self.cloud_api_key.text().strip()
        base_url = self.grok_base_url.text().strip() or "https://api.x.ai/v1"
        if not api_key:
            self._show_test_result("Grok", False, "Brak klucza API.")
            return
        self._test_http_get("Grok", f"{base_url.rstrip('/')}/models", {"Authorization": f"Bearer {api_key}"})

    def _test_deepseek(self) -> None:
        api_key = self.deepseek_api_key.text().strip() or self.cloud_api_key.text().strip()
        base_url = self.deepseek_base_url.text().strip() or "https://api.deepseek.com/v1"
        if not api_key:
            self._show_test_result("DeepSeek", False, "Brak klucza API.")
            return
        self._test_http_get("DeepSeek", f"{base_url.rstrip('/')}/models", {"Authorization": f"Bearer {api_key}"})

    def _test_http_get(self, title: str, url: str, headers: dict[str, str]) -> None:
        try:
            resp = requests.get(url, headers=headers, timeout=12)
            if resp.status_code == 200:
                self._show_test_result(title, True, "Połączenie i autoryzacja działają.")
                return
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
            self._show_test_result(title, False, detail)
        except Exception as exc:
            self._show_test_result(title, False, str(exc))


# ---------------------------------------------------------------------------
# ApiKeyCheckDialog — unchanged logic, kept for main_window compatibility
# ---------------------------------------------------------------------------


class ApiKeyCheckDialog(QtWidgets.QDialog):
    """Standalone dialog that validates all configured API keys at once."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Sprawdzanie kluczy API")
        self.setMinimumWidth(560)
        self.setSizeGripEnabled(True)
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

        desc = QtWidgets.QLabel(
            "Kliknij <b>Testuj wszystko</b> aby zweryfikować poprawność wszystkich "
            "skonfigurowanych kluczy API."
        )
        desc.setWordWrap(True)
        card_layout.addWidget(desc)

        self._grid = QtWidgets.QGridLayout()
        self._grid.setSpacing(6)
        services = [
            ("MusicBrainz", "musicbrainz"),
            ("AcoustID", "acoustid"),
            ("Discogs", "discogs"),
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
        color = "#00E676" if ok else "#FF5252"
        word = "OK" if ok else "BŁĄD"
        label.setText(f'<span style="color:{color};">{word}</span> — {detail}')

    def _set_pending(self, key: str) -> None:
        label = self._results.get(key)
        if label is not None:
            label.setText('<span style="color:#FFD700;">Testowanie…</span>')

    def _set_skipped(self, key: str) -> None:
        label = self._results.get(key)
        if label is not None:
            label.setText('<span style="color:#888;">Brak klucza — pominięto</span>')

    def _run_all_tests(self) -> None:
        self._test_all_btn.setEnabled(False)
        s = load_settings()
        QtWidgets.QApplication.processEvents()

        self._set_pending("musicbrainz")
        QtWidgets.QApplication.processEvents()
        self._test_musicbrainz(s.musicbrainz_app_name or "LumbagoMusicAI")

        # AcoustID — simple reachability check (no key validation endpoint)
        if s.acoustid_api_key:
            self._set_pending("acoustid")
            QtWidgets.QApplication.processEvents()
            self._test_acoustid(s.acoustid_api_key)
        else:
            self._set_skipped("acoustid")

        # Discogs
        if s.discogs_token:
            self._set_pending("discogs")
            QtWidgets.QApplication.processEvents()
            self._test_discogs(s.discogs_token)
        else:
            self._set_skipped("discogs")

        provider_configs = {
            "gemini": (s.gemini_api_key, s.gemini_base_url or "https://generativelanguage.googleapis.com/v1beta"),
            "openai": (s.openai_api_key, s.openai_base_url or "https://api.openai.com/v1"),
            "grok": (s.grok_api_key, s.grok_base_url or "https://api.x.ai/v1"),
            "deepseek": (s.deepseek_api_key, s.deepseek_base_url or "https://api.deepseek.com/v1"),
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

    def _test_acoustid(self, api_key: str) -> None:
        try:
            resp = requests.get(
                "https://api.acoustid.org/v2/lookup",
                params={"client": api_key, "meta": "recordings", "duration": "1", "fingerprint": "test"},
                timeout=12,
            )
            # AcoustID returns 400 for invalid fingerprint but 200/non-401 confirms key is accepted
            if resp.status_code in (200, 400):
                self._set_status("acoustid", True, "Klucz zaakceptowany przez API")
            elif resp.status_code == 401:
                self._set_status("acoustid", False, "Nieautoryzowany klucz API")
            else:
                self._set_status("acoustid", False, f"HTTP {resp.status_code}")
        except Exception as exc:
            self._set_status("acoustid", False, str(exc))

    def _test_discogs(self, token: str) -> None:
        try:
            resp = requests.get(
                "https://api.discogs.com/oauth/identity",
                headers={
                    "Authorization": f"Discogs token={token}",
                    "User-Agent": "LumbagoMusicAI/1.0",
                },
                timeout=12,
            )
            if resp.status_code == 200:
                data = resp.json()
                username = data.get("username", "?")
                self._set_status("discogs", True, f"Zalogowany jako: {username}")
            elif resp.status_code == 401:
                self._set_status("discogs", False, "Nieprawidłowy token")
            else:
                self._set_status("discogs", False, f"HTTP {resp.status_code}")
        except Exception as exc:
            self._set_status("discogs", False, str(exc))

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
