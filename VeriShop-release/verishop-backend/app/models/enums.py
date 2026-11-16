"""
VeriShop Enumerations
Defines all enum types used across the system.
"""

from enum import Enum


class QueryType(str, Enum):
    """Type of search query."""
    TEXT = "TEXT"
    IMAGE = "IMAGE"
    MULTIMODAL = "MULTIMODAL"


class TrustVerdict(str, Enum):
    """Trust verdict with visual symbols."""
    TRUSTED = "TRUSTED"        # ✓
    CAUTION = "CAUTION"        # ⚠
    UNTRUSTED = "UNTRUSTED"    # ✗

    @property
    def symbol(self) -> str:
        symbols = {
            "TRUSTED": "✓",
            "CAUTION": "⚠",
            "UNTRUSTED": "✗",
        }
        return symbols[self.value]


class RiskLevel(str, Enum):
    """Risk level classification."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ProductCategory(str, Enum):
    """Product category classification."""
    ELECTRONICS = "ELECTRONICS"
    CLOTHING = "CLOTHING"
    HOME = "HOME"
    BEAUTY = "BEAUTY"
    SPORTS = "SPORTS"
    FOOD = "FOOD"
    OTHER = "OTHER"


class ReviewSentiment(str, Enum):
    """Review sentiment classification."""
    POSITIVE = "POSITIVE"
    NEUTRAL = "NEUTRAL"
    NEGATIVE = "NEGATIVE"


class ManipulationType(str, Enum):
    """Types of image manipulation detected."""
    NONE = "NONE"
    METADATA_TAMPERING = "METADATA_TAMPERING"
    IMAGE_SPLICING = "IMAGE_SPLICING"
    COPY_MOVE = "COPY_MOVE"
    ENHANCEMENT = "ENHANCEMENT"
