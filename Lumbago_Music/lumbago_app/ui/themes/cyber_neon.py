"""
Lumbago Music AI — Motyw Cyber Neon
=====================================
Pełny QSS: ciemne tło #0d0d0f, cyjanowy akcent #00f5ff.
Styl DJ/club/futurystyczny.
"""

CYBER_NEON_QSS = """
/* ========================================================
   CYBER NEON — Lumbago Music AI Theme
   Tło: #0d0d0f  Akcent: #00f5ff  Tekst: #e0e0e0
   ======================================================== */

/* --- Globalne --- */
* {
    font-family: "Segoe UI", "Inter", Arial, sans-serif;
    font-size: 12px;
    color: #e0e0e0;
}

QMainWindow, QDialog, QWidget {
    background-color: #0d0d0f;
}

/* --- Menu --- */
QMenuBar {
    background-color: #0a0a0c;
    border-bottom: 1px solid #1a1a2e;
}
QMenuBar::item {
    padding: 4px 12px;
    background: transparent;
}
QMenuBar::item:selected {
    background: #00f5ff22;
    color: #00f5ff;
}
QMenu {
    background-color: #111118;
    border: 1px solid #00f5ff33;
    padding: 4px 0;
}
QMenu::item {
    padding: 6px 24px;
}
QMenu::item:selected {
    background-color: #00f5ff22;
    color: #00f5ff;
}
QMenu::separator {
    height: 1px;
    background: #1e1e2e;
    margin: 4px 0;
}

/* --- Pasek narzędzi --- */
QToolBar {
    background-color: #0a0a0c;
    border-bottom: 1px solid #1a1a2e;
    spacing: 4px;
    padding: 2px;
}
QToolButton {
    background: transparent;
    border: 1px solid transparent;
    border-radius: 4px;
    padding: 4px 8px;
    color: #a0a0b0;
}
QToolButton:hover {
    background: #00f5ff15;
    border: 1px solid #00f5ff44;
    color: #00f5ff;
}
QToolButton:pressed {
    background: #00f5ff30;
}
QToolButton:checked {
    background: #00f5ff20;
    border: 1px solid #00f5ff66;
    color: #00f5ff;
}

/* --- Pasek stanu --- */
QStatusBar {
    background-color: #08080a;
    border-top: 1px solid #1a1a2e;
    color: #606070;
    font-size: 11px;
}

/* --- Tabela --- */
QTableView, QTableWidget {
    background-color: #0a0a0c;
    alternate-background-color: #0d0d12;
    gridline-color: #18181e;
    border: 1px solid #1e1e2e;
    selection-background-color: #00f5ff22;
    selection-color: #00f5ff;
}
QTableView::item {
    padding: 4px 8px;
    border: none;
}
QTableView::item:selected {
    background-color: #00f5ff20;
    color: #e0e0e0;
}
QTableView::item:hover {
    background-color: #00f5ff10;
}
QHeaderView::section {
    background-color: #0d0d14;
    color: #00f5ff;
    padding: 5px 8px;
    border: none;
    border-right: 1px solid #1e1e2e;
    border-bottom: 2px solid #00f5ff44;
    font-size: 11px;
    font-weight: bold;
    letter-spacing: 1px;
    text-transform: uppercase;
}
QHeaderView::section:hover {
    background-color: #00f5ff18;
}

/* --- Drzewo --- */
QTreeView, QTreeWidget {
    background-color: #0a0a0c;
    border: 1px solid #1e1e2e;
    selection-background-color: #00f5ff20;
    selection-color: #e0e0e0;
}
QTreeView::item {
    padding: 3px 4px;
}
QTreeView::item:selected {
    background: #00f5ff22;
    color: #00f5ff;
}
QTreeView::item:hover {
    background: #00f5ff12;
}
QTreeView::branch:has-children:!has-siblings:closed,
QTreeView::branch:closed:has-children:has-siblings {
    border-image: none;
    image: url(assets/icons/arrow_right.png);
}
QTreeView::branch:open:has-children:!has-siblings,
QTreeView::branch:open:has-children:has-siblings {
    border-image: none;
    image: url(assets/icons/arrow_down.png);
}

/* --- Przyciski --- */
QPushButton {
    background-color: #15151e;
    color: #c0c0d0;
    border: 1px solid #2a2a3a;
    border-radius: 4px;
    padding: 6px 16px;
    min-width: 80px;
}
QPushButton:hover {
    background-color: #00f5ff18;
    border: 1px solid #00f5ff66;
    color: #00f5ff;
}
QPushButton:pressed {
    background-color: #00f5ff30;
    border: 1px solid #00f5ff99;
}
QPushButton:disabled {
    color: #404040;
    border: 1px solid #1a1a1a;
}
QPushButton[accent="true"] {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #004f4f, stop:1 #007878);
    color: #00f5ff;
    border: 1px solid #00f5ff55;
    font-weight: bold;
}
QPushButton[accent="true"]:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #006060, stop:1 #009090);
    border: 1px solid #00f5ff99;
}

/* --- Pola tekstowe --- */
QLineEdit, QTextEdit, QPlainTextEdit {
    background-color: #0a0a0e;
    border: 1px solid #2a2a3a;
    border-radius: 4px;
    padding: 4px 8px;
    color: #e0e0e0;
    selection-background-color: #00f5ff44;
}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
    border: 1px solid #00f5ff66;
    background-color: #0c0c12;
}
QLineEdit:disabled {
    color: #404050;
    background-color: #0a0a0c;
}

/* --- Combobox --- */
QComboBox {
    background-color: #0f0f16;
    border: 1px solid #2a2a3a;
    border-radius: 4px;
    padding: 4px 8px;
    color: #c0c0d0;
    min-width: 80px;
}
QComboBox:hover {
    border: 1px solid #00f5ff55;
}
QComboBox:focus {
    border: 1px solid #00f5ff77;
}
QComboBox::drop-down {
    border: none;
    width: 20px;
}
QComboBox::down-arrow {
    width: 10px;
    height: 10px;
}
QComboBox QAbstractItemView {
    background-color: #111118;
    border: 1px solid #00f5ff33;
    selection-background-color: #00f5ff25;
    selection-color: #00f5ff;
    outline: none;
}

/* --- Suwaki --- */
QSlider::groove:horizontal {
    height: 4px;
    background: #1e1e2e;
    border-radius: 2px;
}
QSlider::handle:horizontal {
    background: #00f5ff;
    width: 14px;
    height: 14px;
    margin: -5px 0;
    border-radius: 7px;
}
QSlider::handle:horizontal:hover {
    background: #40ffff;
}
QSlider::sub-page:horizontal {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #005060, stop:1 #00c0d0);
    border-radius: 2px;
}

/* --- Scrollbary --- */
QScrollBar:vertical {
    background: #0a0a0c;
    width: 8px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: #2a2a3a;
    min-height: 30px;
    border-radius: 4px;
}
QScrollBar::handle:vertical:hover {
    background: #00f5ff55;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: none;
    height: 0;
}
QScrollBar:horizontal {
    background: #0a0a0c;
    height: 8px;
    margin: 0;
}
QScrollBar::handle:horizontal {
    background: #2a2a3a;
    min-width: 30px;
    border-radius: 4px;
}
QScrollBar::handle:horizontal:hover {
    background: #00f5ff55;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal,
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
    background: none;
    width: 0;
}

/* --- Zakładki --- */
QTabWidget::pane {
    border: 1px solid #1e1e2e;
    background: #0a0a0c;
}
QTabBar::tab {
    background: #0d0d14;
    color: #808090;
    padding: 6px 16px;
    border: 1px solid #1a1a2a;
    border-bottom: none;
    margin-right: 2px;
}
QTabBar::tab:selected {
    background: #0a0a0c;
    color: #00f5ff;
    border-bottom: 2px solid #00f5ff;
}
QTabBar::tab:hover:!selected {
    color: #c0c0d0;
    background: #00f5ff12;
}

/* --- Splitter --- */
QSplitter::handle {
    background: #1a1a2a;
    width: 3px;
    height: 3px;
}
QSplitter::handle:hover {
    background: #00f5ff55;
}

/* --- Grupujące ramki --- */
QGroupBox {
    border: 1px solid #1e1e2e;
    border-radius: 6px;
    margin-top: 8px;
    padding-top: 6px;
    color: #00f5ff;
    font-weight: bold;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 4px;
}

/* --- Pasek postępu --- */
QProgressBar {
    background-color: #0a0a0e;
    border: 1px solid #2a2a3a;
    border-radius: 4px;
    text-align: center;
    color: #00f5ff;
    height: 16px;
}
QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #005060, stop:1 #00c8d8);
    border-radius: 3px;
}

/* --- CheckBox / RadioButton --- */
QCheckBox {
    spacing: 6px;
    color: #c0c0d0;
}
QCheckBox::indicator {
    width: 15px;
    height: 15px;
    border: 1px solid #2a2a3a;
    border-radius: 3px;
    background: #0a0a0c;
}
QCheckBox::indicator:checked {
    background: #00f5ff;
    border: 1px solid #00f5ff;
}
QCheckBox::indicator:hover {
    border: 1px solid #00f5ff77;
}
QRadioButton {
    spacing: 6px;
    color: #c0c0d0;
}
QRadioButton::indicator {
    width: 15px;
    height: 15px;
    border: 1px solid #2a2a3a;
    border-radius: 8px;
    background: #0a0a0c;
}
QRadioButton::indicator:checked {
    background: #00f5ff;
    border: 1px solid #00f5ff;
}

/* --- Tooltips --- */
QToolTip {
    background-color: #111118;
    border: 1px solid #00f5ff44;
    color: #c0c0d0;
    padding: 4px 8px;
    border-radius: 4px;
}

/* --- Dock Widgets --- */
QDockWidget {
    color: #00f5ff;
    font-weight: bold;
}
QDockWidget::title {
    background: #0d0d14;
    padding: 4px 8px;
    border-bottom: 1px solid #1e1e2e;
}

/* --- Spin Box --- */
QSpinBox, QDoubleSpinBox {
    background-color: #0a0a0e;
    border: 1px solid #2a2a3a;
    border-radius: 4px;
    padding: 4px;
    color: #e0e0e0;
}
QSpinBox:focus, QDoubleSpinBox:focus {
    border: 1px solid #00f5ff66;
}
"""
