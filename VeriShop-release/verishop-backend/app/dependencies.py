"""
VeriShop Dependency Injection
Singleton model manager and shared resource providers.
"""

from typing import Any, Optional


class ModelManager:
    """
    Singleton model manager — lazy-loads CLIP and SBERT models.
    Gracefully degrades if models are unavailable.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._clip_model = None
            cls._instance._clip_processor = None
            cls._instance._sbert_model = None
            cls._instance._initialized = False
        return cls._instance

    def get_clip_model(self) -> Any:
        """Get CLIP model, lazy-loading on first access."""
        if self._clip_model is None:
            try:
                from transformers import CLIPModel, CLIPProcessor
                from app.config import settings
                self._clip_model = CLIPModel.from_pretrained(settings.CLIP_MODEL_NAME)
                self._clip_processor = CLIPProcessor.from_pretrained(settings.CLIP_MODEL_NAME)
            except Exception:
                self._clip_model = None
                self._clip_processor = None
        return self._clip_model

    def get_clip_processor(self) -> Any:
        """Get CLIP processor."""
        if self._clip_processor is None:
            self.get_clip_model()
        return self._clip_processor

    def get_sbert_model(self) -> Any:
        """Get SBERT model, lazy-loading on first access."""
        if self._sbert_model is None:
            try:
                from sentence_transformers import SentenceTransformer
                from app.config import settings
                self._sbert_model = SentenceTransformer(settings.SBERT_MODEL_NAME)
            except Exception:
                self._sbert_model = None
        return self._sbert_model

    def is_loaded(self, model_name: str) -> bool:
        """Check if a model is currently loaded."""
        if model_name.lower() == "clip":
            return self._clip_model is not None
        elif model_name.lower() == "sbert":
            return self._sbert_model is not None
        return False


# Singleton instances
_model_manager: Optional[ModelManager] = None
_product_store = None
_vector_store = None


def get_model_manager() -> ModelManager:
    """Get the singleton ModelManager instance."""
    global _model_manager
    if _model_manager is None:
        _model_manager = ModelManager()
    return _model_manager


def get_settings():
    """Get application settings."""
    from app.config import settings
    return settings


def get_product_store():
    """Get the ProductStore instance."""
    global _product_store
    if _product_store is None:
        from app.layers.l6_storage.product_store import ProductStore
        from app.config import settings
        _product_store = ProductStore(db_path=settings.SQLITE_DB_PATH)
    return _product_store


def get_vector_store():
    """Get the VectorStore instance."""
    global _vector_store
    if _vector_store is None:
        from app.layers.l6_storage.vector_store import VectorStore
        from app.config import settings
        _vector_store = VectorStore(index_path=settings.FAISS_INDEX_PATH)
    return _vector_store
