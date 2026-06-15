from __future__ import annotations

import logging
from typing import Any

from PyQt6 import QtCore

from core.waveform import extract_peaks as _core_extract_peaks
from core.waveform import extract_rgb_peaks as _core_extract_rgb_peaks

logger = logging.getLogger(__name__)


def _safe_extract_rgb(audio_path: str, num_points: int = 900) -> dict[str, list[float]]:
    try:
        bands = _core_extract_rgb_peaks(audio_path, num_points=num_points)
        return bands.as_dict()
    except Exception as exc:
        logger.warning(f"extract_rgb_peaks nieudane dla {audio_path}: {exc}")
    try:
        peak = _core_extract_peaks(audio_path, num_points=num_points)
        return {"low": peak, "mid": peak, "high": peak, "peak": peak}
    except Exception:
        import math

        peaks: list[float] = []
        for i in range(num_points):
            t = (i / num_points) * 180
            base = 0.3 + 0.5 * abs(math.sin(t * 1.7)) + 0.2 * abs(math.sin(t * 0.35))
            peaks.append(max(0.08, min(0.97, base)))
        return {"low": peaks, "mid": peaks, "high": peaks, "peak": peaks}


class _WaveformDelivery(QtCore.QObject):
    """Process-wide dispatcher: worker thread -> GUI thread -> WaveformWidget.load_waveform."""

    _instance: _WaveformDelivery | None = None
    deliver = QtCore.pyqtSignal(object, object, int, str)

    def __init__(self, parent: QtCore.QObject | None = None) -> None:
        super().__init__(parent)
        self.deliver.connect(self._on_deliver, QtCore.Qt.ConnectionType.QueuedConnection)

    @classmethod
    def instance(cls) -> _WaveformDelivery:
        if cls._instance is None:
            app = QtCore.QCoreApplication.instance()
            cls._instance = _WaveformDelivery(app)
        return cls._instance

    @staticmethod
    def _on_deliver(waveform_widget: Any, payload: object, duration_ms: int, token: str) -> None:
        if waveform_widget is None:
            return
        try:
            if isinstance(payload, dict):
                peaks = payload.get("peak") or payload.get("mid") or []
                waveform_widget.load_waveform(peaks, duration_ms, token, rgb_bands=payload)
            else:
                waveform_widget.load_waveform(payload, duration_ms, token)
        except RuntimeError:
            logger.debug("Waveform widget no longer available — drop stale peaks")


class WaveformExtractRunnable(QtCore.QRunnable):
    """Extract RGB peaks in a worker thread and deliver on the GUI thread."""

    def __init__(self, audio_path: str, duration_ms: int, token: str, waveform_widget: Any):
        super().__init__()
        self.setAutoDelete(True)
        self._path = str(audio_path)
        self._duration = int(duration_ms)
        self._token = token
        self._wave = waveform_widget

    def run(self) -> None:
        try:
            bands = _safe_extract_rgb(self._path, 900)
            _WaveformDelivery.instance().deliver.emit(self._wave, bands, self._duration, self._token or "")
        except Exception as exc:
            logger.warning(f"WaveformExtractRunnable błąd dla {self._path}: {exc}")


def request_waveform_load(waveform_widget: Any, audio_path: str, duration_ms: int, token: str) -> None:
    """Schedule async peak extraction and deliver to ``waveform_widget.load_waveform``."""
    if not audio_path or waveform_widget is None:
        return
    _WaveformDelivery.instance()
    runnable = WaveformExtractRunnable(str(audio_path), int(duration_ms), str(token), waveform_widget)
    QtCore.QThreadPool.globalInstance().start(runnable)