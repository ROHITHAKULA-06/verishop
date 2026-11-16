"""
L6 — Vector Store
FAISS-based vector similarity search with ID mapping.
"""

import os
import json
from typing import List, Tuple, Optional
import numpy as np
from app.utils.logger import get_logger

logger = get_logger(__name__)


class VectorStore:
    """FAISS-based vector store for embedding similarity search."""

    def __init__(self, dimension: int = 512, index_path: str = "./data/faiss_index"):
        self.dimension = dimension
        self.index_path = index_path
        self.id_map_path = f"{index_path}_ids.json"
        self._index = None
        self._id_map: List[str] = []
        os.makedirs(os.path.dirname(index_path) or ".", exist_ok=True)
        self._init_index()

    def _init_index(self):
        """Create or load FAISS index."""
        try:
            import faiss
            if os.path.exists(self.index_path):
                self._index = faiss.read_index(self.index_path)
                if os.path.exists(self.id_map_path):
                    with open(self.id_map_path, "r") as f:
                        self._id_map = json.load(f)
                logger.info("faiss_index_loaded", count=self._index.ntotal)
            else:
                self._index = faiss.IndexFlatL2(self.dimension)
                logger.info("faiss_index_created", dimension=self.dimension)
        except ImportError:
            logger.warning("faiss_not_available", msg="Using in-memory fallback")
            self._index = None
            self._vectors: List[np.ndarray] = []

    def add(self, embeddings: List[List[float]], ids: List[str]) -> None:
        """Add vectors with IDs."""
        if not embeddings or not ids:
            return

        vectors = np.array(embeddings, dtype=np.float32)

        if self._index is not None:
            self._index.add(vectors)
        else:
            self._vectors.extend([v for v in vectors])

        self._id_map.extend(ids)
        logger.info("vectors_added", count=len(ids))

    def search(self, query_embedding: List[float], top_k: int = 10) -> List[Tuple[str, float]]:
        """Search for similar vectors. Returns (id, distance) pairs."""
        query = np.array([query_embedding], dtype=np.float32)

        if self._index is not None and self._index.ntotal > 0:
            k = min(top_k, self._index.ntotal)
            distances, indices = self._index.search(query, k)

            results = []
            for dist, idx in zip(distances[0], indices[0]):
                if 0 <= idx < len(self._id_map):
                    results.append((self._id_map[idx], float(dist)))
            return results

        elif hasattr(self, "_vectors") and self._vectors:
            # Fallback: brute force search
            vectors = np.array(self._vectors, dtype=np.float32)
            distances = np.linalg.norm(vectors - query, axis=1)
            top_indices = np.argsort(distances)[:top_k]

            results = []
            for idx in top_indices:
                if idx < len(self._id_map):
                    results.append((self._id_map[idx], float(distances[idx])))
            return results

        return []

    def remove(self, ids: List[str]) -> None:
        """Remove vectors by IDs (rebuilds index)."""
        indices_to_keep = [i for i, id_ in enumerate(self._id_map) if id_ not in ids]

        if not indices_to_keep:
            self._id_map = []
            if self._index is not None:
                import faiss
                self._index = faiss.IndexFlatL2(self.dimension)
            else:
                self._vectors = []
            return

        # Rebuild with remaining vectors
        new_ids = [self._id_map[i] for i in indices_to_keep]

        if self._index is not None:
            import faiss
            # Extract and rebuild
            all_vectors = np.array([self._index.reconstruct(i) for i in indices_to_keep])
            self._index = faiss.IndexFlatL2(self.dimension)
            self._index.add(all_vectors)
        elif hasattr(self, "_vectors"):
            self._vectors = [self._vectors[i] for i in indices_to_keep]

        self._id_map = new_ids

    def save(self) -> None:
        """Persist index to disk."""
        if self._index is not None:
            import faiss
            faiss.write_index(self._index, self.index_path)

        with open(self.id_map_path, "w") as f:
            json.dump(self._id_map, f)

        logger.info("vector_store_saved", count=len(self._id_map))

    def load(self) -> None:
        """Load index from disk."""
        self._init_index()

    def count(self) -> int:
        """Number of vectors in index."""
        if self._index is not None:
            return self._index.ntotal
        elif hasattr(self, "_vectors"):
            return len(self._vectors)
        return 0
