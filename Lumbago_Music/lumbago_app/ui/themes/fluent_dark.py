"""
Lumbago Music AI — Motyw Fluent Dark
======================================
Windows Fluent Design System — Dark Mode.
Tło: #202020  Akcent: #60cdff  Powierzchnia: #2b2b2b
"""

FLUENT_DARK_QSS = """
/* ========================================================
   FLUENT DARK — Lumbago Music AI Theme
   Tło: #202020  Akcent: #60cdff  Powierzchnia: #2b2b2b
   ======================================================== */

/* --- Globalne --- */
* {
    font-family: "Segoe UI Variable", "Segoe UI", Arial, sans-serif;
    font-size: 12px;
    color: #e0e0e0;
}

QMainWindow, QDialog, QWidget {
    background-color: #202020;
}

/* --- Menu --- */
QMenuBar {
    background-color: #1c1c1c;
    border-bottom: 1px solid #3a3a3a;
}
QMenuBar::item {
    padding: 4px 12px;
    background: transparent;
    border-radius: 4px;
}
QMenuBar::item:selected {
    background: #60cdff22;
    color: #60cdff;
}
QMenu {
    background-color: #2b2b2b;
    border: 1px solid #404040;
    border-radius: 8px;
    padding: 4px 0;
}
QMenu::item {
    padding: 6px 24px;
    border-radius: 4px;
    margin: 1px 4px;
}
QMenu::item:selected {
    background-color: #60cdff20;
    color: #60cdff;
}
QMenu::separator {
    height: 1px;
    background: #3a3a3a;
    margin: 4px 8px;
}

/* --- Pasek narzędzi --- */
QToolBar {
    background-color: #1c1c1c;
    border-bottom: 1px solid #3a3a3a;
    spacing: 4px;
    padding: 2px;
}
QToolButton {
    background: transparent;
    border: 1px solid transparent;
    border-radius: 4px;
    padding: 5px 10px;
    color: #a0a0a0;
}
QToolButton:hover {
    background: #60cdff18;
    border: 1px solid #60cdff44;
    color: #60cdff;
}
QToolButton:pressed {
    background: #60cdff30;
}
QToolButton:checked {
    background: #60cdff20;
    border: 1px solid #60cdff55;
    color: #60cdff;
}

/* --- Status Bar --- */
QStatusBar {
    background-color: #1c1c1c;
    border-top: 1px solid #3a3a3a;
    color: #707070;
    font-size: 11px;
}

/* --- Tabela --- */
QTableView, QTableWidget {
    background-color: #232323;
    alternate-background-color: #252525;
    gridline-color: #333333;
    border: 1px solid #3a3a3a;
    border-radius: 4px;
    selection-background-color: #60cdff20;
    selection-color: #60cdff;
}
QTableView::item {
    padding: 4px 8px;
}
QTableView::item:selected {
    background-color: #60cdff1e;
    color: #e0e0e0;
}
QTableView::item:hover {
    background-color: #60cdff10;
}
QHeaderView::section {
    background-color: #2b2b2b;
    color: #909090;
    padding: 5px 8px;
    border: none;
    border-right: 1px solid #3a3a3a;
    border-bottom: 1px solid #3a3a3a;
    font-size: 11px;
    font-weight: 600;
}
QHeaderView::section:hover {
    background-color: #60cdff15;
    color: #60cdff;
}

/* --- Drzewo --- */
QTreeView, QTreeWidget {
    background-color: #232323;
    border: 1px solid #3a3a3a;
    border-radius: 4px;
    selection-background-color: #60cdff20;
}
QTreeView::item {
    padding: 3px 4px;
    border-radius: 4px;
}
QTreeView::item:selected {
    background: #60cdff25;
    color: #60cdff;
}
QTreeView::item:hover {
    background: #60cdff12;
}

/* --- Przyciski --- */
QPushButton {
    background-color: #2b2b2b;
    color: #e0e0e0;
    border: 1px solid #454545;
    border-radius: 5px;
    padding: 6px 16px;
    min-width: 80px;
}
QPushButton:hover {
    background-color: #333333;
    border: 1px solid #606060;
}
QPushButton:pressed {
    background-color: #252525;
}
QPushButton:disabled {
    color: #505050;
    border: 1px solid #353535;
    background: #262626;
}
QPushButton[accent="true"] {
    background-color: #60cdff;
    color: #000000;
    border: none;
    font-weight: 600;
}
QPushButton[accent="true"]:hover {
    background-color: #80d8ff;
}
QPushButton[accent="true"]:pressed {
    background-color: #40bfee;
}

/* --- Pola tekstowe --- */
QLineEdit, QTextEdit, QPlainTextEdit {
    background-color: #2b2b2b;
    border: 1px solid #3f3f3f;
    border-radius: 4px;
    padding: 4px 8px;
    color: #e0e0e0;
    selection-background-color: #60cdff44;
}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
    border: 1px solid #60cdff;
    border-bottom: 2px solid #60cdff;
}
QLineEdit:hover, QTextEdit:hover {
    border: 1px solid #606060;
}

/* --- Combobox --- */
QComboBox {
    background-color: #2b2b2b;
    border: 1px solid #3f3f3f;
    border-radius: 4px;
    padding: 4px 8px;
    color: #e0e0e0;
    min-width: 80px;
}
QComboBox:hover {
    border: 1px solid #606060;
}
QComboBox:focus {
    border: 1px solid #60cdff;
}
QComboBox::drop-down {
    border: none;
    width: 20px;
}
QComboBox QAbstractItemView {
    background-color: #2b2b2b;
    border: 1px solid #505050;
    border-radius: 4px;
    selection-background-color: #60cdff25;
    selection-color: #60cdff;
}

/* --- Suwaki --- */
QSlider::groove:horizontal {
    height: 4px;
    background: #3a3a3a;
    border-radius: 2px;
}
QSlider::handle:horizontal {
    background: #60cdff;
    width: 16px;
    height: 16px;
    margin: -6px 0;
    border-radius: 8px;
}
QSlider::handle:horizontal:hover {
    background: #80d8ff;
}
QSlider::sub-page:horizontal {
    background: #60cdff;
    border-radius: 2px;
}

/* --- Scrollbary --- */
QScrollBar:vertical {
    background: transparent;
    width: 10px;
    margin: 2px;
}
QScrollBar::handle:vertical {
    background: #505050;
    min-height: 30px;
    border-radius: 5px;
}
QScrollBar::handle:vertical:hover {
    background: #60cdff77;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: none; height: 0;
}
QScrollBar:horizontal {
    background: transparent;
    height: 10px;
    margin: 2px;
}
QScrollBar::handle:horizontal {
    background: #505050;
    min-width: 30px;
    border-radius: 5px;
}
QScrollBar::handle:horizontal:hover {
    background: #60cdff77;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal,
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
    background: none; width: 0;
}

/* --- Zakładki --- */
QTabWidget::pane {
    border: 1px solid #3a3a3a;
    border-radius: 4px;
    background: #232323;
}
QTabBar::tab {
    background: transparent;
    color: #909090;
    padding: 6px 16px;
    border-bottom: 2px solid transparent;
    margin-right: 4px;
}
QTabBar::tab:selected {
    color: #60cdff;
    border-bottom: 2px solid #60cdff;
}
QTabBar::tab:hover:!selected {
    color: #c0c0c0;
    background: #60cdff10;
}

/* --- Splitter --- */
QSplitter::handle {
    background: #3a3a3a;
    border-radius: 2px;
}
QSplitter::handle:horizontal { width: 3px; }
QSplitter::handle:vertical   { height: 3px; }
QSplitter::handle:hover {
    background: #60cdff77;
}

/* --- GroupBox --- */
QGroupBox {
    border: 1px solid #3a3a3a;
    border-radius: 6px;
    margin-top: 8px;
    padding-top: 6px;
    color: #909090;
    font-weight: 600;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 4px;
}

/* --- Progress Bar --- */
QProgressBar {
    background-color: #2b2b2b;
    border: none;
    border-radius: 4px;
    text-align: center;
    color: #60cdff;
    height: 16px;
}
QProgressBar::chunk {
    background: #60cdff;
    border-radius: 4px;
}

/* --- CheckBox / Radio --- */
QCheckBox { spacing: 6px; color: #c0c0c0; }
QCheckBox::indicator {
    width: 16px; height: 16px;
    border: 1px solid #505050;
    border-radius: 3px;
    background: #2b2b2b;
}
QCheckBox::indicator:checked {
    background: #60cdff;
    border: 1px solid #60cdff;
}
QRadioButton { spacing: 6px; color: #c0c0c0; }
QRadioButton::indicator {
    width: 16px; height: 16px;
    border: 1px solid #505050;
    border-radius: 8px;
    background: #2b2b2b;
}
QRadioButton::indicator:checked {
    background: #60cdff;
    border: 1px solid #60cdff;
}

/* --- Tooltip --- */
QToolTip {
    background-color: #2b2b2b;
    border: 1px solid #505050;
    color: #e0e0e0;
    padding: 4px 8px;
    border-radius: 4px;
}

/* --- Spin Box --- */
QSpinBox, QDoubleSpinBox {
    background-color: #2b2b2b;
    border: 1px solid #3f3f3f;
    border-radius: 4px;
    padding: 4px;
    color: #e0e0e0;
}
QSpinBox:focus, QDoubleSpinBox:focus {
    border: 1px solid #60cdff;
}
"""
