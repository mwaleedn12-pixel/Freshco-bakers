"""
Central application configuration.
All values are loaded from environment variables (.env) — never hardcode secrets.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Freshco Bakers"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    # Security
    SECRET_KEY: str = "change-me-in-env"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    ALGORITHM: str = "HS256"

    # Database (single central PostgreSQL DB — website + POS share it)
    DATABASE_URL: str = "postgresql+psycopg://freshco_user:freshco_pass@localhost:5432/freshco_bakers_db"

    # CORS — restrict to trusted origins in production
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:8080"]

    # Redis (optional, for caching / offline queue later)
    REDIS_URL: str | None = None

    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = 120
    RATE_LIMIT_BURST: int = 30
    RATE_LIMIT_ENABLED: bool = True

    # Trusted hosts (production only — prevents host-header injection)
    ALLOWED_HOSTS: list[str] = ["*"]

    # Logging
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
