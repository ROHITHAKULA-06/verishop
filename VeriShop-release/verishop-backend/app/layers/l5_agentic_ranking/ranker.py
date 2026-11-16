"""
L5 — Agentic Product Ranker
Blends relevance and trust scores with diversity boosting.
A highly relevant but risky listing should NOT automatically beat a well-verified one.
"""

from typing import List, Dict, Any, Optional
from collections import Counter
from app.models.product import Product
from app.models.trust import TrustScore
from app.utils.logger import get_logger

logger = get_logger(__name__)


class AgenticProductRanker:
    """Ranks products by blending relevance and trust scores."""

    DEFAULT_WEIGHTS = {"relevance": 0.4, "trust": 0.6}

    def __init__(self, settings=None):
        self.settings = settings

    def rank(
        self,
        products: List[Product],
        trust_scores: List[TrustScore],
        relevance_scores: List[float],
        query_context: Optional[Dict] = None,
    ) -> List[Dict[str, Any]]:
        """Rank products by blended relevance + trust score."""
        if not products:
            return []

        ranked = []
        for i, product in enumerate(products):
            trust = trust_scores[i] if i < len(trust_scores) else None
            relevance = relevance_scores[i] if i < len(relevance_scores) else 0.5
            trust_val = trust.overall_score if trust else 0.5

            blended = self._compute_blended_score(relevance, trust_val)
            explanation = self._generate_rank_explanation(product, trust, relevance, blended)

            ranked.append({
                "product": product,
                "trust_score": trust,
                "relevance_score": round(relevance, 4),
                "blended_score": round(blended, 4),
                "rank": 0,
                "explanation": explanation,
            })

        # The requested ordering is trust-first; relevance and blended score
        # break ties so unrelated but safe products do not dominate.
        ranked.sort(key=lambda x: (x["trust_score"].overall_score if x["trust_score"] else 0.0, x["blended_score"]), reverse=True)

        # Apply diversity boost
        source_counts = Counter(p.source.source_name for p in products)
        ranked = self._apply_diversity_boost(ranked, source_counts)

        # Re-sort and assign ranks
        ranked.sort(key=lambda x: (x["trust_score"].overall_score if x["trust_score"] else 0.0, x["blended_score"]), reverse=True)
        for i, item in enumerate(ranked):
            item["rank"] = i + 1

        return ranked

    def _compute_blended_score(
        self, relevance: float, trust: float, weights: Optional[Dict] = None
    ) -> float:
        """Compute blended score. Trust-weighted to penalize risky listings."""
        w = weights or self.DEFAULT_WEIGHTS
        blended = relevance * w["relevance"] + trust * w["trust"]

        # Extra penalty for very low trust
        if trust < 0.3:
            blended *= 0.7  # 30% penalty for untrusted listings

        return min(max(blended, 0.0), 1.0)

    def _generate_rank_explanation(
        self, product: Product, trust_score: Optional[TrustScore], relevance: float, blended: float
    ) -> str:
        """Generate human-readable rank explanation."""
        parts = [f"Blended score: {blended:.2f}"]
        parts.append(f"Relevance: {relevance:.2f}")

        if trust_score:
            parts.append(f"Trust: {trust_score.overall_score:.2f} ({trust_score.verdict.value})")
            if trust_score.risk_flags:
                parts.append(f"Risks: {', '.join(trust_score.risk_flags[:3])}")
        else:
            parts.append("Trust: not evaluated")

        return " | ".join(parts)

    def _apply_diversity_boost(
        self, ranked: List[Dict], source_counts: Counter
    ) -> List[Dict]:
        """Slight boost for products from underrepresented sources."""
        if not source_counts or len(source_counts) <= 1:
            return ranked

        max_count = max(source_counts.values())

        for item in ranked:
            source = item["product"].source.source_name
            count = source_counts.get(source, 1)
            # Boost underrepresented sources by up to 5%
            if count < max_count:
                diversity_factor = 1.0 + (1.0 - count / max_count) * 0.05
                item["blended_score"] *= diversity_factor

        return ranked
