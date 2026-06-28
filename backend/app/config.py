"""Application settings loaded from environment / .env."""
from __future__ import annotations

import re
from functools import lru_cache
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from pydantic import AliasChoices, Field, model_validator
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
    # Set by the validator below: whether the DB connection needs TLS. Managed
    # providers (Neon, Supabase, Aiven, ...) require it; local Postgres does not.
    db_ssl_required: bool = False

    @model_validator(mode="after")
    def _normalise_database_url(self) -> "Settings":
        """Make any Postgres URL work with asyncpg.

        - Upgrades ``postgres://`` / ``postgresql://`` to the asyncpg driver
          (Render, Railway, Neon, Supabase all hand out bare ``postgres://``).
        - Strips libpq-only query params (``sslmode``, ``channel_binding``) that
          asyncpg rejects, and records whether TLS is needed so the engine can
          enable it via ``connect_args`` instead.
        """
        url = self.database_url
        if url.startswith("postgres://"):
            url = "postgresql://" + url[len("postgres://") :]
        if url.startswith("postgresql://"):
            url = "postgresql+asyncpg://" + url[len("postgresql://") :]

        parts = urlsplit(url)
        query = dict(parse_qsl(parts.query))
        sslmode = query.pop("sslmode", None)
        query.pop("channel_binding", None)  # asyncpg does not understand this
        self.database_url = urlunsplit(
            (parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment)
        )

        host = (parts.hostname or "").lower()
        if sslmode is not None:
            self.db_ssl_required = sslmode != "disable"
        else:
            is_local = host in {"localhost", "127.0.0.1", "::1", ""}
            # Private platform networks (Render internal, Fly .internal) speak
            # plaintext; only public managed hosts need TLS.
            is_internal = (
                "." not in host
                or host.endswith(".internal")
                or host.endswith(".flycast")
            )
            self.db_ssl_required = not (is_local or is_internal)
        return self

    @property
    def db_connect_args(self) -> dict[str, object]:
        """Extra kwargs for the asyncpg engine (TLS when the provider needs it)."""
        return {"ssl": True} if self.db_ssl_required else {}

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
    def effective_webhook_secret(self) -> str:
        """Telegram's webhook secret token only permits ``A-Z a-z 0-9 _ -``.
        Strip anything else (Render's ``generateValue`` can emit base64 chars)
        so the value is always accepted by ``setWebhook``."""
        cleaned = re.sub(r"[^A-Za-z0-9_-]", "", self.webhook_secret)[:256]
        return cleaned or "finbuddy"

    @property
    def use_webhook(self) -> bool:
        return bool(self.effective_webhook_url)


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]


settings = get_settings()
