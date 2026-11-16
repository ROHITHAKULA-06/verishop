"""
L3b — Vision Pipeline Orchestrator
Orchestrates CLIP image encoding, structural analysis, and semantic comparison.
"""

import time
from typing import Dict, Any, Optional
from PIL import Image

from app.layers.l3b_vision_pipeline.clip_image import CLIPImageEncoder
from app.layers.l3b_vision_pipeline.structural_analyzer import StructuralAnalyzer
from app.layers.l3b_vision_pipeline.semantic_comparator import SemanticComparator
from app.layers.l3b_vision_pipeline.manipulation_detector import ManipulationDetector
from app.models.trust import ImageConsistency
from app.models.enums import ManipulationType
from app.utils.logger import get_logger

logger = get_logger(__name__)


class VisionPipeline:
    """Orchestrates the full vision analysis pipeline."""

    def __init__(self, settings=None, model_manager=None):
        self.settings = settings
        model_name = "openai/clip-vit-base-patch32"
        if settings:
            model_name = getattr(settings, "CLIP_MODEL_NAME", model_name)

        self.clip_encoder = CLIPImageEncoder(model_name=model_name)
        self.structural_analyzer = StructuralAnalyzer()
        self.semantic_comparator = SemanticComparator(clip_encoder=self.clip_encoder)
        self.manipulation_detector = ManipulationDetector()

    async def process(self, processed_image: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the full vision pipeline.
        Input: processed image dict from L2 ImageProcessor
        Output: embeddings, structural features, etc.
        """
        steps = []
        image = processed_image.get("image")

        if image is None:
            return {
                "image_embedding": [],
                "structural_features": {},
                "semantic_features": {},
                "manipulation_results": {},
                "processing_steps": [],
            }

        # Step 1: CLIP image embedding
        t0 = time.perf_counter()
        image_embedding = self.clip_encoder.encode(image)
        steps.append({"step": "clip_image_encoding", "time_ms": (time.perf_counter() - t0) * 1000})

        # Step 2: Structural analysis
        t0 = time.perf_counter()
        structural_features = self.structural_analyzer.analyze(image)
        steps.append({"step": "structural_analysis", "time_ms": (time.perf_counter() - t0) * 1000})

        # Step 3: Manipulation detection
        t0 = time.perf_counter()
        manipulation_results = self.manipulation_detector.detect(image)
        steps.append({"step": "manipulation_detection", "time_ms": (time.perf_counter() - t0) * 1000})

        return {
            "image_embedding": image_embedding,
            "structural_features": structural_features,
            "semantic_features": {},
            "manipulation_results": manipulation_results,
            "processing_steps": steps,
        }

    async def analyze_pair(self, image1: Image.Image, image2: Image.Image) -> ImageConsistency:
        """Compare two images for consistency."""
        comparison = self.semantic_comparator.compare(image1, image2)
        manipulation = self.manipulation_detector.detect(image1)

        return ImageConsistency(
            similarity_score=comparison.get("similarity_score", 0.0),
            manipulation_detected=manipulation.get("is_manipulated", False),
            manipulation_type=ManipulationType(manipulation.get("manipulation_type", "NONE")),
            evidence=manipulation.get("evidence", []),
        )
