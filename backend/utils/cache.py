# utils/cache.py
import redis.asyncio as redis
import json
from typing import Any, Optional, Dict, List
from datetime import datetime, timedelta
from functools import wraps
import hashlib
import pickle

from core.config import settings

class RedisCache:
    """Redis cache manager with advanced features"""
    
    def __init__(self):
        self.client = None
        self.enabled = settings.REDIS_ENABLED
        self.default_ttl = 3600  # 1 hour
        
    async def connect(self):
        """Establish Redis connection"""
        if self.enabled and not self.client:
            self.client = await redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=False
            )
    
    async def disconnect(self):
        """Close Redis connection"""
        if self.client:
            await self.client.close()
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.enabled or not self.client:
            return None
        
        try:
            value = await self.client.get(key)
            if value:
                return pickle.loads(value)
            return None
        except Exception as e:
            print(f"Cache get error: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """Set value in cache with TTL"""
        if not self.enabled or not self.client:
            return False
        
        try:
            serialized = pickle.dumps(value)
            ttl = ttl or self.default_ttl
            await self.client.setex(key, ttl, serialized)
            return True
        except Exception as e:
            print(f"Cache set error: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if not self.enabled or not self.client:
            return False
        
        try:
            await self.client.delete(key)
            return True
        except Exception:
            return False
    
    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern"""
        if not self.enabled or not self.client:
            return 0
        
        try:
            keys = await self.client.keys(pattern)
            if keys:
                return await self.client.delete(*keys)
            return 0
        except Exception:
            return 0
    
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        if not self.enabled or not self.client:
            return False
        
        try:
            return await self.client.exists(key) > 0
        except Exception:
            return False
    
    async def increment(self, key: str, amount: int = 1) -> int:
        """Increment counter"""
        if not self.enabled or not self.client:
            return 0
        
        try:
            return await self.client.incrby(key, amount)
        except Exception:
            return 0
    
    async def get_or_set(self, key: str, callback, ttl: int = None):
        """Get from cache or execute callback and cache result"""
        value = await self.get(key)
        if value is not None:
            return value
        
        value = await callback()
        if value is not None:
            await self.set(key, value, ttl)
        return value
    
    async def clear_all(self) -> bool:
        """Clear all cache (dangerous!)"""
        if not self.enabled or not self.client:
            return False
        
        try:
            await self.client.flushdb()
            return True
        except Exception:
            return False
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        if not self.enabled or not self.client:
            return {"enabled": False}
        
        try:
            info = await self.client.info("stats")
            memory = await self.client.info("memory")
            
            return {
                "enabled": True,
                "total_commands": info.get("total_commands_processed", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "hit_rate": self._calculate_hit_rate(info),
                "used_memory_mb": memory.get("used_memory", 0) / 1024 / 1024,
                "connected_clients": info.get("connected_clients", 0)
            }
        except Exception as e:
            return {"enabled": True, "error": str(e)}
    
    def _calculate_hit_rate(self, info: dict) -> float:
        """Calculate cache hit rate"""
        hits = info.get("keyspace_hits", 0)
        misses = info.get("keyspace_misses", 0)
        total = hits + misses
        if total == 0:
            return 0.0
        return (hits / total) * 100
    
    async def get_ttl(self, key: str) -> int:
        """Get remaining TTL for key"""
        if not self.enabled or not self.client:
            return -2
        
        try:
            return await self.client.ttl(key)
        except Exception:
            return -2

# Global cache instance
cache = RedisCache()

def cached(ttl: int = 3600, key_prefix: str = ""):
    """Decorator for caching function results"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{key_prefix}:{func.__name__}:"
            cache_key += hashlib.md5(
                f"{args}{kwargs}".encode()
            ).hexdigest()
            
            # Try to get from cache
            cached_result = await cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Cache result
            if result is not None:
                await cache.set(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator
