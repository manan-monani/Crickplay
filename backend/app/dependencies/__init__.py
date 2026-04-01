"""FastAPI dependencies for auth, tenant context, etc."""

from app.dependencies.auth import (
    get_current_user,
    get_current_active_user,
    get_current_superuser,
    require_role,
)
from app.dependencies.tenant import (
    get_tenant_context,
    get_db_with_tenant,
)
from app.dependencies.rate_limit import (
    limiter,
    rate_limit_by_tier,
    check_rate_limit,
    get_tier_limit,
)

__all__ = [
    "get_current_user",
    "get_current_active_user",
    "get_current_superuser",
    "require_role",
    "get_tenant_context",
    "get_db_with_tenant",
    "limiter",
    "rate_limit_by_tier",
    "check_rate_limit",
    "get_tier_limit",
]
