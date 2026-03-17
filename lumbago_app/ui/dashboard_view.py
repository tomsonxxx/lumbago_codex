"""Dashboard — główny widok startowy Lumbago Music AI.

Zawiera: statystyki biblioteki, szybkie akcje, ostatnią aktywność.
"""
from __future__ import annotations

from datetime import datetime
from typing import Callable

from PyQt6 import QtCore, QtGui, QtWidgets


def _time_ago(ts: float) -> str:
    """Zwraca opis czasu w formie 'x minut temu', 'x godz. temu', itp."""
    delta = datetime.now().timestamp() - ts
    if delta < 60:
        return "przed chwilą"
    if delta < 3600:
        m = int(delta / 60)
        return f"{m} min temu"
    if delta < 86400:
        h = int(delta / 3600)
        return f"{h} godz. temu"
    d = int(delta / 86400)
    return f"{d} dni temu"


class _StatCard(QtWidgets.QFrame):
    """Karta ze statystyką (liczba + opis)."""

    def __init__(self, value: str, label: str, color: str = "#00d4ff", parent=None):
        super().__init__(parent)
        self.setObjectName("Card")
        self.setMinimumWidth(140)
        lay = QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(20, 18, 20, 18)
        lay.setSpacing(4)

        val_lbl = QtWidgets.QLabel(value)
        val_lbl.setObjectName("StatValue")
        val_lbl.setStyleSheet(f"color: {color}; font-size: 26px; font-weight: 700;")
        val_lbl.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)

        desc_lbl = QtWidgets.QLabel(label)
        desc_lbl.setObjectName("StatLabel")
        desc_lbl.setStyleSheet("color: #64748b; font-size: 11px;")

        lay.addWidget(val_lbl)
        lay.addWidget(desc_lbl)


class _QuickActionBtn(QtWidgets.QPushButton):
    """Przycisk szybkiej akcji (ikona + tekst)."""

    def __init__(self, icon_text: str, label: str, color: str = "#00d4ff", parent=None):
        super().__init__(parent)
        self.setFixedHeight(44)
        lay = QtWidgets.QHBoxLayout(self)
        lay.setContentsMargins(14, 0, 14, 0)
        lay.setSpacing(10)

        icon_lbl = QtWidgets.QLabel(icon_text)
        icon_lbl.setStyleSheet(f"color: {color}; font-size: 16px; background: transparent;")
        text_lbl = QtWidgets.QLabel(label)
        text_lbl.setStyleSheet("color: #e6f7ff; font-size: 13px; background: transparent;")
        arrow_lbl = QtWidgets.QLabel("›")
        arrow_lbl.setStyleSheet("color: #64748b; font-size: 16px; background: transparent;")

        lay.addWidget(icon_lbl)
        lay.addWidget(text_lbl, 1)
        lay.addWidget(arrow_lbl)

        self.setStyleSheet("""
            QPushButton {
                background-color: #111827;
                border: 1px solid #1e2d45;
                border-radius: 10px;
            }
            QPushButton:hover {
                border-color: #00d4ff;
                background-color: #131f30;
            }
            QPushButton:pressed {
                background-color: #0e1828;
            }
        """)


class _ActivityItem(QtWidgets.QWidget):
    """Jeden wpis aktywności (ikona + opis + czas)."""

    _ICONS = {
        "import": ("📥", "#00d4ff"),
        "ai_tag": ("🤖", "#8b5cf6"),
        "duplicate_found": ("🔍", "#f59e0b"),
        "tags_edited": ("✏️", "#4ade80"),
        "export": ("📤", "#ec4899"),
    }

    def __init__(self, entry: dict, parent=None):
        super().__init__(parent)
        lay = QtWidgets.QHBoxLayout(self)
        lay.setContentsMargins(12, 8, 12, 8)
        lay.setSpacing(10)

        entry_type = entry.get("type", "import")
        icon_text, color = self._ICONS.get(entry_type, ("📌", "#94a3b8"))

        icon_lbl = QtWidgets.QLabel(icon_text)
        icon_lbl.setFixedWidth(24)
        icon_lbl.setStyleSheet(f"font-size: 15px; color: {color};")

        msg_lbl = QtWidgets.QLabel(entry.get("message", ""))
        msg_lbl.setStyleSheet("color: #94a3b8; font-size: 12px;")
        msg_lbl.setWordWrap(True)

        ts = entry.get("timestamp", 0)
        time_lbl = QtWidgets.QLabel(_time_ago(ts))
        time_lbl.setStyleSheet("color: #64748b; font-size: 11px;")
        time_lbl.setFixedWidth(90)
        time_lbl.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter)

        lay.addWidget(icon_lbl)
        lay.addWidget(msg_lbl, 1)
        lay.addWidget(time_lbl)

        self.setStyleSheet("""
            QWidget { border-bottom: 1px solid rgba(0,212,255,0.06); }
            QWidget:hover { background-color: rgba(0,212,255,0.03); border-radius: 8px; }
        """)


class DashboardView(QtWidgets.QWidget):
    """Widok Dashboard — strona główna aplikacji."""

    # Sygnały do nawigacji
    navigate_to = QtCore.pyqtSignal(str)  # emituje np. 'library', 'import', 'duplicates'

    def __init__(self, parent=None):
        super().__init__(parent)
        self._activity_log: list[dict] = []
        self._stats = {"tracks": 0, "imports": 0, "ai_tags": 0, "exports": 0}
        self._build_ui()

    def _build_ui(self):
        scroll = QtWidgets.QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        container = QtWidgets.QWidget()
        scroll.setWidget(container)

        outer = QtWidgets.QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

        lay = QtWidgets.QVBoxLayout(container)
        lay.setContentsMargins(32, 28, 32, 28)
        lay.setSpacing(24)

        # ── Nagłówek ──────────────────────────────────────────────────────────
        header_lbl = QtWidgets.QLabel("Witaj w <span style='color:#00d4ff;'>Lumbago Music AI</span>")
        header_lbl.setTextFormat(QtCore.Qt.TextFormat.RichText)
        header_lbl.setStyleSheet("font-size: 24px; font-weight: 700; color: #e6f7ff;")
        sub_lbl = QtWidgets.QLabel("Zacznij od zaimportowania plików muzycznych")
        sub_lbl.setStyleSheet("color: #64748b; font-size: 13px;")
        lay.addWidget(header_lbl)
        lay.addWidget(sub_lbl)

        # ── Statystyki ────────────────────────────────────────────────────────
        stats_row = QtWidgets.QHBoxLayout()
        stats_row.setSpacing(16)
        self._stat_tracks = _StatCard("0", "Pliki w bibliotece", "#00d4ff")
        self._stat_imports = _StatCard("0", "Importów łącznie", "#8b5cf6")
        self._stat_ai = _StatCard("0", "Otagowanych AI", "#4ade80")
        self._stat_exports = _StatCard("0", "Eksportów", "#ec4899")
        for card in (self._stat_tracks, self._stat_imports, self._stat_ai, self._stat_exports):
            stats_row.addWidget(card)
        stats_row.addStretch(1)
        lay.addLayout(stats_row)

        # ── Trzy karty akcji ─────────────────────────────────────────────────
        cards_row = QtWidgets.QHBoxLayout()
        cards_row.setSpacing(16)

        # Karta 1: Nowy Utwór
        card1 = QtWidgets.QFrame()
        card1.setObjectName("Card")
        c1lay = QtWidgets.QVBoxLayout(card1)
        c1lay.setContentsMargins(20, 18, 20, 18)
        c1lay.setSpacing(12)
        c1title = QtWidgets.QLabel("📁  Importuj muzykę")
        c1title.setStyleSheet("color: #e6f7ff; font-size: 14px; font-weight: 600;")
        c1desc = QtWidgets.QLabel("Importuj pliki MP3, FLAC, WAV, OGG z dysku lub folderu.")
        c1desc.setStyleSheet("color: #64748b; font-size: 11px;")
        c1desc.setWordWrap(True)
        c1btn = QtWidgets.QPushButton("Importuj pliki")
        c1btn.setObjectName("PrimaryAction")
        c1btn.clicked.connect(lambda: self.navigate_to.emit("import"))
        c1lay.addWidget(c1title)
        c1lay.addWidget(c1desc)
        c1lay.addWidget(c1btn)

        # Karta 2: AI Tagger
        card2 = QtWidgets.QFrame()
        card2.setObjectName("CardPurple")
        c2lay = QtWidgets.QVBoxLayout(card2)
        c2lay.setContentsMargins(20, 18, 20, 18)
        c2lay.setSpacing(12)
        c2title = QtWidgets.QLabel("🤖  AI Tagger")
        c2title.setStyleSheet("color: #e6f7ff; font-size: 14px; font-weight: 600;")
        c2desc = QtWidgets.QLabel("Automatycznie uzupełnij tagi BPM, tonację, gatunek przez AI.")
        c2desc.setStyleSheet("color: #64748b; font-size: 11px;")
        c2desc.setWordWrap(True)
        c2btn = QtWidgets.QPushButton("Otwórz AI Tagger")
        c2btn.setObjectName("AutoTagApi")
        c2btn.clicked.connect(lambda: self.navigate_to.emit("tagger"))
        c2lay.addWidget(c2title)
        c2lay.addWidget(c2desc)
        c2lay.addWidget(c2btn)

        # Karta 3: Szybkie akcje
        card3 = QtWidgets.QFrame()
        card3.setObjectName("Card")
        c3lay = QtWidgets.QVBoxLayout(card3)
        c3lay.setContentsMargins(20, 18, 20, 18)
        c3lay.setSpacing(8)
        c3title = QtWidgets.QLabel("⚡  Szybkie akcje")
        c3title.setStyleSheet("color: #e6f7ff; font-size: 14px; font-weight: 600;")
        c3lay.addWidget(c3title)

        for icon, label, view, color in [
            ("📚", "Biblioteka", "library", "#00d4ff"),
            ("🔍", "Duplikaty", "duplicates", "#f59e0b"),
            ("🎵", "Odtwarzacz", "player", "#4ade80"),
            ("⚙️", "Ustawienia", "settings", "#8b5cf6"),
        ]:
            btn = _QuickActionBtn(icon, label, color)
            btn.clicked.connect(lambda _, v=view: self.navigate_to.emit(v))
            c3lay.addWidget(btn)

        cards_row.addWidget(card1)
        cards_row.addWidget(card2)
        cards_row.addWidget(card3)
        lay.addLayout(cards_row)

        # ── Ostatnia aktywność ────────────────────────────────────────────────
        activity_frame = QtWidgets.QFrame()
        activity_frame.setObjectName("Card")
        alay = QtWidgets.QVBoxLayout(activity_frame)
        alay.setContentsMargins(20, 16, 20, 16)
        alay.setSpacing(0)

        a_header = QtWidgets.QHBoxLayout()
        a_title = QtWidgets.QLabel("Ostatnia aktywność")
        a_title.setObjectName("SectionTitle")
        a_header.addWidget(a_title)
        a_header.addStretch(1)
        alay.addLayout(a_header)
        alay.addSpacing(10)

        self._activity_container = QtWidgets.QWidget()
        self._activity_layout = QtWidgets.QVBoxLayout(self._activity_container)
        self._activity_layout.setContentsMargins(0, 0, 0, 0)
        self._activity_layout.setSpacing(0)

        self._empty_lbl = QtWidgets.QLabel("Brak aktywności. Zaimportuj pliki aby zacząć.")
        self._empty_lbl.setStyleSheet("color: #64748b; font-size: 12px; padding: 20px;")
        self._empty_lbl.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self._activity_layout.addWidget(self._empty_lbl)

        alay.addWidget(self._activity_container)
        lay.addWidget(activity_frame)
        lay.addStretch(1)

    def update_stats(self, track_count: int, activity_log: list[dict]):
        """Odśwież statystyki i log aktywności."""
        self._activity_log = activity_log

        imports = sum(1 for e in activity_log if e.get("type") == "import")
        ai_tags = sum(1 for e in activity_log if e.get("type") == "ai_tag")
        exports = sum(1 for e in activity_log if e.get("type") == "export")

        self._stat_tracks._find_val_label().setText(str(track_count))
        self._stat_imports._find_val_label().setText(str(imports))
        self._stat_ai._find_val_label().setText(str(ai_tags))
        self._stat_exports._find_val_label().setText(str(exports))

        # Odśwież aktywność
        while self._activity_layout.count():
            item = self._activity_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not activity_log:
            self._activity_layout.addWidget(self._empty_lbl)
            return

        for entry in reversed(activity_log[-15:]):
            item_widget = _ActivityItem(entry)
            self._activity_layout.addWidget(item_widget)


# Patch _StatCard aby udostępniała label wartości
def _find_val_label(self: _StatCard) -> QtWidgets.QLabel:
    for i in range(self.layout().count()):
        item = self.layout().itemAt(i)
        if item and item.widget() and isinstance(item.widget(), QtWidgets.QLabel):
            if item.widget().objectName() == "StatValue" or "font-size: 26px" in item.widget().styleSheet():
                return item.widget()
    return QtWidgets.QLabel()  # fallback


_StatCard._find_val_label = _find_val_label
