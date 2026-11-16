"""
L4 — Anomaly Detector
Detects listing anomalies: age, seller patterns, description quality, image count.
"""

from typing import Dict, Any, List
from app.models.product import Product
from app.models.enums import RiskLevel
from app.utils.logger import get_logger
from datetime import datetime, timedelta

logger = get_logger(__name__)


class AnomalyDetector:
    """Detects anomalies in product listings."""

    def detect(self, product: Product) -> Dict[str, Any]:
        """Run all anomaly detection checks."""
        anomalies = []
        evidence = []

        listing_check = self._check_listing_age(product)
        if listing_check.get("is_anomaly"):
            anomalies.append(listing_check)
            evidence.append(listing_check["reason"])

        seller_check = self._check_seller_patterns(product)
        if seller_check.get("is_anomaly"):
            anomalies.append(seller_check)
            evidence.append(seller_check["reason"])

        desc_check = self._check_description_quality(product)
        if desc_check.get("is_anomaly"):
            anomalies.append(desc_check)
            evidence.append(desc_check["reason"])

        image_check = self._check_image_count(product)
        if image_check.get("is_anomaly"):
            anomalies.append(image_check)
            evidence.append(image_check["reason"])

        # Calculate overall anomaly score
        anomaly_score = min(len(anomalies) * 0.25, 1.0)

        # Determine risk level
        if anomaly_score >= 0.75:
            risk_level = RiskLevel.CRITICAL
        elif anomaly_score >= 0.5:
            risk_level = RiskLevel.HIGH
        elif anomaly_score >= 0.25:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW

        return {
            "anomaly_score": round(anomaly_score, 4),
            "anomalies": anomalies,
            "risk_level": risk_level.value,
            "evidence": evidence,
        }

    def _check_listing_age(self, product: Product) -> Dict[str, Any]:
        """New listings with many reviews are suspicious."""
        age_days = (datetime.utcnow() - product.created_at).days
        review_count = len(product.reviews)

        if age_days < 30 and review_count > 50:
            return {
                "is_anomaly": True,
                "type": "listing_age",
                "reason": f"New listing ({age_days} days) with {review_count} reviews",
                "severity": 0.7,
            }
        if age_days < 7 and review_count > 10:
            return {
                "is_anomaly": True,
                "type": "listing_age",
                "reason": f"Very new listing ({age_days} days) with {review_count} reviews",
                "severity": 0.9,
            }
        return {"is_anomaly": False}

    def _check_seller_patterns(self, product: Product) -> Dict[str, Any]:
        """Check seller ID for suspicious patterns."""
        if not product.seller_id:
            return {
                "is_anomaly": True,
                "type": "seller_id",
                "reason": "No seller ID provided",
                "severity": 0.4,
            }

        # Random-looking seller IDs (very long alphanumeric)
        if len(product.seller_id) > 30 and product.seller_id.isalnum():
            return {
                "is_anomaly": True,
                "type": "seller_id",
                "reason": "Seller ID appears auto-generated",
                "severity": 0.3,
            }
        return {"is_anomaly": False}

    def _check_description_quality(self, product: Product) -> Dict[str, Any]:
        """Check description for quality issues."""
        desc = product.description

        if not desc or len(desc) < 10:
            return {
                "is_anomaly": True,
                "type": "description",
                "reason": "Missing or very short product description",
                "severity": 0.5,
            }

        # Keyword stuffing (same word repeated >5 times)
        words = desc.lower().split()
        if words:
            from collections import Counter
            word_counts = Counter(words)
            most_common = word_counts.most_common(1)[0]
            if most_common[1] > max(5, len(words) * 0.15):
                return {
                    "is_anomaly": True,
                    "type": "description",
                    "reason": f"Possible keyword stuffing: '{most_common[0]}' appears {most_common[1]} times",
                    "severity": 0.6,
                }

        return {"is_anomaly": False}

    def _check_image_count(self, product: Product) -> Dict[str, Any]:
        """Check for suspicious image counts."""
        count = len(product.images)

        if count == 0:
            return {
                "is_anomaly": True,
                "type": "images",
                "reason": "No product images",
                "severity": 0.6,
            }
        if count > 20:
            return {
                "is_anomaly": True,
                "type": "images",
                "reason": f"Unusually high image count: {count}",
                "severity": 0.3,
            }

        return {"is_anomaly": False}
