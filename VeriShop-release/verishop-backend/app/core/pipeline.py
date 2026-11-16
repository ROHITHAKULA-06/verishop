"""
VeriShop Core Pipeline
Orchestrates the full L2→L3→L4→L5→L6→L7 processing pipeline.
"""

import time
from typing import List, Optional
from uuid import uuid4
from datetime import datetime

from app.config import Settings
from app.models.enums import QueryType, TrustVerdict
from app.models.product import Product, ProductSource, ProductPricing, ProductImage, ProductReview
from app.models.trust import TrustScore, RankedProduct, SellerCredibility, TrustFactor
from app.models.schemas import SearchRequest, SearchResponse, ProductResponse, TrustResponse
from app.layers.l2_input_processor.processor import MultimodalInputProcessor
from app.layers.l3a_nlp_pipeline.pipeline import NLPPipeline
from app.layers.l3b_vision_pipeline.pipeline import VisionPipeline
from app.layers.l4_seller_credibility.engine import SellerCredibilityEngine
from app.layers.l5_agentic_ranking.ranker import AgenticProductRanker
from app.layers.l5_agentic_ranking.llm_scoring import LLMGenerativeScorer
from app.layers.l5_agentic_ranking.trust_model import TrustworthyStandardModel
from app.layers.l5_agentic_ranking.synthesizer import GenerativeAISynthesizer
from app.layers.l6_storage.product_store import ProductStore
from app.layers.l6_storage.vector_store import VectorStore
from app.layers.l1_5_retrieval.retriever import LiveSearchRetriever
from app.layers.l1_5_retrieval.scraper import WebScraper
from app.layers.l7_output.verifier import TrustVerifier
from app.layers.l7_output.rule_filter import RuleBasedFilter
from app.layers.l7_output.candidate_selector import CandidateSelector
from app.utils.logger import get_logger
from app.utils.helpers import generate_request_id, cosine_similarity

logger = get_logger(__name__)


class VeriShopPipeline:
    """Full VeriShop processing pipeline — L2 through L7."""

    def __init__(self, settings: Settings):
        self.settings = settings

        # L2
        self.input_processor = MultimodalInputProcessor(settings)
        # L3a, L3b
        self.nlp_pipeline = NLPPipeline(settings)
        self.vision_pipeline = VisionPipeline(settings)
        # L1.5 Live Retrieval
        self.retriever = LiveSearchRetriever()
        self.scraper = WebScraper()
        # L4
        self.credibility_engine = SellerCredibilityEngine(settings)
        # L5
        self.ranker = AgenticProductRanker(settings)
        self.llm_scorer = LLMGenerativeScorer(settings)
        self.trust_model = TrustworthyStandardModel()
        self.synthesizer = GenerativeAISynthesizer(settings)
        # L6
        self.product_store = ProductStore(db_path=settings.SQLITE_DB_PATH)
        self.vector_store = VectorStore(index_path=settings.FAISS_INDEX_PATH)
        # L7
        self.verifier = TrustVerifier()
        self.rule_filter = RuleBasedFilter()
        self.candidate_selector = CandidateSelector()

    async def search(self, request: SearchRequest) -> SearchResponse:
        """Full pipeline: query → ranked, verified results with evidence."""
        request_id = generate_request_id()
        start_time = time.perf_counter()
        timings = {}

        # ── L2: Process input ──
        t = time.perf_counter()
        processed = await self.input_processor.process(
            query=request.query, image_data=request.image_base64 or request.image_url,
        )
        timings["l2_input"] = (time.perf_counter() - t) * 1000

        query_type = processed["query_type"]
        text_embedding = []
        image_embedding = []

        # ── L3a: NLP Pipeline ──
        if processed["processed_text"]:
            t = time.perf_counter()
            nlp_result = await self.nlp_pipeline.process(processed["processed_text"])
            text_embedding = nlp_result.get("text_embedding", [])
            timings["l3a_nlp"] = (time.perf_counter() - t) * 1000

        # ── L3b: Vision Pipeline ──
        if processed["processed_image"]:
            t = time.perf_counter()
            vision_result = await self.vision_pipeline.process(processed["processed_image"])
            image_embedding = vision_result.get("image_embedding", [])
            timings["l3b_vision"] = (time.perf_counter() - t) * 1000

        # ── L1.5: Live Retrieval & Scraping ──
        t = time.perf_counter()
        products = []
        price_unavailable = 0
        scrape_failures = 0
        candidate_urls = 0
        
        # 1. Search the web for live product URLs
        query_str = request.query or "product"
        urls = self.retriever.search(query_str, max_results=max(5, request.max_results))
        
        # 2. Scrape the URLs concurrently
        if urls:
            import asyncio
            # Analyze the requested number of discovered product URLs.
            target_urls = urls[:request.max_results]
            candidate_urls = len(target_urls)
            scrape_tasks = [
                self.scraper.scrape(
                    u["url"], 
                    search_title=u.get("title", ""), 
                    search_snippet=u.get("snippet", "")
                ) 
                for u in target_urls
            ]
            scraped_results = await asyncio.gather(*scrape_tasks, return_exceptions=True)
            for res in scraped_results:
                if isinstance(res, Exception) or res is None:
                    scrape_failures += 1
                    continue
                if res:
                    # Never turn a blocked/unknown price into ₹0 or a sample
                    # listing. Such a result cannot support price comparison.
                    if res.get("price") is None:
                        price_unavailable += 1
                    # Unknown prices remain visible and score as a risk signal;
                    # use zero internally, never display it as a currency value.
                    p = Product(
                        title=res.get("title") or "Unknown Product",
                        description=res.get("description") or "",
                        pricing=ProductPricing(
                            price=res.get("price") or 0.0,
                            currency="INR"
                        ),
                        source=ProductSource(
                            source_name=res.get("domain") or "Unknown",
                            source_url=res.get("url") or ""
                        ),
                        seller_name=res.get("domain") or "Unknown",
                    )
                    for review in res.get("reviews", []):
                        review_values = {
                            "reviewer_id": review.get("reviewer_id", "public-review"),
                            "rating": review.get("rating"),
                            "text": review.get("text", ""),
                        }
                        published = review.get("created_at")
                        if published:
                            try:
                                review_values["created_at"] = datetime.fromisoformat(str(published).replace("Z", "+00:00"))
                            except ValueError:
                                pass
                        try:
                            p.reviews.append(ProductReview(**review_values))
                        except Exception:
                            continue
                    if res.get("image_url"):
                        p.images.append(ProductImage(url=res.get("image_url"), is_primary=True))
                    products.append(p)

        timings["l1_5_retrieval"] = (time.perf_counter() - t) * 1000

        # ── L4: Seller credibility ──
        t = time.perf_counter()
        credibilities = await self.credibility_engine.evaluate_batch(products)
        timings["l4_credibility"] = (time.perf_counter() - t) * 1000

        # ── L5: Trust scoring + ranking ──
        t = time.perf_counter()
        trust_scores = []
        for i, product in enumerate(products):
            cred = credibilities[i]
            llm_result = await self.llm_scorer.score(product)
            ts = self.trust_model.evaluate(cred, llm_score=llm_result)
            if product.pricing.price <= 0:
                ts.verdict = TrustVerdict.CAUTION
                ts.risk_flags = list(dict.fromkeys([*ts.risk_flags, "Current price unavailable from retailer page"]))
            trust_scores.append(ts)

        # Calculate relevance scores using text embedding cosine similarity
        relevance_scores = []
        if text_embedding and products:
            prod_texts = [f"{p.title} {p.description or ''}".strip() for p in products]
            prod_embeddings = self.nlp_pipeline.clip_encoder.encode_batch(prod_texts)
            for prod_emb in prod_embeddings:
                sim = cosine_similarity(text_embedding, prod_emb)
                relevance_scores.append(round(max(0.0, min(1.0, float(sim))), 4))
        else:
            relevance_scores = [0.5 for _ in products]

        ranked_dicts = self.ranker.rank(products, trust_scores, relevance_scores)
        timings["l5_ranking"] = (time.perf_counter() - t) * 1000

        # ── L7: Filter, verify, select ──
        t = time.perf_counter()
        ranked_products = [
            RankedProduct(
                product=d["product"],
                trust_score=d["trust_score"],
                relevance_score=d["relevance_score"],
                blended_score=d["blended_score"],
                rank=d["rank"],
                explanation=d["explanation"],
            )
            for d in ranked_dicts if d["trust_score"] is not None
        ]

        filtered = self.rule_filter.filter(ranked_products)
        selected = self.candidate_selector.select(
            # Keep below-threshold listings so the UI can show them in the
            # Discarded tab. min_trust_score is a display split, not a removal
            # filter; otherwise rejected candidates disappear from the audit.
            filtered, max_results=len(filtered), min_trust=0.0,
        )
        timings["l7_output"] = (time.perf_counter() - t) * 1000

        total_ms = (time.perf_counter() - start_time) * 1000

        # Save search history
        await self.product_store.save_search(request_id, request.query or "", len(selected))

        return SearchResponse(
            request_id=request_id,
            query_type=query_type,
            results=selected,
            total_found=len(selected),
            processing_time_ms=round(total_ms, 2),
            metadata={
                "timings": timings,
                "pipeline_version": "1.1.0",
                "min_trust_score": request.min_trust_score,
                "live_results": len(products),
                "price_unavailable": price_unavailable,
                "candidate_urls": candidate_urls,
                "scrape_failures": scrape_failures,
                "search_status": getattr(self.retriever, "last_status", "unknown"),
                "search_errors": getattr(self.retriever, "last_errors", [])[:3],
                "notice": "Some stores block automated access or omit public price data. Prices are included only when read from the product page." if price_unavailable or scrape_failures else None,
            },
        )

    async def get_product_trust(self, product_id: str) -> TrustResponse:
        """Get trust assessment for a specific product."""
        product = await self.product_store.get_product(product_id)
        if not product:
            from app.core.exceptions import ProcessingError
            raise ProcessingError("Product not found", detail=f"ID: {product_id}")

        cred = await self.credibility_engine.evaluate(product)
        llm = await self.llm_scorer.score(product)
        ts = self.trust_model.evaluate(cred, llm_score=llm)

        return TrustResponse(product_id=product_id, trust_score=ts, seller_credibility=cred)

    async def get_product(self, product_id: str) -> ProductResponse:
        """Get a product by ID with optional trust score."""
        product = await self.product_store.get_product(product_id)
        if not product:
            from app.core.exceptions import ProcessingError
            raise ProcessingError("Product not found", detail=f"ID: {product_id}")

        trust = await self.product_store.get_trust_score(product_id)
        return ProductResponse(product=product, trust_score=trust)

    def _create_sample_products(self, query: str, n: int = 5) -> List[Product]:
        """Create synthetic fixtures for explicit demos/tests; live search never calls this."""
        return [
            Product(
                title=f"Sample {query.title()} {index + 1}",
                pricing=ProductPricing(price=1000.0 + index * 100, currency="INR"),
                source=ProductSource(source_name="Sample data", source_url="https://example.invalid/"),
            )
            for index in range(max(0, n))
        ]
