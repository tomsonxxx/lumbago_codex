"""
VLC Audio Backend dla Lumbago DJ Player.

Zapewnia niezależne odtwarzanie dla pojedynczego decku z obsługą:
- volume
- pitch/tempo (rate)
- seek
- 3-pasmowy EQ
- pobieranie aktualnej pozycji (do waveform playhead)

Wymaga: python-vlc + zainstalowanego VLC na systemie Windows.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

try:
    import vlc
    _VLC_AVAILABLE = True
except Exception as e:   # catches both ImportError and the FileNotFoundError from missing libvlc.dll
    vlc = None
    _VLC_AVAILABLE = False
    _VLC_IMPORT_ERROR = str(e)

logger = logging.getLogger(__name__)


class VlcDeckPlayer:
    """
    Kontroler pojedynczego decku audio opartego na VLC.

    Użycie:
        player = VlcDeckPlayer()
        player.load("ścieżka/do/pliku.mp3")
        player.play()
        player.set_volume(80)
        player.set_rate(1.05)   # +5% tempa
    """

    def __init__(self):
        self._enabled = False
        self._error_message = None
        self._instance = None
        self._player = None
        self._equalizer = None
        self._current_path = None
        self._is_loaded = False
        self.on_end_reached = None

        if not _VLC_AVAILABLE or vlc is None:
            self._error_message = "Brak biblioteki VLC (libvlc.dll nie została znaleziona)."
            if '_VLC_IMPORT_ERROR' in globals() and _VLC_IMPORT_ERROR:
                self._error_message += f" Szczegóły: {_VLC_IMPORT_ERROR}"
            self._error_message += " Zainstaluj VLC z https://www.videolan.org/vlc/"
            return

        self._enabled = True

        # Instancja VLC
        self._instance = vlc.Instance("--no-video", "--quiet")
        self._player = self._instance.media_player_new()

        # Equalizer
        try:
            self._equalizer = vlc.AudioEqualizer.create()
            if self._equalizer:
                self._player.set_equalizer(self._equalizer)
        except Exception:
            self._equalizer = None

        self._current_path = None
        self._is_loaded = False
        self.on_end_reached = None

    # ------------------------------------------------------------------ #
    # Podstawowe sterowanie
    # ------------------------------------------------------------------ #

    def load(self, path: str | Path) -> bool:
        """Wczytuje plik audio do decku."""
        if not self._enabled:
            return False

        path = str(path)
        if not Path(path).exists():
            logger.error(f"Plik nie istnieje: {path}")
            return False

        try:
            media = self._instance.media_new(path)
            self._player.set_media(media)
            self._current_path = path
            self._is_loaded = True
            logger.debug(f"VLC loaded: {path}")
            return True
        except Exception as e:
            logger.exception(f"Błąd ładowania pliku do VLC: {e}")
            self._is_loaded = False
            return False

    def play(self) -> None:
        if self._enabled and self._is_loaded:
            self._player.play()

    def pause(self) -> None:
        if self._enabled and self._is_loaded:
            self._player.pause()

    def stop(self) -> None:
        if self._enabled and self._is_loaded:
            self._player.stop()

    def toggle_play(self) -> bool:
        """Przełącza play/pause. Zwraca True jeśli teraz gra."""
        if not self._enabled or not self._is_loaded:
            return False

        if self._player.is_playing():
            self.pause()
            return False
        else:
            self.play()
            return True

    # ------------------------------------------------------------------ #
    # Pozycja i czas
    # ------------------------------------------------------------------ #

    def get_time(self) -> int:
        """Zwraca aktualną pozycję w milisekundach."""
        if not self._enabled or not self._is_loaded:
            return 0
        t = self._player.get_time()
        return max(0, t) if t >= 0 else 0

    def get_length(self) -> int:
        """Zwraca długość utworu w milisekundach."""
        if not self._enabled or not self._is_loaded:
            return 0
        length = self._player.get_length()
        return max(0, length) if length > 0 else 0

    def seek(self, time_ms: int) -> None:
        """Przeskakuje do podanej pozycji (w milisekundach)."""
        if self._enabled and self._is_loaded and time_ms >= 0:
            self._player.set_time(int(time_ms))

    # ------------------------------------------------------------------ #
    # Głośność i pitch
    # ------------------------------------------------------------------ #

    def set_volume(self, volume: int) -> None:
        """Ustawia głośność 0-100."""
        if self._enabled and self._is_loaded:
            vol = max(0, min(100, int(volume)))
            self._player.audio_set_volume(vol)

    def get_volume(self) -> int:
        if not self._enabled or not self._is_loaded:
            return 0
        return self._player.audio_get_volume()

    def set_rate(self, rate: float) -> None:
        """
        Ustawia tempo/pitch (rate).
        1.0 = normalne tempo
        1.05 = +5%
        0.95 = -5%
        """
        if self._enabled and self._is_loaded:
            self._player.set_rate(float(rate))

    def get_rate(self) -> float:
        if not self._enabled or not self._is_loaded:
            return 1.0
        return self._player.get_rate()

    # ------------------------------------------------------------------ #
    # EQ (3-pasmowy)
    # ------------------------------------------------------------------ #

    def set_eq(self, low: float, mid: float, high: float) -> None:
        """
        Ustawia 3-pasmowy EQ w dB.
        low  ≈  60-250 Hz
        mid  ≈  250-4000 Hz
        high ≈  4000-16000 Hz
        Wartości zazwyczaj w zakresie -12 do +12 dB.
        """
        if not self._equalizer:
            return

        # VLC equalizer ma 10 bandów. Mapujemy nasze 3 pasma na nie.
        # Przybliżenie:
        # band 0-1  → low
        # band 3-5  → mid
        # band 7-9  → high

        low_db = max(-12.0, min(12.0, float(low)))
        mid_db = max(-12.0, min(12.0, float(mid)))
        high_db = max(-12.0, min(12.0, float(high)))

        # Ustawiamy bandy (indeksy 0-9)
        for i in range(10):
            if i <= 1:
                self._equalizer.set_amp_at_index(low_db, i)
            elif i <= 5:
                self._equalizer.set_amp_at_index(mid_db, i)
            else:
                self._equalizer.set_amp_at_index(high_db, i)

    def reset_eq(self) -> None:
        """Resetuje equalizer do zera."""
        if self._equalizer:
            for i in range(10):
                self._equalizer.set_amp_at_index(0.0, i)

    # ------------------------------------------------------------------ #
    # Stan
    # ------------------------------------------------------------------ #

    def is_playing(self) -> bool:
        return bool(self._is_loaded and self._player.is_playing())

    def is_loaded(self) -> bool:
        return self._is_loaded

    def get_current_path(self) -> Optional[str]:
        return self._current_path

    def release(self) -> None:
        """Zwalnia zasoby VLC."""
        try:
            if self._player:
                self._player.stop()
                self._player.release()
            if self._instance:
                self._instance.release()
        except Exception:
            pass
        self._is_loaded = False
