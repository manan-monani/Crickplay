"""
Tenant Context Dependency
Inject tenant context for PostgreSQL Row-Level Security
"""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.db.session import get_db
from app.models.user import User
from app.dependencies.auth import get_current_user


async def get_tenant_context(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> AsyncSession:
    """
    Dependency to set tenant context for Row-Level Security

    Sets the PostgreSQL session variable 'app.current_tenant' to enable RLS policies
    This ensures all queries are automatically filtered by tenant_id

    Usage:
        @app.get("/data")
        async def get_data(db: AsyncSession = Depends(get_tenant_context)):
            # All queries in this endpoint are automatically tenant-scoped
            ...

    Returns:
        Database session with tenant context set
    """
    # Set tenant context in PostgreSQL session
    await db.execute(
        text("SET LOCAL app.current_tenant = :tenant_id"),
        {"tenant_id": str(current_user.tenant_id)},
    )

    return db


async def get_db_with_tenant(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> AsyncSession:
    """
    Alternative name for get_tenant_context for clarity

    Combines authentication and tenant context injection in one dependency
    """
    # Set tenant context in PostgreSQL session
    await db.execute(
        text("SET LOCAL app.current_tenant = :tenant_id"),
        {"tenant_id": str(current_user.tenant_id)},
    )

    return db
