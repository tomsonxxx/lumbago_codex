"""
Background AutoTag Worker

Mechanizm uzupełniania mniej priorytetowych pól "na spokojnie" w tle,
po tym jak użytkownik już otrzymał 10 najważniejszych tagów.

Dzięki temu użytkownik może normalnie pracować z biblioteką,
a reszta metadanych jest uzupełniana asynchronicznie.
"""

from __future__ import annotations

from pathlib import Path
from PyQt6 import QtCore
from copy import deepcopy

from core.models import BACKGROUND_AUTOTAG_FIELDS, Track
from services.autotag_rewrite import UnifiedAutoTagger
from services.metadata_writeback import PendingTrackWrite, apply_track_writes


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
                working = deepcopy(track)
                result = autotagger.enrich_missing_background_fields(
                    working,
                    already_filled_fields=already_filled,
                )
                source_count = len(
                    [
                        c
                        for c in getattr(result, "candidates", []) or []
                        if getattr(c, "error", None) is None and getattr(c, "score", 0) > 0
                    ]
                )
                changes = autotagger.apply_background_fields(
                    track,
                    result,
                    already_filled_fields=already_filled,
                )
                if not changes:
                    if source_count:
                        _process_log(
                            f"[autotag-bg] no background fields after {source_count} sources "
                            f"file={filename}"
                        )
                    continue

                old_values: dict[str, str | None] = {}
                for field, new_value in changes.items():
                    old_values[field] = None

                if changes:
                    try:
                        writeback = apply_track_writes(
                            [
                                PendingTrackWrite(
                                    track=track,
                                    fields={
                                        field: "" if value is None else str(value)
                                        for field, value in changes.items()
                                    },
                                    source="autotag:background",
                                    confidence=None,
                                    change_log_source="autotag:background",
                                    old_values=old_values,
                                )
                            ],
                            max_workers=1,
                            update_mode="single",
                        )
                        if writeback.file_write_errors:
                            _process_log(
                                f"[autotag-bg] writeback errors file={Path(track.path).name} "
                                f"errors={len(writeback.file_write_errors)}"
                            )
                    except Exception as exc:
                        _process_log(f"[autotag-bg] writeback failed file={Path(track.path).name} err={exc}")
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
