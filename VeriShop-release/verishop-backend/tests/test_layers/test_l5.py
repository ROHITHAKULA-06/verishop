"""L5 Agentic Ranking tests."""
import pytest
from app.layers.l5_agentic_ranking.ranker import AgenticProductRanker
from app.layers.l5_agentic_ranking.llm_scoring import LLMGenerativeScorer
from app.layers.l5_agentic_ranking.trust_model import TrustworthyStandardModel
from app.models.trust import SellerCredibility

def test_blended_score():
    ranker = AgenticProductRanker()
    score = ranker._compute_blended_score(relevance=0.8, trust=0.9)
    assert 0 < score <= 1.0

def test_trust_penalty():
    ranker = AgenticProductRanker()
    high_trust = ranker._compute_blended_score(0.8, 0.9)
    low_trust = ranker._compute_blended_score(0.8, 0.2)
    assert high_trust > low_trust

def test_llm_rule_based_fallback(sample_product):
    scorer = LLMGenerativeScorer()
    result = scorer._rule_based_fallback(sample_product)
    assert 0 <= result["llm_score"] <= 1
    assert result["confidence"] > 0

def test_trust_model():
    model = TrustworthyStandardModel()
    cred = SellerCredibility(seller_id="s1", seller_name="Seller", overall_score=0.8,
                             review_authenticity_score=0.8, price_anomaly_score=0.1, account_age_score=0.9, evidence=[])
    result = model.evaluate(cred)
    assert result.verdict is not None
    assert 0 <= result.overall_score <= 1
