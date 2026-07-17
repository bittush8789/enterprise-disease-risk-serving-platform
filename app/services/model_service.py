import logging
from typing import Any, Dict, Optional
import mlflow
import mlflow.pyfunc
from mlflow.tracking import MlflowClient
from mlflow.exceptions import MlflowException
from app.core.config import settings

logger = logging.getLogger("disease_risk_serving")

class MLflowModelService:
    def __init__(self):
        self.model: Optional[Any] = None
        self.model_version: str = "unknown"
        self.metadata: Dict[str, Any] = {}
        mlflow.set_tracking_uri(settings.MLFLOW_TRACKING_URI)
        self.client = MlflowClient()

    def load_model(self, version: Optional[str] = None) -> None:
        """Loads the registered MLflow model from registry.
        
        If version is specified, loads that exact version.
        Otherwise, loads the version assigned to the Production stage.
        """
        try:
            mlflow.set_tracking_uri(settings.MLFLOW_TRACKING_URI)
            if version:
                model_uri = f"models:/{settings.MODEL_NAME}/{version}"
                logger.info(f"Attempting to load model from: {model_uri}")
                loaded_model = mlflow.pyfunc.load_model(model_uri)
                self.model = loaded_model
                self.model_version = version
                self._update_metadata_by_version(version)
            else:
                model_uri = f"models:/{settings.MODEL_NAME}/{settings.MODEL_STAGE}"
                logger.info(f"Attempting to load model from: {model_uri}")
                loaded_model = mlflow.pyfunc.load_model(model_uri)
                self.model = loaded_model
                
                # Fetch production version details
                latest_versions = self.client.get_latest_versions(
                    settings.MODEL_NAME, 
                    stages=[settings.MODEL_STAGE]
                )
                if latest_versions:
                    prod_details = latest_versions[0]
                    self.model_version = prod_details.version
                    self.metadata = {
                        "name": prod_details.name,
                        "version": prod_details.version,
                        "stage": prod_details.current_stage,
                        "run_id": prod_details.run_id,
                        "description": prod_details.description,
                        "last_updated_timestamp": prod_details.last_updated_timestamp
                    }
                else:
                    # Fallback to get details of registered model if latest production version is empty
                    self.model_version = "1"
                    self.metadata = {"name": settings.MODEL_NAME, "version": "1", "stage": settings.MODEL_STAGE}
            
            logger.info(f"Model loaded successfully. Name: {settings.MODEL_NAME}, Version: {self.model_version}")

        except Exception as e:
            logger.error(f"Error loading model from MLflow: {str(e)}")
            # For resilience (e.g. testing or local setup without registry initialized),
            # we don't crash entirely but mark model as None to allow custom exception handler to catch it.
            self.model = None
            self.model_version = "unknown"
            self.metadata = {}
            raise RuntimeError(f"MLflow model registry error: {str(e)}") from e

    def _update_metadata_by_version(self, version: str) -> None:
        """Fetches metadata for a specific model version."""
        try:
            mv = self.client.get_model_version(settings.MODEL_NAME, version)
            self.metadata = {
                "name": mv.name,
                "version": mv.version,
                "stage": mv.current_stage,
                "run_id": mv.run_id,
                "description": mv.description,
                "last_updated_timestamp": mv.last_updated_timestamp
            }
        except Exception as e:
            logger.warning(f"Could not retrieve metadata for model version {version}: {e}")
            self.metadata = {"name": settings.MODEL_NAME, "version": version}

    def predict(self, input_df) -> Any:
        """Runs predictions using the loaded pyfunc model."""
        if self.model is None:
            raise RuntimeError("Model is not loaded.")
        return self.model.predict(input_df)

    def get_info(self) -> Dict[str, Any]:
        """Returns model registry info and metadata."""
        return {
            "model_name": settings.MODEL_NAME,
            "loaded_version": self.model_version,
            "target_stage": settings.MODEL_STAGE,
            "tracking_uri": settings.MLFLOW_TRACKING_URI,
            "metadata": self.metadata,
            "is_loaded": self.model is not None
        }

# Singleton instance
model_service = MLflowModelService()
