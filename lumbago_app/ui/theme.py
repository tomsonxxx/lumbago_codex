from __future__ import annotations


CYBER_QSS = """
QWidget {
    background-color: #0b0f16;
    color: #e8f3ff;
    font-family: Segoe UI;
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

QFrame {
    border-radius: 16px;
}
QFrame#Card {
    background-color: #101522;
    border: 1px solid #1f2a3d;
    border-radius: 14px;
}
QFrame#DialogCard {
    background-color: #0f1322;
    border: 1px solid #1f2a3d;
    border-radius: 16px;
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
    background-color: #16273a;
}

QListView {
    background-color: #0f1322;
    border-radius: 12px;
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
    background-color: #0f1322;
    border-right: 1px solid #1f2a3d;
}
QFrame#DetailPanel {
    background-color: #0f1322;
    border-left: 1px solid #1f2a3d;
}
QFrame#PlayerDock {
    background-color: #0f1322;
    border-top: 1px solid #1f2a3d;
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
