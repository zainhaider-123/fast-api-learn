from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# src/app/config.py → project root, so .env is found regardless of cwd.
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_ENV_FILE = _PROJECT_ROOT / ".env"

# pydantic-settings only fills Settings fields; load_dotenv also exports to os.environ
# (e.g. ANTHROPIC_API_KEY used by pydantic-ai).
load_dotenv(_ENV_FILE, override=False)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
        populate_by_name=True,
    )

    env: str = Field(default="DEV", validation_alias=AliasChoices("ENV", "env"))
    port: int = Field(default=8000, validation_alias=AliasChoices("PORT", "port"))
    database_url: str = Field(
        validation_alias=AliasChoices("DATABASE_URL", "database_url"),
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
