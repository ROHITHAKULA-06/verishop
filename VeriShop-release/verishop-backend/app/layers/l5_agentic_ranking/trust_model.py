"""
L5 — Trustworthy Standard Model
Combines all trust signals into a calibrated TrustScore with verdict.
"""

import math
from typing import List, Dict, Any, Optional
from app.models.enums import TrustVerdict
from app.models.trust import TrustFactor, TrustScore, SellerCredibility
from app.utils.logger import get_logger

logger = get_logger(__name__)


class TrustworthyStandardModel:
    """Calibrated trust model that combines all signals into a final TrustScore."""

    # Verdict thresholds
    TRUSTED_THRESHOLD = 0.8
    CAUTION_THRESHOLD = 0.55

    def __init__(self):
        pass

    def evaluate(
        self,
        seller_credibility: SellerCredibility,
        image_consistency: Optional[Dict] = None,
        llm_score: Optional[Dict] = None,
    ) -> TrustScore:
        """Combine all trust signals into a final TrustScore."""
        factors = []

        # Factor 1: Listing/seller signals (reviews, price anomalies, account cues)
        factors.append(TrustFactor(
            factor_name="Product & Seller Signals",
            score=seller_credibility.overall_score,
            weight=0.25,
            evidence=seller_credibility.evidence[:5],
            details={
                "review_authenticity": seller_credibility.review_authenticity_score,
                "price_anomaly": seller_credibility.price_anomaly_score,
                "account_age": seller_credibility.account_age_score,
            },
        ))

        factors.append(TrustFactor(
            factor_name="Website Trust",
            score=seller_credibility.domain_trust_score,
            weight=0.25,
            evidence=seller_credibility.evidence[:5],
            details={"domain_trust_score": seller_credibility.domain_trust_score},
        ))

        # Factor 2: Image consistency
        if image_consistency:
            img_score = 1.0 - (0.5 if image_consistency.get("is_manipulated") else 0.0)
            factors.append(TrustFactor(
                factor_name="Image Consistency",
                score=img_score,
                weight=0.20,
                evidence=image_consistency.get("evidence", []),
                details={"ela_score": image_consistency.get("ela_score", 0)},
            ))
        else:
            factors.append(TrustFactor(
                factor_name="Image Consistency",
                score=0.5,
                weight=0.20,
                evidence=["Image analysis not performed"],
                details={},
            ))

        # Factor 3: LLM/Rule-based score
        if llm_score:
            factors.append(TrustFactor(
                factor_name="Content Quality",
                score=llm_score.get("llm_score", 0.5),
                weight=0.20,
                evidence=[llm_score.get("reasoning", "")],
                details={"risk_flags": llm_score.get("risk_flags", [])},
            ))
        else:
            factors.append(TrustFactor(
                factor_name="Content Quality",
                score=0.5,
                weight=0.20,
                evidence=["Content scoring not performed"],
                details={},
            ))

        # Factor 4: Overall listing quality
        factors.append(TrustFactor(
            factor_name="Listing Completeness",
            score=0.5,
            weight=0.10,
            evidence=["Default listing quality score"],
            details={},
        ))

        # Calculate raw score
        raw_score = sum(f.score * f.weight for f in factors) / sum(f.weight for f in factors)

        # Calibrate
        calibrated = self._calibrate_score(raw_score)

        # Determine verdict
        if calibrated >= self.TRUSTED_THRESHOLD:
            verdict = TrustVerdict.TRUSTED
        elif calibrated >= self.CAUTION_THRESHOLD:
            verdict = TrustVerdict.CAUTION
        else:
            verdict = TrustVerdict.UNTRUSTED

        # Generate explanation
        explanation = self._generate_explanation(factors, verdict)
        risk_flags = self._extract_risk_flags(factors)

        # Confidence based on data availability
        confidence = min(0.3 + (len([f for f in factors if f.score != 0.5]) * 0.2), 0.95)

        return TrustScore(
            overall_score=round(calibrated, 4),
            verdict=verdict,
            factors=factors,
            explanation=explanation,
            risk_flags=risk_flags,
            confidence=round(confidence, 4),
        )

    def _calibrate_score(self, raw_score: float) -> float:
        """Apply sigmoid calibration to normalize scores."""
        # Sigmoid centered at 0.5 with moderate steepness
        x = (raw_score - 0.5) * 6  # Scale to -3..3 range
        calibrated = 1.0 / (1.0 + math.exp(-x))
        return calibrated

    def _generate_explanation(self, factors: List[TrustFactor], verdict: TrustVerdict) -> str:
        """Generate human-readable trust explanation."""
        verdict_text = {
            TrustVerdict.TRUSTED: "This listing appears trustworthy",
            TrustVerdict.CAUTION: "This listing requires caution",
            TrustVerdict.UNTRUSTED: "This listing shows signs of being untrustworthy",
        }

        parts = [f"{verdict.symbol} {verdict_text[verdict]}."]

        # Add top factors
        sorted_factors = sorted(factors, key=lambda f: abs(f.score - 0.5), reverse=True)
        for f in sorted_factors[:3]:
            if f.score >= 0.7:
                parts.append(f"✓ {f.factor_name}: Strong ({f.score:.0%})")
            elif f.score <= 0.3:
                parts.append(f"✗ {f.factor_name}: Weak ({f.score:.0%})")
            else:
                parts.append(f"⚠ {f.factor_name}: Moderate ({f.score:.0%})")

        return " ".join(parts)

    def _extract_risk_flags(self, factors: List[TrustFactor]) -> List[str]:
        """Extract all risk flags from factors."""
        flags = []
        for f in factors:
            if f.score < 0.4:
                flags.append(f"Low {f.factor_name.lower()} score")
            risk_flags = f.details.get("risk_flags", [])
            if isinstance(risk_flags, list):
                flags.extend(risk_flags)
        return list(set(flags))
