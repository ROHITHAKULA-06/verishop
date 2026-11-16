"""L7 — Candidate Selector: Top-K selection with source diversity."""

from typing import List
from collections import Counter
from app.models.trust import RankedProduct


class CandidateSelector:
    def select(self, ranked_products: List[RankedProduct], max_results: int = 10, min_trust: float = 0.0) -> List[RankedProduct]:
        filtered = self._apply_trust_minimum(ranked_products, min_trust)
        diverse = self._ensure_diversity(filtered)
        result = diverse[:max_results]
        for i, p in enumerate(result):
            p.rank = i + 1
        return result

    def _apply_trust_minimum(self, products: List[RankedProduct], min_trust: float) -> List[RankedProduct]:
        if min_trust <= 0: return products
        return [p for p in products if p.trust_score.overall_score >= min_trust]

    def _ensure_diversity(self, products: List[RankedProduct], max_per_source_pct: float = 0.6) -> List[RankedProduct]:
        if len(products) <= 2: return products
        max_per_source = max(1, int(len(products) * max_per_source_pct))
        source_counts: Counter = Counter()
        result = []
        deferred = []
        for p in products:
            src = p.product.source.source_name
            if source_counts[src] < max_per_source:
                result.append(p)
                source_counts[src] += 1
            else:
                deferred.append(p)
        result.extend(deferred)
        return result
