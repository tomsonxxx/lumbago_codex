from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from lumbago_app.core.config import load_settings


_engine = None
_Session = None


def get_engine():
    global _engine
    if _engine is None:
        settings = load_settings()
        _engine = create_engine(f"sqlite:///{settings.db_path}", future=True)
    return _engine


def get_session_factory():
    global _Session
    if _Session is None:
        _Session = sessionmaker(bind=get_engine(), autoflush=False, future=True)
    return _Session

