"""Configuration de l'application (pydantic-settings)."""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Application
    APP_NAME: str = "Agents IA - Analyse de risques (EBIOS RM)"
    DEBUG: bool = False
    SECRET_KEY: str = "change-me"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 8

    # Base de données
    DATABASE_URL: str = "postgresql+asyncpg://admin:admin@localhost:5432/risk_agents"

    # Redis / Celery
    REDIS_URL: str = "redis://localhost:6379"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"

    # LLM
    LLM_PROVIDER: Literal["opencode_go", "mock"] = "opencode_go"
    LLM_MODEL: str = "deepseek-v4-pro"
    LLM_ENDPOINT_URL: str = "https://opencode.ai/inference/openai/v1/chat/completions"
    LLM_API_KEY: str = ""
    LLM_TIMEOUT_SECONDS: float = 120.0

    # CORS (liste séparée par des virgules)
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
