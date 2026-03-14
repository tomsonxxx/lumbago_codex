from __future__ import annotations


CYBER_QSS = """
QWidget {
    background-color: #0a0a0f;
    color: #e8f8ff;
    font-family: Segoe UI;
    font-size: 12px;
}
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {
    background-color: #141826;
    border: 1px solid #2a2f44;
    border-radius: 12px;
    padding: 8px;
}
QPushButton {
    background-color: #101522;
    border: 1px solid #2b3a55;
    border-radius: 14px;
    padding: 8px 12px;
}
QPushButton:hover {
    border-color: #39ff14;
}
QPushButton#PrimaryAction {
    background-color: #102b24;
    border-color: #39ff14;
}
QLabel#SectionTitle {
    color: #8ef0ff;
    font-weight: bold;
    font-size: 13px;
}
QFrame {
    border-radius: 16px;
}
QHeaderView::section {
    background-color: #121826;
    border: 1px solid #1f2a3d;
    padding: 8px;
}
QTableView {
    gridline-color: #1f2a3d;
    selection-background-color: #153d5b;
    border-radius: 12px;
}
QListView {
    background-color: #0e1220;
    border-radius: 12px;
}
QFrame#Sidebar {
    background-color: #101522;
    border-right: 1px solid #1f2a3d;
}
QFrame#DetailPanel {
    background-color: #101522;
    border-left: 1px solid #1f2a3d;
}
QFrame#PlayerDock {
    background-color: #101522;
    border-top: 1px solid #1f2a3d;
}
"""
