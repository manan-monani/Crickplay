"""
Redis Client Configuration
Connection pool and client management
"""

from redis.asyncio import Redis, ConnectionPool
from typing import Optional
from app.config import get_settings

settings = get_settings()

# Global Redis client instance
_redis_client: Optional[Redis] = None


async def get_redis() -> Redis:
    """
    Get Redis client instance (singleton pattern)

    Creates connection pool on first call, reuses thereafter
    """
    global _redis_client

    if _redis_client is None:
        # Create connection pool
        pool = ConnectionPool.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            max_connections=10,
            socket_timeout=5,
            socket_connect_timeout=5,
        )

        _redis_client = Redis(connection_pool=pool)

    return _redis_client


async def close_redis():
    """Close Redis connection pool"""
    global _redis_client

    if _redis_client:
        await _redis_client.close()
        _redis_client = None
