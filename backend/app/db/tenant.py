"""
Tenant Context Manager
Implements Row-Level Security via PostgreSQL session variable injection
"""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def set_tenant_context(session: AsyncSession, tenant_id: str) -> None:
    """
    Inject tenant context into the PostgreSQL session.

    Must be called before any query to ensure RLS policies
    filter data by the correct tenant_id.

    Args:
        session: Active async database session
        tenant_id: The tenant ID to set for this session
    """
    await session.execute(
        text(f"SET app.current_tenant = :tenant_id"),
        {"tenant_id": tenant_id},
    )


async def clear_tenant_context(session: AsyncSession) -> None:
    """
    Clear tenant context from the PostgreSQL session.

    Call this on session cleanup to prevent tenant context leakage.
    """
    await session.execute(text("RESET app.current_tenant"))


async def get_current_tenant(session: AsyncSession) -> str:
    """
    Get the currently set tenant ID from the PostgreSQL session.

    Returns:
        Current tenant ID or empty string if not set
    """
    result = await session.execute(
        text("SELECT current_setting('app.current_tenant', true)")
    )
    row = result.scalar()
    return row or ""
