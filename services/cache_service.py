"""
Cache service using Redis/Upstash.
Provides caching functionality for search results and frequently accessed data.
"""

import json
from typing import Optional, Any, Dict
from datetime import timedelta

import redis.asyncio as redis
from redis.exceptions import RedisError

from config.settings import get_settings
from utils.logger import logger


class CacheService:
    """
    Cache service using Redis.
    Handles caching of search results and other frequently accessed data.
    """
    
    def __init__(self):
        """Initialize cache service."""
        self.settings = get_settings()
        self.client: Optional[redis.Redis] = None
        self._is_connected = False
        self.default_ttl = self.settings.cache_ttl
    
    async def connect(self) -> None:
        """Connect to Redis."""
        try:
            if not self.settings.cache_enabled:
                logger.warning("⚠️ Cache is disabled in settings")
                return
            
            logger.info("🔌 Connecting to Redis...")
            
            self.client = redis.from_url(
                self.settings.redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_keepalive=True,
            )
            
            # Test connection
            await self.client.ping()
            
            self._is_connected = True
            logger.info("✅ Connected to Redis")
            
        except RedisError as e:
            logger.error(f"❌ Failed to connect to Redis: {e}")
            logger.warning("⚠️ Cache will be disabled")
            self._is_connected = False
        except Exception as e:
            logger.error(f"❌ Unexpected error connecting to Redis: {e}")
            self._is_connected = False
    
    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self.client:
            await self.client.close()
            self._is_connected = False
            logger.info("👋 Disconnected from Redis")
    
    @property
    def is_connected(self) -> bool:
        """Check if connected to Redis."""
        return self._is_connected and self.client is not None
    
    def _make_key(self, prefix: str, identifier: str) -> str:
        """
        Create a cache key.
        
        Args:
            prefix: Key prefix (e.g., 'search', 'price')
            identifier: Unique identifier
            
        Returns:
            str: Cache key
        """
        return f"pharmacy_bot:{prefix}:{identifier}"
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None
        """
        if not self.is_connected:
            return None
        
        try:
            value = await self.client.get(key)
            if value:
                logger.debug(f"Cache HIT: {key}")
                return json.loads(value)
            
            logger.debug(f"Cache MISS: {key}")
            return None
            
        except (RedisError, json.JSONDecodeError) as e:
            logger.warning(f"Error getting from cache: {e}")
            return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (default: from settings)
            
        Returns:
            bool: True if successful
        """
        if not self.is_connected:
            return False
        
        try:
            ttl = ttl or self.default_ttl
            serialized = json.dumps(value, default=str)
            
            await self.client.setex(
                key,
                timedelta(seconds=ttl),
                serialized
            )
            
            logger.debug(f"Cache SET: {key} (TTL: {ttl}s)")
            return True
            
        except (RedisError, TypeError, json.JSONEncodeError) as e:
            logger.warning(f"Error setting cache: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """
        Delete key from cache.
        
        Args:
            key: Cache key
            
        Returns:
            bool: True if deleted
        """
        if not self.is_connected:
            return False
        
        try:
            result = await self.client.delete(key)
            logger.debug(f"Cache DELETE: {key}")
            return result > 0
            
        except RedisError as e:
            logger.warning(f"Error deleting from cache: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.
        
        Args:
            key: Cache key
            
        Returns:
            bool: True if exists
        """
        if not self.is_connected:
            return False
        
        try:
            return await self.client.exists(key) > 0
        except RedisError as e:
            logger.warning(f"Error checking cache existence: {e}")
            return False
    
    async def clear_pattern(self, pattern: str) -> int:
        """
        Clear all keys matching pattern.
        
        Args:
            pattern: Key pattern (e.g., 'search:*')
            
        Returns:
            int: Number of keys deleted
        """
        if not self.is_connected:
            return 0
        
        try:
            keys = []
            async for key in self.client.scan_iter(match=pattern):
                keys.append(key)
            
            if keys:
                deleted = await self.client.delete(*keys)
                logger.info(f"Cleared {deleted} keys matching pattern: {pattern}")
                return deleted
            
            return 0
            
        except RedisError as e:
            logger.warning(f"Error clearing cache pattern: {e}")
            return 0
    
    # ============================================
    # SEARCH CACHE METHODS
    # ============================================
    
    async def get_search_results(self, query: str) -> Optional[Dict]:
        """
        Get cached search results.
        
        Args:
            query: Search query
            
        Returns:
            Cached search results or None
        """
        key = self._make_key("search", query.lower().strip())
        return await self.get(key)
    
    async def cache_search_results(
        self,
        query: str,
        results: Dict,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Cache search results.
        
        Args:
            query: Search query
            results: Search results to cache
            ttl: Time to live in seconds
            
        Returns:
            bool: True if successful
        """
        key = self._make_key("search", query.lower().strip())
        return await self.set(key, results, ttl)
    
    # ============================================
    # PRICE CACHE METHODS
    # ============================================
    
    async def get_medicine_prices(self, medicine_id: str) -> Optional[Dict]:
        """
        Get cached medicine prices.
        
        Args:
            medicine_id: Medicine ID
            
        Returns:
            Cached prices or None
        """
        key = self._make_key("prices", medicine_id)
        return await self.get(key)
    
    async def cache_medicine_prices(
        self,
        medicine_id: str,
        prices: Dict,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Cache medicine prices.
        
        Args:
            medicine_id: Medicine ID
            prices: Prices to cache
            ttl: Time to live in seconds
            
        Returns:
            bool: True if successful
        """
        key = self._make_key("prices", medicine_id)
        return await self.set(key, prices, ttl)
    
    # ============================================
    # RATE LIMITING METHODS
    # ============================================
    
    async def check_rate_limit(
        self,
        user_id: int,
        limit: int,
        window: int = 60
    ) -> bool:
        """
        Check if user has exceeded rate limit.
        
        Args:
            user_id: User ID
            limit: Maximum requests allowed
            window: Time window in seconds
            
        Returns:
            bool: True if within limit, False if exceeded
        """
        if not self.is_connected:
            return True  # Allow if cache unavailable
        
        try:
            key = self._make_key("rate_limit", str(user_id))
            
            # Get current count
            count = await self.client.get(key)
            
            if count is None:
                # First request in window
                await self.client.setex(key, timedelta(seconds=window), "1")
                return True
            
            current_count = int(count)
            
            if current_count >= limit:
                logger.warning(f"Rate limit exceeded for user {user_id}")
                return False
            
            # Increment counter
            await self.client.incr(key)
            return True
            
        except RedisError as e:
            logger.warning(f"Error checking rate limit: {e}")
            return True  # Allow on error
    
    async def get_rate_limit_remaining(
        self,
        user_id: int,
        limit: int
    ) -> int:
        """
        Get remaining requests for user.
        
        Args:
            user_id: User ID
            limit: Maximum requests allowed
            
        Returns:
            int: Remaining requests
        """
        if not self.is_connected:
            return limit
        
        try:
            key = self._make_key("rate_limit", str(user_id))
            count = await self.client.get(key)
            
            if count is None:
                return limit
            
            remaining = limit - int(count)
            return max(0, remaining)
            
        except RedisError as e:
            logger.warning(f"Error getting rate limit remaining: {e}")
            return limit
    
    # ============================================
    # STATISTICS METHODS
    # ============================================
    
    async def increment_counter(self, counter_name: str) -> int:
        """
        Increment a counter.
        
        Args:
            counter_name: Counter name
            
        Returns:
            int: New counter value
        """
        if not self.is_connected:
            return 0
        
        try:
            key = self._make_key("counter", counter_name)
            return await self.client.incr(key)
        except RedisError as e:
            logger.warning(f"Error incrementing counter: {e}")
            return 0
    
    async def get_counter(self, counter_name: str) -> int:
        """
        Get counter value.
        
        Args:
            counter_name: Counter name
            
        Returns:
            int: Counter value
        """
        if not self.is_connected:
            return 0
        
        try:
            key = self._make_key("counter", counter_name)
            value = await self.client.get(key)
            return int(value) if value else 0
        except RedisError as e:
            logger.warning(f"Error getting counter: {e}")
            return 0
    
    # ============================================
    # HEALTH CHECK
    # ============================================
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on cache.
        
        Returns:
            dict: Health status
        """
        try:
            if not self.is_connected:
                return {
                    "status": "disconnected",
                    "healthy": False,
                }
            
            # Ping Redis
            await self.client.ping()
            
            # Get info
            info = await self.client.info()
            
            return {
                "status": "connected",
                "healthy": True,
                "redis_version": info.get("redis_version"),
                "used_memory": info.get("used_memory_human"),
                "connected_clients": info.get("connected_clients"),
                "uptime_days": info.get("uptime_in_days"),
            }
            
        except Exception as e:
            logger.error(f"❌ Cache health check failed: {e}")
            return {
                "status": "error",
                "healthy": False,
                "error": str(e),
            }


# Global cache service instance
_cache_service: Optional[CacheService] = None


async def get_cache_service() -> CacheService:
    """
    Get or create cache service instance.
    
    Returns:
        CacheService: Cache service instance
    """
    global _cache_service
    
    if _cache_service is None:
        _cache_service = CacheService()
        await _cache_service.connect()
    
    return _cache_service


async def close_cache_service() -> None:
    """Close cache service connection."""
    global _cache_service
    
    if _cache_service is not None:
        await _cache_service.disconnect()
        _cache_service = None


__all__ = [
    "CacheService",
    "get_cache_service",
    "close_cache_service",
]

# Made with Bob