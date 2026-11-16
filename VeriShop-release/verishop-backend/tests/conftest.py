"""Pytest configuration and shared fixtures."""
import pytest
import pytest_asyncio
from datetime import datetime
from uuid import uuid4
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.config import Settings
from app.models.product import Product, ProductSource, ProductSpecs, ProductPricing, ProductImage, ProductReview
from app.models.enums import ProductCategory
from app.models.schemas import SearchRequest


@pytest.fixture
def settings():
    return Settings(DEBUG=True, SQLITE_DB_PATH="./data/test_verishop.db", FAISS_INDEX_PATH="./data/test_faiss")


@pytest.fixture
def sample_product():
    now = datetime.utcnow()
    return Product(
        title="Test Wireless Headphones - Premium",
        description="High-quality wireless headphones with noise cancellation and long battery life.",
        specs=ProductSpecs(brand="TestBrand", model="TB-100", category=ProductCategory.ELECTRONICS),
        pricing=ProductPricing(price=79.99, currency="USD", original_price=99.99),
        images=[ProductImage(url="https://example.com/img.jpg", alt_text="Headphones", is_primary=True)],
        reviews=[
            ProductReview(reviewer_id="user1", rating=4.5, text="Great headphones!", verified_purchase=True, created_at=now),
            ProductReview(reviewer_id="user2", rating=3.0, text="Decent for the price.", verified_purchase=True, created_at=now),
        ],
        source=ProductSource(source_name="TestStore"),
        seller_name="Test Seller",
        seller_id="TS001",
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
def sample_search_request():
    return SearchRequest(query="wireless headphones", max_results=5)


@pytest_asyncio.fixture
async def async_client():
    from app.core.pipeline import VeriShopPipeline
    app.state.pipeline = VeriShopPipeline(Settings(DEBUG=True, SQLITE_DB_PATH="./data/test_db.sqlite", FAISS_INDEX_PATH="./data/test_faiss"))
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
