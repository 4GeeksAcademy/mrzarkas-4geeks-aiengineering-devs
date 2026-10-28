from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings


def create_engine() -> AsyncEngine:
    """Create an async SQLAlchemy engine from DATABASE_URL."""

    return create_async_engine(
        get_settings().require_database_url(),
        pool_pre_ping=True,
    )


engine = create_engine() if get_settings().database_url else None
SessionLocal = (
    async_sessionmaker(engine, expire_on_commit=False) if engine is not None else None
)


async def get_session() -> AsyncIterator[AsyncSession]:
    if SessionLocal is None:
        raise RuntimeError("DATABASE_URL is required for database operations")

    async with SessionLocal() as session:
        yield session