"""
Lumbago Music AI — Repozytorium danych
=========================================
Warstwa dostępu do danych (Repository Pattern).
Oddziela logikę biznesową od SQLAlchemy.
"""

import logging
from typing import Any, Optional, Sequence

from sqlalchemy import func, or_, select, update
from sqlalchemy.orm import Session

from lumbago_app.data.models import (
    ChangeLogOrm, MetadataCacheOrm, PlaylistOrm,
    PlaylistTrackOrm, SettingsOrm, TagOrm, TrackOrm,
)

logger = logging.getLogger(__name__)


class TrackRepository:
    """Repozytorium CRUD dla modelu TrackOrm."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, track_id: int) -> Optional[TrackOrm]:
        """Zwraca utwór po ID lub None."""
        return self._session.get(TrackOrm, track_id)

    def get_by_path(self, file_path: str) -> Optional[TrackOrm]:
        """Zwraca utwór po ścieżce pliku lub None."""
        stmt = select(TrackOrm).where(TrackOrm.file_path == file_path)
        return self._session.scalar(stmt)

    def get_by_hash(self, file_hash: str) -> Optional[TrackOrm]:
        """Zwraca utwór po hashu pliku lub None."""
        stmt = select(TrackOrm).where(TrackOrm.file_hash == file_hash)
        return self._session.scalar(stmt)

    def get_all(self, limit: int = 0, offset: int = 0) -> Sequence[TrackOrm]:
        """Zwraca wszystkie utwory z paginacją."""
        stmt = select(TrackOrm).order_by(TrackOrm.artist, TrackOrm.title)
        if offset:
            stmt = stmt.offset(offset)
        if limit:
            stmt = stmt.limit(limit)
        return self._session.scalars(stmt).all()

    def search(
        self,
        query: str,
        genre: Optional[str] = None,
        bpm_min: Optional[float] = None,
        bpm_max: Optional[float] = None,
        key_camelot: Optional[str] = None,
        rating_min: Optional[int] = None,
        limit: int = 500,
    ) -> Sequence[TrackOrm]:
        """
        Wyszukuje utwory wg wielu kryteriów.

        Args:
            query: Tekst do wyszukania w artyście/tytule/albumie.
            genre: Filtr gatunku.
            bpm_min: Minimalne BPM.
            bpm_max: Maksymalne BPM.
            key_camelot: Kod Camelot.
            rating_min: Minimalna ocena.
            limit: Limit wyników.
        """
        stmt = select(TrackOrm)

        if query:
            like = f"%{query}%"
            stmt = stmt.where(
                or_(
                    TrackOrm.title.ilike(like),
                    TrackOrm.artist.ilike(like),
                    TrackOrm.album.ilike(like),
                )
            )
        if genre:
            stmt = stmt.where(TrackOrm.genre == genre)
        if bpm_min is not None:
            stmt = stmt.where(TrackOrm.bpm >= bpm_min)
        if bpm_max is not None:
            stmt = stmt.where(TrackOrm.bpm <= bpm_max)
        if key_camelot:
            stmt = stmt.where(TrackOrm.key_camelot == key_camelot)
        if rating_min is not None:
            stmt = stmt.where(TrackOrm.rating >= rating_min)

        stmt = stmt.limit(limit)
        return self._session.scalars(stmt).all()

    def add(self, track: TrackOrm) -> TrackOrm:
        """Dodaje nowy utwór do sesji."""
        self._session.add(track)
        return track

    def delete(self, track: TrackOrm) -> None:
        """Usuwa utwór z bazy."""
        self._session.delete(track)

    def count(self) -> int:
        """Zwraca liczbę wszystkich utworów."""
        return self._session.scalar(select(func.count()).select_from(TrackOrm)) or 0

    def get_unanalyzed(self, limit: int = 100) -> Sequence[TrackOrm]:
        """Zwraca utwory bez analizy audio."""
        stmt = (
            select(TrackOrm)
            .where(TrackOrm.is_analyzed == False)  # noqa: E712
            .limit(limit)
        )
        return self._session.scalars(stmt).all()

    def get_unfingerprinted(self, limit: int = 100) -> Sequence[TrackOrm]:
        """Zwraca utwory bez fingerprinta."""
        stmt = (
            select(TrackOrm)
            .where(TrackOrm.is_fingerprinted == False)  # noqa: E712
            .limit(limit)
        )
        return self._session.scalars(stmt).all()

    def bulk_update_field(
        self, track_ids: list[int], field: str, value: Any
    ) -> int:
        """
        Masowo aktualizuje pole dla listy ID.

        Returns:
            Liczba zaktualizowanych rekordów.
        """
        result = self._session.execute(
            update(TrackOrm)
            .where(TrackOrm.id.in_(track_ids))
            .values(**{field: value})
        )
        return result.rowcount


class PlaylistRepository:
    """Repozytorium dla Playlists."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_roots(self) -> Sequence[PlaylistOrm]:
        """Zwraca playlisty najwyższego poziomu (bez rodzica)."""
        stmt = (
            select(PlaylistOrm)
            .where(PlaylistOrm.parent_id.is_(None))
            .order_by(PlaylistOrm.sort_order, PlaylistOrm.name)
        )
        return self._session.scalars(stmt).all()

    def get_by_id(self, playlist_id: int) -> Optional[PlaylistOrm]:
        return self._session.get(PlaylistOrm, playlist_id)

    def add(self, playlist: PlaylistOrm) -> PlaylistOrm:
        self._session.add(playlist)
        return playlist

    def delete(self, playlist: PlaylistOrm) -> None:
        self._session.delete(playlist)

    def add_track(
        self, playlist_id: int, track_id: int, position: Optional[int] = None
    ) -> PlaylistTrackOrm:
        """Dodaje utwór do playlisty."""
        if position is None:
            # Oblicz następną pozycję
            stmt = select(func.max(PlaylistTrackOrm.position)).where(
                PlaylistTrackOrm.playlist_id == playlist_id
            )
            max_pos = self._session.scalar(stmt) or 0
            position = max_pos + 1

        entry = PlaylistTrackOrm(
            playlist_id=playlist_id,
            track_id=track_id,
            position=position,
        )
        self._session.add(entry)
        return entry


class SettingsRepository:
    """Repozytorium ustawień aplikacji."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, key: str) -> Optional[Any]:
        """Zwraca wartość ustawienia po kluczu (skonwertowaną do właściwego typu)."""
        stmt = select(SettingsOrm).where(SettingsOrm.key == key)
        row = self._session.scalar(stmt)
        if row is None:
            return None
        return row.get_typed_value()

    def set(self, key: str, value: Any, description: Optional[str] = None) -> None:
        """Ustawia lub aktualizuje wartość ustawienia."""
        stmt = select(SettingsOrm).where(SettingsOrm.key == key)
        row = self._session.scalar(stmt)
        if row is None:
            row = SettingsOrm(key=key)
            self._session.add(row)
        row.value = str(value)
        if description:
            row.description = description


class MetadataCacheRepository:
    """Repozytorium cache metadanych zewnętrznych."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, cache_key: str) -> Optional[MetadataCacheOrm]:
        """Zwraca cache lub None (wliczając wygasłe)."""
        stmt = select(MetadataCacheOrm).where(MetadataCacheOrm.cache_key == cache_key)
        return self._session.scalar(stmt)

    def get_fresh(self, cache_key: str) -> Optional[MetadataCacheOrm]:
        """Zwraca cache tylko jeśli nie wygasł."""
        row = self.get(cache_key)
        if row and not row.is_expired:
            row.hit_count += 1
            return row
        return None

    def set(self, row: MetadataCacheOrm) -> MetadataCacheOrm:
        """Zapisuje lub aktualizuje cache."""
        existing = self.get(row.cache_key)
        if existing:
            existing.data_json = row.data_json
            existing.expires_at = row.expires_at
            return existing
        self._session.add(row)
        return row
