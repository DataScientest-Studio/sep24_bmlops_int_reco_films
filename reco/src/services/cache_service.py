from typing import Any, Optional, Dict
import aioredis
import json
import logging
from datetime import datetime
import pickle

logger = logging.getLogger(__name__)

class CacheService:
    def __init__(self, redis_url: str = "redis://localhost"):
        self.redis = aioredis.from_url(redis_url, decode_responses=True)
        
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        try:
            value = await self.redis.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Error retrieving from cache: {str(e)}")
            return None
            
    async def set(
        self,
        key: str,
        value: Any,
        expire: int = None
    ) -> bool:
        """Set value in cache with optional expiration."""
        try:
            serialized_value = json.dumps(value)
            if expire:
                await self.redis.setex(key, expire, serialized_value)
            else:
                await self.redis.set(key, serialized_value)
            return True
        except Exception as e:
            logger.error(f"Error setting cache: {str(e)}")
            return False
            
    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        try:
            await self.redis.delete(key)
            return True
        except Exception as e:
            logger.error(f"Error deleting from cache: {str(e)}")
            return False
            
    async def get_model(self, key: str) -> Optional[Any]:
        """Get model from cache."""
        try:
            value = await self.redis.get(f"model:{key}")
            if value:
                return pickle.loads(value)
            return None
        except Exception as e:
            logger.error(f"Error retrieving model from cache: {str(e)}")
            return None
            
    async def set_model(
        self,
        key: str,
        model: Any,
        expire: int = None
    ) -> bool:
        """Set model in cache with optional expiration."""
        try:
            serialized_model = pickle.dumps(model)
            if expire:
                await self.redis.setex(f"model:{key}", expire, serialized_model)
            else:
                await self.redis.set(f"model:{key}", serialized_model)
            return True
        except Exception as e:
            logger.error(f"Error setting model in cache: {str(e)}")
            return False
            
    async def clear_pattern(self, pattern: str) -> bool:
        """Clear all keys matching pattern."""
        try:
            keys = await self.redis.keys(pattern)
            if keys:
                await self.redis.delete(*keys)
            return True
        except Exception as e:
            logger.error(f"Error clearing cache pattern: {str(e)}")
            return False
            
    async def get_metrics(self, metric_name: str) -> Optional[Dict]:
        """Get cached metrics."""
        try:
            value = await self.redis.hgetall(f"metrics:{metric_name}")
            if value:
                return {k: float(v) for k, v in value.items()}
            return None
        except Exception as e:
            logger.error(f"Error retrieving metrics from cache: {str(e)}")
            return None
            
    async def set_metrics(
        self,
        metric_name: str,
        metrics: Dict[str, float],
        expire: int = None
    ) -> bool:
        """Set metrics in cache with optional expiration."""
        try:
            await self.redis.hmset(f"metrics:{metric_name}", metrics)
            if expire:
                await self.redis.expire(f"metrics:{metric_name}", expire)
            return True
        except Exception as e:
            logger.error(f"Error setting metrics in cache: {str(e)}")
            return False
            
    async def close(self):
        """Close Redis connection."""
        await self.redis.close() 