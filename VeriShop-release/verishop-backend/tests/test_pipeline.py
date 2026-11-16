"""Pipeline tests."""
import pytest
from app.config import Settings
from app.core.pipeline import VeriShopPipeline

@pytest.fixture
def pipeline():
    settings = Settings(DEBUG=True, SQLITE_DB_PATH="./data/test_pipe.db", FAISS_INDEX_PATH="./data/test_faiss_pipe")
    return VeriShopPipeline(settings)

def test_pipeline_initialization(pipeline):
    assert pipeline.input_processor is not None
    assert pipeline.nlp_pipeline is not None
    assert pipeline.vision_pipeline is not None
    assert pipeline.credibility_engine is not None
    assert pipeline.ranker is not None

def test_sample_product_generation(pipeline):
    products = pipeline._create_sample_products("headphones", n=5)
    assert len(products) == 5
    for p in products:
        assert p.title
        assert p.pricing.price > 0
