import logging
import time
import pandas as pd
from typing import Dict, Any
from sqlalchemy.orm import Session
from app.models.prediction import PredictionRequest, PredictionResponse
from app.services.cache_service import cache_service
from app.services.model_service import model_service
from app.services.logging_service import logging_service
from app.core.exceptions import PredictionServiceException

logger = logging.getLogger("disease_risk_serving")

class PredictionService:
    def predict(self, request: PredictionRequest, db: Session) -> PredictionResponse:
        """Orchestrates prediction flow: Cache checking, model execution, logging, and caching."""
        request_dict = request.model_dump()
        start_time = time.time()

        # 1. Try fetching from Redis Cache
        try:
            cached_data = cache_service.get_prediction(request_dict)
            if cached_data:
                # Override the latency to represent cache retrieval latency
                latency_ms = (time.time() - start_time) * 1000
                cached_data["latency_ms"] = round(latency_ms, 2)
                return PredictionResponse(**cached_data)
        except Exception as e:
            # If Redis fails, check if we must enforce cache availability.
            # Per functional requirements: handle Redis failure by throwing service unavailable
            logger.error(f"Redis cache check failed: {e}")
            raise PredictionServiceException("Prediction service unavailable (Cache Error)") from e

        # 2. Cache Miss - Run ML Model Prediction
        # Preprocess features into the format expected by the model
        try:
            # Convert request fields to features dataframe
            features = {
                "age": request.age,
                "gender": 1 if request.gender == "Male" else (0 if request.gender == "Female" else 0.5),
                "bmi": request.bmi,
                "glucose_level": request.glucose_level,
                "blood_pressure": request.blood_pressure,
                "insulin_level": request.insulin_level,
                "family_history": 1 if request.family_history else 0
            }
            features_df = pd.DataFrame([features])
            
            # Verify model is loaded
            if model_service.model is None:
                logger.info("Model not loaded, attempting to load...")
                model_service.load_model()
                
            inference_start = time.time()
            prediction_output = model_service.predict(features_df)
            inference_time = (time.time() - inference_start) * 1000
            
            # Parse output. If model_service returns a list/numpy array
            if hasattr(prediction_output, "tolist"):
                prob_val = prediction_output.tolist()[0]
            elif isinstance(prediction_output, list):
                prob_val = prediction_output[0]
            else:
                prob_val = float(prediction_output)

            # Safeguard probability boundaries
            prob_val = max(0.0, min(1.0, prob_val))
            
        except Exception as e:
            logger.error(f"Inference failure: {e}")
            raise PredictionServiceException("Prediction service unavailable (Inference Error)") from e

        # 3. Apply Disease Risk Classification Business Rules
        # 0.00 - 0.30 = LOW RISK
        # 0.31 - 0.70 = MEDIUM RISK
        # 0.71 - 1.00 = HIGH RISK
        if prob_val <= 0.30:
            risk_level = "LOW"
            prediction = "LOW_RISK"
        elif prob_val <= 0.70:
            risk_level = "MEDIUM"
            prediction = "MEDIUM_RISK"
        else:
            risk_level = "HIGH"
            prediction = "HIGH_RISK"

        # Calculate latency
        total_latency_ms = (time.time() - start_time) * 1000

        # Construct prediction response
        response = PredictionResponse(
            patient_id=request.patient_id,
            disease_probability=round(prob_val, 2),
            risk_level=risk_level,
            prediction=prediction,
            model_version=model_service.model_version,
            latency_ms=round(total_latency_ms, 2)
        )
        response_dict = response.model_dump()

        # 4. Log transaction to PostgreSQL Database
        try:
            logging_service.log_prediction(
                db=db,
                patient_id=request.patient_id,
                request_data=request_dict,
                prediction_result=response_dict,
                disease_probability=response.disease_probability,
                latency_ms=response.latency_ms,
                model_version=response.model_version
            )
        except Exception as e:
            logger.error(f"PostgreSQL logging failed: {e}")
            raise PredictionServiceException("Prediction service unavailable (Database Error)") from e

        # 5. Cache result in Redis for subsequent requests
        try:
            cache_service.set_prediction(request_dict, response_dict)
        except Exception as e:
            logger.error(f"Redis cache write failed: {e}")
            raise PredictionServiceException("Prediction service unavailable (Cache Error)") from e

        return response

prediction_service = PredictionService()
