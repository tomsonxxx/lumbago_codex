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
