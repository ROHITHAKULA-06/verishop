"""L4 Seller Credibility tests."""
import pytest
from app.layers.l4_seller_credibility.review_authenticator import ReviewAuthenticator
from app.layers.l4_seller_credibility.price_scorer import PriceAnomalyScorer
from app.layers.l4_seller_credibility.anomaly_detector import AnomalyDetector

def test_review_authenticator_empty():
    ra = ReviewAuthenticator()
    result = ra.authenticate([])
    assert result["authenticity_score"] == 0.5

def test_review_authenticator_with_reviews(sample_product):
    ra = ReviewAuthenticator()
    result = ra.authenticate(sample_product.reviews)
    assert 0 <= result["authenticity_score"] <= 1

def test_price_scorer(sample_product):
    ps = PriceAnomalyScorer()
    result = ps.score(sample_product, market_prices=[60, 70, 80, 90, 100])
    assert "anomaly_score" in result
    assert "z_score" in result

def test_anomaly_detector(sample_product):
    ad = AnomalyDetector()
    result = ad.detect(sample_product)
    assert "anomaly_score" in result
    assert "risk_level" in result
