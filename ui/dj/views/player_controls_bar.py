"""
ui/dj/views/player_controls_bar.py

Pasek sterowania WMP/VLC — głośność + mute + opcjonalny transport.
Per SZPIEG_DJ_Player_Redesign_2026.md (basic odtwarzacz).
"""

from __future__ import annotations

from PyQt6 import QtCore, QtWidgets

from ui.dj.styles import BoothMetrics, get_slider_stylesheet


class PlayerControlsBar(QtWidgets.QWidget):
    """VOL slider + mute — standard media player chrome (WMP/VLC)."""

    volume_changed = QtCore.pyqtSignal(int)
    mute_toggled = QtCore.pyqtSignal(bool)

    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self._metrics = BoothMetrics(mode="normal")
        self._muted = False
        self._saved_volume = 85
        self._compact_strip = False
        self._transport_btns: tuple[QtWidgets.QPushButton, ...] | None = None
        self._transport_attached = False

        self._row = QtWidgets.QHBoxLayout(self)
        self._row.setContentsMargins(0, 0, 0, 0)
        self._row.setSpacing(self._metrics.px(8))

        vol_icon = QtWidgets.QLabel("🔊")
        vol_icon.setFixedWidth(self._metrics.px(22))
        self._vol_icon = vol_icon
        self._row.addWidget(vol_icon, 0)

        self.volume_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(85)
        self.volume_slider.setStyleSheet(get_slider_stylesheet("horizontal"))
        self.volume_slider.setToolTip("Głośność odtwarzania (0–100%)")
        self.volume_slider.valueChanged.connect(self._on_volume)
        self._row.addWidget(self.volume_slider, 1)

        self.volume_label = QtWidgets.QLabel("85")
        self.volume_label.setStyleSheet(self._metrics.value_label_stylesheet())
        self.volume_label.setMinimumWidth(self._metrics.px(28))
        self._row.addWidget(self.volume_label, 0)

        self.mute_btn = QtWidgets.QPushButton("M")
        self.mute_btn.setCheckable(True)
        self.mute_btn.setFixedSize(self._metrics.px(32), self._metrics.px(28))
        self.mute_btn.setToolTip("Wycisz / przywróć głośność")
        self.mute_btn.toggled.connect(self._on_mute)
        self._row.addWidget(self.mute_btn, 0)

    def register_transport_buttons(
        self,
        cue_btn: QtWidgets.QPushButton,
        play_btn: QtWidgets.QPushButton,
        stop_btn: QtWidgets.QPushButton,
    ) -> None:
        """Rejestruje transport do wbudowania w compact bottom strip (Winamp mini)."""
        self._transport_btns = (cue_btn, play_btn, stop_btn)

    def set_compact_strip(self, compact: bool) -> None:
        """Jeden rząd: VOL + CUE ▶ ■ (ikony) — per SZPIEG compact pilot."""
        if self._compact_strip == compact:
            return
        self._compact_strip = compact
        if compact:
            self.volume_label.setVisible(False)
            self.mute_btn.setVisible(False)
            self.volume_slider.setMaximumWidth(self._metrics.px(100))
            self._attach_transport()
        else:
            self.volume_label.setVisible(True)
            self.mute_btn.setVisible(True)
            self.volume_slider.setMaximumWidth(16777215)
            self._detach_transport()

    def _attach_transport(self) -> None:
        if self._transport_attached or not self._transport_btns:
            return
        mute_idx = self._row.indexOf(self.mute_btn)
        insert_at = mute_idx if mute_idx >= 0 else self._row.count()
        for i, btn in enumerate(self._transport_btns):
            self._row.insertWidget(insert_at + i, btn, 0)
        self._transport_attached = True

    def _detach_transport(self) -> None:
        if not self._transport_attached or not self._transport_btns:
            return
        for btn in self._transport_btns:
            self._row.removeWidget(btn)
            btn.setParent(None)
        self._transport_attached = False

    def apply_metrics(self, metrics: BoothMetrics) -> None:
        self._metrics = metrics
        self.volume_label.setStyleSheet(metrics.value_label_stylesheet())
        w, h = metrics.px(32), metrics.px(28)
        self.mute_btn.setFixedSize(w, h)

    def _on_volume(self, value: int) -> None:
        if self._muted and value > 0:
            self.mute_btn.blockSignals(True)
            self.mute_btn.setChecked(False)
            self.mute_btn.blockSignals(False)
            self._muted = False
            self._vol_icon.setText("🔊")
        self.volume_label.setText(str(value))
        self._saved_volume = value
        self.volume_changed.emit(value)

    def _on_mute(self, checked: bool) -> None:
        self._muted = checked
        if checked:
            self._saved_volume = self.volume_slider.value()
            self.volume_slider.blockSignals(True)
            self.volume_slider.setValue(0)
            self.volume_slider.blockSignals(False)
            self.volume_label.setText("0")
            self._vol_icon.setText("🔇")
            self.volume_changed.emit(0)
        else:
            restore = max(1, self._saved_volume)
            self.volume_slider.blockSignals(True)
            self.volume_slider.setValue(restore)
            self.volume_slider.blockSignals(False)
            self.volume_label.setText(str(restore))
            self._vol_icon.setText("🔊")
            self.volume_changed.emit(restore)
        self.mute_toggled.emit(checked)

    def set_volume(self, percent: int) -> None:
        self.volume_slider.blockSignals(True)
        self.volume_slider.setValue(max(0, min(100, percent)))
        self.volume_slider.blockSignals(False)
        self.volume_label.setText(str(self.volume_slider.value()))


__all__ = ["PlayerControlsBar"]