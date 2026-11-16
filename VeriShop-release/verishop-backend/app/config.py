"""
VeriShop Backend Configuration
Loads settings from environment variables and .env file.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # App Config
    APP_NAME: str = "VeriShop"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]

    # Model Settings
    CLIP_MODEL_NAME: str = "openai/clip-vit-base-patch32"
    SBERT_MODEL_NAME: str = "all-MiniLM-L6-v2"
    LAZY_LOAD_MODELS: bool = True

    # LLM Provider
    LLM_PROVIDER: str = "none"
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"

    # Storage
    SQLITE_DB_PATH: str = "./data/verishop.db"
    FAISS_INDEX_PATH: str = "./data/faiss_index"
    FAKE_STORE_DB_PATH: str = "./data/fake_store.db"

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


settings = Settings()
