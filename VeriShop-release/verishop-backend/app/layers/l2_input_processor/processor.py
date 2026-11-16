"""
L2 — Multimodal Input Processor
Dispatches input to text and image processors, determines query type.
"""

from typing import Optional, Dict, Any
from app.models.enums import QueryType
from app.layers.l2_input_processor.image_processor import ImageProcessor
from app.layers.l2_input_processor.text_processor import TextProcessor
from app.utils.logger import get_logger

logger = get_logger(__name__)


class MultimodalInputProcessor:
    """Processes multimodal input (text, image, or both)."""

    def __init__(self, settings=None):
        self.settings = settings
        self.image_processor = ImageProcessor()
        self.text_processor = TextProcessor()

    async def process(
        self, query: Optional[str] = None, image_data: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Process multimodal input and determine query type.
        Returns processed text and/or image data with metadata.
        """
        processed_text = None
        processed_image = None
        query_type = QueryType.TEXT

        # Process text
        if query and query.strip():
            processed_text = self.text_processor.process(query)
            query_type = QueryType.TEXT

        # Process image
        if image_data:
            try:
                processed_image = self.image_processor.process(image_data)
                query_type = QueryType.IMAGE
            except Exception as e:
                logger.warning("image_processing_failed", error=str(e))

        # Both present = multimodal
        if processed_text and processed_image:
            query_type = QueryType.MULTIMODAL

        return {
            "query_type": query_type,
            "processed_text": processed_text,
            "processed_image": processed_image,
            "raw_query": query,
            "raw_image": image_data is not None,
        }
