"""SQLAlchemy async engine and session factory for PostgreSQL."""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from src.infrastructure.config import settings


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


engine = create_async_engine(settings.database_url, echo=False, future=True)

SessionFactory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield a database session (used as a FastAPI dependency).

    Unconditionally clears the RLS identity claim before yielding. Pooled
    connections are reused across requests, so a request that never sets its
    own claim (unauthenticated, or authenticated but forgets to) must never
    inherit a previous request's — that would leak one user's row-level
    access into another request's session. `AuthenticatedSessionDep`
    (`interfaces/http/dependencies.py`) then sets the real claim for
    authenticated requests, on the same session.
    """
    async with SessionFactory() as session:
        await session.execute(
            text("SELECT set_config('request.jwt.claim.sub', '', false)")
        )
        yield session


async def init_db() -> None:
    """Create tables. For real projects use Alembic migrations instead."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
