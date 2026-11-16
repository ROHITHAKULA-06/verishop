"""
L2 — Text Processor
Cleans, normalizes, and tokenizes text queries.
"""

import re
from typing import Dict, Any

from app.utils.logger import get_logger

logger = get_logger(__name__)


class TextProcessor:
    """Processes and cleans text queries for downstream NLP."""

    # HTML tag pattern
    HTML_TAG_RE = re.compile(r"<[^>]+>")
    # Multiple whitespace
    WHITESPACE_RE = re.compile(r"\s+")
    # Non-product characters (keep alphanumeric, spaces, hyphens, dots, $, #)
    SPECIAL_CHAR_RE = re.compile(r"[^\w\s\-\.\$\#\,\/\(\)]", re.UNICODE)

    def process(self, query: str) -> Dict[str, Any]:
        """
        Clean and normalize text query.
        Returns processed text with tokens and metadata.
        """
        if not query or not query.strip():
            return {
                "cleaned_text": "",
                "tokens": [],
                "language": "en",
                "char_count": 0,
                "word_count": 0,
            }

        cleaned = self._clean_text(query)
        tokens = self._tokenize(cleaned)

        return {
            "cleaned_text": cleaned,
            "tokens": tokens,
            "language": self._detect_language(cleaned),
            "char_count": len(cleaned),
            "word_count": len(tokens),
        }

    def _clean_text(self, text: str) -> str:
        """Remove HTML tags, excessive whitespace, and unwanted characters."""
        # Remove HTML tags
        text = self.HTML_TAG_RE.sub(" ", text)
        # Remove special characters (keep product-relevant ones)
        text = self.SPECIAL_CHAR_RE.sub(" ", text)
        # Collapse whitespace
        text = self.WHITESPACE_RE.sub(" ", text)
        return text.strip()

    def _tokenize(self, text: str) -> list:
        """Simple whitespace tokenizer."""
        return [t for t in text.lower().split() if len(t) > 0]

    def _detect_language(self, text: str) -> str:
        """Basic language detection (defaults to English)."""
        # Simple heuristic: check for common non-English characters
        if re.search(r"[\u4e00-\u9fff]", text):
            return "zh"
        if re.search(r"[\u3040-\u309f\u30a0-\u30ff]", text):
            return "ja"
        if re.search(r"[\u0900-\u097f]", text):
            return "hi"
        return "en"
