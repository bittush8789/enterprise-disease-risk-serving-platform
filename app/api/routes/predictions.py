from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.models.prediction import PredictionRequest, PredictionResponse
from app.services.prediction_service import prediction_service
from app.services.logging_service import logging_service
from app.api.dependencies import get_database_session, ProtectedEndpointDependencies

router = APIRouter(tags=["Predictions"])

@router.post("/predict", response_model=PredictionResponse, status_code=status.HTTP_200_OK)
def predict_disease(
    request: PredictionRequest,
    deps: ProtectedEndpointDependencies = Depends()
):
    """Predicts disease risk using ML models, logs the run, and caches the prediction."""
    return prediction_service.predict(request=request, db=deps.db)

@router.get("/predictions", response_model=List[dict], status_code=status.HTTP_200_OK)
def get_predictions(
    patient_id: Optional[str] = Query(None, description="Filter predictions by Patient ID"),
    limit: int = Query(100, ge=1, le=1000, description="Number of logs to retrieve"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    deps: ProtectedEndpointDependencies = Depends()
):
    """Retrieves prediction history logs from PostgreSQL."""
    logs = logging_service.get_prediction_history(
        db=deps.db,
        patient_id=patient_id,
        limit=limit,
        offset=offset
    )
    # Serialize logs to simple JSON format
    return [
        {
            "id": str(log.id),
            "patient_id": log.patient_id,
            "request_data": log.request_data,
            "prediction_result": log.prediction_result,
            "disease_probability": log.disease_probability,
            "latency_ms": log.latency_ms,
            "model_version": log.model_version,
            "created_at": log.created_at.isoformat()
        }
        for log in logs
    ]
