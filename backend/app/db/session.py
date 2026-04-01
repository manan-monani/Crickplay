"""
Database session management with async SQLAlchemy
Provides async session factory and dependency injection for FastAPI
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.pool import NullPool, QueuePool
from app.config import get_settings

settings = get_settings()

# Create async engine with connection pooling
engine: AsyncEngine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
    pool_pre_ping=True,  # Verify connections before using
    pool_size=10,  # Maximum connections in pool
    max_overflow=20,  # Additional connections beyond pool_size
    pool_recycle=3600,  # Recycle connections after 1 hour
)

# Create session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency for database sessions

    Usage:
        @app.get("/endpoint")
        async def endpoint(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_db_with_tenant(tenant_id: str) -> AsyncGenerator[AsyncSession, None]:
    """
    Database session with tenant context for Row-Level Security

    Sets PostgreSQL session variable app.current_tenant before query execution

    Usage:
        @app.get("/endpoint")
        async def endpoint(db: AsyncSession = Depends(get_db_with_tenant("tenant_123"))):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            # Set tenant context for Row-Level Security
            await session.execute(f"SET LOCAL app.current_tenant = '{tenant_id}'")
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
