import uuid
from sqlalchemy import Column, String, Float, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from app.database.session import Base

class PredictionLog(Base):
    __tablename__ = "prediction_logs"

    # UUID type decorator mapping for PostgreSQL UUID type
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(String(100), nullable=False, index=True)
    request_data = Column(JSON, nullable=False)
    prediction_result = Column(JSON, nullable=False)
    disease_probability = Column(Float, nullable=False)
    latency_ms = Column(Float, nullable=False)
    model_version = Column(String(50), nullable=False)
    created_at = Column(DateTime, nullable=False)
