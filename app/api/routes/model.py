from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from app.services.model_service import model_service
from app.core.security import verify_api_key

router = APIRouter(prefix="/model", tags=["Model Registry"])

@router.get("/info", response_model=dict)
def get_model_info(api_key: str = Depends(verify_api_key)):
    """Fetches metadata about the currently active model version and configuration."""
    return model_service.get_info()

@router.post("/reload", response_model=dict, status_code=status.HTTP_200_OK)
def reload_model(
    version: Optional[str] = Query(None, description="Specific version to load. If omitted, loads Production."),
    api_key: str = Depends(verify_api_key)
):
    """Triggers a manual reload of the model from the MLflow Model Registry."""
    try:
        model_service.load_model(version=version)
        return {
            "status": "success",
            "message": f"Model reloaded successfully. Active version: {model_service.model_version}",
            "info": model_service.get_info()
        }
    except Exception as e:
        # FastAPI exceptions handler will catch general RuntimeErrors,
        # but let's log and return a specialized payload.
        raise RuntimeError(f"Failed to reload model: {e}") from e
