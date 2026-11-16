"""
L3a — Query Expansion
Generates expanded query variants via synonym injection and attribute extraction.
"""

from typing import List, Dict, Optional
from app.utils.logger import get_logger

logger = get_logger(__name__)


class QueryExpander:
    """Expands search queries with synonyms, hyponyms, and variants."""

    # Common product term synonyms
    SYNONYM_MAP = {
        "headphones": ["earphones", "earbuds", "headset", "audio"],
        "laptop": ["notebook", "computer", "ultrabook"],
        "phone": ["smartphone", "mobile", "cellphone", "handset"],
        "tv": ["television", "display", "monitor", "screen"],
        "shoes": ["sneakers", "footwear", "boots", "trainers"],
        "watch": ["smartwatch", "timepiece", "wearable"],
        "camera": ["dslr", "mirrorless", "webcam", "camcorder"],
        "tablet": ["ipad", "e-reader", "slate"],
        "speaker": ["bluetooth speaker", "soundbar", "audio speaker"],
        "keyboard": ["mechanical keyboard", "wireless keyboard"],
        "mouse": ["gaming mouse", "wireless mouse", "trackpad"],
        "charger": ["adapter", "power supply", "charging cable"],
        "case": ["cover", "sleeve", "protector", "shell"],
        "cheap": ["affordable", "budget", "low-cost", "inexpensive"],
        "best": ["top-rated", "highest-rated", "premium", "top"],
        "wireless": ["bluetooth", "cordless", "wifi"],
        "gaming": ["gamer", "esports", "game"],
    }

    def __init__(self):
        pass

    def expand(self, query: str, entities: Optional[Dict] = None) -> List[str]:
        """
        Generate expanded queries from the original.
        Returns original + 3-5 expanded variants.
        """
        variants = [query]

        # Synonym injection
        synonym_variants = self._inject_synonyms(query)
        variants.extend(synonym_variants)

        # Brand-model split
        if entities:
            brand = entities.get("brand")
            model = entities.get("model")
            if brand and model:
                variants.append(f"{brand} {model}")
            if brand:
                variants.append(f"{brand} {query}")

        # Attribute-based variants
        attr_variants = self._generate_variants(query)
        variants.extend(attr_variants)

        # Deduplicate while preserving order
        seen = set()
        unique = []
        for v in variants:
            v_lower = v.lower().strip()
            if v_lower and v_lower not in seen:
                seen.add(v_lower)
                unique.append(v)

        # Cap at original + 5 variants
        return unique[:6]

    def _inject_synonyms(self, query: str) -> List[str]:
        """Replace words with synonyms to create variants."""
        variants = []
        words = query.lower().split()

        for i, word in enumerate(words):
            synonyms = self._get_synonyms(word)
            for syn in synonyms[:2]:  # Max 2 synonyms per word
                new_words = words.copy()
                new_words[i] = syn
                variants.append(" ".join(new_words))

        return variants

    def _get_synonyms(self, word: str) -> List[str]:
        """Look up synonyms for a word."""
        return self.SYNONYM_MAP.get(word.lower(), [])

    def _generate_variants(self, query: str) -> List[str]:
        """Generate query variants using common patterns."""
        variants = []
        q = query.lower().strip()

        # Add "buy" prefix for product queries
        if not q.startswith("buy"):
            variants.append(f"buy {q}")

        # Add "review" suffix
        if "review" not in q:
            variants.append(f"{q} review")

        return variants
