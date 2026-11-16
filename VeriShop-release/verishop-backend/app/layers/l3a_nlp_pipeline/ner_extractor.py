"""
L3a — Product NER Extractor
Regex-based named entity extraction for product attributes.
No dependency on spacy model being loaded.
"""

import re
from typing import Dict, List, Optional, Any
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ProductNERExtractor:
    """Extracts product entities (brand, model, specs) using regex patterns."""

    # Common brand names for product matching
    KNOWN_BRANDS = [
        "apple", "samsung", "sony", "lg", "dell", "hp", "lenovo", "asus",
        "acer", "microsoft", "google", "amazon", "nike", "adidas", "puma",
        "bose", "jbl", "sennheiser", "logitech", "corsair", "razer",
        "intel", "amd", "nvidia", "canon", "nikon", "gopro", "fitbit",
        "garmin", "philips", "panasonic", "toshiba", "huawei", "xiaomi",
        "oneplus", "oppo", "realme", "vivo", "motorola", "nokia",
        "dyson", "bosch", "whirlpool", "kitchenaid", "instant pot",
    ]

    # Price pattern: $XX.XX or XX.XX USD etc.
    PRICE_RE = re.compile(r"\$\s?(\d+(?:,\d{3})*(?:\.\d{2})?)")

    # Dimensions: 10x20x30, 10" x 20"
    DIMENSION_RE = re.compile(
        r"(\d+(?:\.\d+)?)\s*[\"\'x×X]\s*(\d+(?:\.\d+)?)\s*(?:[\"\'x×X]\s*(\d+(?:\.\d+)?))?",
    )

    # Weight: 5.2 lb, 500g, 2.5 kg
    WEIGHT_RE = re.compile(
        r"(\d+(?:\.\d+)?)\s*(kg|g|lb|lbs|oz|ounces|pounds|grams|kilograms)",
        re.IGNORECASE,
    )

    # Quantity: 2-pack, set of 3
    QUANTITY_RE = re.compile(
        r"(\d+)\s*[-\s]?(pack|piece|set|count|pcs|units|ct)", re.IGNORECASE
    )

    # Model number patterns: XX-XXXX, XXXX123
    MODEL_RE = re.compile(r"\b([A-Z]{1,4}[\-]?\d{2,6}[A-Z]?\d{0,3})\b", re.IGNORECASE)

    def __init__(self):
        self.brand_pattern = re.compile(
            r"\b(" + "|".join(re.escape(b) for b in self.KNOWN_BRANDS) + r")\b",
            re.IGNORECASE,
        )

    def extract(self, text: str) -> Dict[str, Any]:
        """
        Extract product entities from text.
        Returns brand, model, category, attributes, price mentions, quantities.
        """
        return {
            "brand": self._extract_brand(text),
            "model": self._extract_model(text),
            "category": self._infer_category(text),
            "attributes": self._extract_attributes(text),
            "price_mentions": self._extract_prices(text),
            "dimensions": self._extract_dimensions(text),
            "quantities": self._extract_quantities(text),
        }

    def _extract_brand(self, text: str) -> Optional[str]:
        """Extract known brand name from text."""
        match = self.brand_pattern.search(text)
        return match.group(1).title() if match else None

    def _extract_model(self, text: str) -> Optional[str]:
        """Extract model number from text."""
        match = self.MODEL_RE.search(text)
        return match.group(1) if match else None

    def _extract_prices(self, text: str) -> List[float]:
        """Extract price mentions from text."""
        matches = self.PRICE_RE.findall(text)
        prices = []
        for m in matches:
            try:
                prices.append(float(m.replace(",", "")))
            except ValueError:
                continue
        return prices

    def _extract_dimensions(self, text: str) -> List[str]:
        """Extract dimension specifications."""
        matches = self.DIMENSION_RE.findall(text)
        dims = []
        for m in matches:
            if m[2]:
                dims.append(f"{m[0]}x{m[1]}x{m[2]}")
            else:
                dims.append(f"{m[0]}x{m[1]}")
        return dims

    def _extract_quantities(self, text: str) -> List[Dict[str, Any]]:
        """Extract quantity mentions."""
        matches = self.QUANTITY_RE.findall(text)
        return [{"count": int(m[0]), "unit": m[1].lower()} for m in matches]

    def _extract_attributes(self, text: str) -> Dict[str, Any]:
        """Extract product attributes like weight, color."""
        attrs = {}

        # Weight
        weight_match = self.WEIGHT_RE.search(text)
        if weight_match:
            attrs["weight"] = f"{weight_match.group(1)} {weight_match.group(2)}"

        # Color
        colors = ["black", "white", "red", "blue", "green", "silver", "gold",
                  "gray", "grey", "pink", "purple", "orange", "brown", "navy"]
        for color in colors:
            if re.search(rf"\b{color}\b", text, re.IGNORECASE):
                attrs["color"] = color.title()
                break

        return attrs

    def _infer_category(self, text: str) -> Optional[str]:
        """Infer product category from text."""
        category_keywords = {
            "ELECTRONICS": ["laptop", "phone", "tablet", "computer", "headphone",
                           "speaker", "camera", "tv", "monitor", "keyboard", "mouse"],
            "CLOTHING": ["shirt", "pants", "dress", "jacket", "shoes", "sneakers",
                        "boots", "hat", "socks", "clothing", "wear"],
            "HOME": ["furniture", "lamp", "chair", "table", "bed", "sofa",
                    "kitchen", "appliance", "vacuum", "blender"],
            "BEAUTY": ["skincare", "makeup", "perfume", "shampoo", "cream",
                      "serum", "lotion", "beauty"],
            "SPORTS": ["fitness", "gym", "yoga", "running", "bicycle", "sports",
                      "exercise", "workout"],
            "FOOD": ["snack", "coffee", "tea", "food", "organic", "protein",
                    "supplement", "vitamin"],
        }

        text_lower = text.lower()
        for category, keywords in category_keywords.items():
            if any(kw in text_lower for kw in keywords):
                return category

        return "OTHER"
