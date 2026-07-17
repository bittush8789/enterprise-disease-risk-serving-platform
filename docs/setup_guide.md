# Document 4: Setup & Configuration Guide

This guide describes how to run and configure the Enterprise Disease Risk Serving Platform.

---

## Prerequisites

Before setting up, ensure you have the following installed:
- **Docker** (v20.10.0 or higher)
- **Docker Compose** (v2.0.0 or higher)
- **Python** (v3.8 to v3.13) - *Only required for local development runs without Docker*

---

## Option A: Docker Compose Deployment (Recommended)

Docker Compose sets up all services (PostgreSQL, Redis, MLflow server, bootstrapping container, and FastAPI app) in an isolated virtual network.

### Step 1: Clone the repository & inspect configuration
Review the [`.env`](file:///d:/10-MLOps-projects/Real-Time%20Disease%20Risk%20Prediction/.env) configurations. The defaults are already configured to link container names (`db`, `redis`, `mlflow`).

### Step 2: Spin up the docker containers
Run the following build command in the root folder containing `docker-compose.yml`:
```bash
docker-compose up --build -d
```

### Step 3: Verify the bootstrap training process
The application depends on `mlflow-init` completing successfully. Monitor this container's logging:
```bash
docker logs -f disease_risk_mlflow_init
```
*Expected log output:*
```text
Waiting for MLflow tracking server at: http://mlflow:5000 ...
MLflow server is reachable!
Generating synthetic clinical dataset...
Training Random Forest Classifier...
Model trained. Accuracy: 0.8933, ROC AUC: 0.9412
Registering model in MLflow registry...
Promoting version 1 to Production...
Model version 1 is now in Production stage.
```

### Step 4: Verify the running services
Run `docker ps` to verify all five services are active:
```bash
docker ps
```
- `disease_risk_db` (Port 5432)
- `disease_risk_redis` (Port 6379)
- `disease_risk_mlflow` (Port 5000)
- `disease_risk_app` (Port 8000)

---

## Option B: Local Developer Run

If you wish to run the app outside Docker:

### Step 1: Setup virtual environment & dependencies
```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
pip install -r requirements.txt
```

### Step 2: Update local environment settings
Open your local [`.env`](file:///d:/10-MLOps-projects/Real-Time%20Disease%20Risk%20Prediction/.env) file and replace:
- `POSTGRES_HOST=db` $\rightarrow$ `POSTGRES_HOST=localhost`
- `REDIS_HOST=redis` $\rightarrow$ `REDIS_HOST=localhost`
- Ensure local Postgres and Redis are running on your system ports.

### Step 3: Run the MLflow tracking server locally
```bash
mlflow server --host 127.0.0.1 --port 5000 --backend-store-uri sqlite:///mlflow.db --default-artifact-root ./mlruns
```

### Step 4: Execute bootstrap training
```bash
python scripts/train_and_register.py
```

### Step 5: Start local FastAPI server
```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

---

## Service URLs & Dashboards

- **FastAPI Documentation (Swagger UI):** `http://localhost:8000/docs`
- **FastAPI Alternative Docs (ReDoc):** `http://localhost:8000/redoc`
- **MLflow Registry Server UI:** `http://localhost:5000`
- **Health Check Endpoint:** `http://localhost:8000/health`
