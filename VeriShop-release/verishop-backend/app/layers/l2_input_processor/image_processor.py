"""
L2 — Image Processor
Validates, resizes, and extracts metadata from product images.
"""

import base64
from io import BytesIO
from typing import Dict, Any, Union

from PIL import Image, ExifTags
from app.utils.logger import get_logger

logger = get_logger(__name__)

MIN_SIZE = 50
MAX_SIZE = 4096
PROCESSING_SIZE = 512


class ImageProcessor:
    """Processes product images for downstream analysis."""

    def process(self, image_data: Union[bytes, str]) -> Dict[str, Any]:
        """
        Accept base64, URL reference, or raw bytes.
        Returns processed image with metadata and thumbnail.
        """
        image = self._load_image(image_data)
        self._validate(image)

        metadata = self._extract_metadata(image)
        thumbnail = self._create_thumbnail(image)
        processed = self._resize_for_processing(image)

        return {
            "image": processed,
            "original_image": image,
            "metadata": metadata,
            "thumbnail": thumbnail,
        }

    def _load_image(self, image_data: Union[bytes, str]) -> Image.Image:
        """Load image from various input formats."""
        if isinstance(image_data, str):
            # Base64 encoded
            if image_data.startswith("data:image"):
                image_data = image_data.split(",", 1)[1]
            raw = base64.b64decode(image_data)
            return Image.open(BytesIO(raw)).convert("RGB")
        elif isinstance(image_data, bytes):
            return Image.open(BytesIO(image_data)).convert("RGB")
        elif isinstance(image_data, Image.Image):
            return image_data.convert("RGB")
        else:
            raise ValueError(f"Unsupported image input type: {type(image_data)}")

    def _validate(self, image: Image.Image) -> None:
        """Validate image dimensions."""
        w, h = image.size
        if w < MIN_SIZE or h < MIN_SIZE:
            raise ValueError(f"Image too small: {w}x{h} (min {MIN_SIZE}x{MIN_SIZE})")
        if w > MAX_SIZE or h > MAX_SIZE:
            raise ValueError(f"Image too large: {w}x{h} (max {MAX_SIZE}x{MAX_SIZE})")

    def _extract_metadata(self, image: Image.Image) -> Dict[str, Any]:
        """Extract image metadata including EXIF data."""
        w, h = image.size
        meta = {
            "width": w,
            "height": h,
            "format": image.format or "unknown",
            "mode": image.mode,
            "size_bytes": self._estimate_size(image),
        }

        # Extract EXIF if available
        try:
            exif_data = image.getexif()
            if exif_data:
                exif_dict = {}
                for tag_id, value in exif_data.items():
                    tag = ExifTags.TAGS.get(tag_id, tag_id)
                    if isinstance(value, (str, int, float)):
                        exif_dict[str(tag)] = value
                meta["exif"] = exif_dict
        except Exception:
            meta["exif"] = {}

        return meta

    def _create_thumbnail(self, image: Image.Image) -> Image.Image:
        """Create a 128x128 thumbnail."""
        thumb = image.copy()
        thumb.thumbnail((128, 128))
        return thumb

    def _resize_for_processing(self, image: Image.Image) -> Image.Image:
        """Resize to max PROCESSING_SIZE while maintaining aspect ratio."""
        w, h = image.size
        if max(w, h) <= PROCESSING_SIZE:
            return image.copy()

        if w > h:
            new_w = PROCESSING_SIZE
            new_h = int(h * PROCESSING_SIZE / w)
        else:
            new_h = PROCESSING_SIZE
            new_w = int(w * PROCESSING_SIZE / h)

        return image.resize((new_w, new_h), Image.LANCZOS)

    @staticmethod
    def _estimate_size(image: Image.Image) -> int:
        """Estimate image size in bytes."""
        buf = BytesIO()
        image.save(buf, format="PNG")
        return buf.tell()
