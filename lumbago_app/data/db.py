from __future__ import annotations

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker

from lumbago_app.core.config import load_settings


_engine = None
_Session = None


def get_engine():
    global _engine
    if _engine is None:
        settings = load_settings()
        _engine = create_engine(f"sqlite:///{settings.db_path}", future=True)

        @event.listens_for(_engine, "connect")
        def _set_wal_mode(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.close()

    return _engine


def ensure_fts(engine=None) -> None:
    eng = engine or get_engine()
    with eng.connect() as conn:
        conn.execute(text(
            """
            CREATE VIRTUAL TABLE IF NOT EXISTS tracks_fts
            USING fts5(title, artist, album, genre, content='tracks', content_rowid='id')
            """
        ))
        conn.execute(text(
            """
            INSERT OR IGNORE INTO tracks_fts(rowid, title, artist, album, genre)
            SELECT id, COALESCE(title,''), COALESCE(artist,''), COALESCE(album,''), COALESCE(genre,'')
            FROM tracks
            WHERE id NOT IN (SELECT rowid FROM tracks_fts)
            """
        ))
        conn.commit()


def fts_search(query: str, engine=None) -> list[int]:
    if not query:
        return []
    eng = engine or get_engine()
    escaped = query.replace('"', '""')
    with eng.connect() as conn:
        try:
            rows = conn.execute(
                text("SELECT rowid FROM tracks_fts WHERE tracks_fts MATCH :q ORDER BY rank"),
                {"q": f'"{escaped}"*'},
            ).fetchall()
            return [row[0] for row in rows]
        except Exception:
            return []


def get_session_factory():
    global _Session
    if _Session is None:
        _Session = sessionmaker(bind=get_engine(), autoflush=False, future=True)
    return _Session


def reset_engine() -> None:
    global _engine, _Session
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _Session = None
