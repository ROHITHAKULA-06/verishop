"""
VeriShop FastAPI Application
Main entry point with CORS, exception handling, and lifespan management.
"""

import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.core.exceptions import VeriShopError
from app.core.pipeline import VeriShopPipeline
from app.api.v1.router import v1_router
from app.api.websocket import ws_router
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Global pipeline instance
pipeline: VeriShopPipeline = None
start_time: float = 0


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize resources on startup, cleanup on shutdown."""
    global pipeline, start_time
    start_time = time.time()

    logger.info("verishop_starting", version=settings.APP_VERSION)

    # Initialize pipeline
    pipeline = VeriShopPipeline(settings)
    app.state.pipeline = pipeline
    app.state.start_time = start_time

    logger.info("verishop_started", host=settings.HOST, port=settings.PORT)

    yield

    # Cleanup
    logger.info("verishop_shutting_down")


app = FastAPI(
    title="VeriShop API",
    description=(
        "VeriShop: An Agentic Multimodal Deep Learning Framework for "
        "Trust-Aware Online Shopping and Product Verification. "
        "Provides product search, trust scoring, and verification services."
    ),
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(VeriShopError)
async def verishop_error_handler(request: Request, exc: VeriShopError):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.message,
            "detail": exc.detail,
            "request_id": None,
        },
    )


@app.exception_handler(Exception)
async def general_error_handler(request: Request, exc: Exception):
    logger.error("unhandled_error", error=str(exc), path=request.url.path)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if settings.DEBUG else "An unexpected error occurred",
        },
    )


# Include routers
app.include_router(v1_router)
app.include_router(ws_router)


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """API information and documentation links."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "description": "VeriShop — Trust-Aware Product Verification API",
        "docs": "/docs",
        "health": "/api/v1/health",
        "search": "POST /api/v1/search",
    }
