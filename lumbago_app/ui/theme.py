from __future__ import annotations

import json
import pathlib


CYBER_QSS = """
QWidget {
    background-color: #0b0f16;
    color: #e8f3ff;
    font-family: "Segoe UI", "Noto Sans", "Arial";
    font-size: 12px;
}

QDialog, QMainWindow {
    background-color: #0b0f16;
}

QAbstractButton {
    icon-size: 16px;
}

QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QTextEdit, QPlainTextEdit {
    background-color: #141a2a;
    border: 1px solid #283247;
    border-radius: 10px;
    padding: 8px 10px;
    selection-background-color: #1e3f5a;
}
QLineEdit#SearchInput {
    background-color: #101623;
    border: 1px solid #2b3a55;
    border-radius: 18px;
    padding: 8px 14px;
}
QLineEdit#FilterInput, QDoubleSpinBox#FilterSpin, QComboBox#ViewToggle {
    background-color: #101623;
    border: 1px solid #2b3a55;
    border-radius: 10px;
}
QComboBox {
    padding-right: 22px;
}
QComboBox::drop-down {
    border: none;
    width: 20px;
}
QComboBox::down-arrow {
    image: none;
    border-left: 6px solid transparent;
    border-right: 6px solid transparent;
    border-top: 6px solid #8fb8d8;
    margin-right: 6px;
}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus, QTextEdit:focus, QPlainTextEdit:focus {
    border-color: #63f2ff;
}

QPushButton, QToolButton {
    background-color: #141a2a;
    border: 1px solid #2b3a55;
    border-radius: 12px;
    padding: 8px 12px;
}
QPushButton:hover, QToolButton:hover {
    border-color: #63f2ff;
}
QPushButton:pressed, QToolButton:pressed {
    background-color: #1a2236;
}
QPushButton#PrimaryAction {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #63f2ff, stop:1 #ff6bd5);
    color: #0b0f16;
    border: 1px solid #5ad7e3;
    font-weight: 600;
}
QPushButton#PrimaryAction:hover {
    border-color: #8ff7ff;
}
QPushButton#AutoTagApi {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #63f2ff, stop:1 #6ad1ff);
    color: #0b0f16;
    border: 1px solid #5ad7e3;
    font-weight: 600;
}
QPushButton#AutoTagSearch {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #ff6bd5, stop:1 #b64cff);
    color: #0b0f16;
    border: 1px solid #ff5bd0;
    font-weight: 600;
}
QPushButton#DangerAction {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #ff6b6b, stop:1 #ff2d82);
    color: #0b0f16;
    border: 1px solid #ff5c7a;
    font-weight: 600;
}

QLabel#SectionTitle {
    color: #63f2ff;
    font-weight: 700;
    font-size: 13px;
    letter-spacing: 0.4px;
}
QLabel#DialogTitle {
    color: #e8f3ff;
    font-weight: 700;
    font-size: 16px;
    padding: 2px 0 6px 0;
}
QLabel#ModePill {
    background-color: #101623;
    border: 1px solid #2b3a55;
    border-radius: 12px;
    padding: 4px 10px;
    color: #cfe6ff;
}
QLabel#ModePill[mode="api"] {
    border-color: #63f2ff;
    color: #63f2ff;
}
QLabel#ModePill[mode="mixed"] {
    border-color: #ff6bd5;
    color: #ff6bd5;
}

QFrame {
    border-radius: 16px;
}
QFrame#Card {
    background-color: #131a2b;
    border: 1px solid #243048;
    border-radius: 16px;
}
QFrame#HeaderBar {
    background-color: #121826;
    border: 1px solid #243048;
    border-radius: 16px;
}
QFrame#Toolbar {
    background-color: #121826;
    border: 1px solid #243048;
    border-radius: 16px;
}
QFrame#Card {
    background-color: rgba(16, 21, 34, 210);
    border: 1px solid #22324a;
    border-radius: 14px;
}
QFrame#DialogCard {
    background-color: rgba(15, 19, 34, 220);
    border: 1px solid #22324a;
    border-radius: 16px;
}
QLabel#DialogHint {
    color: #8fb8d8;
    padding: 4px 2px 0 2px;
}

QHeaderView::section {
    background-color: #12182a;
    border: 1px solid #1f2a3d;
    padding: 8px;
    color: #cfe6ff;
}
QHeaderView::section:hover {
    border-color: #2b4b6a;
}

QTableView, QTreeView {
    background-color: #0f1322;
    gridline-color: #1f2a3d;
    selection-background-color: #1c3a52;
    border-radius: 12px;
    alternate-background-color: #0d111d;
}
QTableView::item:selected, QTreeView::item:selected {
    background-color: #1c3a52;
}
QTableView::item:hover, QTreeView::item:hover {
    background-color: #17283d;
}
QTableView::item:hover, QTreeView::item:hover {
    background-color: #16273a;
}

QListView {
    background-color: #0f1322;
    border-radius: 12px;
}
QListView::item:selected {
    background-color: #3b224a;
    color: #ffe7ff;
}
QListView::item:hover {
    background-color: #1a2236;
}
QListView::item:selected {
    background-color: #1c3a52;
}
QListView::item:hover {
    background-color: #16273a;
}

QTabWidget::pane {
    border: 1px solid #1f2a3d;
    border-radius: 12px;
    padding: 6px;
}
QTabBar::tab {
    background-color: #101522;
    border: 1px solid #1f2a3d;
    border-radius: 10px;
    padding: 6px 10px;
    margin-right: 6px;
}
QTabBar::tab:hover {
    border-color: #2b4b6a;
}
QTabBar::tab:selected {
    border-color: #63f2ff;
    color: #63f2ff;
}

QSlider::groove:horizontal {
    background: #1a2236;
    height: 6px;
    border-radius: 3px;
}
QSlider::sub-page:horizontal {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #63f2ff, stop:1 #ff6bd5);
    border-radius: 3px;
}
QSlider::add-page:horizontal {
    background: #1a2236;
    border-radius: 3px;
}
QSlider::handle:horizontal {
    background: #e8f3ff;
    border: 1px solid #63f2ff;
    width: 14px;
    margin: -6px 0;
    border-radius: 7px;
}

QProgressBar {
    background-color: #141a2a;
    border: 1px solid #2b3a55;
    border-radius: 8px;
    text-align: center;
}
QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #63f2ff, stop:1 #ff6bd5);
    border-radius: 8px;
}

QScrollBar:vertical {
    background: #0b0f16;
    width: 10px;
    margin: 4px 2px 4px 2px;
}
QScrollBar::handle:vertical {
    background: #1b2539;
    border-radius: 5px;
}
QScrollBar::handle:vertical:hover {
    background: #27334a;
}
QScrollBar:horizontal {
    background: #0b0f16;
    height: 10px;
    margin: 2px 4px 2px 4px;
}
QScrollBar::handle:horizontal {
    background: #1b2539;
    border-radius: 5px;
}
QScrollBar::handle:horizontal:hover {
    background: #27334a;
}

QSlider::groove:horizontal {
    height: 6px;
    background: #162134;
    border-radius: 3px;
}
QSlider::handle:horizontal {
    width: 14px;
    margin: -4px 0;
    border-radius: 7px;
    background: #63f2ff;
    border: 1px solid #5ad7e3;
}
QSlider::groove:vertical {
    width: 6px;
    background: #162134;
    border-radius: 3px;
}
QSlider::handle:vertical {
    height: 14px;
    margin: 0 -4px;
    border-radius: 7px;
    background: #63f2ff;
    border: 1px solid #5ad7e3;
}

QProgressBar {
    background-color: #12182a;
    border: 1px solid #1f2a3d;
    border-radius: 8px;
    text-align: center;
    color: #cfe6ff;
}
QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #63f2ff, stop:1 #39ffb6);
    border-radius: 8px;
}

QCheckBox, QRadioButton {
    spacing: 8px;
}
QCheckBox::indicator, QRadioButton::indicator {
    width: 16px;
    height: 16px;
}
QCheckBox::indicator {
    border: 1px solid #2b3a55;
    border-radius: 4px;
    background: #0f1322;
}
QCheckBox::indicator:checked {
    background: #63f2ff;
    border-color: #5ad7e3;
}
QRadioButton::indicator {
    border: 1px solid #2b3a55;
    border-radius: 8px;
    background: #0f1322;
}
QRadioButton::indicator:checked {
    background: #63f2ff;
    border-color: #5ad7e3;
}

QSplitter::handle {
    background: #101522;
}

QGroupBox {
    border: 1px solid #1f2a3d;
    border-radius: 12px;
    margin-top: 10px;
    padding: 10px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 6px;
    color: #cfe6ff;
}

QFrame#Sidebar {
    background-color: rgba(15, 19, 34, 230);
    border-right: 1px solid #22324a;
}
QFrame#DetailPanel {
    background-color: rgba(15, 19, 34, 230);
    border-left: 1px solid #22324a;
}
QFrame#PlayerDock {
    background-color: rgba(15, 19, 34, 230);
    border-top: 1px solid #22324a;
}

QMenu {
    background-color: #11182a;
    border: 1px solid #1f2a3d;
    padding: 6px;
}
QMenu::item:selected {
    background-color: #1c3a52;
}

QToolTip {
    background-color: #11182a;
    color: #e8f3ff;
    border: 1px solid #1f2a3d;
    padding: 6px;
}

QToolBar {
    background-color: #0f1322;
    border-bottom: 1px solid #1f2a3d;
    spacing: 6px;
}
QStatusBar {
    background-color: #0f1322;
    border-top: 1px solid #1f2a3d;
    color: #8fb8d8;
}

QMessageBox {
    background-color: #0f1322;
}
QMessageBox QLabel {
    color: #e8f3ff;
}
"""


class TokenEngine:
    """Prosty silnik tokenów kolorów motywu.

    Umożliwia podmienianie wartości kolorów w arkuszu QSS poprzez słownik tokenów.
    Domyślne tokeny odpowiadają palecie CYBER_QSS.
    """

    _DEFAULTS: dict[str, str] = {
        "bg_base": "#0b0f16",
        "bg_surface": "#141a2a",
        "bg_elevated": "#131a2b",
        "border": "#283247",
        "border_accent": "#2b3a55",
        "text_primary": "#e8f3ff",
        "text_secondary": "#8fb8d8",
        "text_muted": "#cfe6ff",
        "accent_cyan": "#63f2ff",
        "accent_pink": "#ff6bd5",
        "accent_green": "#39ff14",
        "selection": "#1c3a52",
    }

    _THEMES_DIR: pathlib.Path = pathlib.Path(__file__).parent.parent.parent / "assets" / "themes"

    def __init__(
        self,
        theme_name_or_overrides: str | dict[str, str] | None = None,
        overrides: dict[str, str] | None = None,
    ) -> None:
        self._tokens: dict[str, str] = dict(self._DEFAULTS)
        self._theme_data: dict = {}
        if isinstance(theme_name_or_overrides, str):
            self._load_from_json(theme_name_or_overrides)
            if overrides:
                self._tokens.update(overrides)
        elif isinstance(theme_name_or_overrides, dict):
            self._tokens.update(theme_name_or_overrides)
        elif overrides:
            self._tokens.update(overrides)

    def _load_from_json(self, theme_name: str) -> None:
        """Ładuje tokeny z pliku JSON motywu."""
        token_file = self._THEMES_DIR / f"{theme_name}.tokens.json"
        if not token_file.exists():
            return
        try:
            data = json.loads(token_file.read_text(encoding="utf-8"))
            self._theme_data = data
            colors = data.get("colors", {})
            self._tokens.update(colors)
        except (json.JSONDecodeError, OSError):
            pass

    def generate_qss(self) -> str:
        """Generuje arkusz QSS na podstawie załadowanych tokenów.

        Jeśli załadowano motyw z JSON, tokeny kolorów są podstawiane w CYBER_QSS.
        W przeciwnym razie zwraca domyślny CYBER_QSS.
        """
        return self.render(CYBER_QSS) if self._theme_data else CYBER_QSS

    def get(self, token: str) -> str:
        """Zwraca wartość tokenu lub pusty string gdy token nie istnieje."""
        return self._tokens.get(token, "")

    def set(self, token: str, value: str) -> None:
        """Ustawia wartość tokenu."""
        self._tokens[token] = value

    def render(self, template: str) -> str:
        """Podmienia tokeny w formacie {token_name} wewnątrz szablonu QSS."""
        result = template
        for key, value in self._tokens.items():
            result = result.replace(f"{{{key}}}", value)
        return result

    def stylesheet(self) -> str:
        """Zwraca gotowy stylesheet CYBER_QSS (bez podstawiania tokenów)."""
        return CYBER_QSS


def apply_theme(app: object, theme_name: str = "cyberpunk") -> None:
    """Wczytuje motyw z JSON i stosuje QSS do aplikacji.

    Parameters
    ----------
    app:
        Instancja ``QApplication`` lub dowolny obiekt posiadający metodę
        ``setStyleSheet(str)``.
    theme_name:
        Nazwa motywu odpowiadająca plikowi ``{theme_name}.tokens.json``
        w katalogu ``assets/themes/``. Domyślnie ``"cyberpunk"``.
    """
    engine = TokenEngine(theme_name)
    app.setStyleSheet(engine.generate_qss())
