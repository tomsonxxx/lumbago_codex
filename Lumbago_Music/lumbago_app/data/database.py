"""
Lumbago Music AI — Inicjalizacja bazy danych
=============================================
SQLAlchemy engine, SessionLocal, auto-upgrade Alembic,
fallback dodawania brakujących kolumn.
"""

import logging
import os
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine, event, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

logger = logging.getLogger(__name__)

# Silnik i fabryka sesji — inicjalizowane przez init_database()
_engine: Engine | None = None
_SessionFactory: sessionmaker | None = None  # type: ignore[type-arg]


def _get_database_url() -> str:
    """Wczytuje URL bazy danych z konfiguracji."""
    try:
        from lumbago_app.core.config import get_settings
        return get_settings().DATABASE_URL
    except Exception:
        return os.environ.get("DATABASE_URL", "sqlite:///lumbago.db")


def _configure_sqlite(engine: Engine) -> None:
    """Konfiguruje SQLite: WAL mode, foreign keys, busy timeout."""
    if "sqlite" not in engine.url.drivername:
        return

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn: object, _: object) -> None:
        cursor = dbapi_conn.cursor()  # type: ignore[union-attr]
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA busy_timeout=5000")
        cursor.execute("PRAGMA cache_size=-32768")  # 32 MB
        cursor.close()

    logger.debug("SQLite PRAGMA skonfigurowane (WAL, FK, busy_timeout)")


def _run_alembic_upgrade(engine: Engine) -> bool:
    """
    Uruchamia migracje Alembic ('alembic upgrade head').

    Returns:
        True jeśli sukces, False jeśli Alembic niedostępny.
    """
    try:
        from alembic import command
        from alembic.config import Config

        migrations_dir = Path(__file__).parent / "migrations"
        if not migrations_dir.exists():
            logger.debug("Brak katalogu migrations — pomijam Alembic")
            return False

        alembic_ini = Path(__file__).parent.parent.parent / "alembic.ini"
        if not alembic_ini.exists():
            logger.debug("Brak alembic.ini — pomijam Alembic")
            return False

        cfg = Config(str(alembic_ini))
        cfg.set_main_option("sqlalchemy.url", str(engine.url))
        command.upgrade(cfg, "head")
        logger.info("Migracje Alembic wykonane ('upgrade head')")
        return True
    except Exception as exc:
        logger.warning("Alembic upgrade nie powiódł się: %s", exc)
        return False


def _ensure_schema(engine: Engine) -> None:
    """
    Tworzy brakujące tabele i dodaje brakujące kolumny (fallback bez Alembic).
    Bezpieczne do wielokrotnego wywołania (idempotentne).
    """
    from lumbago_app.data.models import Base

    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())

    # Utwórz brakujące tabele
    Base.metadata.create_all(engine, checkfirst=True)
    logger.info("Schemat bazy danych zainicjalizowany")

    # Dodaj brakujące kolumny (SQLite nie obsługuje ALTER TABLE ADD COLUMN IF NOT EXISTS)
    for table_name, table in Base.metadata.tables.items():
        if table_name not in existing_tables:
            continue  # nowa tabela — już stworzona
        try:
            existing_cols = {
                col["name"] for col in inspector.get_columns(table_name)
            }
            with engine.begin() as conn:
                for col in table.columns:
                    if col.name not in existing_cols:
                        col_type = col.type.compile(engine.dialect)
                        nullable = "NULL" if col.nullable else "NOT NULL DEFAULT ''"
                        sql = (
                            f"ALTER TABLE {table_name} "
                            f"ADD COLUMN {col.name} {col_type} {nullable}"
                        )
                        try:
                            conn.execute(text(sql))
                            logger.info(
                                "Dodano brakującą kolumnę: %s.%s", table_name, col.name
                            )
                        except Exception as col_exc:
                            logger.debug(
                                "Kolumna %s.%s: %s", table_name, col.name, col_exc
                            )
        except Exception as tbl_exc:
            logger.warning(
                "Błąd podczas sprawdzania kolumn tabeli %s: %s", table_name, tbl_exc
            )


def _reset_database(engine: Engine) -> None:
    """Dropuje wszystkie tabele i tworzy je od nowa (tylko gdy LUMBAGO_RESET_DB=1)."""
    from lumbago_app.data.models import Base
    logger.warning("RESET_DB: Usuwam wszystkie tabele bazy danych!")
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    logger.warning("RESET_DB: Baza danych zresetowana")


def init_database() -> None:
    """
    Inicjalizuje połączenie z bazą danych.
    Wywołaj raz przy starcie aplikacji przed użyciem get_session().
    """
    global _engine, _SessionFactory

    db_url = _get_database_url()
    logger.info("Inicjalizacja bazy: %s", db_url.split("@")[-1])  # ukryj hasło

    _engine = create_engine(
        db_url,
        echo=os.environ.get("LUMBAGO_VERBOSE") == "1",
        pool_pre_ping=True,
        connect_args={"check_same_thread": False} if "sqlite" in db_url else {},
    )

    _configure_sqlite(_engine)

    # Reset DB jeśli zażądany
    if os.environ.get("LUMBAGO_RESET_DB") == "1":
        _reset_database(_engine)
    else:
        # Próba Alembic, fallback do create_all
        if not _run_alembic_upgrade(_engine):
            _ensure_schema(_engine)

    _SessionFactory = sessionmaker(
        bind=_engine,
        autoflush=True,
        autocommit=False,
        expire_on_commit=False,
    )

    logger.info("Baza danych gotowa")


def get_engine() -> Engine:
    """Zwraca silnik SQLAlchemy. Wymaga wcześniejszego wywołania init_database()."""
    if _engine is None:
        raise RuntimeError("init_database() nie zostało wywołane")
    return _engine


def get_session() -> Session:
    """
    Zwraca nową sesję SQLAlchemy.

    Uwaga: Sesja musi być zamknięta ręcznie lub przez context manager.
    Preferuj użycie session_scope().
    """
    if _SessionFactory is None:
        raise RuntimeError("init_database() nie zostało wywołane")
    return _SessionFactory()


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """
    Context manager dla transakcji SQLAlchemy.

    Użycie::

        with session_scope() as session:
            track = session.get(TrackOrm, 1)

    Automatycznie commituje lub robi rollback.
    """
    session = get_session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
