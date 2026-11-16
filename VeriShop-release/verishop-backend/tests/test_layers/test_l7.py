"""L7 Output & Verification tests."""
from app.layers.l7_output.rule_filter import RuleBasedFilter
from app.layers.l7_output.candidate_selector import CandidateSelector
from app.layers.l7_output.verifier import TrustVerifier
from app.models.trust import RankedProduct, TrustScore, TrustFactor
from app.models.enums import TrustVerdict

def _make_ranked(product, score=0.7, verdict=TrustVerdict.TRUSTED):
    ts = TrustScore(overall_score=score, verdict=verdict, factors=[], explanation="Test", risk_flags=[], confidence=0.8)
    return RankedProduct(product=product, trust_score=ts, relevance_score=0.8, blended_score=score, rank=1, explanation="Test")

def test_rule_filter(sample_product):
    rf = RuleBasedFilter()
    rp = _make_ranked(sample_product)
    result = rf.filter([rp])
    assert len(result) == 1

def test_candidate_selector(sample_product):
    cs = CandidateSelector()
    rp = _make_ranked(sample_product)
    result = cs.select([rp], max_results=5, min_trust=0.0)
    assert len(result) == 1
    assert result[0].rank == 1

def test_trust_verifier(sample_product):
    tv = TrustVerifier()
    ts = TrustScore(overall_score=0.8, verdict=TrustVerdict.TRUSTED,
                    factors=[TrustFactor(factor_name="Test", score=0.8, weight=1.0, evidence=["Good"], details={})],
                    explanation="Trusted", risk_flags=[], confidence=0.8)
    result = tv.verify(ts, sample_product)
    assert result["verdict"] == TrustVerdict.TRUSTED
    assert "actionable_advice" in result
