# Enterprise Disease Risk Serving Platform

A high-performance, production-grade clinical risk assessment platform serving real-time machine learning predictions for diabetes risk and logging clinical transactions.

---

## 🚀 Quick Start (Docker Compose)

Spin up the entire stack (PostgreSQL, Redis, MLflow Server, Bootstrap script, and FastAPI App) with a single command:

```bash
docker-compose up --build -d
```

### 1. Wait for Bootstrap
Check the model training and registration progress:
```bash
docker logs -f disease_risk_mlflow_init
```

### 2. Verify Health
Ensure all components are connected and the model is loaded:
```bash
curl http://localhost:8000/health
```

### 3. Run AI FDE Client Verification
Execute the client integration demo to test prediction requests, verify the Redis cache latency speedup, and check error handling:
```bash
python scripts/client_integration_demo.py
```

---

## 📂 Project Directory Structure

```text
Real-Time Disease Risk Prediction/
├── app/
│   ├── api/
│   │   ├── routes/
│   │   │   ├── model.py            # Routes for model info and reloading
│   │   │   └── predictions.py      # Routes for /predict and history log
│   │   └── dependencies.py         # DB session & API key authentication injection
│   ├── core/
│   │   ├── config.py               # Pydantic Settings configuration loader
│   │   ├── exceptions.py           # Standardized clinical error handlers
│   │   └── security.py             # X-API-Key validator middleware
│   ├── database/
│   │   ├── models.py               # SQLAlchemy db log mapping
│   │   └── session.py              # Postgres connection pool config
│   ├── models/
│   │   └── prediction.py           # Pydantic schema validation models
│   ├── services/
│   │   ├── cache_service.py        # Redis client manager
│   │   ├── logging_service.py      # Postgres logger client
│   │   ├── model_service.py        # MLflow model loader interface
│   │   └── prediction_service.py   # Primary pipeline orchestrator
│   └── main.py                     # FastAPI entry point, lifecycle events, and /health
├── docs/                           # Dedicated Technical Documentation Library
├── scripts/
│   ├── train_and_register.py       # Bootstrap training & model promotion script
│   └── client_integration_demo.py  # FDE client integration tester tool
├── tests/                          # 18-test offline validation suite (87% coverage)
├── Dockerfile                      # Production-grade multi-stage secure container build
├── docker-compose.yml              # Container infrastructure composer
├── requirements.txt                # Python libraries
├── .env                            # App environment secrets configuration
└── README.md
```

---

## 📖 Technical Documentation Library

Detailed documentation guides are available in the **[docs/](file:///d:/10-MLOps-projects/Real-Time%20Disease%20Risk%20Prediction/docs/)** folder:

1. **[Project Overview](file:///d:/10-MLOps-projects/Real-Time%20Disease%20Risk%20Prediction/docs/project_overview.md):** Technology stack details and MLOps core features.
2. **[Healthcare Business Problem](file:///d:/10-MLOps-projects/Real-Time%20Disease%20Risk%20Prediction/docs/healthcare_business_problem.md):** Clinical relevance, late-diagnosis complications, and EHR workflow value.
3. **[Architecture & Design](file:///d:/10-MLOps-projects/Real-Time%20Disease%20Risk%20Prediction/docs/architecture_diagram.md):** High-Level Design (HLD) flow, Low-Level Design (LLD), and Component sequence diagram.
4. **[Setup & Configuration](file:///d:/10-MLOps-projects/Real-Time%20Disease%20Risk%20Prediction/docs/setup_guide.md):** Guides for Docker Compose and local developer environment runs.
5. **[API Specifications](file:///d:/10-MLOps-projects/Real-Time%20Disease%20Risk%20Prediction/docs/api_documentation.md):** Detailed endpoint requests, query parameters, outputs, and auth details.
6. **[Deployment & Network](file:///d:/10-MLOps-projects/Real-Time%20Disease%20Risk%20Prediction/docs/deployment_guide.md):** Docker network layouts, volumes, and staging environment setups.
7. **[Troubleshooting Guide](file:///d:/10-MLOps-projects/Real-Time%20Disease%20Risk%20Prediction/docs/troubleshooting_guide.md):** Diagnosing database drops, redis timeouts, port conflicts, and validation errors.
8. **[Scaling Guide (10,000+ RPM)](file:///d:/10-MLOps-projects/Real-Time%20Disease%20Risk%20Prediction/docs/scaling_guide.md):** Gunicorn worker settings, DB connection pooling sizing, and Redis LRU eviction policies.

---

## 🧪 Testing Suite Validation

Run tests and check code coverage locally:
```bash
pytest --cov=app tests/
```
*Current test suite: 18 tests passing, 87% overall coverage, 91% coverage on model loading interfaces.*
