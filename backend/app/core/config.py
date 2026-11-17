"""
Central application configuration.
All values are loaded from environment variables (.env) — never hardcode secrets.
"""
from functools import lru_cache
from pydantic import field_validator
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
    DATABASE_URL_UNPOOLED: str | None = None
    NEON_BRANCH: str | None = None

    @field_validator("DATABASE_URL", "DATABASE_URL_UNPOOLED", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: str | None) -> str | None:
        if not v:
            return v
        if v.startswith("postgres://"):
            v = "postgresql://" + v[len("postgres://"):]
        if v.startswith("postgresql://") and not v.startswith("postgresql+"):
            v = "postgresql+psycopg://" + v[len("postgresql://"):]
        return v

    # CORS — restrict to trusted origins in production (default allow all in dev)
    CORS_ORIGINS: list[str] = ["*"]

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

    # n8n Automation Webhooks
    N8N_ENABLED: bool = True
    N8N_WEBHOOK_URL: str = "http://localhost:5678/webhook/freshco-events"
    N8N_WEBHOOK_SECRET: str = "freshco-n8n-secret-key-2026"
    N8N_TIMEOUT_SECONDS: float = 3.0

    model_config = SettingsConfigDict(
        env_file=(".env", ".env.local", "../.env.local", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )



@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
