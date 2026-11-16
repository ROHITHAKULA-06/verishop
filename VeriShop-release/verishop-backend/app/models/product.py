"""
VeriShop Product Models
Normalized product schema for cross-source representation.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from uuid import UUID, uuid4
from datetime import datetime
from app.models.enums import ProductCategory


class ProductSource(BaseModel):
    """Source information for a product listing."""
    source_name: str
    source_url: str = ""
    listing_id: str = ""
    scraped_at: datetime = Field(default_factory=datetime.utcnow)


class ProductSpecs(BaseModel):
    """Product specifications and attributes."""
    brand: str = "Unknown"
    model: str = ""
    category: ProductCategory = ProductCategory.OTHER
    attributes: Dict[str, Any] = Field(default_factory=dict)


class ProductPricing(BaseModel):
    """Product pricing information with history."""
    price: float
    currency: str = "INR"
    original_price: Optional[float] = None
    discount_pct: Optional[float] = None
    price_history: List[Dict[str, Any]] = Field(default_factory=list)


class ProductReview(BaseModel):
    """Individual product review."""
    reviewer_id: str = ""
    rating: float = Field(ge=0, le=5)
    text: str = ""
    verified_purchase: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ProductImage(BaseModel):
    """Product image with optional embedding."""
    url: str
    alt_text: str = ""
    is_primary: bool = False
    embedding: Optional[List[float]] = None


class Product(BaseModel):
    """
    Unified product representation.
    Normalizes data from multiple e-commerce sources into a single schema.
    """
    id: UUID = Field(default_factory=uuid4)
    title: str
    description: str = ""
    specs: ProductSpecs = Field(default_factory=ProductSpecs)
    pricing: ProductPricing
    images: List[ProductImage] = Field(default_factory=list)
    reviews: List[ProductReview] = Field(default_factory=list)
    source: ProductSource
    seller_name: str = ""
    seller_id: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    def to_storage_dict(self) -> dict:
        """Serialize to a dictionary suitable for storage."""
        return self.model_dump(mode="json")

    @classmethod
    def from_storage_dict(cls, data: dict) -> "Product":
        """Deserialize from a storage dictionary."""
        return cls.model_validate(data)
