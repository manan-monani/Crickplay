"""
Caching Service
Redis-based caching with TTL support
"""

import json
from typing import Any, Optional
from redis.asyncio import Redis
from app.services.redis_client import get_redis


class CacheService:
    """Service for caching operations"""

    def __init__(self):
        self.redis: Optional[Redis] = None

    async def _get_redis(self) -> Redis:
        """Get Redis client instance"""
        if self.redis is None:
            self.redis = await get_redis()
        return self.redis

    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache

        Args:
            key: Cache key

        Returns:
            Cached value (deserialized from JSON) or None if not found
        """
        redis = await self._get_redis()
        value = await redis.get(key)

        if value is None:
            return None

        try:
            return json.loads(value)
        except json.JSONDecodeError:
            # Return raw string if not JSON
            return value

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set value in cache

        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized)
            ttl: Time to live in seconds (None = no expiration)

        Returns:
            True if successful
        """
        redis = await self._get_redis()

        # Serialize value to JSON
        if isinstance(value, (dict, list, tuple)):
            value = json.dumps(value)
        elif not isinstance(value, str):
            value = json.dumps(value)

        if ttl:
            return await redis.setex(key, ttl, value)
        else:
            return await redis.set(key, value)

    async def delete(self, key: str) -> int:
        """
        Delete key from cache

        Args:
            key: Cache key to delete

        Returns:
            Number of keys deleted
        """
        redis = await self._get_redis()
        return await redis.delete(key)

    async def delete_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching pattern

        Args:
            pattern: Pattern to match (e.g., "match:*")

        Returns:
            Number of keys deleted
        """
        redis = await self._get_redis()
        keys = await redis.keys(pattern)

        if not keys:
            return 0

        return await redis.delete(*keys)

    async def exists(self, key: str) -> bool:
        """
        Check if key exists in cache

        Args:
            key: Cache key

        Returns:
            True if key exists
        """
        redis = await self._get_redis()
        return await redis.exists(key) > 0

    async def ttl(self, key: str) -> int:
        """
        Get time to live for key

        Args:
            key: Cache key

        Returns:
            TTL in seconds, -1 if no expiration, -2 if key doesn't exist
        """
        redis = await self._get_redis()
        return await redis.ttl(key)

    def generate_key(self, *parts: str) -> str:
        """
        Generate cache key from parts

        Args:
            *parts: Key parts to join with ':'

        Returns:
            Cache key string

        Example:
            generate_key("match", "123", "stats") -> "match:123:stats"
        """
        return ":".join(str(p) for p in parts)


# Singleton instance
cache_service = CacheService()
