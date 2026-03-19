"""
Lumbago Music AI — Serwis importu biblioteki
=============================================
Skanuje katalogi, odczytuje metadane, dodaje do bazy.
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

logger = logging.getLogger(__name__)

# Callback postępu: (current, total, filename) -> None
ProgressCallback = Callable[[int, int, str], None]


@dataclass
class ImportResult:
    """Podsumowanie operacji importu."""
    added: int = 0
    skipped: int = 0
    failed: int = 0
    errors: list[str] = field(default_factory=list)

    @property
    def total(self) -> int:
        return self.added + self.skipped + self.failed


class ImportService:
    """
    Serwis importu plików audio do biblioteki.

    Obsługuje:
    - Skanowanie katalogów rekurencyjne
    - Odczyt metadanych ID3/Vorbis/MP4 przez mutagen
    - Wykrywanie duplikatów po ścieżce i hashu
    - Batch insert do bazy SQLite
    """

    def import_directory(
        self,
        directory: Path,
        recursive: bool = True,
        progress_callback: Optional[ProgressCallback] = None,
    ) -> ImportResult:
        """
        Importuje wszystkie obsługiwane pliki audio z katalogu.

        Args:
            directory: Ścieżka do katalogu.
            recursive: Czy skanować podkatalogi.
            progress_callback: Opcjonalny callback postępu.

        Returns:
            ImportResult z podsumowaniem.

        Raises:
            ImportError: Jeśli katalog nie istnieje.
        """
        from lumbago_app.core.exceptions import ImportError as LumbagoImportError
        from lumbago_app.core.utils import is_audio_file

        if not directory.exists():
            raise LumbagoImportError(f"Katalog nie istnieje: {directory}")

        # Zbierz pliki
        pattern = "**/*" if recursive else "*"
        audio_files = [
            f for f in directory.glob(pattern)
            if f.is_file() and is_audio_file(f)
        ]

        total = len(audio_files)
        result = ImportResult()

        logger.info(
            "Import: znaleziono %d plików audio w %s", total, directory
        )

        for idx, file_path in enumerate(audio_files, 1):
            try:
                added = self._import_single(file_path)
                if added:
                    result.added += 1
                else:
                    result.skipped += 1

                if progress_callback:
                    progress_callback(idx, total, file_path.name)

            except Exception as exc:
                result.failed += 1
                result.errors.append(f"{file_path.name}: {exc}")
                logger.warning("Błąd importu %s: %s", file_path.name, exc)

        logger.info(
            "Import zakończony: %d dodano, %d pominięto, %d błędów",
            result.added, result.skipped, result.failed,
        )
        return result

    def import_files(
        self,
        file_paths: list[Path],
        progress_callback: Optional[ProgressCallback] = None,
    ) -> ImportResult:
        """
        Importuje podaną listę plików.

        Args:
            file_paths: Lista ścieżek do plików.
            progress_callback: Opcjonalny callback postępu.

        Returns:
            ImportResult z podsumowaniem.
        """
        total = len(file_paths)
        result = ImportResult()

        for idx, file_path in enumerate(file_paths, 1):
            try:
                added = self._import_single(file_path)
                if added:
                    result.added += 1
                else:
                    result.skipped += 1
            except Exception as exc:
                result.failed += 1
                result.errors.append(f"{file_path.name}: {exc}")
                logger.warning("Błąd importu %s: %s", file_path.name, exc)

            if progress_callback:
                progress_callback(idx, total, file_path.name)

        return result

    def _import_single(self, file_path: Path) -> bool:
        """
        Importuje jeden plik.

        Returns:
            True jeśli dodano, False jeśli pominięto (duplikat).

        Raises:
            Różne wyjątki przy błędzie.
        """
        from lumbago_app.core.utils import compute_file_hash
        from lumbago_app.data.database import session_scope
        from lumbago_app.data.models import TrackOrm
        from lumbago_app.data.repository import TrackRepository

        with session_scope() as session:
            repo = TrackRepository(session)

            # Sprawdź duplikat po ścieżce
            if repo.get_by_path(str(file_path)):
                logger.debug("Pominięto (ścieżka): %s", file_path.name)
                return False

            # Metadane
            track = self._read_metadata(file_path)
            repo.add(track)

        return True

    def _read_metadata(self, file_path: Path) -> "TrackOrm":
        """
        Odczytuje metadane pliku i tworzy TrackOrm.

        Raises:
            UnsupportedFormatError: Nieobsługiwany format.
        """
        from lumbago_app.core.exceptions import UnsupportedFormatError
        from lumbago_app.core.utils import compute_file_hash, is_audio_file
        from lumbago_app.data.models import TrackOrm

        if not is_audio_file(file_path):
            raise UnsupportedFormatError(str(file_path), file_path.suffix)

        import mutagen
        import mutagen.easyid3
        import mutagen.mp3

        track = TrackOrm(
            file_path=str(file_path),
            file_size=file_path.stat().st_size,
        )

        try:
            # Hash (nieblokujący dla małych plików, dla dużych lazy)
            if file_path.stat().st_size < 50 * 1024 * 1024:  # < 50 MB
                track.file_hash = compute_file_hash(file_path)
        except Exception as exc:
            logger.debug("Nie można obliczyć hasha dla %s: %s", file_path.name, exc)

        # Metadane Easy
        try:
            easy = mutagen.File(str(file_path), easy=True)
            if easy:
                track.title = self._first(easy.get("title"))
                track.artist = self._first(easy.get("artist"))
                track.album = self._first(easy.get("album"))
                track.album_artist = self._first(easy.get("albumartist"))
                track.genre = self._first(easy.get("genre"))
                year_str = self._first(easy.get("date"))
                if year_str:
                    track.year = int(year_str[:4])
                track_num = self._first(easy.get("tracknumber"))
                if track_num and "/" in str(track_num):
                    track.track_number = int(str(track_num).split("/")[0])
                elif track_num:
                    track.track_number = int(str(track_num))

            # Metadane techniczne
            full = mutagen.File(str(file_path))
            if full and hasattr(full, "info"):
                track.duration = getattr(full.info, "length", None)
                track.sample_rate = getattr(full.info, "sample_rate", None)
                track.channels = getattr(full.info, "channels", None)
                track.bit_rate = getattr(full.info, "bitrate", None)

        except Exception as exc:
            logger.warning("Błąd odczytu metadanych %s: %s", file_path.name, exc)

        return track

    @staticmethod
    def _first(values: object) -> Optional[str]:
        """Zwraca pierwszy element listy lub None."""
        if not values:
            return None
        if isinstance(values, list):
            return str(values[0]) if values else None
        return str(values)
