import hashlib
import json
import logging
from typing import Any, Dict, Optional
import redis
from app.core.config import settings

logger = logging.getLogger("disease_risk_serving")

class RedisCacheService:
    def __init__(self):
        # Configure connection pool for production scalability
        self.pool = redis.ConnectionPool(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD,
            decode_responses=True,
            socket_timeout=2.0,      # Short timeouts to keep response times low
            socket_connect_timeout=2.0,
            retry_on_timeout=True,
            max_connections=50        # Connection pooling
        )
        self.client = redis.Redis(connection_pool=self.pool)

    def _generate_key(self, data: Dict[str, Any]) -> str:
        """Generate an MD5 hash of the request dictionary for the cache key."""
        # Ensure dict sorting for consistent key generation
        serialized = json.dumps(data, sort_keys=True).encode("utf-8")
        hash_val = hashlib.md5(serialized).hexdigest()
        return f"prediction:{hash_val}"

    def get_prediction(self, request_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Fetch cached prediction by request data hash."""
        key = self._generate_key(request_data)
        try:
            val = self.client.get(key)
            if val:
                logger.info(f"Cache hit for key {key}")
                return json.loads(val)
            return None
        except redis.RedisError as e:
            logger.error(f"Redis cache GET failure: {e}")
            raise RuntimeError("Redis connection error") from e

    def set_prediction(self, request_data: Dict[str, Any], response_data: Dict[str, Any], ttl: int = 300) -> None:
        """Cache the prediction response."""
        key = self._generate_key(request_data)
        try:
            serialized_response = json.dumps(response_data)
            self.client.setex(key, ttl, serialized_response)
            logger.info(f"Successfully cached response under key {key} for {ttl}s")
        except redis.RedisError as e:
            logger.error(f"Redis cache SET failure: {e}")
            raise RuntimeError("Redis connection error") from e

    def check_health(self) -> bool:
        """Check Redis connection status."""
        try:
            self.client.ping()
            return True
        except redis.RedisError as e:
            logger.error(f"Redis health check failed: {e}")
            return False

# Singleton instance
cache_service = RedisCacheService()
