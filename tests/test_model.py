import pytest
import pandas as pd
import numpy as np
from unittest.mock import MagicMock, patch
from app.services.prediction_service import prediction_service
from app.services.model_service import model_service, MLflowModelService
from app.models.prediction import PredictionRequest
from scripts.train_and_register import DiseaseRiskModelWrapper

def test_risk_classification_boundaries(db_session):
    # Test boundary 0.30 (LOW RISK)
    with patch.object(model_service, "predict", return_value=[0.30]):
        req = PredictionRequest(
            patient_id="PAT-LOW", age=30, gender="Male", bmi=22.0,
            glucose_level=90.0, blood_pressure=110.0, insulin_level=40.0, family_history=False
        )
        resp = prediction_service.predict(req, db_session)
        assert resp.risk_level == "LOW"
        assert resp.prediction == "LOW_RISK"
        assert resp.disease_probability == 0.30

    # Test boundary 0.31 (MEDIUM RISK)
    with patch.object(model_service, "predict", return_value=[0.31]):
        req = PredictionRequest(
            patient_id="PAT-MED", age=35, gender="Female", bmi=25.0,
            glucose_level=110.0, blood_pressure=120.0, insulin_level=60.0, family_history=False
        )
        resp = prediction_service.predict(req, db_session)
        assert resp.risk_level == "MEDIUM"
        assert resp.prediction == "MEDIUM_RISK"
        assert resp.disease_probability == 0.31

    # Test boundary 0.70 (MEDIUM RISK)
    with patch.object(model_service, "predict", return_value=[0.70]):
        req = PredictionRequest(
            patient_id="PAT-MED2", age=40, gender="Female", bmi=28.0,
            glucose_level=125.0, blood_pressure=130.0, insulin_level=70.0, family_history=True
        )
        resp = prediction_service.predict(req, db_session)
        assert resp.risk_level == "MEDIUM"
        assert resp.prediction == "MEDIUM_RISK"
        assert resp.disease_probability == 0.70

    # Test boundary 0.71 (HIGH RISK)
    with patch.object(model_service, "predict", return_value=[0.71]):
        req = PredictionRequest(
            patient_id="PAT-HIGH", age=50, gender="Male", bmi=35.0,
            glucose_level=160.0, blood_pressure=150.0, insulin_level=110.0, family_history=True
        )
        resp = prediction_service.predict(req, db_session)
        assert resp.risk_level == "HIGH"
        assert resp.prediction == "HIGH_RISK"
        assert resp.disease_probability == 0.71

def test_disease_risk_model_wrapper():
    # Mock scikit-learn classifier
    class DummyClassifier:
        def predict_proba(self, X):
            res = []
            for val in X["age"]:
                if val > 50:
                    res.append([0.1, 0.9])
                else:
                    res.append([0.8, 0.2])
            return np.array(res)

    classifier = DummyClassifier()
    wrapper = DiseaseRiskModelWrapper(classifier)
    
    # Check predict interface for MLflow pyfunc model input
    df_input = pd.DataFrame({
        "age": [60, 25],
        "gender": [1, 0],
        "bmi": [32.0, 21.0],
        "glucose_level": [180.0, 95.0],
        "blood_pressure": [140.0, 110.0],
        "insulin_level": [120.0, 30.0],
        "family_history": [1, 0]
    })
    
    probs = wrapper.predict(context=None, model_input=df_input)
    assert len(probs) == 2
    assert probs[0] == 0.9
    assert probs[1] == 0.2

# --- Unit Tests for MLflowModelService to Increase Coverage ---

def test_mlflow_model_service_load_success():
    with patch("app.services.model_service.mlflow.pyfunc.load_model") as mock_load, \
         patch("app.services.model_service.MlflowClient") as mock_client_class:
         
         mock_client = MagicMock()
         mock_client_class.return_value = mock_client
         
         mock_version = MagicMock()
         mock_version.version = "5"
         mock_version.name = "disease-risk-model"
         mock_version.current_stage = "Production"
         mock_version.run_id = "run-123"
         mock_version.description = "Test description"
         mock_version.last_updated_timestamp = 123456789
         mock_client.get_latest_versions.return_value = [mock_version]
         
         service = MLflowModelService()
         service.load_model()
         
         assert service.model_version == "5"
         assert service.model is not None
         assert service.metadata["run_id"] == "run-123"
         mock_load.assert_called_once_with("models:/disease-risk-model/Production")

def test_mlflow_model_service_load_specific_version():
    with patch("app.services.model_service.mlflow.pyfunc.load_model") as mock_load, \
         patch("app.services.model_service.MlflowClient") as mock_client_class:
         
         mock_client = MagicMock()
         mock_client_class.return_value = mock_client
         
         mock_version = MagicMock()
         mock_version.version = "3"
         mock_version.name = "disease-risk-model"
         mock_version.current_stage = "None"
         mock_version.run_id = "run-456"
         mock_version.description = "Specific version"
         mock_version.last_updated_timestamp = 987654321
         mock_client.get_model_version.return_value = mock_version
         
         service = MLflowModelService()
         service.load_model(version="3")
         
         assert service.model_version == "3"
         mock_client.get_model_version.assert_called_once_with("disease-risk-model", "3")
         mock_load.assert_called_once_with("models:/disease-risk-model/3")

def test_mlflow_model_service_load_failure():
    with patch("app.services.model_service.mlflow.pyfunc.load_model", side_effect=Exception("Registry connection refused")), \
         patch("app.services.model_service.MlflowClient") as mock_client_class:
         
         mock_client = MagicMock()
         mock_client_class.return_value = mock_client
         
         service = MLflowModelService()
         with pytest.raises(RuntimeError) as exc_info:
             service.load_model()
             
         assert "MLflow model registry error" in str(exc_info.value)
         assert service.model is None

def test_mlflow_model_service_predict_and_info():
    with patch("app.services.model_service.MlflowClient"):
        service = MLflowModelService()
        # Predict without model loaded raises RuntimeError
        with pytest.raises(RuntimeError):
            service.predict(pd.DataFrame())
            
        service.model = MagicMock()
        service.model.predict.return_value = [0.45]
        res = service.predict(pd.DataFrame({"age": [30]}))
        assert res == [0.45]
        
        info = service.get_info()
        assert info["model_name"] == "disease-risk-model"
        assert info["is_loaded"] is True
