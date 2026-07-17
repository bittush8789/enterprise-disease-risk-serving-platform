import os
import time
import logging
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, roc_auc_score
import mlflow
import mlflow.pyfunc
import httpx
from app.core.config import settings

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("train_and_register")

# Custom MLflow Python Model wrapper to return probabilities
class DiseaseRiskModelWrapper(mlflow.pyfunc.PythonModel):
    def __init__(self, model):
        self.model = model

    def predict(self, context, model_input: pd.DataFrame) -> np.ndarray:
        """Returns the probability of the patient having the disease (class 1)."""
        # Ensure correct column ordering matching feature list
        feature_cols = [
            "age", "gender", "bmi", "glucose_level", 
            "blood_pressure", "insulin_level", "family_history"
        ]
        
        # Ensure we have a dataframe with correct columns
        df_input = model_input[feature_cols]
        probabilities = self.model.predict_proba(df_input)
        
        # probabilities shape is (N, 2), return probability of class 1
        return probabilities[:, 1]

def wait_for_mlflow():
    """Wait until MLflow server is online and responding."""
    tracking_uri = settings.MLFLOW_TRACKING_URI
    logger.info(f"Waiting for MLflow tracking server at: {tracking_uri} ...")
    max_retries = 12
    for i in range(max_retries):
        try:
            # Check MLflow UI/Health endpoints
            response = httpx.get(tracking_uri, timeout=5.0)
            if response.status_code == 200 or response.status_code == 302:
                logger.info("MLflow server is reachable!")
                return
        except Exception:
            pass
        logger.info(f"MLflow not ready yet. Retry {i+1}/{max_retries} in 5 seconds...")
        time.sleep(5)
    raise RuntimeError("MLflow tracking server was not reachable after 60 seconds.")

def generate_synthetic_data(num_samples: int = 1500) -> pd.DataFrame:
    """Generates synthetic patient records for Diabetes Risk Prediction."""
    np.random.seed(42)
    
    age = np.random.randint(18, 85, size=num_samples)
    gender = np.random.choice([0, 1], size=num_samples) # 1 = Male, 0 = Female
    bmi = np.random.uniform(18.0, 42.0, size=num_samples)
    glucose_level = np.random.uniform(70.0, 240.0, size=num_samples)
    blood_pressure = np.random.uniform(70.0, 170.0, size=num_samples)
    insulin_level = np.random.uniform(10.0, 320.0, size=num_samples)
    family_history = np.random.choice([0, 1], size=num_samples, p=[0.6, 0.4])

    # Logodds function representing diabetes risk formula
    log_odds = (
        -7.5 
        + 0.025 * age 
        + 0.2 * gender 
        + 0.09 * bmi 
        + 0.02 * glucose_level 
        + 0.005 * blood_pressure 
        + 0.003 * insulin_level 
        + 1.6 * family_history
    )
    
    probabilities = 1 / (1 + np.exp(-log_odds))
    target = (probabilities > np.random.uniform(0, 1, size=num_samples)).astype(int)

    df = pd.DataFrame({
        "age": age,
        "gender": gender,
        "bmi": bmi,
        "glucose_level": glucose_level,
        "blood_pressure": blood_pressure,
        "insulin_level": insulin_level,
        "family_history": family_history,
        "target": target
    })
    return df

def main():
    # 1. Connect to MLflow
    wait_for_mlflow()
    mlflow.set_tracking_uri(settings.MLFLOW_TRACKING_URI)
    
    # 2. Load and Split Dataset
    logger.info("Generating synthetic clinical dataset...")
    df = generate_synthetic_data()
    X = df.drop(columns=["target"])
    y = df["target"]
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # 3. Train Model
    logger.info("Training Random Forest Classifier...")
    n_estimators = 120
    max_depth = 8
    model = RandomForestClassifier(n_estimators=n_estimators, max_depth=max_depth, random_state=42)
    model.fit(X_train, y_train)
    
    # Evaluate
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]
    
    accuracy = accuracy_score(y_test, y_pred)
    roc_auc = roc_auc_score(y_test, y_prob)
    
    logger.info(f"Model trained. Accuracy: {accuracy:.4f}, ROC AUC: {roc_auc:.4f}")
    
    # 4. Log to MLflow
    experiment_name = "disease-risk-prediction"
    mlflow.set_experiment(experiment_name)
    
    with mlflow.start_run(run_name="bootstrap-model-run") as run:
        # Log parameters & metrics
        mlflow.log_param("n_estimators", n_estimators)
        mlflow.log_param("max_depth", max_depth)
        mlflow.log_metric("accuracy", accuracy)
        mlflow.log_metric("roc_auc", roc_auc)
        
        # Log input dataset schema signature
        signature = mlflow.models.signature.infer_signature(X_train, y_prob)
        
        # Log the model wrapped in custom PyFunc
        logger.info("Registering model in MLflow registry...")
        wrapped_model = DiseaseRiskModelWrapper(model)
        
        # This will register the model in registry under settings.MODEL_NAME
        model_info = mlflow.pyfunc.log_model(
            artifact_path="model",
            python_model=wrapped_model,
            registered_model_name=settings.MODEL_NAME,
            signature=signature
        )
        
        run_id = run.info.run_id
        logger.info(f"MLflow Run ID: {run_id}")
        logger.info(f"Model version registered.")

    # 5. Transition newly registered model version to Production stage
    client = mlflow.tracking.MlflowClient()
    latest_versions = client.get_latest_versions(settings.MODEL_NAME, stages=["None"])
    if latest_versions:
        # Grab the latest version registered
        latest_version = latest_versions[-1].version
        logger.info(f"Promoting version {latest_version} to Production...")
        client.transition_model_version_stage(
            name=settings.MODEL_NAME,
            version=latest_version,
            stage=settings.MODEL_STAGE
        )
        logger.info(f"Model version {latest_version} is now in {settings.MODEL_STAGE} stage.")
    else:
        logger.warning("Could not find registered version. Stage promotion skipped.")

if __name__ == "__main__":
    main()
