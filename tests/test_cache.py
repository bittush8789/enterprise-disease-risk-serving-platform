import pytest
from unittest.mock import patch
import redis
from app.services.cache_service import RedisCacheService

def test_cache_key_consistency():
    service = RedisCacheService()
    payload1 = {"patient_id": "PAT-1234", "age": 30, "gender": "Female"}
    payload2 = {"gender": "Female", "patient_id": "PAT-1234", "age": 30} # columns shuffled
    
    key1 = service._generate_key(payload1)
    key2 = service._generate_key(payload2)
    
    # MD5 keys should be equal even if dict keys are shuffled (due to sort_keys=True)
    assert key1 == key2
    assert key1.startswith("prediction:")

def test_cache_get_and_set():
    service = RedisCacheService()
    # Replace real client with mock
    class LocalMockClient:
        def __init__(self):
            self.data = {}
        def get(self, key):
            return self.data.get(key)
        def setex(self, key, ttl, val):
            self.data[key] = val
            return True
            
    service.client = LocalMockClient()
    
    req = {"patient_id": "P1", "age": 20}
    resp = {"probability": 0.15}
    
    assert service.get_prediction(req) is None
    service.set_prediction(req, resp, ttl=60)
    assert service.get_prediction(req) == resp

def test_cache_redis_error_propagation():
    service = RedisCacheService()
    
    # Mock redis client throwing exception
    class FailingClient:
        def get(self, key):
            raise redis.RedisError("Connection refused")
        def setex(self, key, ttl, val):
            raise redis.RedisError("Connection refused")
            
    service.client = FailingClient()
    req = {"patient_id": "P1", "age": 20}
    
    with pytest.raises(RuntimeError) as exc_info:
        service.get_prediction(req)
    assert "Redis connection error" in str(exc_info.value)
    
    with pytest.raises(RuntimeError) as exc_info:
        service.set_prediction(req, {}, 300)
    assert "Redis connection error" in str(exc_info.value)
