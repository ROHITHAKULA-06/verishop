"""
L4 — Price Anomaly Scorer
Statistical price anomaly detection using z-scores and discount analysis.
"""

from typing import Dict, Any, List, Optional
import numpy as np
from app.models.product import Product
from app.utils.logger import get_logger

logger = get_logger(__name__)


class PriceAnomalyScorer:
    """Scores price anomalies using statistical methods."""

    def score(self, product: Product, market_prices: Optional[List[float]] = None) -> Dict[str, Any]:
        """Score price anomaly for a product."""
        evidence = []
        price = product.pricing.price

        if price <= 0:
            return {
                "anomaly_score": 1.0,
                "is_anomaly": True,
                "price_position": "below",
                "z_score": -10.0,
                "evidence": ["Price is zero or negative"],
            }

        # Z-score analysis
        z_score = 0.0
        price_position = "within"

        if market_prices and len(market_prices) >= 3:
            z_score = self._calculate_z_score(price, market_prices)
            if z_score < -2:
                price_position = "below"
                evidence.append(f"Price is {abs(z_score):.1f} std devs below market average")
            elif z_score > 2:
                price_position = "above"
                evidence.append(f"Price is {z_score:.1f} std devs above market average")
        else:
            evidence.append("No market price data available for comparison")

        # Discount legitimacy
        discount_result = self._check_discount_legitimacy(product)
        if discount_result.get("is_suspicious"):
            evidence.append(discount_result["reason"])

        # Price history analysis
        history_result = self._check_price_history(product)
        if history_result.get("is_suspicious"):
            evidence.append(history_result["reason"])

        # Calculate anomaly score
        anomaly_score = 0.0
        if abs(z_score) > 3:
            anomaly_score += 0.5
        elif abs(z_score) > 2:
            anomaly_score += 0.3

        if discount_result.get("is_suspicious"):
            anomaly_score += 0.3
        if history_result.get("is_suspicious"):
            anomaly_score += 0.2

        anomaly_score = min(anomaly_score, 1.0)

        return {
            "anomaly_score": round(anomaly_score, 4),
            "is_anomaly": anomaly_score > 0.5,
            "price_position": price_position,
            "z_score": round(z_score, 4),
            "evidence": evidence,
        }

    def _calculate_z_score(self, price: float, prices: List[float]) -> float:
        """Calculate statistical z-score."""
        prices_arr = np.array(prices)
        mean = np.mean(prices_arr)
        std = np.std(prices_arr)
        if std == 0:
            return 0.0
        return float((price - mean) / std)

    def _check_discount_legitimacy(self, product: Product) -> Dict[str, Any]:
        """Check for suspiciously high discounts."""
        pricing = product.pricing

        if pricing.original_price and pricing.original_price > 0:
            actual_discount = (pricing.original_price - pricing.price) / pricing.original_price * 100
            if actual_discount > 80:
                return {
                    "is_suspicious": True,
                    "reason": f"Extremely high discount: {actual_discount:.0f}% off",
                }
            if actual_discount < 0:
                return {
                    "is_suspicious": True,
                    "reason": "Current price exceeds 'original' price",
                }

        if pricing.discount_pct and pricing.discount_pct > 80:
            return {
                "is_suspicious": True,
                "reason": f"Claimed discount of {pricing.discount_pct:.0f}% is suspiciously high",
            }

        return {"is_suspicious": False}

    def _check_price_history(self, product: Product) -> Dict[str, Any]:
        """Analyze price history for manipulation patterns."""
        history = product.pricing.price_history
        if not history or len(history) < 3:
            return {"is_suspicious": False}

        prices = [h.get("price", 0) for h in history if isinstance(h.get("price"), (int, float))]
        if len(prices) < 3:
            return {"is_suspicious": False}

        # Check for artificial price inflation before discount
        # Pattern: steady -> spike -> dramatic drop
        if len(prices) >= 3:
            recent = prices[-3:]
            if recent[1] > recent[0] * 1.5 and recent[2] < recent[1] * 0.5:
                return {
                    "is_suspicious": True,
                    "reason": "Price history shows inflate-then-discount pattern",
                }

        return {"is_suspicious": False}
