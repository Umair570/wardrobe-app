from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

# Base directory reaching the repo root (wardrobe-app/) where .env lives.
# Path: backend/app/core/config.py -> core/ -> app/ -> backend/ -> wardrobe-app/
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent


class Settings(BaseSettings):
    # Supabase Configuration
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_role_key: str = ""

    # MongoDB Configuration
    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "wardrobe_db"

    # Qdrant Vector DB
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: Optional[str] = None
    qdrant_collection: str = "wardrobe_items"

    # Groq LLM Infrastructure
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"

    # Embedding Model (Phase 6)
    # Controls which model is used by the ingestion pipeline.
    # Options: clip | fashion-clip | siglip
    embedding_model: str = "fashion-clip"

    # LLM Settings & Fallbacks
    llm_provider: str = "groq"
    llm_model: str = "llama-3.3-70b-versatile"
    openrouter_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None
    hf_token: Optional[str] = None

    # Storage Buckets
    supabase_bucket_wardrobe: str = "wardrobe-originals"
    supabase_bucket_cutouts: str = "wardrobe-cutouts"
    supabase_bucket_body: str = "body-photos"
    supabase_bucket_generated: str = "visualizations"
    upload_dir: str = "uploads"

    # Backend Settings
    backend_base_url: str = "http://localhost:8000"

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        extra="ignore",
    )


settings = Settings()
