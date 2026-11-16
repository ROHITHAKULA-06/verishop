"""
L5 — LLM Generative Scorer
Pluggable LLM scoring with rule-based fallback (no external LLM required).
"""

from typing import Dict, Any, Optional, List
from app.models.product import Product
from app.utils.logger import get_logger

logger = get_logger(__name__)


class LLMGenerativeScorer:
    """LLM-based product scoring with pluggable provider and rule-based fallback."""

    def __init__(self, settings=None):
        self.provider = "none"
        self.api_key = ""
        self.model = "gpt-4o-mini"

        if settings:
            self.provider = getattr(settings, "LLM_PROVIDER", "none")
            self.api_key = getattr(settings, "OPENAI_API_KEY", "")
            self.model = getattr(settings, "OPENAI_MODEL", "gpt-4o-mini")

    async def score(self, product: Product, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Score a product using LLM or rule-based fallback."""
        if self.provider == "openai" and self.api_key:
            try:
                prompt = self._build_prompt(product, context or {})
                response = await self._call_openai(prompt)
                return self._parse_llm_response(response)
            except Exception as e:
                logger.warning("llm_scoring_failed", error=str(e))

        # Fallback to rule-based scoring
        return self._rule_based_fallback(product)

    async def _call_openai(self, prompt: str) -> str:
        """Call OpenAI API."""
        try:
            import httpx
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": 500,
                        "temperature": 0.3,
                    },
                )
                data = response.json()
                return data["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error("openai_call_failed", error=str(e))
            raise

    def _build_prompt(self, product: Product, context: Dict) -> str:
        """Build evaluation prompt for LLM."""
        return f"""Evaluate this product listing for trustworthiness on a scale of 0-1.

Product: {product.title}
Description: {product.description[:500] if product.description else 'N/A'}
Price: {product.pricing.price} {product.pricing.currency}
Seller: {product.seller_name or 'Unknown'}
Reviews: {len(product.reviews)} reviews
Images: {len(product.images)} images

Respond ONLY in this exact JSON format:
{{"score": 0.X, "reasoning": "...", "risk_flags": ["flag1", "flag2"], "confidence": 0.X}}"""

    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response into structured format."""
        try:
            import json
            # Try to extract JSON from response
            start = response.find("{")
            end = response.rfind("}") + 1
            if start >= 0 and end > start:
                data = json.loads(response[start:end])
                return {
                    "llm_score": float(data.get("score", 0.5)),
                    "reasoning": data.get("reasoning", ""),
                    "risk_flags": data.get("risk_flags", []),
                    "confidence": float(data.get("confidence", 0.5)),
                }
        except (json.JSONDecodeError, ValueError):
            pass

        return self._rule_based_fallback_score(0.5)

    def _rule_based_fallback(self, product: Product) -> Dict[str, Any]:
        """Heuristic scoring when no LLM is available."""
        score = 0.5
        reasoning_parts = []
        risk_flags = []

        # Description quality
        desc_len = len(product.description) if product.description else 0
        if desc_len > 200:
            score += 0.1
            reasoning_parts.append("Good description length")
        elif desc_len < 50:
            score -= 0.1
            risk_flags.append("Short description")
            reasoning_parts.append("Very short description")

        # Image count
        img_count = len(product.images)
        if img_count >= 3:
            score += 0.1
            reasoning_parts.append(f"{img_count} product images")
        elif img_count == 0:
            score -= 0.15
            risk_flags.append("No images")

        # Review count
        review_count = len(product.reviews)
        if review_count >= 10:
            score += 0.1
            reasoning_parts.append(f"{review_count} reviews available")
        elif review_count == 0:
            score -= 0.05
            reasoning_parts.append("No reviews")

        # Price reasonableness
        price = product.pricing.price
        if 1.0 < price < 10000:
            score += 0.05
        elif price <= 0 or price > 500000:
            score -= 0.15
            risk_flags.append("Unusual price")

        # Seller info completeness
        if product.seller_name and product.seller_id:
            score += 0.1
            reasoning_parts.append("Complete seller info")
        else:
            score -= 0.05
            risk_flags.append("Incomplete seller info")

        score = max(0.0, min(1.0, score))

        return {
            "llm_score": round(score, 4),
            "reasoning": "; ".join(reasoning_parts),
            "risk_flags": risk_flags,
            "confidence": 0.6,  # Lower confidence for rule-based
        }

    def _rule_based_fallback_score(self, default: float) -> Dict[str, Any]:
        return {
            "llm_score": default,
            "reasoning": "Could not parse LLM response",
            "risk_flags": [],
            "confidence": 0.3,
        }
