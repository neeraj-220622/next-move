"""
NextMove — centralised configuration.

All settings are read from environment variables (or a .env file in the
backend working directory).  No secret values are stored here; every
sensitive field must be supplied at runtime.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application-wide settings loaded from environment / .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ──────────────────────────────────────────────────────────
    app_name: str = Field(default="NextMove", alias="APP_NAME")
    app_env: str = Field(default="development", alias="APP_ENV")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # ── Server ───────────────────────────────────────────────────────────────
    backend_host: str = Field(default="127.0.0.1", alias="BACKEND_HOST")
    backend_port: int = Field(default=8000, alias="BACKEND_PORT")

    # ── CORS ─────────────────────────────────────────────────────────────────
    frontend_origin: str = Field(
        default="http://localhost:5173", alias="FRONTEND_ORIGIN"
    )

    # ── Hindsight memory server ───────────────────────────────────────────────
    hindsight_base_url: str = Field(
        default="http://localhost:8888", alias="HINDSIGHT_BASE_URL"
    )
    hindsight_timeout: int = Field(default=10, alias="HINDSIGHT_TIMEOUT")

    # ── Local LLM ────────────────────────────────────────────────────────────
    llm_provider: str = Field(default="local", alias="LLM_PROVIDER")
    llm_model: str = Field(default="", alias="LLM_MODEL")
    llm_base_url: str = Field(
        default="http://localhost:11434/v1", alias="LLM_BASE_URL"
    )
    llm_timeout: int = Field(default=30, alias="LLM_TIMEOUT")

    # ── Forecasting ──────────────────────────────────────────────────────────
    forecasting_model: str = Field(default="baseline", alias="FORECASTING_MODEL")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached singleton settings instance."""
    return Settings()
