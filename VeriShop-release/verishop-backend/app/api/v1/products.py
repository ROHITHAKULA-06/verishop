"""API v1 — Products endpoints."""
from fastapi import APIRouter, Request, HTTPException
from app.models.schemas import ProductResponse

router = APIRouter()

@router.get("/products", tags=["Products"])
async def list_products(request: Request, limit: int = 20):
    """List recent products."""
    pipeline = request.app.state.pipeline
    searches = await pipeline.product_store.get_recent_searches(limit=limit)
    return {"searches": searches, "count": len(searches)}

@router.get("/products/{product_id}", response_model=ProductResponse, tags=["Products"])
async def get_product(request: Request, product_id: str):
    """Get a product by ID."""
    pipeline = request.app.state.pipeline
    try:
        return await pipeline.get_product(product_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))
