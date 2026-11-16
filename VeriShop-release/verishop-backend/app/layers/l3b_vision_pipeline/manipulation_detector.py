"""
L3b — Manipulation Detector
Detects image manipulation via ELA, metadata analysis, and copy-move detection.
"""

from typing import Dict, Any, List
from io import BytesIO
from PIL import Image
import numpy as np
from app.models.enums import ManipulationType
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ManipulationDetector:
    """Detects image manipulation and tampering."""

    def detect(self, image: Image.Image) -> Dict[str, Any]:
        """
        Run all manipulation detection checks.
        Returns detection results with evidence.
        """
        evidence = []

        # Error Level Analysis
        ela_score = self._error_level_analysis(image)
        if ela_score > 0.3:
            evidence.append(f"ELA score {ela_score:.2f} indicates possible editing")

        # Metadata consistency
        meta_result = self._check_metadata_consistency(image)
        evidence.extend(meta_result.get("issues", []))

        # Copy-move detection
        img_array = np.array(image.convert("RGB"))
        copy_move = self._detect_copy_move(img_array)
        if copy_move:
            evidence.append("Possible copy-move regions detected")

        # Determine manipulation type
        is_manipulated = ela_score > 0.4 or copy_move or len(meta_result.get("issues", [])) > 0
        manipulation_type = ManipulationType.NONE

        if is_manipulated:
            if copy_move:
                manipulation_type = ManipulationType.COPY_MOVE
            elif ela_score > 0.4:
                manipulation_type = ManipulationType.IMAGE_SPLICING
            elif meta_result.get("software_edited"):
                manipulation_type = ManipulationType.ENHANCEMENT

        confidence = min(ela_score + (0.2 if copy_move else 0) + (0.1 if meta_result.get("software_edited") else 0), 1.0)

        return {
            "is_manipulated": is_manipulated,
            "manipulation_type": manipulation_type.value,
            "confidence": round(confidence, 4),
            "evidence": evidence,
            "ela_score": round(ela_score, 4),
        }

    def _error_level_analysis(self, image: Image.Image, quality: int = 90) -> float:
        """
        Error Level Analysis: resave at lower quality and compare.
        High difference suggests manipulation.
        """
        try:
            original = image.convert("RGB")
            # Resave at lower quality
            buffer = BytesIO()
            original.save(buffer, format="JPEG", quality=quality)
            buffer.seek(0)
            resaved = Image.open(buffer).convert("RGB")

            # Compare pixel differences
            orig_arr = np.array(original, dtype=np.float32)
            resaved_arr = np.array(resaved, dtype=np.float32)

            diff = np.abs(orig_arr - resaved_arr)
            mean_diff = np.mean(diff)

            # Normalize to 0-1 range (typical values 0-30)
            ela_score = min(mean_diff / 30.0, 1.0)
            return ela_score
        except Exception as e:
            logger.warning("ela_failed", error=str(e))
            return 0.0

    def _check_metadata_consistency(self, image: Image.Image) -> Dict[str, Any]:
        """Check EXIF metadata for signs of editing."""
        result = {"issues": [], "software_edited": False}

        try:
            exif = image.getexif()
            if not exif:
                result["issues"].append("No EXIF metadata found (may have been stripped)")
                return result

            # Check for editing software tags
            software_tags = [305, 0x0131]  # Software tag
            for tag in software_tags:
                if tag in exif:
                    software = str(exif[tag])
                    editing_tools = ["photoshop", "gimp", "lightroom", "snapseed", "pixlr", "canva"]
                    if any(tool in software.lower() for tool in editing_tools):
                        result["software_edited"] = True
                        result["issues"].append(f"Edited with: {software}")

        except Exception:
            pass

        return result

    def _detect_copy_move(self, image_array: np.ndarray) -> bool:
        """Simple block-matching for copy-move detection."""
        try:
            gray = np.mean(image_array, axis=2) if image_array.ndim == 3 else image_array
            h, w = gray.shape

            if h < 32 or w < 32:
                return False

            block_size = 16
            blocks = {}
            threshold = 5.0  # Max mean absolute difference to consider a match

            for y in range(0, h - block_size, block_size // 2):
                for x in range(0, w - block_size, block_size // 2):
                    block = gray[y:y + block_size, x:x + block_size]
                    block_hash = hash(block.tobytes())

                    if block_hash in blocks:
                        prev_y, prev_x = blocks[block_hash]
                        # Ensure blocks are not adjacent
                        if abs(y - prev_y) > block_size * 2 or abs(x - prev_x) > block_size * 2:
                            return True
                    else:
                        blocks[block_hash] = (y, x)

            return False
        except Exception:
            return False
