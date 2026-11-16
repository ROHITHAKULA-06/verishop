"""
L6 — Product Store
SQLite-backed product storage with async wrappers.
"""

import json
import os
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.models.product import Product
from app.models.trust import TrustScore
from app.utils.logger import get_logger

logger = get_logger(__name__)
_executor = ThreadPoolExecutor(max_workers=4)


class ProductStore:
    """SQLite-backed product storage with full-text search."""

    def __init__(self, db_path: str = "./data/verishop.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
        self._init_db()

    def _init_db(self):
        """Create tables if they don't exist."""
        conn = sqlite3.connect(self.db_path)
        try:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS products (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    data JSON NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS trust_scores (
                    product_id TEXT PRIMARY KEY,
                    score_data JSON NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (product_id) REFERENCES products(id)
                );
                CREATE TABLE IF NOT EXISTS search_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    request_id TEXT NOT NULL,
                    query TEXT,
                    results_count INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
                CREATE INDEX IF NOT EXISTS idx_products_title ON products(title);
                CREATE INDEX IF NOT EXISTS idx_search_created ON search_history(created_at);
            """)
            conn.commit()
        finally:
            conn.close()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    async def save_product(self, product: Product) -> str:
        """Save a product and return its ID."""
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(_executor, self._save_product_sync, product)

    def _save_product_sync(self, product: Product) -> str:
        conn = self._get_conn()
        try:
            product_id = str(product.id)
            data = json.dumps(product.to_storage_dict())
            conn.execute(
                "INSERT OR REPLACE INTO products (id, title, data, updated_at) VALUES (?, ?, ?, ?)",
                (product_id, product.title, data, datetime.utcnow().isoformat()),
            )
            conn.commit()
            return product_id
        finally:
            conn.close()

    async def get_product(self, product_id: str) -> Optional[Product]:
        """Get a product by ID."""
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(_executor, self._get_product_sync, product_id)

    def _get_product_sync(self, product_id: str) -> Optional[Product]:
        conn = self._get_conn()
        try:
            row = conn.execute("SELECT data FROM products WHERE id = ?", (product_id,)).fetchone()
            if row:
                return Product.from_storage_dict(json.loads(row["data"]))
            return None
        finally:
            conn.close()

    async def search_products(self, query: str, limit: int = 10) -> List[Product]:
        """Full-text search for products."""
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(_executor, self._search_sync, query, limit)

    def _search_sync(self, query: str, limit: int) -> List[Product]:
        conn = self._get_conn()
        try:
            rows = conn.execute(
                "SELECT data FROM products WHERE title LIKE ? LIMIT ?",
                (f"%{query}%", limit),
            ).fetchall()
            return [Product.from_storage_dict(json.loads(r["data"])) for r in rows]
        finally:
            conn.close()

    async def save_trust_score(self, product_id: str, trust_score: TrustScore):
        """Save trust score for a product."""
        import asyncio
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(_executor, self._save_trust_sync, product_id, trust_score)

    def _save_trust_sync(self, product_id: str, trust_score: TrustScore):
        conn = self._get_conn()
        try:
            data = json.dumps(trust_score.model_dump(mode="json"))
            conn.execute(
                "INSERT OR REPLACE INTO trust_scores (product_id, score_data) VALUES (?, ?)",
                (product_id, data),
            )
            conn.commit()
        finally:
            conn.close()

    async def get_trust_score(self, product_id: str) -> Optional[TrustScore]:
        """Get trust score for a product."""
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(_executor, self._get_trust_sync, product_id)

    def _get_trust_sync(self, product_id: str) -> Optional[TrustScore]:
        conn = self._get_conn()
        try:
            row = conn.execute("SELECT score_data FROM trust_scores WHERE product_id = ?", (product_id,)).fetchone()
            if row:
                return TrustScore.model_validate(json.loads(row["score_data"]))
            return None
        finally:
            conn.close()

    async def save_search(self, request_id: str, query: str, results_count: int):
        """Save a search to history."""
        import asyncio
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(_executor, self._save_search_sync, request_id, query, results_count)

    def _save_search_sync(self, request_id: str, query: str, results_count: int):
        conn = self._get_conn()
        try:
            conn.execute(
                "INSERT INTO search_history (request_id, query, results_count) VALUES (?, ?, ?)",
                (request_id, query, results_count),
            )
            conn.commit()
        finally:
            conn.close()

    async def get_recent_searches(self, limit: int = 20) -> List[Dict]:
        """Get recent search history."""
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(_executor, self._get_searches_sync, limit)

    def _get_searches_sync(self, limit: int) -> List[Dict]:
        conn = self._get_conn()
        try:
            rows = conn.execute(
                "SELECT * FROM search_history ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    async def delete_product(self, product_id: str) -> bool:
        """Delete a product."""
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(_executor, self._delete_sync, product_id)

    def _delete_sync(self, product_id: str) -> bool:
        conn = self._get_conn()
        try:
            cursor = conn.execute("DELETE FROM products WHERE id = ?", (product_id,))
            conn.execute("DELETE FROM trust_scores WHERE product_id = ?", (product_id,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()
