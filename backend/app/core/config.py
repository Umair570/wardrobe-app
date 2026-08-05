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
    qdrant_score_threshold: float = 0.0

    # Groq LLM Infrastructure
    groq_api_key: str = ""
    groq_model: str = "llama-3.1-8b-instant"

    # Embedding Model (Phase 6)
    # Controls which model is used by the ingestion pipeline.
    # Options: clip | fashion-clip | siglip
    embedding_model: str = "fashion-clip"

    # LLM Settings & Fallbacks
    # The stylist is a multi-step tool-calling agent, so the model needs solid
    # function-calling: it has to sequence get_weather → several search_wardrobe
    # calls → present_outfits and keep item IDs verbatim throughout. Small or
    # legacy chat models (gpt-3.5-turbo, llama-3.1-8b) drop tool calls and
    # garble IDs. Override with LLM_MODEL in .env.
    llm_provider: str = "openrouter"
    llm_model: str = "openai/gpt-4o-mini"
    openrouter_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None
    hf_token: Optional[str] = None

    @property
    def active_llm_api_key(self) -> Optional[str]:
        p = self.llm_provider.lower()
        if p == "openrouter":
            return self.openrouter_api_key
        elif p == "openai":
            return self.openai_api_key
        return self.groq_api_key

    @property
    def active_llm_base_url(self) -> str:
        p = self.llm_provider.lower()
        if p == "openrouter":
            return "https://openrouter.ai/api/v1/chat/completions"
        elif p == "openai":
            return "https://api.openai.com/v1/chat/completions"
        return "https://api.groq.com/openai/v1/chat/completions"

    @property
    def active_llm_model(self) -> str:
        p = self.llm_provider.lower()
        if p == "groq":
            return self.groq_model
        return self.llm_model

    # Storage Buckets
    supabase_bucket_wardrobe: str = "wardrobe-originals"
    supabase_bucket_cutouts: str = "wardrobe-cutouts"
    supabase_bucket_body: str = "body-photos"
    supabase_bucket_generated: str = "visualizations"
    # Project root is BASE_DIR, so we store uploads securely outside of the Uvicorn watch scope
    upload_dir: str = str(BASE_DIR / ".uploads")
    max_upload_size_mb: int = 50

    # Backend Settings
    backend_base_url: str = "http://localhost:8000"

    # Virtual Try-On inference architecture
    ootd_provider: str = "gradio"
    modal_ootd_endpoint: str = ""

    model_config = SettingsConfigDict(
        env_file=(".env", str(BASE_DIR / ".env")),
        extra="ignore",
    )


settings = Settings()
