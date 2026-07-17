# Document 5: API Documentation

All protected endpoints require authentication using the `X-API-Key` request header.

- **Default API Key:** `dev-secret-key-12345`
- **Location:** Header parameter `X-API-Key`

---

## Endpoint 1: Health Status Check

* **Path:** `GET /health`
* **Authentication Required:** No
* **Description:** Performs health checks against database query responsiveness, Redis ping status, and checks if the MLflow model is loaded in memory.
* **Curl Command:**
  ```bash
  curl http://localhost:8000/health
  ```
* **Success Response (200 OK):**
  ```json
  {
      "status": "healthy",
      "environment": "development",
      "services": {
          "database": "connected",
          "cache": "connected",
          "model": "loaded"
      }
  }
  ```
* **Degraded Response (503 Service Unavailable):**
  ```json
  {
      "status": "unhealthy",
      "environment": "development",
      "services": {
          "database": "disconnected",
          "cache": "connected",
          "model": "loaded"
      }
  }
  ```

---

## Endpoint 2: Disease Prediction Request

* **Path:** `POST /predict`
* **Authentication Required:** Yes (`X-API-Key`)
* **Description:** Runs model inference, classifies risk levels, logs run metrics to database, and writes output to cache.
* **Curl Command:**
  ```bash
  curl -X POST http://localhost:8000/predict \
       -H "X-API-Key: dev-secret-key-12345" \
       -H "Content-Type: application/json" \
       -d '{
           "patient_id": "PAT-1001",
           "age": 45,
           "gender": "Male",
           "bmi": 31.5,
           "glucose_level": 185.0,
           "blood_pressure": 145.0,
           "insulin_level": 120.0,
           "family_history": true
       }'
  ```
* **Request Fields Specification:**
  - `patient_id` (str, required): Unique patient tracking code.
  - `age` (int, required): Age in years (`0` to `120`).
  - `gender` (str, required): biological gender (`"Male"`, `"Female"`, `"Other"`).
  - `bmi` (float, required): Body Mass Index (`0.0` to `100.0`).
  - `glucose_level` (float, required): Fasting glucose level in mg/dL.
  - `blood_pressure` (float, required): Systolic blood pressure in mmHg.
  - `insulin_level` (float, required): Insulin levels in mIU/L.
  - `family_history` (bool, required): Patient family chronic history.
* **Success Response (200 OK):**
  ```json
  {
      "patient_id": "PAT-1001",
      "disease_probability": 0.85,
      "risk_level": "HIGH",
      "prediction": "HIGH_RISK",
      "model_version": "1",
      "latency_ms": 12.4
  }
  ```

---

## Endpoint 3: Prediction Transaction Log History

* **Path:** `GET /predictions`
* **Authentication Required:** Yes (`X-API-Key`)
* **Description:** Queries database prediction logging history.
* **Query Parameters:**
  - `patient_id` (str, optional): Filters logs for specific patient.
  - `limit` (int, optional, default=100): Maximum records to fetch.
  - `offset` (int, optional, default=0): Pagination offset index.
* **Curl Command:**
  ```bash
  curl -H "X-API-Key: dev-secret-key-12345" "http://localhost:8000/predictions?patient_id=PAT-1001&limit=5"
  ```
* **Success Response (200 OK):**
  ```json
  [
      {
          "id": "83be992c-80df-4d51-9653-e910f545a90d",
          "patient_id": "PAT-1001",
          "request_data": {
              "patient_id": "PAT-1001",
              "age": 45,
              "gender": "Male",
              "bmi": 31.5,
              "glucose_level": 185.0,
              "blood_pressure": 145.0,
              "insulin_level": 120.0,
              "family_history": true
          },
          "prediction_result": {
              "patient_id": "PAT-1001",
              "disease_probability": 0.85,
              "risk_level": "HIGH",
              "prediction": "HIGH_RISK",
              "model_version": "1",
              "latency_ms": 12.4
          },
          "disease_probability": 0.85,
          "latency_ms": 12.4,
          "model_version": "1",
          "created_at": "2026-07-18T02:30:00.123456"
      }
  ]
  ```

---

## Endpoint 4: Active Model Registry Info

* **Path:** `GET /model/info`
* **Authentication Required:** Yes (`X-API-Key`)
* **Description:** Retrieves registry details and metadata from MLflow.
* **Curl Command:**
  ```bash
  curl -H "X-API-Key: dev-secret-key-12345" http://localhost:8000/model/info
  ```
* **Success Response (200 OK):**
  ```json
  {
      "model_name": "disease-risk-model",
      "loaded_version": "1",
      "target_stage": "Production",
      "tracking_uri": "http://mlflow:5000",
      "metadata": {
          "name": "disease-risk-model",
          "version": "1",
          "stage": "Production",
          "run_id": "18f0a6d5bc89...",
          "description": "Random Forest diabetes model",
          "last_updated_timestamp": 1783456789000
      },
      "is_loaded": true
  }
  ```

---

## Endpoint 5: Reload Serving Model

* **Path:** `POST /model/reload`
* **Authentication Required:** Yes (`X-API-Key`)
* **Description:** Hot-reloads the active in-memory model from MLflow registry.
* **Query Parameters:**
  - `version` (str, optional): Target model version (e.g. `2`). If omitted, pulls latest version flagged as `Production`.
* **Curl Command:**
  ```bash
  curl -X POST -H "X-API-Key: dev-secret-key-12345" "http://localhost:8000/model/reload?version=2"
  ```
* **Success Response (200 OK):**
  ```json
  {
      "status": "success",
      "message": "Model reloaded successfully. Active version: 2",
      "info": {
          "model_name": "disease-risk-model",
          "loaded_version": "2",
          "target_stage": "Production",
          "tracking_uri": "http://mlflow:5000",
          "is_loaded": true
      }
  }
  ```

---

## Error Handling Specifications

When database connectivity fails, cache instances crash, or request schemas are invalid, the API returns standardized error response formatting.

* **Database / Cache Offline / MLflow Failure Response (503 Service Unavailable):**
  ```json
  {
      "status": "error",
      "message": "Prediction service unavailable"
  }
  ```
* **Invalid Input Format (400 Bad Request):**
  ```json
  {
      "status": "error",
      "message": "Prediction service unavailable"
  }
  ```
