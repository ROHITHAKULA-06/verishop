"""
L3a — SBERT Encoder
Generates SBERT semantic embeddings for text similarity.
"""

import hashlib
from typing import List
from app.utils.logger import get_logger

logger = get_logger(__name__)

SBERT_DIM = 384


class SBERTEncoder:
    """Sentence-BERT encoder with lazy loading and mock fallback."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self._model = None
        self._loaded = False

    def _load_model(self):
        """Lazy-load sentence-transformers model."""
        if self._loaded:
            return
        try:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.model_name)
            self._loaded = True
            logger.info("sbert_model_loaded", model=self.model_name)
        except Exception as e:
            logger.warning("sbert_model_unavailable", error=str(e))
            self._loaded = False

    def encode(self, text: str) -> List[float]:
        """Generate SBERT embedding (384-dim). Falls back to mock."""
        self._load_model()

        if self._model is not None:
            try:
                embedding = self._model.encode(text, convert_to_numpy=True)
                return embedding.tolist()
            except Exception as e:
                logger.warning("sbert_encode_failed", error=str(e))

        return self._mock_embedding(text)

    def encode_batch(self, texts: List[str]) -> List[List[float]]:
        """Encode a batch of texts."""
        self._load_model()

        if self._model is not None:
            try:
                embeddings = self._model.encode(texts, convert_to_numpy=True)
                return embeddings.tolist()
            except Exception as e:
                logger.warning("sbert_batch_encode_failed", error=str(e))

        return [self._mock_embedding(t) for t in texts]

    def similarity(self, text1: str, text2: str) -> float:
        """Compute cosine similarity between two texts."""
        import numpy as np
        emb1 = np.array(self.encode(text1))
        emb2 = np.array(self.encode(text2))
        norm1 = np.linalg.norm(emb1)
        norm2 = np.linalg.norm(emb2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return float(np.dot(emb1, emb2) / (norm1 * norm2))

    def _mock_embedding(self, text: str) -> List[float]:
        """Generate a deterministic mock embedding."""
        import numpy as np
        seed = int(hashlib.md5(text.encode()).hexdigest(), 16) % (2**31)
        rng = np.random.RandomState(seed)
        vec = rng.randn(SBERT_DIM).astype(float)
        vec = vec / (np.linalg.norm(vec) + 1e-8)
        return vec.tolist()
