from __future__ import annotations

import os
import struct
import sys
import tempfile
import time
import wave

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication

from core.models import Track
from ui.dj_player_window import DJPlayerWindow


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance() or QApplication(sys.argv)
    yield app


def _make_wav(path: str, seconds: int = 2) -> None:
    with wave.open(path, "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(44100)
        wf.writeframes(struct.pack("<h", 0) * 44100 * seconds)


def test_odtwarzacz_load_updates_ui_and_waveform(qapp):
    fd, path = tempfile.mkstemp(suffix=".wav")
    os.close(fd)
    _make_wav(path)

    try:
        win = DJPlayerWindow()
        track = Track(path=path, title="Test Title", artist="Test Artist", bpm=128.0, duration=180)
        win.load_track_to_deck("A", track)

        odt = win.odtwarzacz_view
        assert odt is not None

        for _ in range(240):
            qapp.processEvents()
            time.sleep(0.05)
            if len(odt.waveform._peaks) > 0:
                break

        assert "Test Artist" in odt.title_label.text()
        assert odt._current_duration_ms > 0
        assert len(odt.waveform._peaks) > 0
        assert win.content_stack.currentIndex() == win._odt_stack_index()
    finally:
        os.remove(path)