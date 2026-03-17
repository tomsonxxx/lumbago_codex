from __future__ import annotations


# Kolory design system (zgodne z React UI)
# --bg-primary:    #0a0d1a  (głęboki granatowy)
# --bg-card:       rgba(13, 17, 42, 0.85) → przybliżenie: #0d112a
# --accent-cyan:   #00d4ff
# --accent-purple: #8b5cf6
# --accent-pink:   #ec4899
# --text-primary:  #e6f7ff
# --text-muted:    #94a3b8
# --text-hint:     #64748b
# --border-subtle: rgba(0, 212, 255, 0.15) → #002030 (przybliżenie)

CYBER_QSS = """
QWidget {
    background-color: #0a0d1a;
    color: #e6f7ff;
    font-family: "Segoe UI", "Noto Sans", "Arial";
    font-size: 12px;
}

QDialog, QMainWindow {
    background-color: #0a0d1a;
}

QAbstractButton {
    icon-size: 16px;
}

/* ─── Inputs ─────────────────────────────────────────────────────────────── */
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QTextEdit, QPlainTextEdit {
    background-color: #111827;
    border: 1px solid #1e2d45;
    border-radius: 10px;
    padding: 8px 10px;
    color: #e6f7ff;
    selection-background-color: #1e3f5a;
}
QLineEdit#SearchInput {
    background-color: #0e1525;
    border: 1px solid #1e2d45;
    border-radius: 20px;
    padding: 8px 16px;
    font-size: 13px;
}
QLineEdit#FilterInput, QDoubleSpinBox#FilterSpin, QComboBox#ViewToggle {
    background-color: #0e1525;
    border: 1px solid #1e2d45;
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
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 5px solid #94a3b8;
    margin-right: 6px;
}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus,
QTextEdit:focus, QPlainTextEdit:focus {
    border-color: #00d4ff;
    background-color: #0f1830;
}

/* ─── Buttons ─────────────────────────────────────────────────────────────── */
QPushButton, QToolButton {
    background-color: #131d30;
    border: 1px solid #1e2d45;
    border-radius: 10px;
    padding: 8px 14px;
    color: #94a3b8;
}
QPushButton:hover, QToolButton:hover {
    border-color: #00d4ff;
    color: #e6f7ff;
    background-color: #162030;
}
QPushButton:pressed, QToolButton:pressed {
    background-color: #0e1828;
}
QPushButton:disabled, QToolButton:disabled {
    opacity: 0.4;
    color: #64748b;
}

QPushButton#PrimaryAction {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #ec4899, stop:1 #8b5cf6);
    color: #ffffff;
    border: none;
    font-weight: 700;
    border-radius: 10px;
    padding: 9px 18px;
}
QPushButton#PrimaryAction:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #f472b6, stop:1 #a78bfa);
}
QPushButton#AutoTagApi {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #00d4ff, stop:1 #8b5cf6);
    color: #0a0d1a;
    border: none;
    font-weight: 700;
}
QPushButton#AutoTagSearch {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #ec4899, stop:1 #8b5cf6);
    color: #ffffff;
    border: none;
    font-weight: 700;
}
QPushButton#DangerAction {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #ef4444, stop:1 #ec4899);
    color: #ffffff;
    border: none;
    font-weight: 700;
}

/* ─── Nav Sidebar ─────────────────────────────────────────────────────────── */
QFrame#NavSidebar {
    background-color: #080b18;
    border-right: 1px solid rgba(0, 212, 255, 0.1);
    border-radius: 0px;
}
QPushButton#NavItem {
    background-color: transparent;
    border: none;
    border-radius: 10px;
    padding: 10px;
    color: #64748b;
}
QPushButton#NavItem:hover {
    background-color: rgba(0, 212, 255, 0.08);
    color: #94a3b8;
}
QPushButton#NavItemActive {
    background-color: rgba(0, 212, 255, 0.12);
    border: none;
    border-left: 3px solid #00d4ff;
    border-radius: 0px 10px 10px 0px;
    padding: 10px;
    color: #00d4ff;
}
QPushButton#NavItemActive:hover {
    background-color: rgba(0, 212, 255, 0.16);
}

/* ─── TopBar ──────────────────────────────────────────────────────────────── */
QFrame#TopBar {
    background-color: #080b18;
    border-bottom: 1px solid rgba(0, 212, 255, 0.08);
    border-radius: 0px;
}

/* ─── Player bar ──────────────────────────────────────────────────────────── */
QFrame#PlayerDock {
    background-color: #090c1c;
    border-top: 1px solid rgba(0, 212, 255, 0.12);
    border-radius: 0px;
}

/* ─── Cards / panels ──────────────────────────────────────────────────────── */
QFrame#Card {
    background-color: #0d112a;
    border: 1px solid rgba(0, 212, 255, 0.12);
    border-radius: 16px;
}
QFrame#CardPurple {
    background-color: #0d112a;
    border: 1px solid rgba(139, 92, 246, 0.2);
    border-radius: 16px;
}
QFrame#DialogCard {
    background-color: #0d112a;
    border: 1px solid rgba(0, 212, 255, 0.12);
    border-radius: 16px;
}
QFrame#Sidebar {
    background-color: #080b18;
    border-right: 1px solid rgba(0, 212, 255, 0.1);
    border-radius: 0px;
}
QFrame#DetailPanel {
    background-color: #080b18;
    border-left: 1px solid rgba(0, 212, 255, 0.1);
    border-radius: 0px;
}
QFrame#HeaderBar {
    background-color: #0b0f1f;
    border: 1px solid rgba(0, 212, 255, 0.1);
    border-radius: 14px;
}
QFrame#Toolbar {
    background-color: #0b0f1f;
    border: 1px solid rgba(0, 212, 255, 0.1);
    border-radius: 14px;
}

/* ─── Labels ──────────────────────────────────────────────────────────────── */
QLabel#SectionTitle {
    color: #00d4ff;
    font-weight: 700;
    font-size: 13px;
    letter-spacing: 0.3px;
}
QLabel#DialogTitle {
    color: #e6f7ff;
    font-weight: 700;
    font-size: 16px;
    padding: 2px 0 6px 0;
}
QLabel#HintLabel {
    color: #64748b;
    font-size: 11px;
}
QLabel#DialogHint {
    color: #64748b;
    font-size: 11px;
    padding: 2px;
}
QLabel#ModePill {
    background-color: #0e1525;
    border: 1px solid #1e2d45;
    border-radius: 12px;
    padding: 4px 10px;
    color: #94a3b8;
    font-size: 11px;
}
QLabel#ModePill[mode="api"] {
    border-color: #00d4ff;
    color: #00d4ff;
}
QLabel#ModePill[mode="mixed"] {
    border-color: #ec4899;
    color: #ec4899;
}
QLabel#StatValue {
    color: #00d4ff;
    font-weight: 700;
    font-size: 22px;
}
QLabel#StatLabel {
    color: #64748b;
    font-size: 11px;
}

/* ─── Table / List ────────────────────────────────────────────────────────── */
QHeaderView::section {
    background-color: #0b0f22;
    border: 1px solid #1a2236;
    padding: 8px;
    color: #94a3b8;
    font-size: 11px;
    font-weight: 600;
}
QHeaderView::section:hover {
    border-color: #00d4ff;
    color: #e6f7ff;
}

QTableView, QTreeView {
    background-color: #0a0d1a;
    gridline-color: #1a2236;
    selection-background-color: rgba(0, 212, 255, 0.1);
    selection-color: #e6f7ff;
    border: none;
    border-radius: 0px;
    alternate-background-color: #0d1020;
}
QTableView::item:selected, QTreeView::item:selected {
    background-color: rgba(0, 212, 255, 0.1);
    color: #e6f7ff;
}
QTableView::item:hover, QTreeView::item:hover {
    background-color: rgba(0, 212, 255, 0.05);
}

QListView {
    background-color: #0a0d1a;
    border: none;
    border-radius: 0px;
}
QListView::item:selected {
    background-color: rgba(0, 212, 255, 0.1);
    color: #e6f7ff;
}
QListView::item:hover {
    background-color: rgba(0, 212, 255, 0.05);
}

QTreeWidget {
    background-color: #0a0d1a;
    border: none;
}
QTreeWidget::item:selected {
    background-color: rgba(0, 212, 255, 0.1);
    color: #00d4ff;
}
QTreeWidget::item:hover {
    background-color: rgba(0, 212, 255, 0.05);
}

/* ─── Tabs ────────────────────────────────────────────────────────────────── */
QTabWidget::pane {
    border: 1px solid #1a2236;
    border-radius: 12px;
    padding: 6px;
    background-color: #0d112a;
}
QTabBar::tab {
    background-color: #0e1525;
    border: 1px solid #1a2236;
    border-radius: 8px;
    padding: 7px 14px;
    margin-right: 4px;
    color: #64748b;
}
QTabBar::tab:hover {
    border-color: #00d4ff;
    color: #94a3b8;
}
QTabBar::tab:selected {
    border-color: #00d4ff;
    color: #00d4ff;
    background-color: rgba(0, 212, 255, 0.08);
}

/* ─── Slider ──────────────────────────────────────────────────────────────── */
QSlider::groove:horizontal {
    background: #1a2236;
    height: 6px;
    border-radius: 3px;
}
QSlider::sub-page:horizontal {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00d4ff, stop:1 #8b5cf6);
    border-radius: 3px;
}
QSlider::add-page:horizontal {
    background: #1a2236;
    border-radius: 3px;
}
QSlider::handle:horizontal {
    background: #e6f7ff;
    border: 2px solid #00d4ff;
    width: 14px;
    margin: -5px 0;
    border-radius: 7px;
}
QSlider::groove:vertical {
    width: 6px;
    background: #1a2236;
    border-radius: 3px;
}
QSlider::handle:vertical {
    height: 14px;
    margin: 0 -5px;
    border-radius: 7px;
    background: #00d4ff;
    border: 2px solid #e6f7ff;
}

/* ─── Progress bar ────────────────────────────────────────────────────────── */
QProgressBar {
    background-color: #111827;
    border: 1px solid #1a2236;
    border-radius: 8px;
    text-align: center;
    color: #94a3b8;
    font-size: 11px;
}
QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00d4ff, stop:1 #8b5cf6);
    border-radius: 8px;
}

/* ─── Scrollbar ───────────────────────────────────────────────────────────── */
QScrollBar:vertical {
    background: #0a0d1a;
    width: 8px;
    margin: 2px;
}
QScrollBar::handle:vertical {
    background: #1a2236;
    border-radius: 4px;
    min-height: 20px;
}
QScrollBar::handle:vertical:hover {
    background: #00d4ff;
}
QScrollBar:horizontal {
    background: #0a0d1a;
    height: 8px;
    margin: 2px;
}
QScrollBar::handle:horizontal {
    background: #1a2236;
    border-radius: 4px;
    min-width: 20px;
}
QScrollBar::handle:horizontal:hover {
    background: #00d4ff;
}
QScrollBar::add-line, QScrollBar::sub-line { width: 0; height: 0; }

/* ─── Checkboxes / Radio ──────────────────────────────────────────────────── */
QCheckBox, QRadioButton { spacing: 8px; }
QCheckBox::indicator, QRadioButton::indicator { width: 16px; height: 16px; }
QCheckBox::indicator {
    border: 1px solid #1e2d45;
    border-radius: 4px;
    background: #0e1525;
}
QCheckBox::indicator:checked {
    background: #00d4ff;
    border-color: #00b8db;
}
QRadioButton::indicator {
    border: 1px solid #1e2d45;
    border-radius: 8px;
    background: #0e1525;
}
QRadioButton::indicator:checked {
    background: #00d4ff;
    border-color: #00b8db;
}

/* ─── Splitter / Group ────────────────────────────────────────────────────── */
QSplitter::handle { background: #1a2236; }
QGroupBox {
    border: 1px solid #1a2236;
    border-radius: 12px;
    margin-top: 10px;
    padding: 10px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 6px;
    color: #94a3b8;
}

/* ─── Menu / Tooltip ──────────────────────────────────────────────────────── */
QMenu {
    background-color: #0d112a;
    border: 1px solid #1a2236;
    padding: 6px;
    border-radius: 10px;
}
QMenu::item { padding: 6px 16px; border-radius: 6px; }
QMenu::item:selected {
    background-color: rgba(0, 212, 255, 0.1);
    color: #00d4ff;
}
QMenu::separator { height: 1px; background: #1a2236; margin: 4px 8px; }

QToolTip {
    background-color: #0d112a;
    color: #e6f7ff;
    border: 1px solid rgba(0, 212, 255, 0.2);
    padding: 6px 10px;
    border-radius: 8px;
    font-size: 11px;
}

/* ─── Toolbar / Status ────────────────────────────────────────────────────── */
QToolBar {
    background-color: #080b18;
    border-bottom: 1px solid #1a2236;
    spacing: 6px;
}
QStatusBar {
    background-color: #060910;
    border-top: 1px solid rgba(0, 212, 255, 0.08);
    color: #64748b;
    font-size: 11px;
}

/* ─── MessageBox ──────────────────────────────────────────────────────────── */
QMessageBox { background-color: #0d112a; }
QMessageBox QLabel { color: #e6f7ff; }
"""

MINIMAL_DARK_QSS = """
QWidget {
    background-color: #1e1e1e;
    color: #d4d4d4;
    font-family: "Segoe UI", "Noto Sans", "Arial";
    font-size: 12px;
}
QDialog, QMainWindow {
    background-color: #1e1e1e;
}
QAbstractButton { icon-size: 16px; }
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QTextEdit, QPlainTextEdit {
    background-color: #252526;
    border: 1px solid #3c3c3c;
    border-radius: 6px;
    padding: 6px 8px;
    selection-background-color: #264f78;
}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus, QTextEdit:focus {
    border-color: #569cd6;
}
QPushButton, QToolButton {
    background-color: #2d2d2d;
    border: 1px solid #3c3c3c;
    border-radius: 6px;
    padding: 6px 12px;
    color: #d4d4d4;
}
QPushButton:hover, QToolButton:hover {
    background-color: #3c3c3c;
    border-color: #569cd6;
}
QPushButton:pressed, QToolButton:pressed { background-color: #264f78; }
QPushButton#PrimaryAction {
    background-color: #0e639c;
    color: #fff;
    border-color: #1177bb;
    font-weight: 600;
}
QPushButton#PrimaryAction:hover { background-color: #1177bb; }
QPushButton#DangerAction {
    background-color: #6e1f1f;
    color: #f48771;
    border-color: #8b3333;
    font-weight: 600;
}
QLabel#SectionTitle { color: #569cd6; font-weight: 700; font-size: 13px; }
QLabel#DialogTitle { color: #d4d4d4; font-weight: 700; font-size: 16px; padding: 2px 0 6px 0; }
QLabel#ModePill { background-color: #252526; border: 1px solid #3c3c3c; border-radius: 8px; padding: 3px 8px; }
QFrame { border-radius: 8px; }
QFrame#Card { background-color: #252526; border: 1px solid #3c3c3c; border-radius: 8px; }
QFrame#DialogCard { background-color: #252526; border: 1px solid #3c3c3c; border-radius: 10px; }
QFrame#Toolbar { background-color: #2d2d2d; border-bottom: 1px solid #3c3c3c; border-radius: 0px; }
QFrame#Sidebar { background-color: #252526; border-right: 1px solid #3c3c3c; border-radius: 0px; }
QFrame#PlayerDock { background-color: #252526; border-top: 1px solid #3c3c3c; border-radius: 0px; }
QTableView, QTableWidget, QListView, QListWidget, QTreeView, QTreeWidget {
    background-color: #1e1e1e;
    alternate-background-color: #252526;
    gridline-color: #2d2d2d;
    border: 1px solid #3c3c3c;
    border-radius: 4px;
}
QTableView::item:selected, QTableWidget::item:selected,
QListView::item:selected, QListWidget::item:selected {
    background-color: #264f78;
    color: #fff;
}
QHeaderView::section {
    background-color: #2d2d2d;
    border: none;
    border-right: 1px solid #3c3c3c;
    border-bottom: 1px solid #3c3c3c;
    padding: 4px 8px;
}
QScrollBar:vertical { background-color: #1e1e1e; width: 10px; }
QScrollBar::handle:vertical { background-color: #424242; border-radius: 5px; min-height: 20px; }
QScrollBar::handle:vertical:hover { background-color: #569cd6; }
QScrollBar:horizontal { background-color: #1e1e1e; height: 10px; }
QScrollBar::handle:horizontal { background-color: #424242; border-radius: 5px; min-width: 20px; }
QTabWidget::pane { border: 1px solid #3c3c3c; background-color: #252526; }
QTabBar::tab { background-color: #2d2d2d; border: 1px solid #3c3c3c; padding: 6px 14px; }
QTabBar::tab:selected { background-color: #252526; border-bottom: none; color: #569cd6; }
QStatusBar { background-color: #007acc; color: #fff; border-top: 1px solid #005f9e; }
QProgressBar { background-color: #252526; border: 1px solid #3c3c3c; border-radius: 4px; height: 8px; text-align: center; }
QProgressBar::chunk { background-color: #0e639c; border-radius: 4px; }
QMenuBar { background-color: #2d2d2d; }
QMenuBar::item:selected { background-color: #3c3c3c; }
QMenu { background-color: #252526; border: 1px solid #454545; }
QMenu::item:selected { background-color: #094771; }
QMessageBox { background-color: #252526; }
QMessageBox QLabel { color: #d4d4d4; }
"""


def get_qss(theme_name: str = "cyber") -> str:
    """Zwraca arkusz QSS dla podanego motywu. Dostępne: 'cyber', 'minimal_dark'."""
    if theme_name == "minimal_dark":
        return MINIMAL_DARK_QSS
    return CYBER_QSS
