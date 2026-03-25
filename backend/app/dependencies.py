"""
FastAPI Dependencies
Reusable dependencies for authentication, authorization, and tenant context
"""

import uuid
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.tenant import set_tenant_context
from app.models.user import User
from app.services.auth import decode_token, get_user_by_id

security = HTTPBearer()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """
    Extract and validate the current user from the Bearer token.
    Raises 401 if token is invalid or user not found.
    """
    payload = decode_token(credentials.credentials)
    if not payload or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    user = await get_user_by_id(db, uuid.UUID(user_id))
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    return user


async def get_current_user_with_tenant(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """
    Get current user and inject their tenant context into PostgreSQL session.
    This enables Row-Level Security for all subsequent queries.
    """
    if user.tenant_id:
        await set_tenant_context(db, str(user.tenant_id))
    return user


def require_role(*roles: str):
    """
    Factory for role-based access control dependency.

    Usage:
        @router.get("/admin", dependencies=[Depends(require_role("admin"))])
    """

    async def _check_role(
        user: Annotated[User, Depends(get_current_user)],
    ) -> User:
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of roles: {', '.join(roles)}",
            )
        return user

    return _check_role


# Type aliases for convenience
CurrentUser = Annotated[User, Depends(get_current_user)]
TenantUser = Annotated[User, Depends(get_current_user_with_tenant)]
DbSession = Annotated[AsyncSession, Depends(get_db)]
