"""
L4 — Review Relationship Graph
Identifies coordinated fake reviews through reviewer clustering.
"""

from typing import List, Dict, Any, Set
from collections import defaultdict
from app.models.product import ProductReview
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ReviewRelationshipGraph:
    """Builds and analyzes reviewer relationship graphs to detect coordination."""

    def __init__(self):
        pass

    def build_graph(self, reviews: List[ProductReview]) -> Dict[str, Any]:
        """Build reviewer relationship graph and detect suspicious clusters."""
        if len(reviews) < 3:
            return {
                "graph_density": 0.0,
                "clusters": [],
                "suspicious_clusters": [],
                "coordinated_review_score": 0.0,
            }

        # Find clusters
        clusters = self._find_reviewer_clusters(reviews)

        # Detect coordination in each cluster
        suspicious_clusters = []
        coordination_scores = []

        for cluster in clusters:
            if len(cluster) >= 2:
                score = self._detect_coordination(cluster, reviews)
                coordination_scores.append(score)
                if score > 0.6:
                    suspicious_clusters.append(list(cluster))

        # Graph density
        n = len(set(r.reviewer_id for r in reviews))
        edges = sum(len(c) * (len(c) - 1) / 2 for c in clusters)
        max_edges = n * (n - 1) / 2 if n > 1 else 1
        density = edges / max_edges if max_edges > 0 else 0

        avg_coordination = sum(coordination_scores) / len(coordination_scores) if coordination_scores else 0

        return {
            "graph_density": round(density, 4),
            "clusters": [list(c) for c in clusters],
            "suspicious_clusters": suspicious_clusters,
            "coordinated_review_score": round(avg_coordination, 4),
        }

    def _find_reviewer_clusters(self, reviews: List[ProductReview]) -> List[Set[str]]:
        """Group reviewers by timing patterns and text similarity."""
        # Group by review date
        date_groups = defaultdict(set)
        for review in reviews:
            date_key = review.created_at.strftime("%Y-%m-%d")
            date_groups[date_key].add(review.reviewer_id)

        # Clusters are groups of 2+ reviewers who posted on the same day
        clusters = [group for group in date_groups.values() if len(group) >= 2]

        # Also check for text similarity clusters
        text_groups = defaultdict(set)
        for review in reviews:
            if review.text:
                # Simple: group by first 20 chars
                key = review.text[:20].lower().strip()
                text_groups[key].add(review.reviewer_id)

        text_clusters = [group for group in text_groups.values() if len(group) >= 2]
        clusters.extend(text_clusters)

        return clusters

    def _detect_coordination(self, cluster: Set[str], reviews: List[ProductReview]) -> float:
        """Score coordination likelihood for a cluster of reviewers."""
        cluster_reviews = [r for r in reviews if r.reviewer_id in cluster]

        if len(cluster_reviews) < 2:
            return 0.0

        score = 0.0
        factors = 0

        # Factor 1: Similar timestamps
        timestamps = sorted([r.created_at for r in cluster_reviews])
        if len(timestamps) >= 2:
            time_diffs = [(timestamps[i + 1] - timestamps[i]).total_seconds()
                         for i in range(len(timestamps) - 1)]
            avg_diff = sum(time_diffs) / len(time_diffs)
            # Reviews within 1 hour = suspicious
            if avg_diff < 3600:
                score += 0.4
            factors += 1

        # Factor 2: Similar ratings
        ratings = [r.rating for r in cluster_reviews]
        if ratings:
            rating_std = max(ratings) - min(ratings)
            if rating_std < 0.5:
                score += 0.3
            factors += 1

        # Factor 3: Similar review lengths
        lengths = [len(r.text) for r in cluster_reviews if r.text]
        if len(lengths) >= 2:
            import numpy as np
            length_std = np.std(lengths)
            if length_std < 20:
                score += 0.3
            factors += 1

        return min(score, 1.0)
