"""L3a NLP Pipeline tests."""
from app.layers.l3a_nlp_pipeline.ner_extractor import ProductNERExtractor
from app.layers.l3a_nlp_pipeline.normalizer import TextNormalizer
from app.layers.l3a_nlp_pipeline.query_expansion import QueryExpander
from app.layers.l3a_nlp_pipeline.clip_text import CLIPTextEncoder
from app.layers.l3a_nlp_pipeline.sbert_encoder import SBERTEncoder

def test_ner_extraction():
    ner = ProductNERExtractor()
    result = ner.extract("Apple iPhone 14 Pro 128GB $999.99 in black 6.1 inches")
    assert result["brand"] == "Apple"
    assert len(result["price_mentions"]) > 0
    assert 999.99 in result["price_mentions"]

def test_normalizer():
    norm = TextNormalizer()
    assert "in" in norm.normalize("10 inches display")
    assert "lb" in norm.normalize("5 pounds weight")

def test_deduplication():
    norm = TextNormalizer()
    texts = ["wireless headphones", "wireless headphones bluetooth", "wireless headphones"]
    result = norm.deduplicate_texts(texts, threshold=0.85)
    assert len(result) <= len(texts)

def test_query_expansion():
    exp = QueryExpander()
    result = exp.expand("wireless headphones")
    assert len(result) >= 2
    assert "wireless headphones" in result

def test_clip_text_mock():
    enc = CLIPTextEncoder()
    emb = enc.encode("test product")
    assert len(emb) == 512

def test_sbert_mock():
    enc = SBERTEncoder()
    emb = enc.encode("test product")
    assert len(emb) == 384
