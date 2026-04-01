"""
Rate Limiting Dependency
Tier-based rate limiting using SlowAPI
"""

from fastapi import Request, HTTPException, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.config import get_settings

settings = get_settings()


# Create limiter instance
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["1000/hour"],  # Default limit
    storage_uri=settings.REDIS_URL,
)


def get_rate_limit_key(request: Request) -> str:
    """
    Generate rate limit key based on user/tenant

    Uses user email from JWT if available, otherwise falls back to IP
    """
    # Try to get user from JWT
    if hasattr(request.state, "user"):
        user = request.state.user
        return f"user:{user.email}"

    # Fallback to IP address
    return get_remote_address(request)


def get_tier_limit(tier: str) -> str:
    """
    Get rate limit string for subscription tier

    Args:
        tier: Subscription tier (fan, professional, enterprise)

    Returns:
        Rate limit string (e.g., "100/hour")
    """
    limits = {
        "fan": "100/hour",
        "professional": "1000/hour",
        "enterprise": "10000/hour",  # Effectively unlimited
        "admin": "10000/hour",
    }
    return limits.get(tier, "100/hour")


def rate_limit_by_tier(tier: str):
    """
    Decorator for rate limiting by subscription tier

    Usage:
        @router.get("/endpoint")
        @rate_limit_by_tier("professional")
        async def endpoint():
            ...
    """

    def decorator(func):
        limit_string = get_tier_limit(tier)
        return limiter.limit(limit_string)(func)

    return decorator


def check_rate_limit(request: Request, tier: str) -> bool:
    """
    Check if request is within rate limit for tier

    Args:
        request: FastAPI request
        tier: Subscription tier

    Returns:
        True if within limit

    Raises:
        HTTPException 429: If rate limit exceeded
    """
    limit_string = get_tier_limit(tier)

    try:
        # SlowAPI will raise RateLimitExceeded if limit is hit
        limiter.check(request, limit_string)
        return True
    except RateLimitExceeded:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded for {tier} tier. Limit: {limit_string}",
        )
