import logging
from fastapi import FastAPI, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.config import settings
from app.core.exceptions import setup_exception_handlers
from app.database.session import engine, Base, get_db
from app.services.cache_service import cache_service
from app.services.model_service import model_service
from app.api.routes import model, predictions

# Set up logging configuration
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("disease_risk_serving")

# Initialize database tables on startup
try:
    if engine is not None:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables initialized successfully.")
except Exception as e:
    logger.error(f"Error during database table creation: {e}")

# Create FastAPI app instance
app = FastAPI(
    title="Enterprise Disease Risk Serving Platform",
    description="Production-grade real-time AI serving platform predicting patient disease risk",
    version="1.0.0"
)

# Register Exception Handlers
setup_exception_handlers(app)

# Register Routers
app.include_router(predictions.router)
app.include_router(model.router)

@app.on_event("startup")
def startup_event():
    """Run startup sequences: load model from MLflow registry."""
    logger.info("Initializing application startup sequence...")
    try:
        model_service.load_model()
    except Exception as e:
        logger.error(f"Startup warning: Could not pre-load model from MLflow: {e}")
        # We don't crash the server to allow the container to start, 
        # allowing admins to inspect and reload the model later.

@app.get("/health", tags=["System Status"])
def health_check(db: Session = Depends(get_db)):
    """Health Check endpoint verifying database, cache, and model connectivity."""
    db_healthy = False
    try:
        # Simple query to check database responsiveness
        db.execute(text("SELECT 1"))
        db_healthy = True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")

    cache_healthy = cache_service.check_health()
    model_loaded = model_service.model is not None

    overall_healthy = db_healthy and cache_healthy and model_loaded

    status_code = status.HTTP_200_OK if overall_healthy else status.HTTP_503_SERVICE_UNAVAILABLE

    return JSONResponse(
        status_code=status_code,
        content={
            "status": "healthy" if overall_healthy else "unhealthy",
            "environment": settings.APP_ENV,
            "services": {
                "database": "connected" if db_healthy else "disconnected",
                "cache": "connected" if cache_healthy else "disconnected",
                "model": "loaded" if model_loaded else "unloaded"
            }
        }
    )
