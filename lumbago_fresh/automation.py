from __future__ import annotations

from pathlib import Path

from PyQt6 import QtCore

from .scanner import iter_audio_files


class WatchFolderService(QtCore.QObject):
    new_files = QtCore.pyqtSignal(list)
    status = QtCore.pyqtSignal(str)

    def __init__(self, parent: QtCore.QObject | None = None) -> None:
        super().__init__(parent)
        self._timer = QtCore.QTimer(self)
        self._timer.timeout.connect(self._poll)
        self._known_paths: set[str] = set()
        self._folder: Path | None = None
        self._interval_ms = 6000

    def configure(self, folder: str, interval_sec: int) -> None:
        self._folder = Path(folder) if folder else None
        self._interval_ms = max(2, int(interval_sec)) * 1000
        if self._timer.isActive():
            self._timer.start(self._interval_ms)

    def set_known_paths(self, paths: list[str]) -> None:
        self._known_paths = set(paths)

    def start(self) -> None:
        if self._folder is None or not self._folder.exists():
            self.status.emit("Watch-folder nieaktywny: brak folderu.")
            return
        self._timer.start(self._interval_ms)
        self.status.emit(f"Watch-folder aktywny: {self._folder}")

    def stop(self) -> None:
        self._timer.stop()
        self.status.emit("Watch-folder zatrzymany.")

    def _poll(self) -> None:
        folder = self._folder
        if folder is None or not folder.exists():
            return
        found: list[str] = []
        for path in iter_audio_files(folder):
            normalized = str(path.resolve())
            if normalized not in self._known_paths:
                self._known_paths.add(normalized)
                found.append(normalized)
        if found:
            self.new_files.emit(found)

