"""API v1 — Search endpoint."""
from fastapi import APIRouter, Request, HTTPException
from app.models.schemas import SearchRequest, SearchResponse, ErrorResponse
from app.core.exceptions import VeriShopError

router = APIRouter()

@router.post("/search", response_model=SearchResponse, responses={400: {"model": ErrorResponse}}, tags=["Search"])
async def search_products(request: Request, search_request: SearchRequest):
    """Search for products with trust-aware ranking."""
    pipeline = request.app.state.pipeline
    if not pipeline:
        raise HTTPException(status_code=503, detail="Pipeline not initialized")
    try:
        result = await pipeline.search(search_request)
        return result
    except VeriShopError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
