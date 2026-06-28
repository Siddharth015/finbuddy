"""Application settings loaded from environment / .env."""
from __future__ import annotations

from functools import lru_cache

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Telegram
    bot_token: str
    webhook_url: str = ""
    webhook_secret: str = "change-me"
    # Public HTTPS URL of this deployment. PaaS platforms expose it automatically
    # (Render sets ``RENDER_EXTERNAL_URL``). Used as the default for both the
    # webhook and the Mini App so you never have to paste the URL by hand.
    public_url: str = Field(
        "", validation_alias=AliasChoices("PUBLIC_URL", "RENDER_EXTERNAL_URL")
    )

    # Database
    database_url: str = "postgresql+asyncpg://finbuddy:finbuddy@localhost:5432/finbuddy"

    @field_validator("database_url", mode="after")
    @classmethod
    def _force_asyncpg_driver(cls, value: str) -> str:
        """Normalise managed-Postgres URLs (``postgres://`` / ``postgresql://``)
        to the async driver SQLAlchemy needs. PaaS providers such as Render and
        Railway hand out plain ``postgres://...`` strings."""
        if value.startswith("postgres://"):
            value = "postgresql://" + value[len("postgres://") :]
        if value.startswith("postgresql://"):
            value = "postgresql+asyncpg://" + value[len("postgresql://") :]
        return value

    # AI
    ai_provider: str = "groq"
    groq_api_key: str = ""
    ai_model: str = "llama-3.3-70b-versatile"

    # Mini App
    cors_origins: str = "http://localhost:5173"
    default_currency: str = "INR"
    # Public HTTPS URL where the Mini App frontend is hosted. Enables the
    # "Open Dashboard" button inside Telegram.
    miniapp_url: str = ""
    # Filesystem path to the built Mini App (``frontend/dist``). When set and the
    # folder exists, FastAPI serves the dashboard from the same origin as the API.
    frontend_dist: str = ""

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def effective_webhook_url(self) -> str:
        """Explicit ``WEBHOOK_URL`` wins; otherwise fall back to the platform URL."""
        return (self.webhook_url or self.public_url).rstrip("/")

    @property
    def effective_miniapp_url(self) -> str:
        """Explicit ``MINIAPP_URL`` wins; otherwise serve the Mini App on this origin."""
        return (self.miniapp_url or self.public_url).rstrip("/")

    @property
    def use_webhook(self) -> bool:
        return bool(self.effective_webhook_url)


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]


settings = get_settings()
