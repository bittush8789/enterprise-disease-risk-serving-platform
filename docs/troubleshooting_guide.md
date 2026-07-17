# Document 7: Troubleshooting Guide

This guide describes how to identify, debug, and resolve common issues on the platform.

---

## Issue 1: API Returns 503 "Prediction service unavailable"

This error indicates that one of the critical dependency layers (PostgreSQL, Redis, or MLflow Model Registry) is unreachable or has failed.

### Step 1: Query `/health` endpoint
Run a curl command to check service health breakdown:
```bash
curl http://localhost:8000/health
```

### Step 2: Inspect individual service states

#### A. If `database` is "disconnected"
- **Symptom:** Logs show `Postgres connection failure` or `sqlalchemy.exc.OperationalError`.
- **Cause:** PostgreSQL container has crashed, is initializing, or credentials in `.env` do not match.
- **Resolution:**
  1. Check PostgreSQL container status:
     ```bash
     docker logs disease_risk_db
     ```
  2. Verify DB connection credentials in `.env` (`POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`).
  3. Restart database container:
     ```bash
     docker-compose restart db
     ```

#### B. If `cache` is "disconnected"
- **Symptom:** Logs show `Redis cache GET failure` or `ConnectionError`.
- **Cause:** Redis server is down or socket times out.
- **Resolution:**
  1. Check Redis logs:
     ```bash
     docker logs disease_risk_redis
     ```
  2. Test ping directly within the container:
     ```bash
     docker exec -it disease_risk_redis redis-cli ping
     ```
  3. Restart Redis container:
     ```bash
     docker-compose restart redis
     ```

#### C. If `model` is "unloaded"
- **Symptom:** Health check shows model status as "unloaded". Prediction requests fail.
- **Cause:** MLflow tracking server is down, or `mlflow-init` bootstrap script failed to train/register the model.
- **Resolution:**
  1. Check if the MLflow container is running and listening on port `5000`:
     ```bash
     docker logs disease_risk_mlflow
     ```
  2. Check the logs of the training bootstrap script to identify compilation/registry errors:
     ```bash
     docker logs disease_risk_mlflow_init
     ```
  3. If the model was trained but not loaded, trigger a manual reload once MLflow is online:
     ```bash
     curl -X POST -H "X-API-Key: dev-secret-key-12345" http://localhost:8000/model/reload
     ```

---

## Issue 2: Docker Port Bind Conflict on Startup

- **Symptom:** `docker-compose up` fails with:
  `Bind for 0.0.0.0:8000 failed: port is already allocated` or `port 5432 is already allocated`.
- **Cause:** Another service (like local PostgreSQL, local Redis, or another dev server) is already listening on the host port.
- **Resolution:**
  1. Identify the process using the target port (e.g., port 8000):
     - On Windows (PowerShell):
       ```powershell
       netstat -ano | findstr :8000
       ```
     - On Linux/macOS:
       ```bash
       lsof -i :8000
       ```
  2. Kill the conflicting process, or change the exposed host ports in `docker-compose.yml` (e.g., change `"8000:8000"` to `"8080:8000"`).

---

## Issue 3: Pydantic Validation Error during predictions

- **Symptom:** API returns `400 Bad Request` with `{"status": "error", "message": "Prediction service unavailable"}`.
- **Cause:** The client request payload is missing mandatory fields (e.g. `bmi` or `glucose_level`) or contains values outside allowed ranges (e.g. negative age).
- **Resolution:**
  1. Check application container stdout logs to view the validation errors:
     ```bash
     docker logs disease_risk_app
     ```
     *Look for lines like:* `Validation failure on /predict: [{'type': 'missing', 'loc': ('body', 'bmi')}]`.
  2. Adjust your client JSON payload to match the schema constraints defined in the API documentation.
