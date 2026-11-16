"""
L5 — Generative AI Synthesizer
Generates human-readable summaries, comparisons, and recommendations.
"""

from typing import List, Dict, Any, Optional
from app.utils.logger import get_logger

logger = get_logger(__name__)


class GenerativeAISynthesizer:
    """Synthesizes ranking results into human-readable summaries."""

    def __init__(self, settings=None):
        self.settings = settings

    def synthesize(self, ranked_products: List[Dict], query_context: Dict) -> Dict[str, Any]:
        """Generate a synthesis of ranking results."""
        if not ranked_products:
            return {
                "summary": "No products found matching your query.",
                "highlights": [],
                "warnings": [],
                "recommendation": "Try a different search query.",
            }

        summary = self._generate_comparison_summary(ranked_products)
        warnings = self._generate_warnings(ranked_products)
        recommendation = self._generate_recommendation(ranked_products[0])

        highlights = []
        for item in ranked_products[:3]:
            product = item["product"]
            trust = item.get("trust_score")
            score_text = f"(trust: {trust.overall_score:.0%})" if trust else ""
            highlights.append(f"{product.title} — ${product.pricing.price:.2f} {score_text}")

        return {
            "summary": summary,
            "highlights": highlights,
            "warnings": warnings,
            "recommendation": recommendation,
        }

    def _generate_comparison_summary(self, products: List[Dict]) -> str:
        """Compare top products."""
        n = len(products)
        if n == 0:
            return "No products to compare."

        top = products[0]
        product = top["product"]
        trust = top.get("trust_score")

        parts = [f"Found {n} product(s)."]

        if trust:
            parts.append(
                f"Top result: \"{product.title}\" at ${product.pricing.price:.2f} "
                f"with trust score {trust.overall_score:.0%} ({trust.verdict.value})."
            )
        else:
            parts.append(f"Top result: \"{product.title}\" at ${product.pricing.price:.2f}.")

        if n >= 2:
            price_range = [p["product"].pricing.price for p in products]
            parts.append(
                f"Price range: ${min(price_range):.2f} – ${max(price_range):.2f}."
            )

        # Count trusted vs cautious
        trusted = sum(1 for p in products if p.get("trust_score") and p["trust_score"].verdict.value == "TRUSTED")
        cautioned = sum(1 for p in products if p.get("trust_score") and p["trust_score"].verdict.value == "CAUTION")
        untrusted = sum(1 for p in products if p.get("trust_score") and p["trust_score"].verdict.value == "UNTRUSTED")

        if trusted:
            parts.append(f"{trusted} listing(s) rated as trusted.")
        if cautioned:
            parts.append(f"{cautioned} listing(s) flagged for caution.")
        if untrusted:
            parts.append(f"{untrusted} listing(s) rated as untrusted.")

        return " ".join(parts)

    def _generate_warnings(self, products: List[Dict]) -> List[str]:
        """Extract key warnings from rankings."""
        warnings = []

        for item in products:
            trust = item.get("trust_score")
            if trust and trust.risk_flags:
                product = item["product"]
                for flag in trust.risk_flags[:2]:
                    warnings.append(f"{product.title}: {flag}")

        return warnings[:10]  # Cap at 10 warnings

    def _generate_recommendation(self, top_product: Dict) -> str:
        """Generate recommendation with evidence."""
        product = top_product["product"]
        trust = top_product.get("trust_score")

        if trust:
            if trust.verdict.value == "TRUSTED":
                return (
                    f"We recommend \"{product.title}\" — it has a trust score of "
                    f"{trust.overall_score:.0%} with no major risk flags. "
                    f"Price: ${product.pricing.price:.2f}."
                )
            elif trust.verdict.value == "CAUTION":
                return (
                    f"\"{product.title}\" is the top result but has some caution flags "
                    f"(trust: {trust.overall_score:.0%}). Verify seller history before purchasing."
                )
            else:
                return (
                    f"⚠ The top result \"{product.title}\" has low trust "
                    f"({trust.overall_score:.0%}). We recommend reviewing alternative listings."
                )

        return f"Top result: \"{product.title}\" at ${product.pricing.price:.2f}."
