"""Async database engine, session factory, and lifecycle helpers."""

from collections.abc import AsyncGenerator

from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.models.base import Base

settings = get_settings()

engine = create_async_engine(settings.database_url, echo=False, future=True)
async_session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


@event.listens_for(Engine, "connect")
def _enable_sqlite_foreign_keys(dbapi_connection, connection_record) -> None:  # noqa: ANN001
    """Enable foreign-key enforcement on SQLite connections.

    SQLite disables foreign keys by default, which breaks ``ON DELETE CASCADE``.
    This is a no-op for other backends.

    Args:
        dbapi_connection: The raw DB-API connection.
        connection_record: SQLAlchemy's per-connection bookkeeping record.
    """
    if settings.database_url.startswith("sqlite"):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield a request-scoped async session.

    Yields:
        AsyncSession: A session that is closed when the request ends.
    """
    async with async_session_factory() as session:
        yield session


async def init_db() -> None:
    """Create all tables for the registered models.

    Used for the local walking skeleton; production should use migrations.
    """
    import app.models  # noqa: F401  (ensure models are registered)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
