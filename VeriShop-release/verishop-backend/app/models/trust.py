"""
VeriShop Trust Models
Evidence-based trust scoring and verification schemas.
Every trust score ships with its contributing evidence — never a bare score.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from app.models.enums import TrustVerdict, ManipulationType
from app.models.product import Product


class TrustFactor(BaseModel):
    """Individual trust factor with score, weight, and evidence."""
    factor_name: str
    score: float = Field(ge=0.0, le=1.0)
    weight: float = Field(ge=0.0, le=1.0)
    evidence: List[str] = Field(default_factory=list)
    details: Dict[str, Any] = Field(default_factory=dict)


class TrustScore(BaseModel):
    """
    Composite trust score with verdict and full evidence trail.
    Explainability is non-negotiable: never output a trust score
    without its contributing factors.
    """
    overall_score: float = Field(ge=0.0, le=1.0)
    verdict: TrustVerdict
    factors: List[TrustFactor] = Field(default_factory=list)
    explanation: str = ""
    risk_flags: List[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0, default=0.5)


class ImageConsistency(BaseModel):
    """Image consistency check results."""
    similarity_score: float = Field(ge=0.0, le=1.0)
    manipulation_detected: bool = False
    manipulation_type: ManipulationType = ManipulationType.NONE
    evidence: List[str] = Field(default_factory=list)


class SellerCredibility(BaseModel):
    """Aggregated seller credibility assessment."""
    seller_id: str
    seller_name: str
    overall_score: float = Field(ge=0.0, le=1.0)
    domain_trust_score: float = Field(ge=0.0, le=1.0, default=0.5)
    review_authenticity_score: float = Field(ge=0.0, le=1.0, default=0.5)
    price_anomaly_score: float = Field(ge=0.0, le=1.0, default=0.5)
    account_age_score: float = Field(ge=0.0, le=1.0, default=0.5)
    evidence: List[str] = Field(default_factory=list)


class RankedProduct(BaseModel):
    """Product with ranking metadata and trust evidence."""
    product: Product
    trust_score: TrustScore
    relevance_score: float = Field(ge=0.0, le=1.0)
    blended_score: float = Field(ge=0.0, le=1.0)
    rank: int = 0
    explanation: str = ""
