"""
L4 — Review Authenticator
Analyzes review authenticity through sentiment distribution, patterns, and verified ratio.
"""

from typing import List, Dict, Any
from collections import Counter
from app.models.product import ProductReview
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ReviewAuthenticator:
    """Authenticates product reviews by analyzing patterns and distributions."""

    def authenticate(self, reviews: List[ProductReview]) -> Dict[str, Any]:
        """Authenticate reviews and return authenticity assessment."""
        if not reviews:
            return {
                "authenticity_score": 0.5,
                "fake_review_count": 0,
                "suspicious_patterns": ["No reviews to analyze"],
                "evidence": ["No reviews available for authentication"],
            }

        suspicious_patterns = []
        evidence = []

        # Analyze sentiment distribution
        sentiment_result = self._analyze_sentiment_distribution(reviews)
        if sentiment_result.get("is_suspicious"):
            suspicious_patterns.append(sentiment_result["reason"])
            evidence.append(sentiment_result["evidence"])

        # Detect review patterns
        patterns = self._detect_review_patterns(reviews)
        suspicious_patterns.extend(patterns)

        # Check verified purchase ratio
        verified_ratio = self._check_verified_ratio(reviews)
        if verified_ratio < 0.3:
            evidence.append(f"Low verified purchase ratio: {verified_ratio:.0%}")

        # Analyze review lengths
        length_result = self._analyze_review_lengths(reviews)
        if length_result.get("is_suspicious"):
            suspicious_patterns.append(length_result["reason"])

        # Calculate authenticity score
        penalty = len(suspicious_patterns) * 0.15
        authenticity_score = max(0.0, min(1.0,
            0.5 + (verified_ratio * 0.3) - penalty + (sentiment_result.get("naturalness", 0.5) * 0.2)
        ))

        fake_count = int(len(reviews) * (1 - authenticity_score) * 0.5)

        return {
            "authenticity_score": round(authenticity_score, 4),
            "fake_review_count": fake_count,
            "suspicious_patterns": suspicious_patterns,
            "evidence": evidence,
        }

    def _analyze_sentiment_distribution(self, reviews: List[ProductReview]) -> Dict[str, Any]:
        """Check if rating distribution is natural or suspicious."""
        ratings = [r.rating for r in reviews]
        if not ratings:
            return {"is_suspicious": False, "naturalness": 0.5}

        counter = Counter([round(r) for r in ratings])
        total = len(ratings)
        distribution = {i: counter.get(i, 0) / total for i in range(1, 6)}

        # Suspicious: >80% are 5-star
        five_star_ratio = distribution.get(5, 0)
        if five_star_ratio > 0.8:
            return {
                "is_suspicious": True,
                "reason": f"Abnormally high 5-star ratio: {five_star_ratio:.0%}",
                "evidence": f"Rating distribution skewed: {five_star_ratio:.0%} five-star reviews",
                "naturalness": 0.2,
            }

        # Suspicious: bimodal (1-star and 5-star dominate)
        extremes = distribution.get(1, 0) + distribution.get(5, 0)
        if extremes > 0.85:
            return {
                "is_suspicious": True,
                "reason": "Bimodal rating distribution (mostly 1★ and 5★)",
                "evidence": "Unusual bimodal pattern suggests review manipulation",
                "naturalness": 0.3,
            }

        return {"is_suspicious": False, "naturalness": 0.8}

    def _detect_review_patterns(self, reviews: List[ProductReview]) -> List[str]:
        """Detect suspicious review patterns."""
        patterns = []
        texts = [r.text.lower().strip() for r in reviews if r.text]

        # Duplicate text detection
        text_counter = Counter(texts)
        duplicates = {t: c for t, c in text_counter.items() if c > 1 and t}
        if duplicates:
            patterns.append(f"Found {len(duplicates)} duplicate review texts")

        # Excessive short reviews
        short_reviews = [t for t in texts if len(t) < 20]
        if len(short_reviews) > len(texts) * 0.6:
            patterns.append(f"Excessive short reviews: {len(short_reviews)}/{len(texts)}")

        # Same-day review clusters
        dates = [r.created_at.date() for r in reviews]
        date_counts = Counter(dates)
        for date, count in date_counts.items():
            if count > 5 and count > len(reviews) * 0.3:
                patterns.append(f"Review cluster on {date}: {count} reviews")

        return patterns

    def _check_verified_ratio(self, reviews: List[ProductReview]) -> float:
        """Calculate ratio of verified purchases."""
        if not reviews:
            return 0.5
        verified = sum(1 for r in reviews if r.verified_purchase)
        return verified / len(reviews)

    def _analyze_review_lengths(self, reviews: List[ProductReview]) -> Dict[str, Any]:
        """Check if review lengths are suspiciously uniform."""
        lengths = [len(r.text) for r in reviews if r.text]
        if len(lengths) < 3:
            return {"is_suspicious": False}

        import numpy as np
        std_dev = np.std(lengths)
        mean_len = np.mean(lengths)

        # Very uniform lengths are suspicious
        if std_dev < 10 and mean_len > 20:
            return {
                "is_suspicious": True,
                "reason": f"Suspiciously uniform review lengths (std={std_dev:.1f})",
            }

        # Very short average
        if mean_len < 15:
            return {
                "is_suspicious": True,
                "reason": f"Average review length very short ({mean_len:.0f} chars)",
            }

        return {"is_suspicious": False}
