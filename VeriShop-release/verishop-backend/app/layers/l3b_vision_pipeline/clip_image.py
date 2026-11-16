"""
L3b — CLIP Image Encoder
Generates CLIP image embeddings for visual similarity and cross-modal matching.
"""

import hashlib
from typing import List
from PIL import Image
from app.utils.logger import get_logger

logger = get_logger(__name__)

CLIP_DIM = 512


class CLIPImageEncoder:
    """CLIP image encoder with lazy loading and mock fallback."""

    def __init__(self, model_name: str = "openai/clip-vit-base-patch32"):
        self.model_name = model_name
        self._model = None
        self._processor = None
        self._loaded = False

    def _load_model(self):
        """Lazy-load CLIP model."""
        if self._loaded:
            return
        try:
            from transformers import CLIPModel, CLIPProcessor
            self._model = CLIPModel.from_pretrained(self.model_name)
            self._processor = CLIPProcessor.from_pretrained(self.model_name)
            self._loaded = True
            logger.info("clip_image_model_loaded", model=self.model_name)
        except Exception as e:
            logger.warning("clip_image_model_unavailable", error=str(e))
            self._loaded = False

    def encode(self, image: Image.Image) -> List[float]:
        """Generate CLIP image embedding (512-dim). Falls back to mock."""
        self._load_model()

        if self._model is not None and self._processor is not None:
            try:
                import torch
                inputs = self._processor(images=image, return_tensors="pt")
                with torch.no_grad():
                    outputs = self._model.get_image_features(**inputs)
                return outputs[0].cpu().numpy().tolist()
            except Exception as e:
                logger.warning("clip_image_encode_failed", error=str(e))

        return self._mock_embedding(image)

    def encode_batch(self, images: List[Image.Image]) -> List[List[float]]:
        """Encode a batch of images."""
        self._load_model()

        if self._model is not None and self._processor is not None:
            try:
                import torch
                inputs = self._processor(images=images, return_tensors="pt")
                with torch.no_grad():
                    outputs = self._model.get_image_features(**inputs)
                return outputs.cpu().numpy().tolist()
            except Exception as e:
                logger.warning("clip_image_batch_encode_failed", error=str(e))

        return [self._mock_embedding(img) for img in images]

    def text_image_similarity(self, text: str, image: Image.Image) -> float:
        """Compute CLIP cross-modal similarity between text and image."""
        self._load_model()

        if self._model is not None and self._processor is not None:
            try:
                import torch
                inputs = self._processor(text=[text], images=image, return_tensors="pt", padding=True)
                with torch.no_grad():
                    outputs = self._model(**inputs)
                logits = outputs.logits_per_image
                return float(logits[0][0].cpu().item()) / 100.0
            except Exception as e:
                logger.warning("clip_text_image_similarity_failed", error=str(e))

        return 0.5  # Neutral fallback

    def _mock_embedding(self, image: Image.Image) -> List[float]:
        """Generate a deterministic mock embedding from image content."""
        import numpy as np
        # Use image size + mode as seed
        seed_str = f"{image.size}_{image.mode}"
        seed = int(hashlib.md5(seed_str.encode()).hexdigest(), 16) % (2**31)
        rng = np.random.RandomState(seed)
        vec = rng.randn(CLIP_DIM).astype(float)
        vec = vec / (np.linalg.norm(vec) + 1e-8)
        return vec.tolist()
