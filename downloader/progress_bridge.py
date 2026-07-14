from __future__ import annotations

"""
Progress Bridge — PyQt6 sygnały dla yt-dlp hooks.

Umożliwia bezpieczny transfer postępu z wątku download do UI.

Per prompt: playlist_progress, file_progress, log, error, finished.
"""

from PyQt6 import QtCore


class ProgressBridge(QtCore.QObject):
    """Emituje sygnały z workera (QThread) do UI."""

    # (current, total, title_or_status)
    playlist_progress = QtCore.pyqtSignal(int, int, str)
    # (percent 0-100, filename)
    file_progress = QtCore.pyqtSignal(int, str)
    # dowolny komunikat do logu
    log_message = QtCore.pyqtSignal(str)
    # błąd per-plik lub ogólny (nie przerywa kolejki)
    error = QtCore.pyqtSignal(str)
    # sukces/porażka całego zadania
    finished = QtCore.pyqtSignal(bool, str)  # success, summary_message

    def __init__(self, parent: QtCore.QObject | None = None) -> None:
        super().__init__(parent)
