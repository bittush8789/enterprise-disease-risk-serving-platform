import pytest
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
from app.services.logging_service import logging_service
from app.database.models import PredictionLog

def test_database_log_and_retrieve(db_session):
    patient_id = "PAT-9999"
    request_data = {"age": 45, "gender": "Male"}
    prediction_result = {"disease_probability": 0.85, "risk_level": "HIGH"}
    disease_probability = 0.85
    latency_ms = 15.4
    model_version = "1"
    
    # 1. Log prediction
    log_entry = logging_service.log_prediction(
        db=db_session,
        patient_id=patient_id,
        request_data=request_data,
        prediction_result=prediction_result,
        disease_probability=disease_probability,
        latency_ms=latency_ms,
        model_version=model_version
    )
    
    assert log_entry.id is not None
    assert log_entry.patient_id == patient_id
    assert log_entry.disease_probability == disease_probability
    assert log_entry.latency_ms == latency_ms
    assert log_entry.model_version == model_version
    assert isinstance(log_entry.created_at, datetime)
    
    # 2. Retrieve prediction history
    history = logging_service.get_prediction_history(db=db_session, patient_id=patient_id)
    assert len(history) == 1
    assert history[0].patient_id == patient_id
    assert history[0].disease_probability == disease_probability

    # Filter with non-existent patient
    history_empty = logging_service.get_prediction_history(db=db_session, patient_id="PAT-NONE")
    assert len(history_empty) == 0

def test_database_error_handling(db_session):
    # Mock session to trigger error on add
    class FailingSession:
        def add(self, instance):
            raise SQLAlchemyError("Mock operational database failure")
        def rollback(self):
            pass
            
    with pytest.raises(RuntimeError) as exc_info:
        logging_service.log_prediction(
            db=FailingSession(),
            patient_id="PAT-ERR",
            request_data={},
            prediction_result={},
            disease_probability=0.0,
            latency_ms=0.0,
            model_version="1"
        )
    assert "Database logging error" in str(exc_info.value)
