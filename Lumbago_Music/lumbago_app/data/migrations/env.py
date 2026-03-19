"""Alembic env.py — konfiguracja środowiska migracji."""

import os
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context

# Dodaj korzeń projektu do PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from lumbago_app.data.models import Base

# Konfiguracja z alembic.ini
config = context.config
if config.config_file_name:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def get_url() -> str:
    """Wczytuje URL bazy z konfiguracji lub env."""
    try:
        from lumbago_app.core.config import get_settings
        return get_settings().DATABASE_URL
    except Exception:
        return os.environ.get("DATABASE_URL", "sqlite:///lumbago.db")


def run_migrations_offline() -> None:
    url = get_url()
    context.configure(
        url=url, target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    from sqlalchemy import engine_from_config, pool
    cfg = config.get_section(config.config_ini_section) or {}
    cfg["sqlalchemy.url"] = get_url()
    connectable = engine_from_config(
        cfg, prefix="sqlalchemy.", poolclass=pool.NullPool
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
