"""
Background AutoTag Worker

Mechanizm uzupełniania mniej priorytetowych pól "na spokojnie" w tle,
po tym jak użytkownik już otrzymał 10 najważniejszych tagów.

Dzięki temu użytkownik może normalnie pracować z biblioteką,
a reszta metadanych jest uzupełniana asynchronicznie.
"""

from __future__ import annotations

from PyQt6 import QtCore
from copy import deepcopy

from core.models import BACKGROUND_AUTOTAG_FIELDS, Track
from services.autotag_rewrite import UnifiedAutoTagger


class BackgroundAutotagWorker(QtCore.QObject):
    """
    Worker działający w osobnym wątku QThread.

    Uzupełnia pola z BACKGROUND_AUTOTAG_FIELDS dla listy utworów.
    """

    # Sygnały
    progress = QtCore.pyqtSignal(int, int, str)           # current, total, filename
    track_updated = QtCore.pyqtSignal(str, dict)          # track_path, {field: value}
    finished = QtCore.pyqtSignal(int, int)                # updated_count, total_processed

    def __init__(
        self,
        tracks: list[Track],
        settings,
        parent: QtCore.QObject | None = None,
    ):
        super().__init__(parent)
        self.tracks = tracks
        self.settings = settings
        self._stop_requested = False

    def stop(self) -> None:
        self._stop_requested = True

    def run(self) -> None:
        if not self.tracks:
            self.finished.emit(0, 0)
            return

        autotagger = UnifiedAutoTagger(self.settings, logger=None)
        updated_count = 0
        total = len(self.tracks)

        # Log startu (jeśli main_window ma _process_log)
        try:
            from ui.main_window import _process_log
            _process_log(f"[autotag-bg] start | tracks={total}")
        except Exception:
            pass

        for idx, track in enumerate(self.tracks):
            if self._stop_requested:
                break

            filename = track.path.split("\\")[-1].split("/")[-1]
            self.progress.emit(idx + 1, total, filename)

            # Zbieramy które pola już są wypełnione
            already_filled = {
                field for field in BACKGROUND_AUTOTAG_FIELDS
                if getattr(track, field, None)
            }

            if len(already_filled) == len(BACKGROUND_AUTOTAG_FIELDS):
                continue  # nic więcej do uzupełnienia

            try:
                result = autotagger.enrich_missing_background_fields(
                    deepcopy(track),
                    already_filled_fields=already_filled,
                )

                if result.best_match is None:
                    continue

                changes: dict[str, str | int | float] = {}
                for field in BACKGROUND_AUTOTAG_FIELDS:
                    if field in already_filled:
                        continue
                    new_value = getattr(result.best_match, field, None)
                    current_value = getattr(track, field, None)
                    if new_value and not current_value:
                        setattr(track, field, new_value)
                        changes[field] = new_value

                if changes:
                    updated_count += 1
                    self.track_updated.emit(track.path, changes)

                if (idx + 1) % 5 == 0 or idx == total - 1:
                    self.progress.emit(idx + 1, total, filename)

            except Exception:
                # W tle nie chcemy wysadzać całego programu
                continue

        try:
            from ui.main_window import _process_log
            _process_log(f"[autotag-bg] finished | updated={updated_count}/{total}")
        except Exception:
            pass

        self.finished.emit(updated_count, total)
