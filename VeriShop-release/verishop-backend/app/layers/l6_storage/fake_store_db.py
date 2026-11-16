"""
L6 — Fake Store DB
Labeled product database for training and evaluation.
"""

import json
import os
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import uuid4

from app.models.product import Product, ProductSource, ProductPricing, ProductImage, ProductSpecs
from app.models.enums import ProductCategory
from app.utils.logger import get_logger

logger = get_logger(__name__)
_executor = ThreadPoolExecutor(max_workers=2)


class FakeStoreDB:
    """Labeled product database for training/evaluation data."""

    def __init__(self, db_path: str = "./data/fake_store.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS labeled_products (
                    id TEXT PRIMARY KEY,
                    product_data JSON NOT NULL,
                    is_fake BOOLEAN NOT NULL,
                    label_source TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
        finally:
            conn.close()

    async def add_labeled_product(self, product: Product, is_fake: bool, label_source: str) -> str:
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            _executor, self._add_sync, product, is_fake, label_source
        )

    def _add_sync(self, product: Product, is_fake: bool, label_source: str) -> str:
        conn = sqlite3.connect(self.db_path)
        try:
            pid = str(product.id)
            conn.execute(
                "INSERT OR REPLACE INTO labeled_products (id, product_data, is_fake, label_source) VALUES (?, ?, ?, ?)",
                (pid, json.dumps(product.to_storage_dict()), is_fake, label_source),
            )
            conn.commit()
            return pid
        finally:
            conn.close()

    async def get_labeled_products(self, is_fake: Optional[bool] = None, limit: int = 100) -> List[Dict]:
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(_executor, self._get_labeled_sync, is_fake, limit)

    def _get_labeled_sync(self, is_fake: Optional[bool], limit: int) -> List[Dict]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            if is_fake is not None:
                rows = conn.execute(
                    "SELECT * FROM labeled_products WHERE is_fake = ? LIMIT ?",
                    (is_fake, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM labeled_products LIMIT ?", (limit,)
                ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    async def get_stats(self) -> Dict[str, Any]:
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(_executor, self._get_stats_sync)

    def _get_stats_sync(self) -> Dict[str, Any]:
        conn = sqlite3.connect(self.db_path)
        try:
            total = conn.execute("SELECT COUNT(*) FROM labeled_products").fetchone()[0]
            fake = conn.execute("SELECT COUNT(*) FROM labeled_products WHERE is_fake = 1").fetchone()[0]
            legit = total - fake
            sources = conn.execute("SELECT DISTINCT label_source FROM labeled_products").fetchall()
            return {
                "total": total,
                "fake_count": fake,
                "legitimate_count": legit,
                "sources": [s[0] for s in sources],
            }
        finally:
            conn.close()

    def seed_sample_data(self):
        """Seed database with sample fake and legitimate products."""
        conn = sqlite3.connect(self.db_path)
        try:
            existing = conn.execute("SELECT COUNT(*) FROM labeled_products").fetchone()[0]
            if existing > 0:
                return

            now = datetime.utcnow()
            # Generate 10 fake + 10 legitimate products
            products = []
            for i in range(10):
                # Legitimate product
                legit = Product(
                    title=f"Genuine Product {i+1} - Premium Quality",
                    description=f"High-quality authentic product with detailed description and specifications. "
                               f"Made with premium materials. Warranty included. Product #{i+1}.",
                    specs=ProductSpecs(brand="TrustBrand", model=f"TB-{1000+i}", category=ProductCategory.ELECTRONICS),
                    pricing=ProductPricing(price=49.99 + i * 10, currency="USD"),
                    images=[ProductImage(url=f"https://example.com/legit_{i}.jpg", is_primary=True)],
                    source=ProductSource(source_name="TrustedStore"),
                    seller_name=f"Verified Seller {i+1}",
                    seller_id=f"VS{i+1:04d}",
                    created_at=now, updated_at=now,
                )
                products.append((legit, False, "seed_data"))

                # Fake product
                fake = Product(
                    title=f"AMAZING DEAL Product {i+1} BUY NOW!!!",
                    description=f"Best product ever. Buy now. Limited stock.",
                    specs=ProductSpecs(brand="Unknown", category=ProductCategory.OTHER),
                    pricing=ProductPricing(price=1.99, currency="USD", original_price=999.99, discount_pct=99),
                    images=[],
                    source=ProductSource(source_name="ShadyMarket"),
                    seller_name="",
                    seller_id=f"{'x' * 30}",
                    created_at=now, updated_at=now,
                )
                products.append((fake, True, "seed_data"))

            for product, is_fake, source in products:
                pid = str(product.id)
                conn.execute(
                    "INSERT OR IGNORE INTO labeled_products (id, product_data, is_fake, label_source) VALUES (?, ?, ?, ?)",
                    (pid, json.dumps(product.to_storage_dict()), is_fake, source),
                )
            conn.commit()
            logger.info("fake_store_seeded", count=len(products))
        finally:
            conn.close()
