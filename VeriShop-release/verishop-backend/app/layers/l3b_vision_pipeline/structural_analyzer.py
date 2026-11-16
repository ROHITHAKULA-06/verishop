"""
L3b — Structural Analyzer
Analyzes image structural properties: edges, colors, sharpness, brightness.
"""

from typing import Dict, Any, List, Tuple
from PIL import Image, ImageStat, ImageFilter
import numpy as np
from app.utils.logger import get_logger

logger = get_logger(__name__)


class StructuralAnalyzer:
    """Analyzes structural properties of product images."""

    def analyze(self, image: Image.Image) -> Dict[str, Any]:
        """Full structural analysis of an image."""
        img_array = np.array(image.convert("RGB"))
        w, h = image.size

        return {
            "width": w,
            "height": h,
            "aspect_ratio": round(w / h, 2) if h > 0 else 0,
            "dominant_colors": self._compute_dominant_colors(image),
            "brightness": self._compute_brightness(image),
            "contrast": self._compute_contrast(image),
            "sharpness": self._estimate_sharpness(img_array),
            "has_text_overlay": self._detect_text_overlay(img_array),
            "edge_density": self._compute_edge_density(img_array),
            "texture_uniformity": self._compute_texture_uniformity(img_array),
        }

    def _compute_edge_density(self, image_array: np.ndarray) -> float:
        """Compute edge density using gradient magnitude."""
        gray = np.mean(image_array, axis=2) if image_array.ndim == 3 else image_array
        # Sobel-like gradient
        gx = np.diff(gray, axis=1)
        gy = np.diff(gray, axis=0)
        min_h = min(gx.shape[0], gy.shape[0])
        min_w = min(gx.shape[1], gy.shape[1])
        magnitude = np.sqrt(gx[:min_h, :min_w] ** 2 + gy[:min_h, :min_w] ** 2)
        # Normalize to 0-1
        density = float(np.mean(magnitude > 30))
        return round(density, 4)

    def _compute_dominant_colors(self, image: Image.Image, n: int = 5) -> List[Tuple[int, ...]]:
        """Extract dominant colors by quantization."""
        small = image.copy()
        small.thumbnail((64, 64))
        # Quantize to n colors
        quantized = small.quantize(colors=n, method=Image.Quantize.MEDIANCUT)
        palette = quantized.getpalette()
        if not palette:
            return []
        colors = []
        for i in range(min(n, len(palette) // 3)):
            r, g, b = palette[i * 3:(i + 1) * 3]
            colors.append((r, g, b))
        return colors

    def _compute_brightness(self, image: Image.Image) -> float:
        """Compute average brightness (0-255)."""
        gray = image.convert("L")
        stat = ImageStat.Stat(gray)
        return round(stat.mean[0], 2)

    def _compute_contrast(self, image: Image.Image) -> float:
        """Compute contrast as standard deviation of pixel values."""
        gray = image.convert("L")
        stat = ImageStat.Stat(gray)
        return round(stat.stddev[0], 2)

    def _estimate_sharpness(self, image_array: np.ndarray) -> float:
        """Estimate sharpness via Laplacian variance."""
        gray = np.mean(image_array, axis=2) if image_array.ndim == 3 else image_array
        # Laplacian kernel approximation
        h, w = gray.shape
        if h < 3 or w < 3:
            return 0.0
        laplacian = (
            gray[:-2, 1:-1] + gray[2:, 1:-1] + gray[1:-1, :-2] + gray[1:-1, 2:]
            - 4 * gray[1:-1, 1:-1]
        )
        variance = float(np.var(laplacian))
        # Normalize (typical range 0-1000+)
        return round(min(variance / 500.0, 1.0), 4)

    def _detect_text_overlay(self, image_array: np.ndarray) -> bool:
        """Simple heuristic to detect text overlays (high-contrast edges)."""
        edge_density = self._compute_edge_density(image_array)
        # High edge density in small regions could indicate text
        return edge_density > 0.15

    def _compute_texture_uniformity(self, image_array: np.ndarray) -> float:
        """Compute texture uniformity (low variance = uniform)."""
        gray = np.mean(image_array, axis=2) if image_array.ndim == 3 else image_array
        # Divide into 4x4 grid and check variance across blocks
        h, w = gray.shape
        bh, bw = h // 4, w // 4
        if bh == 0 or bw == 0:
            return 1.0

        block_vars = []
        for i in range(4):
            for j in range(4):
                block = gray[i * bh:(i + 1) * bh, j * bw:(j + 1) * bw]
                block_vars.append(np.var(block))

        # Low variance across blocks = high uniformity
        overall_var = np.var(block_vars)
        uniformity = 1.0 / (1.0 + overall_var / 1000.0)
        return round(uniformity, 4)
