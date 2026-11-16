"""
L3a — Text Normalizer
Normalizes and deduplicates text using Jaccard similarity.
"""

import re
import unicodedata
from typing import List, Dict, Any
from app.utils.logger import get_logger

logger = get_logger(__name__)


class TextNormalizer:
    """Normalizes text and removes near-duplicates."""

    # Unit standardization map
    UNIT_MAP = {
        "inches": "in", "inch": "in",
        "pounds": "lb", "pound": "lb", "lbs": "lb",
        "ounces": "oz", "ounce": "oz",
        "kilograms": "kg", "kilogram": "kg",
        "grams": "g", "gram": "g",
        "centimeters": "cm", "centimeter": "cm",
        "millimeters": "mm", "millimeter": "mm",
        "meters": "m", "meter": "m",
        "feet": "ft", "foot": "ft",
        "gigabytes": "GB", "gigabyte": "GB",
        "megabytes": "MB", "megabyte": "MB",
        "terabytes": "TB", "terabyte": "TB",
        "milliamp": "mAh", "milliamps": "mAh",
    }

    def normalize(self, text: str) -> str:
        """Normalize text: lowercase, unicode, units, whitespace."""
        if not text:
            return ""

        # Unicode normalization
        text = unicodedata.normalize("NFKD", text)
        # Lowercase
        text = text.lower()
        # Standardize units
        for full, abbrev in self.UNIT_MAP.items():
            text = re.sub(rf"\b{full}\b", abbrev, text, flags=re.IGNORECASE)
        # Remove excessive punctuation (keep single instances)
        text = re.sub(r"([^\w\s])\1+", r"\1", text)
        # Collapse whitespace
        text = re.sub(r"\s+", " ", text).strip()

        return text

    def deduplicate_texts(self, texts: List[str], threshold: float = 0.85) -> List[str]:
        """Remove near-duplicate texts using Jaccard similarity."""
        if len(texts) <= 1:
            return texts

        unique = [texts[0]]
        for text in texts[1:]:
            is_dup = False
            tokens_new = set(text.lower().split())
            for existing in unique:
                tokens_existing = set(existing.lower().split())
                similarity = self._jaccard(tokens_new, tokens_existing)
                if similarity >= threshold:
                    is_dup = True
                    break
            if not is_dup:
                unique.append(text)

        return unique

    def standardize_product_fields(self, fields: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize brand names, model numbers, categories."""
        result = {}
        for key, value in fields.items():
            if isinstance(value, str):
                result[key] = self.normalize(value)
            else:
                result[key] = value
        return result

    @staticmethod
    def _jaccard(set1: set, set2: set) -> float:
        """Compute Jaccard similarity between two sets."""
        if not set1 and not set2:
            return 1.0
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        return intersection / union if union > 0 else 0.0
