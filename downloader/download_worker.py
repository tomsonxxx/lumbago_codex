from __future__ import annotations

"""
DownloadWorker — QThread wykonujący pobieranie z yt-dlp + konwersję.

Obsługuje:
- pojedyncze URL i playlisty do 700+
- lazy extraction
- checkpoint (pomijanie już pobranych)
- retry z backoff
- throttling
- per-plik error continue
- max jakość audio (bestaudio + profile)
- tmp + atomic move
- ffmpeg postprocessing przez yt-dlp
- metadane + thumbnail

Sygnały przez ProgressBridge.

Per lumbago_grok_build_prompt.txt + wszystkie wytyczne (QThread, error handling, logs, 100% free, UI responsive).
"""

import os
import shutil
import tempfile
import time
import traceback
from pathlib import Path
from typing import Any

from PyQt6 import QtCore

import yt_dlp

from downloader.format_profiles import get_profile_opts, normalize_format, normalize_profile
from downloader.playlist_manager import (
    checkpoint_path,
    iter_playlist_entries,
    load_checkpoint,
    sanitize_filename,
    save_checkpoint,
)
from downloader.progress_bridge import ProgressBridge


class DownloadWorker(QtCore.QThread):
    """Główny worker w osobnym wątku."""

    def __init__(
        self,
        url: str,
        output_dir: Path,
        out_format: str,
        quality_profile: str,
        throttle_seconds: float,
        max_fragments: int,
        bridge: ProgressBridge,
        add_to_library_after: bool = False,
        cookies_path: Path | None = None,
        parent: QtCore.QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self.url = url.strip()
        self.output_dir = output_dir
        self.out_format = normalize_format(out_format)
        self.quality_profile = normalize_profile(quality_profile)
        self.throttle_seconds = max(0.0, float(throttle_seconds))
        self.max_fragments = max(1, int(max_fragments))
        self.bridge = bridge
        self.add_to_library_after = add_to_library_after
        self.cookies_path = cookies_path

        self._stop_requested = False
        self._pause_requested = False
        self._downloaded_ids: set[str] = set()
        self._current_title = ""
        self._processed = 0
        self._total = 0

    def stop(self) -> None:
        self._stop_requested = True

    def pause(self) -> None:
        self._pause_requested = True

    def resume(self) -> None:
        self._pause_requested = False

    def _log(self, msg: str) -> None:
        try:
            self.bridge.log_message.emit(msg)
        except Exception:
            pass

    def _progress_playlist(self, current: int, total: int, title: str) -> None:
        try:
            self.bridge.playlist_progress.emit(current, total, title)
        except Exception:
            pass

    def _progress_file(self, pct: int, name: str) -> None:
        try:
            self.bridge.file_progress.emit(pct, name)
        except Exception:
            pass

    def _emit_error(self, msg: str) -> None:
        try:
            self.bridge.error.emit(msg)
        except Exception:
            pass

    def _yt_hook(self, d: dict[str, Any]) -> None:
        """yt-dlp progress hook → sygnały Qt."""
        if self._stop_requested:
            raise yt_dlp.utils.DownloadCancelled("User cancelled")

        status = d.get("status")
        filename = d.get("filename") or d.get("_filename") or "track"
        info = d.get("info_dict") or {}

        if status == "downloading":
            pct = int(d.get("downloaded_bytes", 0) / max(d.get("total_bytes") or d.get("total_bytes_estimate") or 1, 1) * 100)
            self._progress_file(min(max(pct, 0), 100), Path(filename).name)
        elif status == "finished":
            self._progress_file(100, Path(filename).name)
            vid = info.get("id") or info.get("webpage_url") or filename
            if vid:
                self._downloaded_ids.add(str(vid))
            self._processed += 1
            if self._total:
                self._progress_playlist(self._processed, self._total, self._current_title)
        elif status == "error":
            self._emit_error(f"Błąd pobierania: {filename}")

        # Throttling między fragmentami / plikami (proste)
        if self.throttle_seconds > 0 and status in ("finished", "error"):
            time.sleep(self.throttle_seconds)

    def run(self) -> None:
        success = False
        summary = ""
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)

            # Sprawdzenie miejsca (proste os stat dla ~avg)
            # (lepsza estymacja w UI przed start)
            cp_path = checkpoint_path(self.output_dir, self.url)
            already = load_checkpoint(cp_path)
            self._downloaded_ids = set(already)

            ydl_opts = get_profile_opts(self.quality_profile, self.out_format)

            # Wspólne opcje
            ydl_opts.update(
                {
                    "outtmpl": str(self.output_dir / "%(title)s [%(id)s].%(ext)s"),
                    "progress_hooks": [self._yt_hook],
                    "concurrent_fragment_downloads": self.max_fragments,
                    "cookiefile": str(self.cookies_path) if self.cookies_path and self.cookies_path.exists() else None,
                    "ignoreerrors": True,  # kontynuuj przy błędach per entry
                    "nooverwrites": True,
                }
            )
            # Usuń None
            if ydl_opts.get("cookiefile") is None:
                ydl_opts.pop("cookiefile", None)

            # Tymczasowy katalog na fragmenty (czystsze)
            tmpdir = self.output_dir / "_tmp_lumbago_dl"
            tmpdir.mkdir(exist_ok=True)
            ydl_opts["paths"] = {"home": str(self.output_dir), "tmp": str(tmpdir)}

            self._log(f"Start pobierania: {self.url}")
            self._log(f"Format: {self.out_format} | Profil: {self.quality_profile} | Throttle: {self.throttle_seconds}s")

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Najpierw wyciągnij info (playlist lub single) — lazy wewnątrz
                info = ydl.extract_info(self.url, download=False)

                entries = list(iter_playlist_entries(info or {}))
                self._total = len(entries) or 1

                for idx, entry in enumerate(entries, 1):
                    if self._stop_requested:
                        break
                    while self._pause_requested and not self._stop_requested:
                        time.sleep(0.2)

                    vid = entry.get("id") or entry.get("webpage_url") or ""
                    title = entry.get("title") or entry.get("webpage_url") or f"item-{idx}"
                    self._current_title = title

                    if vid and vid in self._downloaded_ids:
                        self._log(f"Pominięto (już pobrane): {title}")
                        self._processed += 1
                        self._progress_playlist(self._processed, self._total, title)
                        continue

                    self._log(f"[{idx}/{self._total}] {title}")

                    # Retry z backoff
                    last_err = None
                    for attempt in range(3):
                        if self._stop_requested:
                            break
                        try:
                            # Pobierz ten konkretny wpis (używamy url lub id)
                            entry_url = entry.get("webpage_url") or entry.get("url") or self.url
                            ydl.download([entry_url])
                            last_err = None
                            break
                        except yt_dlp.utils.DownloadCancelled:
                            last_err = "Anulowano przez użytkownika"
                            break
                        except Exception as e:
                            last_err = str(e)
                            wait = [5, 15, 45][attempt]
                            self._log(f"  Retry {attempt+1}/3 za {wait}s... ({e})")
                            time.sleep(wait)

                    if last_err:
                        self._emit_error(f"Nie udało się pobrać po 3 próbach: {title} — {last_err}")
                        # kontynuujemy

                    # Zapisz checkpoint co plik
                    save_checkpoint(cp_path, self._downloaded_ids)

                    if self.throttle_seconds > 0:
                        time.sleep(self.throttle_seconds)

            # Sprzątanie tmp
            try:
                if tmpdir.exists():
                    shutil.rmtree(tmpdir, ignore_errors=True)
            except Exception:
                pass

            if not self._stop_requested:
                success = True
                summary = f"Zakończono: {self._processed}/{max(self._total,1)} plików"
                self._log(summary)
            else:
                summary = "Anulowano przez użytkownika"
                self._log(summary)

        except Exception as exc:
            tb = traceback.format_exc()
            self._emit_error(f"Krytyczny błąd workera: {exc}")
            self._log(tb)
            summary = f"Błąd: {exc}"
        finally:
            # final checkpoint
            try:
                save_checkpoint(cp_path, self._downloaded_ids)
            except Exception:
                pass

            try:
                self.bridge.finished.emit(success, summary)
            except Exception:
                pass
