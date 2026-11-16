"""API v1 — Trust endpoint."""
from fastapi import APIRouter, Request, HTTPException
from app.models.schemas import TrustResponse

router = APIRouter()

@router.get("/trust/{product_id}", response_model=TrustResponse, tags=["Trust"])
async def get_trust_score(request: Request, product_id: str):
    """Get trust assessment for a product."""
    pipeline = request.app.state.pipeline
    try:
        return await pipeline.get_product_trust(product_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))
