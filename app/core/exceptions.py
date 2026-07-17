import logging
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
import redis

logger = logging.getLogger("disease_risk_serving")

# Define a custom exception for internal infrastructure or service errors
class PredictionServiceException(Exception):
    def __init__(self, message: str = "Prediction service unavailable"):
        self.message = message
        super().__init__(self.message)

async def service_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catches all internal infrastructure errors and formats the response."""
    logger.error(f"Internal Service Error on {request.url.path}: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=503,
        content={"status": "error", "message": "Prediction service unavailable"}
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Catches request validation errors (invalid inputs/missing data)."""
    logger.warning(f"Validation failure on {request.url.path}: {exc.errors()}")
    return JSONResponse(
        status_code=400,
        content={"status": "error", "message": "Prediction service unavailable"}
    )

def setup_exception_handlers(app) -> None:
    """Registers exception handlers to the FastAPI app."""
    # Catch custom service exceptions
    app.add_exception_handler(PredictionServiceException, service_exception_handler)
    
    # Catch SQLAlchemy errors
    app.add_exception_handler(SQLAlchemyError, service_exception_handler)
    
    # Catch Redis errors
    app.add_exception_handler(redis.RedisError, service_exception_handler)
    
    # Catch runtime issues (e.g. model not loaded)
    app.add_exception_handler(RuntimeError, service_exception_handler)
    
    # Catch FastAPI request validation errors
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
