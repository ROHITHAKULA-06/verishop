"""API v1 — Aggregated router."""
from fastapi import APIRouter
from app.api.v1.health import router as health_router
from app.api.v1.search import router as search_router
from app.api.v1.products import router as products_router
from app.api.v1.trust import router as trust_router

v1_router = APIRouter(prefix="/api/v1")
v1_router.include_router(health_router)
v1_router.include_router(search_router)
v1_router.include_router(products_router)
v1_router.include_router(trust_router)
