"""Alembic migration environment.

Configured for async SQLAlchemy with asyncpg. The DATABASE_URL env var is
read at runtime so the same migrations work across environments.
"""

from __future__ import annotations

import asyncio
import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import Connection, pool
from sqlalchemy.ext.asyncio import create_async_engine

# Import Base so all ORM models are registered in Base.metadata before
# Alembic inspects it for autogenerate support.
from src.infrastructure.database.engine import Base
import src.infrastructure.database.models  # noqa: F401  — registers models

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _get_url() -> str:
    return os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://shelflife:shelflife@localhost:5432/shelflife",
    )


def _do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def _run_online() -> None:
    engine = create_async_engine(_get_url(), poolclass=pool.NullPool)
    async with engine.connect() as conn:
        await conn.run_sync(_do_run_migrations)
    await engine.dispose()


def run_migrations_offline() -> None:
    context.configure(
        url=_get_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(_run_online())
