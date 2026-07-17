import pytest
from unittest.mock import patch
from app.services.cache_service import cache_service

def test_health_check_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["services"]["database"] == "connected"
    assert data["services"]["cache"] == "connected"
    assert data["services"]["model"] == "loaded"

def test_predict_requires_authentication(client):
    payload = {
        "patient_id": "PAT-1001",
        "age": 45,
        "gender": "Male",
        "bmi": 31.5,
        "glucose_level": 185.0,
        "blood_pressure": 145.0,
        "insulin_level": 120.0,
        "family_history": True
    }
    # No API Key
    response = client.post("/predict", json=payload)
    assert response.status_code == 401
    assert "API Key missing" in response.json()["detail"]

    # Invalid API Key
    response = client.post("/predict", json=payload, headers={"X-API-Key": "wrong-key"})
    assert response.status_code == 401
    assert "Invalid API Key" in response.json()["detail"]

def test_predict_success_and_caching(client, auth_headers):
    payload = {
        "patient_id": "PAT-1002",
        "age": 55,
        "gender": "Female",
        "bmi": 32.5,
        "glucose_level": 150.0,
        "blood_pressure": 130.0,
        "insulin_level": 80.0,
        "family_history": True
    }
    
    # First request: Cache miss, computes and saves to DB/cache
    response = client.post("/predict", json=payload, headers=auth_headers)
    assert response.status_code == 200
    data1 = response.json()
    assert data1["patient_id"] == "PAT-1002"
    assert data1["disease_probability"] == 0.85
    assert data1["risk_level"] == "HIGH"
    assert data1["prediction"] == "HIGH_RISK"
    assert data1["model_version"] == "1"
    assert "latency_ms" in data1
    
    # Second request: Cache hit, reads from Redis cache
    response = client.post("/predict", json=payload, headers=auth_headers)
    assert response.status_code == 200
    data2 = response.json()
    assert data2["patient_id"] == "PAT-1002"
    assert data2["disease_probability"] == 0.85
    assert data2["risk_level"] == "HIGH"
    
    # Validate cache contents
    cached_key = cache_service._generate_key(payload)
    assert cache_service.client.get(cached_key) is not None

def test_predict_validation_error_maps_to_standard_error(client, auth_headers):
    # Invalid Payload: Missing bmi
    invalid_payload = {
        "patient_id": "PAT-1003",
        "age": 45,
        "gender": "Male",
        "glucose_level": 185.0,
        "blood_pressure": 145.0,
        "insulin_level": 120.0,
        "family_history": True
    }
    response = client.post("/predict", json=invalid_payload, headers=auth_headers)
    assert response.status_code == 400
    # Custom validation handler response:
    assert response.json() == {"status": "error", "message": "Prediction service unavailable"}

def test_get_predictions_history(client, auth_headers):
    # Send a prediction first to populate database for this test case
    payload = {
        "patient_id": "PAT-LOGGED",
        "age": 45,
        "gender": "Male",
        "bmi": 28.0,
        "glucose_level": 120.0,
        "blood_pressure": 115.0,
        "insulin_level": 45.0,
        "family_history": False
    }
    client.post("/predict", json=payload, headers=auth_headers)

    # Now retrieve logged predictions
    response = client.get("/predictions", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["patient_id"] == "PAT-LOGGED"
    assert "disease_probability" in data[0]

    # Filter by patient_id
    response = client.get("/predictions?patient_id=PAT-LOGGED", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) == 1

def test_model_info_endpoint(client, auth_headers):
    response = client.get("/model/info", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["model_name"] == "disease-risk-model"
    assert data["loaded_version"] == "1"
    assert data["target_stage"] == "Production"

def test_model_reload_endpoint(client, auth_headers):
    with patch("app.services.model_service.model_service.load_model") as mock_load:
        response = client.post("/model/reload?version=2", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["status"] == "success"
        mock_load.assert_called_once_with(version="2")
