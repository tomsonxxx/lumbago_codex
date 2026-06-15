from __future__ import annotations

import os
import sys

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6 import QtCore, QtWidgets

from core.models import Track
from ui.main_window import AutoTagWorker, AutoTagWorkerSignals


@pytest.fixture(scope="module")
def qapp():
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
    yield app


def test_autotag_signals_parented_and_deliver_progress(qapp):
    parent = QtWidgets.QWidget()
    signals = AutoTagWorkerSignals(parent)
    received: list[tuple[int, int, str, str]] = []

    def on_progress(c, t, n, d):
        received.append((c, t, n, d))

    signals.progress.connect(on_progress)
    signals.deliver_progress(2, 5, "track.mp3", "test stage")
    qapp.processEvents()
    assert received == [(2, 5, "track.mp3", "test stage")]


def test_autotag_worker_emit_progress_via_invoke(qapp):
    parent = QtWidgets.QWidget()
    signals = AutoTagWorkerSignals(parent)
    received: list[tuple[int, int, str, str]] = []
    signals.progress.connect(lambda c, t, n, d: received.append((c, t, n, d)))

    worker = AutoTagWorker([], object(), signals)
    worker._emit_progress(1, 3, "-", "queued emit")
    qapp.processEvents()
    assert received == [(1, 3, "-", "queued emit")]