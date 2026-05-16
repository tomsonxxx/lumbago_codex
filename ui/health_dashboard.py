"""Health Report Dashboard dla Lumbago_Music."""
from __future__ import annotations
import logging
from typing import TYPE_CHECKING
from PyQt6 import QtCore, QtGui, QtWidgets

if TYPE_CHECKING:
    from core.models import Track

logger = logging.getLogger(__name__)


class FieldBar(QtWidgets.QWidget):
    action_requested = QtCore.pyqtSignal(str)

    def __init__(self, field, label, icon, parent=None):
        super().__init__(parent); self.field = field
        layout = QtWidgets.QHBoxLayout(self); layout.setContentsMargins(0,2,0,2); layout.setSpacing(8)
        li = QtWidgets.QLabel(icon); li.setFixedWidth(20); layout.addWidget(li)
        ln = QtWidgets.QLabel(label); ln.setFixedWidth(80); ln.setStyleSheet("color:#8fb8d8;font-size:11px;"); layout.addWidget(ln)
        self.progress = QtWidgets.QProgressBar(); self.progress.setRange(0,100); self.progress.setFixedHeight(12); self.progress.setTextVisible(False); layout.addWidget(self.progress, stretch=1)
        self.lbl_pct = QtWidgets.QLabel("—"); self.lbl_pct.setFixedWidth(45); self.lbl_pct.setStyleSheet("font-size:11px;color:#e8f3ff;"); layout.addWidget(self.lbl_pct)
        self.btn_fix = QtWidgets.QPushButton("Napraw"); self.btn_fix.setFixedSize(60,20); self.btn_fix.setStyleSheet("font-size:10px;")
        self.btn_fix.clicked.connect(lambda: self.action_requested.emit(self.field)); layout.addWidget(self.btn_fix)

    def update_value(self, pct: float, missing: int):
        self.progress.setValue(int(pct)); self.lbl_pct.setText(f"{pct:.0f}%"); self.btn_fix.setVisible(missing > 0)
        color = "#39ff14" if pct >= 90 else ("#ffaa00" if pct >= 60 else "#ff4f4f")
        self.progress.setStyleSheet(f"QProgressBar{{background:#1e2d42;border-radius:6px;}}QProgressBar::chunk{{background:{color};border-radius:6px;}}")


class HealthReportDashboard(QtWidgets.QDialog):
    action_requested = QtCore.pyqtSignal(str)

    FIELD_DEFS = [("bpm","BPM","🎵"),("key","Klucz","🔑"),("genre","Gatunek","🎸"),
                  ("artwork","Okładka","🖼"),("mood","Nastrój","😊"),("energy","Energia","⚡"),
                  ("year","Rok","📅"),("rating","Rating","★")]

    def __init__(self, tracks: list, parent=None):
        super().__init__(parent); self.setWindowTitle("Raport zdrowia biblioteki")
        self.setMinimumSize(500,560); self.setModal(True)
        self._tracks = tracks; self._stats = self._compute_stats()
        self._bars: dict[str,FieldBar] = {}; self._build_ui()

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self); layout.setSpacing(12); layout.setContentsMargins(20,16,20,16)

        title = QtWidgets.QLabel("📊  Raport zdrowia biblioteki")
        title.setStyleSheet("font-size:16px;font-weight:bold;color:#e8f3ff;"); layout.addWidget(title)

        stats_frame = QtWidgets.QFrame(); stats_frame.setProperty("card",True)
        sl = QtWidgets.QHBoxLayout(stats_frame); sl.setContentsMargins(12,10,12,10)
        total = self._stats.get("total",0); score = self._stats.get("overall_score",0)
        dur_h = sum((t.duration or 0) for t in self._tracks) / 3600
        for icon, val, lbl in [("🎵",str(total),"tracków"),("⏱",f"{dur_h:.1f}h","łączny czas"),("💯",f"{score:.0f}%","wynik zdrowia")]:
            col = QtWidgets.QVBoxLayout()
            lv = QtWidgets.QLabel(val); lv.setStyleSheet("font-size:20px;font-weight:bold;color:#63f2ff;"); lv.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            ls = QtWidgets.QLabel(f"{icon} {lbl}"); ls.setStyleSheet("font-size:10px;color:#8fb8d8;"); ls.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            col.addWidget(lv); col.addWidget(ls); sl.addLayout(col)
        layout.addWidget(stats_frame)

        layout.addWidget(self._sep("Kompletność pól"))
        ff = QtWidgets.QFrame(); ff.setProperty("card",True)
        fl = QtWidgets.QVBoxLayout(ff); fl.setContentsMargins(12,10,12,10); fl.setSpacing(4)
        fstats = self._stats.get("fields",{})
        for field, label, icon in self.FIELD_DEFS:
            bar = FieldBar(field, label, icon)
            bar.action_requested.connect(self._on_action)
            self._bars[field] = bar
            fs = fstats.get(field,{})
            bar.update_value(fs.get("pct",0), fs.get("missing",0))
            fl.addWidget(bar)
        layout.addWidget(ff)

        layout.addWidget(self._sep("Szybkie akcje"))
        al = QtWidgets.QHBoxLayout()
        for txt, key in [("🎵 Analizuj BPM","fix_bpm"),("🤖 AI Tagger","run_ai"),("🔍 Duplikaty","find_duplicates"),("🖼 Okładki","fix_artwork")]:
            btn = QtWidgets.QPushButton(txt); btn.clicked.connect(lambda _,k=key: (self.action_requested.emit(k), self.accept()))
            al.addWidget(btn)
        layout.addLayout(al)

        bc = QtWidgets.QPushButton("Zamknij"); bc.setFixedWidth(100); bc.clicked.connect(self.reject)
        layout.addWidget(bc, alignment=QtCore.Qt.AlignmentFlag.AlignRight)

    def _compute_stats(self) -> dict:
        try:
            from services.fuzzy_dedup import FuzzyDedupService
            return FuzzyDedupService().compute_health_stats(self._tracks)
        except Exception as exc:
            logger.warning("health_stats error: %s", exc); return {"total":len(self._tracks),"fields":{},"overall_score":0}

    def _on_action(self, field: str):
        am = {"bpm":"fix_bpm","key":"fix_key","genre":"run_ai","artwork":"fix_artwork","mood":"run_ai","energy":"run_ai"}
        self.action_requested.emit(am.get(field, f"fix_{field}")); self.accept()

    @staticmethod
    def _sep(text: str) -> QtWidgets.QWidget:
        f = QtWidgets.QFrame(); l = QtWidgets.QHBoxLayout(f); l.setContentsMargins(0,4,0,4)
        l1 = QtWidgets.QFrame(); l1.setFrameShape(QtWidgets.QFrame.Shape.HLine); l1.setStyleSheet("color:#1e2d42;")
        lb = QtWidgets.QLabel(text); lb.setStyleSheet("color:#4a6080;font-size:10px;font-weight:bold;padding:0 8px;")
        l2 = QtWidgets.QFrame(); l2.setFrameShape(QtWidgets.QFrame.Shape.HLine); l2.setStyleSheet("color:#1e2d42;")
        l.addWidget(l1,stretch=1); l.addWidget(lb); l.addWidget(l2,stretch=1); return f
