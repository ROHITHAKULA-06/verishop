"""
L3b — Semantic Comparator
Compares images semantically using embeddings and structural features.
"""

from typing import Dict, Any, List, Optional
from PIL import Image
import numpy as np
from app.utils.logger import get_logger

logger = get_logger(__name__)


class SemanticComparator:
    """Compares images semantically for similarity and text-image relevance."""

    def __init__(self, clip_encoder=None):
        self.clip_encoder = clip_encoder

    def compare(self, image1: Image.Image, image2: Image.Image) -> Dict[str, Any]:
        """Compare two images for similarity."""
        # Embedding similarity
        similarity_score = 0.5
        if self.clip_encoder:
            emb1 = np.array(self.clip_encoder.encode(image1))
            emb2 = np.array(self.clip_encoder.encode(image2))
            norm1, norm2 = np.linalg.norm(emb1), np.linalg.norm(emb2)
            if norm1 > 0 and norm2 > 0:
                similarity_score = float(np.dot(emb1, emb2) / (norm1 * norm2))

        # Structural similarity (histogram comparison)
        structural_sim = self._histogram_similarity(image1, image2)

        # Color similarity
        color_sim = self._color_similarity(image1, image2)

        content_match = similarity_score > 0.8 and structural_sim > 0.7

        return {
            "similarity_score": round(similarity_score, 4),
            "structural_similarity": round(structural_sim, 4),
            "color_similarity": round(color_sim, 4),
            "content_match": content_match,
        }

    def compare_with_text(self, image: Image.Image, text: str) -> Dict[str, Any]:
        """Compare an image with text description."""
        relevance_score = 0.5
        if self.clip_encoder:
            relevance_score = self.clip_encoder.text_image_similarity(text, image)

        description_match = relevance_score > 0.25
        evidence = []
        if description_match:
            evidence.append(f"Image-text relevance score: {relevance_score:.2f} (match)")
        else:
            evidence.append(f"Image-text relevance score: {relevance_score:.2f} (low match)")

        return {
            "relevance_score": round(relevance_score, 4),
            "description_match": description_match,
            "evidence": evidence,
        }

    def _histogram_similarity(self, img1: Image.Image, img2: Image.Image) -> float:
        """Compare histograms of two images."""
        hist1 = np.array(img1.convert("RGB").resize((64, 64)).histogram(), dtype=float)
        hist2 = np.array(img2.convert("RGB").resize((64, 64)).histogram(), dtype=float)

        # Normalize
        hist1 = hist1 / (hist1.sum() + 1e-8)
        hist2 = hist2 / (hist2.sum() + 1e-8)

        # Bhattacharyya coefficient
        return float(np.sum(np.sqrt(hist1 * hist2)))

    def _color_similarity(self, img1: Image.Image, img2: Image.Image) -> float:
        """Compare average colors of two images."""
        avg1 = np.mean(np.array(img1.convert("RGB").resize((32, 32))), axis=(0, 1))
        avg2 = np.mean(np.array(img2.convert("RGB").resize((32, 32))), axis=(0, 1))

        # Euclidean distance normalized to 0-1
        dist = np.linalg.norm(avg1 - avg2) / (255.0 * np.sqrt(3))
        return round(1.0 - dist, 4)
