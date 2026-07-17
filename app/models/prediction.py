from typing import Literal
from pydantic import BaseModel, Field

class PredictionRequest(BaseModel):
    patient_id: str = Field(..., description="Unique identifier for the patient", min_length=1)
    age: int = Field(..., description="Age of the patient in years", ge=0, le=120)
    gender: Literal["Male", "Female", "Other"] = Field(..., description="Biological gender of the patient")
    bmi: float = Field(..., description="Body Mass Index", gt=0.0, le=100.0)
    glucose_level: float = Field(..., description="Fasting blood glucose level in mg/dL", gt=0.0)
    blood_pressure: float = Field(..., description="Systolic blood pressure in mmHg", gt=0.0)
    insulin_level: float = Field(..., description="Insulin level in mIU/L", ge=0.0)
    family_history: bool = Field(..., description="Family history of disease status")

    class Config:
        json_schema_extra = {
            "example": {
                "patient_id": "PAT-1001",
                "age": 45,
                "gender": "Male",
                "bmi": 31.5,
                "glucose_level": 185.0,
                "blood_pressure": 145.0,
                "insulin_level": 120.0,
                "family_history": True
            }
        }

class PredictionResponse(BaseModel):
    patient_id: str
    disease_probability: float
    risk_level: Literal["LOW", "MEDIUM", "HIGH"]
    prediction: Literal["LOW_RISK", "MEDIUM_RISK", "HIGH_RISK"]
    model_version: str
    latency_ms: float
