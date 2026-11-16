"""
L3a — NLP Pipeline Orchestrator
Orchestrates CLIP text, SBERT, query expansion, normalization, and NER extraction.
"""

import time
from typing import Dict, Any, Optional

from app.layers.l3a_nlp_pipeline.clip_text import CLIPTextEncoder
from app.layers.l3a_nlp_pipeline.sbert_encoder import SBERTEncoder
from app.layers.l3a_nlp_pipeline.query_expansion import QueryExpander
from app.layers.l3a_nlp_pipeline.normalizer import TextNormalizer
from app.layers.l3a_nlp_pipeline.ner_extractor import ProductNERExtractor
from app.utils.logger import get_logger

logger = get_logger(__name__)


class NLPPipeline:
    """Orchestrates the full NLP pipeline for text queries."""

    def __init__(self, settings=None, model_manager=None):
        self.settings = settings
        model_name = "openai/clip-vit-base-patch32"
        sbert_name = "all-MiniLM-L6-v2"
        if settings:
            model_name = getattr(settings, "CLIP_MODEL_NAME", model_name)
            sbert_name = getattr(settings, "SBERT_MODEL_NAME", sbert_name)

        self.clip_encoder = CLIPTextEncoder(model_name=model_name)
        self.sbert_encoder = SBERTEncoder(model_name=sbert_name)
        self.query_expander = QueryExpander()
        self.normalizer = TextNormalizer()
        self.ner_extractor = ProductNERExtractor()

    async def process(self, processed_text: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the full NLP pipeline.
        Input: processed text dict from L2 TextProcessor
        Output: embeddings, expanded queries, entities, etc.
        """
        steps = []
        cleaned_text = processed_text.get("cleaned_text", "")

        if not cleaned_text:
            return {
                "text_embedding": [],
                "semantic_embedding": [],
                "expanded_queries": [],
                "normalized_text": "",
                "entities": {},
                "processing_steps": [],
            }

        # Step 1: NER extraction
        t0 = time.perf_counter()
        entities = self.ner_extractor.extract(cleaned_text)
        steps.append({"step": "ner_extraction", "time_ms": (time.perf_counter() - t0) * 1000})

        # Step 2: CLIP text embedding
        t0 = time.perf_counter()
        text_embedding = self.clip_encoder.encode(cleaned_text)
        steps.append({"step": "clip_text_encoding", "time_ms": (time.perf_counter() - t0) * 1000})

        # Step 3: SBERT encoding
        t0 = time.perf_counter()
        semantic_embedding = self.sbert_encoder.encode(cleaned_text)
        steps.append({"step": "sbert_encoding", "time_ms": (time.perf_counter() - t0) * 1000})

        # Step 4: Query expansion
        t0 = time.perf_counter()
        expanded_queries = self.query_expander.expand(cleaned_text, entities)
        steps.append({"step": "query_expansion", "time_ms": (time.perf_counter() - t0) * 1000})

        # Step 5: Normalization & dedup
        t0 = time.perf_counter()
        normalized_text = self.normalizer.normalize(cleaned_text)
        expanded_queries = self.normalizer.deduplicate_texts(expanded_queries)
        steps.append({"step": "normalization", "time_ms": (time.perf_counter() - t0) * 1000})

        return {
            "text_embedding": text_embedding,
            "semantic_embedding": semantic_embedding,
            "expanded_queries": expanded_queries,
            "normalized_text": normalized_text,
            "entities": entities,
            "processing_steps": steps,
        }
