"""Background task monitor â€” animated widget shown at the bottom of the sidebar."""
from __future__ import annotations

import time
from dataclasses import dataclass, field

from PyQt6 import QtCore, QtGui, QtWidgets


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class BackgroundTask:
    task_id: str
    name: str
    total: int
    current: int = 0
    detail: str = ""
    started_at: float = field(default_factory=time.monotonic)
    finished: bool = False
    finished_at: float | None = None


class BackgroundTaskManager(QtCore.QObject):
    task_added = QtCore.pyqtSignal(str)
    task_updated = QtCore.pyqtSignal(str)
    task_finished = QtCore.pyqtSignal(str)
    log_appended = QtCore.pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._tasks: dict[str, BackgroundTask] = {}
        self._counter = 0

    def add_task(self, name: str, total: int, detail: str = "") -> str:
        self._counter += 1
        task_id = f"task_{self._counter}"
        self._tasks[task_id] = BackgroundTask(task_id=task_id, name=name, total=total, detail=detail)
        self.task_added.emit(task_id)
        return task_id

    def update_task(
        self,
        task_id: str,
        current: int,
        total: int | None = None,
        detail: str | None = None,
    ):
        task = self._tasks.get(task_id)
        if task is None or task.finished:
            return
        task.current = current
        if total is not None:
            task.total = total
        if detail is not None and detail != task.detail:
            task.detail = detail
            self.log_appended.emit(f"[{task.name}] {detail}")
        self.task_updated.emit(task_id)

    def finish_task(self, task_id: str):
        task = self._tasks.get(task_id)
        if task is None:
            return
        task.finished = True
        task.current = task.total
        task.finished_at = time.monotonic()
        self.task_finished.emit(task_id)

    def cancel_task(self, task_id: str):
        if task_id in self._tasks:
            del self._tasks[task_id]
        self.task_finished.emit(task_id)

    def get_task(self, task_id: str) -> BackgroundTask | None:
        return self._tasks.get(task_id)

    def active_count(self) -> int:
        return sum(1 for t in self._tasks.values() if not t.finished)

    def cleanup_finished(self, older_than: float = 5.0):
        now = time.monotonic()
        to_remove = [
            tid for tid, t in self._tasks.items()
            if t.finished and t.finished_at is not None and (now - t.finished_at) > older_than
        ]
        for tid in to_remove:
            del self._tasks[tid]


# ---------------------------------------------------------------------------
# Animated pie indicator
# ---------------------------------------------------------------------------

class _PieWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._value = 0.0
        self._spin = 0
        self._indeterminate = False
        self.setFixedSize(30, 30)
        t = QtCore.QTimer(self)
        t.timeout.connect(self._tick)
        t.start(40)

    def set_progress(self, value: float):
        self._value = max(0.0, min(1.0, value))
        self._indeterminate = False
        self.update()

    def set_indeterminate(self):
        self._indeterminate = True
        self.update()

    def _tick(self):
        if self._indeterminate:
            self._spin = (self._spin + 15) % 360
            self.update()

    def paintEvent(self, event):
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        r = self.rect().adjusted(2, 2, -2, -2)

        p.setPen(QtGui.QPen(QtGui.QColor("#1e2d42"), 2))
        p.setBrush(QtGui.QColor("#0d1320"))
        p.drawEllipse(r)

        p.setPen(QtCore.Qt.PenStyle.NoPen)
        if self._indeterminate:
            p.setBrush(QtGui.QColor("#4a9eff"))
            p.drawPie(r, (90 - self._spin) * 16, -100 * 16)
        elif self._value > 0:
            color = "#22c55e" if self._value >= 1.0 else "#4a9eff"
            p.setBrush(QtGui.QColor(color))
            p.drawPie(r, 90 * 16, int(-self._value * 360 * 16))

            p.setPen(QtGui.QColor("#c0d8f0"))
            font = p.font()
            font.setPointSize(5)
            font.setBold(True)
            p.setFont(font)
            p.drawText(r, QtCore.Qt.AlignmentFlag.AlignCenter, f"{int(self._value*100)}%")
        p.end()


# ---------------------------------------------------------------------------
# Single task row
# ---------------------------------------------------------------------------

def _eta_str(task: BackgroundTask) -> str:
    if task.finished:
        return "Ukonczono"
    if task.current <= 0:
        return "obliczanie..."
    elapsed = time.monotonic() - task.started_at
    if elapsed < 0.5:
        return "obliczanie..."
    rate = task.current / elapsed
    remaining = task.total - task.current
    if rate <= 0 or remaining <= 0:
        return ""
    secs = remaining / rate
    if secs < 60:
        return f"~{int(secs)}s"
    return f"~{int(secs//60)}m {int(secs%60):02d}s"


class _TaskRow(QtWidgets.QFrame):
    cancel_requested = QtCore.pyqtSignal(str)

    def __init__(self, task: BackgroundTask, parent=None):
        super().__init__(parent)
        self.task_id = task.task_id
        self.setObjectName("BgTaskRow")
        self.setStyleSheet(
            "QFrame#BgTaskRow{background:#0a1018;border:1px solid #1e2d42;"
            "border-radius:6px;margin:2px 0;}"
        )

        vl = QtWidgets.QVBoxLayout(self)
        vl.setContentsMargins(8, 6, 8, 6)
        vl.setSpacing(4)

        # Top: pie + name + close
        top = QtWidgets.QHBoxLayout()
        top.setSpacing(5)
        self._pie = _PieWidget()
        top.addWidget(self._pie)

        self._lbl_name = QtWidgets.QLabel(task.name)
        self._lbl_name.setStyleSheet("color:#8fb8d8;font-size:12px;font-weight:bold;")
        self._lbl_name.setWordWrap(True)
        top.addWidget(self._lbl_name, 1)

        btn_x = QtWidgets.QPushButton("x")
        btn_x.setFixedSize(16, 16)
        btn_x.setToolTip("Anuluj lub usuń zadanie")
        btn_x.setStyleSheet(
            "QPushButton{color:#4a6080;background:transparent;border:none;font-size:13px;}"
            "QPushButton:hover{color:#ff5555;}"
        )
        btn_x.clicked.connect(lambda: self.cancel_requested.emit(self.task_id))
        top.addWidget(btn_x)
        vl.addLayout(top)

        # Progress bar
        self._bar = QtWidgets.QProgressBar()
        self._bar.setTextVisible(False)
        self._bar.setFixedHeight(6)
        self._bar.setStyleSheet(
            "QProgressBar{background:#1e2d42;border:none;border-radius:3px;}"
            "QProgressBar::chunk{background:#4a9eff;border-radius:3px;}"
        )
        vl.addWidget(self._bar)

        self._lbl_detail = QtWidgets.QLabel()
        self._lbl_detail.setStyleSheet("color:#88a8c8;font-size:11px;")
        self._lbl_detail.setWordWrap(True)
        self._lbl_detail.setMaximumHeight(40)
        vl.addWidget(self._lbl_detail)
        self._last_detail = ""
        self._last_meta = ""
        self._lbl_meta = QtWidgets.QLabel()
        self._lbl_meta.setStyleSheet("color:#6f8bab;font-size:10px;")
        self._lbl_meta.setWordWrap(True)
        vl.addWidget(self._lbl_meta)

        # Bottom: count + eta
        bot = QtWidgets.QHBoxLayout()
        self._lbl_count = QtWidgets.QLabel()
        self._lbl_count.setStyleSheet("color:#4a7090;font-size:10px;")
        self._lbl_eta = QtWidgets.QLabel()
        self._lbl_eta.setStyleSheet("color:#4a7090;font-size:10px;")
        self._lbl_eta.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter)
        bot.addWidget(self._lbl_count)
        bot.addWidget(self._lbl_eta, 1)
        vl.addLayout(bot)

        self.refresh(task)

    def refresh(self, task: BackgroundTask, *, update_detail: bool = True):
        total = max(task.total, 1)
        self._bar.setMaximum(total)
        self._bar.setValue(min(task.current, total))
        pct = task.current / total
        self._pie.set_progress(pct)
        count_text = f"{task.current} / {task.total}"
        if self._lbl_count.text() != count_text:
            self._lbl_count.setText(count_text)
        eta_text = _eta_str(task)
        if self._lbl_eta.text() != eta_text:
            self._lbl_eta.setText(eta_text)
        if update_detail:
            detail = task.detail.strip()
            if detail != self._last_detail:
                self._last_detail = detail
                self._lbl_detail.setText(detail)
                self._lbl_detail.setVisible(bool(detail))
        elapsed = max(0.0, time.monotonic() - task.started_at)
        meta_text = f"Czas: {int(elapsed)}s | ID: {task.task_id}"
        if meta_text != self._last_meta:
            self._last_meta = meta_text
            self._lbl_meta.setText(meta_text)

        if task.finished:
            self.setStyleSheet(
                "QFrame#BgTaskRow{background:#071208;border:1px solid #1a3020;"
                "border-radius:6px;margin:2px 0;}"
            )
            self._bar.setStyleSheet(
                "QProgressBar{background:#1e2d42;border:none;border-radius:3px;}"
                "QProgressBar::chunk{background:#22c55e;border-radius:3px;}"
            )


# ---------------------------------------------------------------------------
# Monitor widget (shown at bottom of sidebar)
# ---------------------------------------------------------------------------

class BackgroundTaskMonitorWidget(QtWidgets.QWidget):
    def __init__(self, manager: BackgroundTaskManager, parent=None):
        super().__init__(parent)
        self._manager = manager
        self._rows: dict[str, _TaskRow] = {}

        outer = QtWidgets.QVBoxLayout(self)
        outer.setContentsMargins(0, 4, 0, 0)
        outer.setSpacing(2)

        # Separator
        sep = QtWidgets.QFrame()
        sep.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        sep.setStyleSheet("color:#1e2d42;")
        outer.addWidget(sep)

        # Header
        hdr = QtWidgets.QHBoxLayout()
        lbl = QtWidgets.QLabel("Procesy w tle")
        lbl.setStyleSheet("color:#4a9eff;font-size:11px;font-weight:bold;")
        self._badge = QtWidgets.QLabel("")
        self._badge.setStyleSheet("color:#4a6080;font-size:10px;")
        hdr.addWidget(lbl)
        hdr.addStretch()
        hdr.addWidget(self._badge)
        outer.addLayout(hdr)

        # Scroll area for task rows
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setMinimumHeight(180)
        scroll.setMaximumHeight(460)
        scroll.setStyleSheet("QScrollArea{border:none;background:transparent;}")
        self._container = QtWidgets.QWidget()
        self._vl = QtWidgets.QVBoxLayout(self._container)
        self._vl.setContentsMargins(0, 0, 0, 0)
        self._vl.setSpacing(2)
        self._vl.addStretch()
        scroll.setWidget(self._container)
        outer.addWidget(scroll)
        self._scroll = scroll
        self._user_scrolled_up = False
        scroll.verticalScrollBar().valueChanged.connect(self._on_scroll_changed)

        log_hdr = QtWidgets.QLabel("Log zadań")
        log_hdr.setStyleSheet("color:#6f8bab;font-size:10px;font-weight:bold;")
        outer.addWidget(log_hdr)
        self._log_view = QtWidgets.QPlainTextEdit()
        self._log_view.setReadOnly(True)
        self._log_view.setMaximumBlockCount(400)
        self._log_view.setMinimumHeight(90)
        self._log_view.setMaximumHeight(180)
        self._log_view.setFont(QtGui.QFont("Consolas", 9))
        self._log_view.setPlaceholderText("Postęp i komunikaty zadań...")
        self._log_view.verticalScrollBar().valueChanged.connect(self._on_log_scroll_changed)
        outer.addWidget(self._log_view)
        self._log_user_scrolled_up = False

        # Refresh timer for ETA updates
        t = QtCore.QTimer(self)
        t.timeout.connect(self._tick)
        t.start(500)

        manager.task_added.connect(self._on_added)
        manager.task_updated.connect(self._on_updated)
        manager.task_finished.connect(self._on_finished)
        manager.log_appended.connect(self._append_log_line)

        self.setVisible(False)

    # --- slots ---

    def _on_scroll_changed(self, value: int) -> None:
        sb = self._scroll.verticalScrollBar()
        self._user_scrolled_up = value < (sb.maximum() - 8)

    def _on_log_scroll_changed(self, value: int) -> None:
        sb = self._log_view.verticalScrollBar()
        self._log_user_scrolled_up = value < (sb.maximum() - 8)

    def _append_log_line(self, line: str) -> None:
        if not line.strip():
            return
        sb = self._log_view.verticalScrollBar()
        at_bottom = sb.maximum() <= 0 or sb.value() >= (sb.maximum() - 8)
        self._log_view.appendPlainText(line)
        if at_bottom and not self._log_user_scrolled_up:
            sb.setValue(sb.maximum())

    def _with_preserved_scroll(self, callback) -> None:
        sb = self._scroll.verticalScrollBar()
        pos = sb.value()
        callback()
        if self._user_scrolled_up:
            sb.setValue(min(pos, sb.maximum()))

    def _on_added(self, task_id: str):
        task = self._manager.get_task(task_id)
        if task is None:
            return
        row = _TaskRow(task)
        row.cancel_requested.connect(self._manager.cancel_task)
        self._rows[task_id] = row
        def _insert() -> None:
            self._vl.insertWidget(self._vl.count() - 1, row)

        self._with_preserved_scroll(_insert)
        self._append_log_line(f"[{task.name}] start ({task.total})")
        self._sync_visibility()

    def _on_updated(self, task_id: str):
        task = self._manager.get_task(task_id)
        row = self._rows.get(task_id)
        if task and row:
            self._with_preserved_scroll(lambda: row.refresh(task, update_detail=True))

    def _on_finished(self, task_id: str):
        task = self._manager.get_task(task_id)
        row = self._rows.get(task_id)
        if task and row:
            self._with_preserved_scroll(lambda: row.refresh(task, update_detail=True))
            self._append_log_line(f"[{task.name}] zakończono")
        self._sync_visibility()
        QtCore.QTimer.singleShot(4000, lambda: self._remove_row(task_id))

    def _remove_row(self, task_id: str):
        row = self._rows.pop(task_id, None)
        if row:
            self._vl.removeWidget(row)
            row.deleteLater()
        self._manager.cleanup_finished()
        self._sync_visibility()

    def _tick(self):
        for task_id, row in self._rows.items():
            task = self._manager.get_task(task_id)
            if task and not task.finished:
                self._with_preserved_scroll(lambda r=row, t=task: r.refresh(t, update_detail=False))

    def _sync_visibility(self):
        n = len(self._rows)
        self.setVisible(n > 0)
        self._badge.setText(f"({n})" if n > 0 else "")

