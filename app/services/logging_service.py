import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.database.models import PredictionLog

logger = logging.getLogger("disease_risk_serving")

class LoggingService:
    def log_prediction(
        self,
        db: Session,
        patient_id: str,
        request_data: Dict[str, Any],
        prediction_result: Dict[str, Any],
        disease_probability: float,
        latency_ms: float,
        model_version: str
    ) -> PredictionLog:
        """Saves a prediction transaction to the PostgreSQL database."""
        try:
            log_entry = PredictionLog(
                id=uuid.uuid4(),
                patient_id=patient_id,
                request_data=request_data,
                prediction_result=prediction_result,
                disease_probability=disease_probability,
                latency_ms=latency_ms,
                model_version=model_version,
                created_at=datetime.utcnow()
            )
            db.add(log_entry)
            db.commit()
            db.refresh(log_entry)
            logger.info(f"Successfully logged prediction to database for patient {patient_id}")
            return log_entry
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"PostgreSQL logging failure: {e}")
            raise RuntimeError("Database logging error") from e

    def get_prediction_history(
        self,
        db: Session,
        patient_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[PredictionLog]:
        """Fetches history of predictions with optional filters."""
        try:
            query = db.query(PredictionLog)
            if patient_id:
                query = query.filter(PredictionLog.patient_id == patient_id)
            return query.order_by(PredictionLog.created_at.desc()).offset(offset).limit(limit).all()
        except SQLAlchemyError as e:
            logger.error(f"PostgreSQL fetch failure: {e}")
            raise RuntimeError("Database read error") from e

logging_service = LoggingService()
