"""
VeriShop Helpers
Shared utility functions used across all layers.
"""

import uuid
import base64
import time
import re
from io import BytesIO
from functools import wraps
from typing import Generator, List, Any

import numpy as np
import aiohttp
from PIL import Image


def generate_request_id() -> str:
    """Generate a unique request ID."""
    return str(uuid.uuid4())


def cosine_similarity(a, b) -> float:
    """Compute cosine similarity between two vectors."""
    a = np.array(a, dtype=np.float32)
    b = np.array(b, dtype=np.float32)
    a_norm = np.linalg.norm(a)
    b_norm = np.linalg.norm(b)
    if a_norm == 0 or b_norm == 0:
        return 0.0
    return float(np.dot(a, b) / (a_norm * b_norm))


def normalize_text(text: str) -> str:
    """Normalize text: lowercase, strip, collapse whitespace."""
    if not text:
        return ""
    text = text.lower().strip()
    text = re.sub(r"\s+", " ", text)
    return text


def safe_float(value, default: float = 0.0) -> float:
    """Safely convert a value to float."""
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def chunk_list(lst: List[Any], size: int) -> Generator:
    """Split a list into chunks of given size."""
    for i in range(0, len(lst), size):
        yield lst[i : i + size]


def timing_decorator(func):
    """Async decorator that logs execution time."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = await func(*args, **kwargs)
        elapsed_ms = (time.perf_counter() - start) * 1000
        # Use print as a fallback; structured logging is preferred in production
        print(f"[TIMING] {func.__name__} took {elapsed_ms:.2f} ms")
        return result
    return wrapper


async def download_image(url: str, timeout_seconds: int = 10) -> bytes:
    """Download an image from a URL with timeout."""
    timeout = aiohttp.ClientTimeout(total=timeout_seconds)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(url) as response:
            response.raise_for_status()
            return await response.read()


def base64_to_image(b64_string: str) -> Image.Image:
    """Convert a base64 string to a PIL Image."""
    if b64_string.startswith("data:image"):
        b64_string = b64_string.split(",", 1)[1]
    image_data = base64.b64decode(b64_string)
    return Image.open(BytesIO(image_data))


def image_to_base64(image: Image.Image, fmt: str = "PNG") -> str:
    """Convert a PIL Image to a base64 string."""
    buffered = BytesIO()
    image.save(buffered, format=fmt)
    return base64.b64encode(buffered.getvalue()).decode("utf-8")
