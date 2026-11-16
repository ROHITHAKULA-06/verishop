"""
L3a — CLIP Text Encoder
Generates CLIP text embeddings for cross-modal similarity.
"""

import hashlib
from typing import List, Optional
from app.utils.logger import get_logger

logger = get_logger(__name__)

CLIP_DIM = 512


class CLIPTextEncoder:
    """CLIP text encoder with lazy loading and mock fallback."""

    def __init__(self, model_name: str = "openai/clip-vit-base-patch32"):
        self.model_name = model_name
        self._model = None
        self._processor = None
        self._loaded = False

    def _load_model(self):
        """Lazy-load CLIP model and processor."""
        if self._loaded:
            return
        try:
            from transformers import CLIPModel, CLIPProcessor
            self._model = CLIPModel.from_pretrained(self.model_name)
            self._processor = CLIPProcessor.from_pretrained(self.model_name)
            self._loaded = True
            logger.info("clip_text_model_loaded", model=self.model_name)
        except Exception as e:
            logger.warning("clip_text_model_unavailable", error=str(e))
            self._loaded = False

    def encode(self, text: str) -> List[float]:
        """Generate CLIP text embedding (512-dim). Falls back to mock if unavailable."""
        self._load_model()

        if self._model is not None and self._processor is not None:
            try:
                import torch
                inputs = self._processor(text=[text], return_tensors="pt", padding=True, truncation=True)
                with torch.no_grad():
                    outputs = self._model.get_text_features(**inputs)
                embedding = outputs[0].cpu().numpy().tolist()
                return embedding
            except Exception as e:
                logger.warning("clip_text_encode_failed", error=str(e))

        return self._mock_embedding(text)

    def encode_batch(self, texts: List[str]) -> List[List[float]]:
        """Encode a batch of texts."""
        self._load_model()

        if self._model is not None and self._processor is not None:
            try:
                import torch
                inputs = self._processor(text=texts, return_tensors="pt", padding=True, truncation=True)
                with torch.no_grad():
                    outputs = self._model.get_text_features(**inputs)
                return outputs.cpu().numpy().tolist()
            except Exception as e:
                logger.warning("clip_text_batch_encode_failed", error=str(e))

        return [self._mock_embedding(t) for t in texts]

    def _mock_embedding(self, text: str) -> List[float]:
        """Generate a deterministic mock embedding from text hash."""
        import numpy as np
        seed = int(hashlib.md5(text.encode()).hexdigest(), 16) % (2**31)
        rng = np.random.RandomState(seed)
        vec = rng.randn(CLIP_DIM).astype(float)
        vec = vec / (np.linalg.norm(vec) + 1e-8)
        return vec.tolist()
