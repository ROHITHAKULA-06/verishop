"""L7 — Rule-Based Filter: Hard constraint filtering on product listings."""

from typing import List
from app.models.trust import RankedProduct
from app.models.product import Product


class RuleBasedFilter:
    BLOCKED_SELLERS = set()  # Populate from config/DB
    MIN_DESCRIPTION_LENGTH = 10

    def __init__(self):
        pass

    def filter(self, products: List[RankedProduct]) -> List[RankedProduct]:
        passed = []
        for p in products:
            if p.product.pricing.price <= 0.0:
                if "Price not available" not in p.trust_score.risk_flags:
                    p.trust_score.risk_flags.append("Price not available")
            if self._passes_all(p.product):
                passed.append(p)
        return passed

    def _passes_all(self, product: Product) -> bool:
        return (self._check_minimum_info(product) and self._check_blocked_sellers(product)
                and self._check_price_floor(product) and self._check_description_length(product))

    def _check_minimum_info(self, p: Product) -> bool:
        return bool(p.title)

    def _check_blocked_sellers(self, p: Product) -> bool:
        return p.seller_id not in self.BLOCKED_SELLERS

    def _check_price_floor(self, p: Product) -> bool:
        return p.pricing.price >= 0.0

    def _check_description_length(self, p: Product) -> bool:
        return len(p.description or "") >= self.MIN_DESCRIPTION_LENGTH or len(p.title) >= 5
