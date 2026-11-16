"""L7 — Trust Verifier: Final verification pass producing trust verdict with actionable advice."""

from typing import Dict, Any, List
from app.models.enums import TrustVerdict
from app.models.trust import TrustScore
from app.models.product import Product


class TrustVerifier:
    def verify(self, trust_score: TrustScore, product: Product) -> Dict[str, Any]:
        confidence = self._assess_overall_confidence(trust_score, product)
        risk_flags = trust_score.risk_flags
        evidence = [f.evidence[0] for f in trust_score.factors if f.evidence]
        advice = self._generate_actionable_advice(trust_score.verdict, risk_flags)
        return {
            "verdict": trust_score.verdict, "confidence": round(confidence, 4),
            "summary": trust_score.explanation, "risk_flags": risk_flags,
            "evidence_summary": evidence[:10], "actionable_advice": advice,
        }

    def _assess_overall_confidence(self, ts: TrustScore, p: Product) -> float:
        conf = ts.confidence
        if len(p.reviews) > 5: conf += 0.1
        if len(p.images) > 0: conf += 0.05
        if p.description and len(p.description) > 100: conf += 0.05
        return min(conf, 0.99)

    def _generate_actionable_advice(self, verdict: TrustVerdict, flags: List[str]) -> str:
        if verdict == TrustVerdict.TRUSTED:
            return "This listing appears safe. Standard purchase precautions apply."
        elif verdict == TrustVerdict.CAUTION:
            return "Proceed with caution — verify seller history and return policy before purchasing."
        return "This listing shows significant risk indicators. We recommend avoiding this listing or conducting thorough verification before any purchase."
