"""API v1 — Health endpoint."""
import time
from fastapi import APIRouter, Request
from app.models.schemas import HealthResponse
from app.config import settings
from app.dependencies import get_model_manager

router = APIRouter()

@router.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check(request: Request):
    mm = get_model_manager()
    uptime = time.time() - getattr(request.app.state, "start_time", time.time())
    return HealthResponse(
        status="healthy",
        version=settings.APP_VERSION,
        models_loaded={"clip": mm.is_loaded("clip"), "sbert": mm.is_loaded("sbert")},
        uptime_seconds=round(uptime, 2),
    )
