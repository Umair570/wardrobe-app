from motor.motor_asyncio import AsyncIOMotorClient
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

# wardrobe-app/backend/app/database/mongodb.py
# BASE_DIR must reach the repo root (wardrobe-app/) where .env lives.
# Path chain: mongodb.py → database/ → app/ → backend/ → wardrobe-app/
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent


class Settings(BaseSettings):
    mongodb_uri: str
    mongodb_db_name: str
    upload_dir: str = "uploads"

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        extra="ignore",   # ignore LLM_PROVIDER, OPENROUTER_API_KEY, etc.
    )


settings = Settings()
client = AsyncIOMotorClient(settings.mongodb_uri)
db = client[settings.mongodb_db_name]
wardrobe_collection = db["wardrobe_items"]