"""
VeriShop API Schemas
Request and response models for the API layer.
"""

from pydantic import BaseModel, Field, model_validator
from typing import List, Dict, Optional, Any
from datetime import datetime
from app.models.enums import QueryType
from app.models.product import Product
from app.models.trust import TrustScore, RankedProduct, SellerCredibility


class SearchRequest(BaseModel):
    """Search request — requires at least a text query or image."""
    query: Optional[str] = None
    image_base64: Optional[str] = None
    image_url: Optional[str] = None
    max_results: int = Field(default=50, ge=1, le=100)
    min_trust_score: float = 0.0
    include_evidence: bool = True

    @model_validator(mode="after")
    def check_query_or_image(self) -> "SearchRequest":
        if not self.query and not self.image_base64 and not self.image_url:
            raise ValueError(
                "At least one of query, image_base64, or image_url must be provided."
            )
        return self


class SearchResponse(BaseModel):
    """Search results with full evidence trail."""
    request_id: str
    query_type: QueryType
    results: List[RankedProduct]
    total_found: int
    processing_time_ms: float
    metadata: Dict[str, Any] = {}


class ProductResponse(BaseModel):
    """Single product with optional trust score."""
    product: Product
    trust_score: Optional[TrustScore] = None


class TrustResponse(BaseModel):
    """Trust assessment for a specific product."""
    product_id: str
    trust_score: TrustScore
    seller_credibility: Optional[SellerCredibility] = None


class HealthResponse(BaseModel):
    """API health check response."""
    status: str
    version: str
    models_loaded: Dict[str, bool]
    uptime_seconds: float


class ErrorResponse(BaseModel):
    """Structured error response."""
    error: str
    detail: str
    request_id: Optional[str] = None


class WebSocketMessage(BaseModel):
    """WebSocket message for real-time progress updates."""
    type: str  # 'progress' | 'result' | 'error'
    data: Dict[str, Any]
    timestamp: datetime
