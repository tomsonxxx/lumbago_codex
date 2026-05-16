"""Watch Folder Service - monitoruje foldery i wykrywa nowe pliki audio."""
from __future__ import annotations
import logging
from pathlib import Path
from PyQt6 import QtCore

logger = logging.getLogger(__name__)
AUDIO_EXTENSIONS = frozenset({".mp3",".flac",".aac",".m4a",".ogg",".wav",".aiff",".aif",".wma",".opus",".mp4"})
DEBOUNCE_MS = 800


class WatchFolderService(QtCore.QObject):
    new_files_detected = QtCore.pyqtSignal(list)
    error_occurred = QtCore.pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._watcher = QtCore.QFileSystemWatcher(self)
        self._watched: set[Path] = set()
        self._known: dict[Path, set[Path]] = {}
        self._pending: set[Path] = set()
        self._timer = QtCore.QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(DEBOUNCE_MS)
        self._watcher.directoryChanged.connect(self._on_changed)
        self._timer.timeout.connect(self._emit_pending)

    def add_folder(self, folder: Path) -> bool:
        folder = folder.resolve()
        if not folder.is_dir():
            self.error_occurred.emit(f"Katalog nie istnieje: {folder}"); return False
        if folder in self._watched: return False
        self._known[folder] = self._scan(folder)
        self._watched.add(folder)
        self._watcher.addPath(str(folder))
        logger.info("WatchFolder: +%s (%d plików)", folder, len(self._known[folder]))
        return True

    def remove_folder(self, folder: Path) -> None:
        folder = folder.resolve()
        if folder not in self._watched: return
        self._watcher.removePath(str(folder))
        self._watched.discard(folder)
        self._known.pop(folder, None)

    def watched_folders(self) -> list[Path]:
        return sorted(self._watched)

    def _on_changed(self, path_str: str) -> None:
        folder = Path(path_str)
        if folder not in self._watched: return
        current = self._scan(folder)
        known = self._known.get(folder, set())
        new = current - known
        if new:
            self._pending.update(new)
            self._known[folder] = current
            self._timer.start()

    def _emit_pending(self) -> None:
        if self._pending:
            paths = [str(p) for p in sorted(self._pending)]
            self._pending.clear()
            self.new_files_detected.emit(paths)

    @staticmethod
    def _scan(folder: Path) -> set[Path]:
        try:
            return {f for f in folder.iterdir() if f.is_file() and f.suffix.lower() in AUDIO_EXTENSIONS}
        except PermissionError:
            return set()
