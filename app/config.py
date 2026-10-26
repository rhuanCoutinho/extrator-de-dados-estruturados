"""Environment-backed application settings."""

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    anthropic_api_key: str | None = os.getenv("ANTHROPIC_API_KEY")
    anthropic_model: str = os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./data/extractions.db")
    max_input_chars: int = int(os.getenv("MAX_INPUT_CHARS", "30000"))
    app_env: str = os.getenv("APP_ENV", "development")


settings = Settings()
