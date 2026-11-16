"""
L4 — Seller Credibility Engine
Orchestrates review authentication, graph analysis, anomaly detection, and price scoring.
"""

from typing import List, Optional
from app.models.product import Product
from app.models.trust import SellerCredibility
from app.layers.l4_seller_credibility.review_authenticator import ReviewAuthenticator
from app.layers.l4_seller_credibility.review_graph import ReviewRelationshipGraph
from app.layers.l4_seller_credibility.anomaly_detector import AnomalyDetector
from app.layers.l4_seller_credibility.price_scorer import PriceAnomalyScorer
from app.layers.l4_seller_credibility.seller_aggregator import SellerScoreAggregator
from app.layers.l4_seller_credibility.domain_trust import WebsiteTrustEvaluator
from app.utils.logger import get_logger

logger = get_logger(__name__)


class SellerCredibilityEngine:
    """Evaluates seller and domain credibility through multi-factor analysis."""

    def __init__(self, settings=None):
        self.settings = settings
        self.review_authenticator = ReviewAuthenticator()
        self.review_graph = ReviewRelationshipGraph()
        self.anomaly_detector = AnomalyDetector()
        self.price_scorer = PriceAnomalyScorer()
        self.domain_evaluator = WebsiteTrustEvaluator()
        self.aggregator = SellerScoreAggregator()

    async def evaluate(self, product: Product) -> SellerCredibility:
        """Evaluate seller credibility for a product."""
        # Run all sub-components
        review_auth = self.review_authenticator.authenticate(product.reviews)
        review_graph_result = self.review_graph.build_graph(product.reviews)
        anomalies = self.anomaly_detector.detect(product)
        price_score = self.price_scorer.score(product)
        
        from urllib.parse import urlparse
        domain_url = product.source.source_url if (product.source and product.source.source_url) else ""
        if domain_url:
            if not domain_url.startswith(("http://", "https://")):
                domain_url = f"https://{domain_url}"
            domain_name = urlparse(domain_url).netloc
        else:
            raw_target = (
                (product.seller_id if product.seller_id and "." in product.seller_id else "")
                or (product.source.source_name if product.source and "." in product.source.source_name else "")
                or (f"{product.source.source_name.lower().replace(' ', '')}.com" if product.source and product.source.source_name and product.source.source_name != "Unknown" else "")
                or (f"{product.seller_name.lower().replace(' ', '')}.com" if product.seller_name and product.seller_name != "Unknown" else "")
                or (f"{product.seller_id}.com" if product.seller_id else "unknown.com")
            )
            raw_target = raw_target.lower().strip()
            domain_url = f"https://{raw_target}"
            domain_name = urlparse(domain_url).netloc or raw_target

        import asyncio
        domain_trust = await asyncio.to_thread(self.domain_evaluator.evaluate, domain_url, domain_name)

        # Aggregate scores
        credibility = self.aggregator.aggregate(
            review_auth=review_auth,
            review_graph=review_graph_result,
            anomalies=anomalies,
            price_score=price_score,
            domain_trust=domain_trust,
            product=product,
        )

        return credibility

    async def evaluate_batch(self, products: List[Product]) -> List[SellerCredibility]:
        """Evaluate credibility for multiple products in parallel."""
        if not products:
            return []
        import asyncio
        results = await asyncio.gather(*(self.evaluate(product) for product in products))
        return list(results)
