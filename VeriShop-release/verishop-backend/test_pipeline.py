"""
Test the end-to-end VeriShop Pipeline via L2 to L7.
"""
import asyncio
from app.config import settings
from app.core.pipeline import VeriShopPipeline
from app.models.schemas import SearchRequest

async def main():
    pipeline = VeriShopPipeline(settings)
    
    print("=" * 60)
    print("Running Full VeriShop Pipeline Search")
    print("=" * 60)
    
    request = SearchRequest(
        query="nothing ear 2",
        max_results=5,
        min_trust_score=0.4
    )
    
    response = await pipeline.search(request)
    
    print(f"\nProcessing Time: {response.processing_time_ms} ms")
    print(f"Total Found: {response.total_found}")
    
    for i, res in enumerate(response.results):
        p = res.product
        print(f"\n[{i+1}] {p.title}")
        print(f"    URL: {p.source.source_url}")
        print(f"    Trust Score: {res.trust_score.overall_score:.2%}")
        print(f"    Blended Rank: {res.blended_score:.2f}")
        print(f"    Explanation: {res.explanation}")

if __name__ == "__main__":
    asyncio.run(main())
