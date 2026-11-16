"""Public product discovery using independent, retailer-targeted web searches."""
from typing import Dict, List
from concurrent.futures import ThreadPoolExecutor
from ddgs import DDGS
from app.utils.logger import get_logger

logger = get_logger(__name__)


class LiveSearchRetriever:
    """Find candidate product pages; page scraping validates the actual price."""

    def __init__(self):
        self.last_errors: List[str] = []
        self.last_status = "not_started"

    def search(self, query: str, max_results: int = 15) -> List[Dict[str, str]]:
        logger.info("live_search_start", query=query, max_results=max_results)
        seen_urls = set()
        results: List[Dict[str, str]] = []
        self.last_errors = []
        self.last_status = "ok"
        queries = [f"{query} buy price India"]
        groups = (
            "site:amazon.in OR site:flipkart.com OR site:myntra.com",
            "site:ajio.com OR site:nykaa.com OR site:meesho.com OR site:firstcry.com",
            "site:croma.com OR site:reliancedigital.in OR site:tatacliq.com OR site:vijaysales.com",
            "site:jiomart.com OR site:snapdeal.com OR site:shopclues.com OR site:poorvika.com",
            "site:pepperfry.com OR site:urbanladder.com OR site:decathlon.in OR site:ikea.com/in",
        )
        queries.extend(f"{query} {group}" for group in groups)

        # Each provider call is isolated: one timeout or rejected query must
        # not discard results already found by the other strategies.
        def search_one(search_query):
            try:
                with DDGS() as ddgs:
                    rows = ddgs.text(search_query, region="in-en", max_results=max(10, min(max_results, 20)))
                    return [(search_query, row) for row in (rows or [])]
            except Exception as exc:
                logger.warning("live_search_strategy_failed", query=search_query, error=str(exc))
                return [(search_query, {"_error": str(exc)[:240]})]

        with ThreadPoolExecutor(max_workers=min(6, len(queries))) as pool:
            batches = list(pool.map(search_one, queries))
        for search_query, row in (item for batch in batches for item in batch):
            if "_error" in row:
                self.last_errors.append(row["_error"])
                continue
            url = row.get("href", "")
            if not url or url in seen_urls:
                continue
            seen_urls.add(url)
            results.append({"url": url, "title": row.get("title", ""), "snippet": row.get("body", "")})

        if not results:
            self.last_status = "provider_error" if self.last_errors else "no_candidates"
        logger.info("live_search_complete", total_found=len(results), status=self.last_status, failed_strategies=len(self.last_errors))
        return results[:max_results]
