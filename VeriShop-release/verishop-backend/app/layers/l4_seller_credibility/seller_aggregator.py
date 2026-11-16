"""
L4 — Seller Score Aggregator
Weighted aggregation of all credibility sub-scores into SellerCredibility.
"""

from typing import Dict, Any, List
from app.models.product import Product
from app.models.trust import SellerCredibility
from app.utils.logger import get_logger

logger = get_logger(__name__)


class SellerScoreAggregator:
    """Aggregates all credibility sub-scores into a single SellerCredibility."""

    # Default weights for sub-components
    DEFAULT_WEIGHTS = {
        "review_auth": 0.20,
        "review_graph": 0.15,
        "anomalies": 0.20,
        "price": 0.20,
        "domain": 0.25,
    }

    def aggregate(
        self,
        review_auth: Dict[str, Any],
        review_graph: Dict[str, Any],
        anomalies: Dict[str, Any],
        price_score: Dict[str, Any],
        domain_trust: Dict[str, Any],
        product: Product,
    ) -> SellerCredibility:
        """Aggregate sub-scores into SellerCredibility."""
        scores = {
            "review_auth": review_auth.get("authenticity_score", 0.5),
            "review_graph": 1.0 - review_graph.get("coordinated_review_score", 0.0),
            "anomalies": 1.0 - anomalies.get("anomaly_score", 0.0),
            "price": 1.0 - price_score.get("anomaly_score", 0.0),
            "domain": domain_trust.get("overall_score", 0.5),
        }

        # Keep domain reputation as a separate signal. Its score is exposed
        # independently and added as its own factor in the final trust model.
        listing_scores = {key: value for key, value in scores.items() if key != "domain"}
        listing_weights = {key: value for key, value in self.DEFAULT_WEIGHTS.items() if key != "domain"}
        overall = self._apply_weights(listing_scores, listing_weights)
        evidence = self._consolidate_evidence(
            review_auth.get("evidence", []),
            [f"Coordinated review score: {review_graph.get('coordinated_review_score', 0):.2f}"],
            anomalies.get("evidence", []),
            price_score.get("evidence", []),
            domain_trust.get("evidence", []),
            domain_trust.get("risk_flags", []),
        )

        return SellerCredibility(
            seller_id=product.seller_id or "unknown",
            seller_name=product.seller_name or "Unknown Seller",
            overall_score=round(overall, 4),
            domain_trust_score=round(scores["domain"], 4),
            review_authenticity_score=round(scores["review_auth"], 4),
            price_anomaly_score=round(1.0 - scores["price"], 4),
            account_age_score=round(scores["anomalies"], 4),
            evidence=evidence,
        )

    def _apply_weights(self, scores: Dict[str, float], weights: Dict[str, float]) -> float:
        """Compute weighted average of scores."""
        total = 0.0
        total_weight = 0.0
        for key, weight in weights.items():
            if key in scores:
                total += scores[key] * weight
                total_weight += weight
        return total / total_weight if total_weight > 0 else 0.5

    def _consolidate_evidence(self, *evidence_lists: List[str]) -> List[str]:
        """Merge and deduplicate evidence from all sources."""
        seen = set()
        consolidated = []
        for evidence_list in evidence_lists:
            for item in evidence_list:
                if item and item not in seen:
                    seen.add(item)
                    consolidated.append(item)
        return consolidated
