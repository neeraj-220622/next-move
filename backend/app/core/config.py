"""
NextMove — centralised configuration.

All settings are read from environment variables (or a .env file in the
backend working directory).  No secret values are stored here; every
sensitive field must be supplied at runtime.

Environment Variables
---------------------
See .env.example at the repository root for the full reference list with
defaults.  Sensitive variables (``LLM_API_KEY``) must be supplied at
runtime and are never logged or echoed.
"""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

_VALID_LLM_PROVIDERS = {"local", "openai-compatible", "disabled"}
_VALID_FORECASTING_MODELS = {"baseline", "sklearn", "scikit-learn", "xgboost"}


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
        default="http://127.0.0.1:8888", alias="HINDSIGHT_BASE_URL"
    )
    hindsight_timeout: int = Field(default=10, alias="HINDSIGHT_TIMEOUT")

    # ── LLM (Groq / OpenAI-compatible) ───────────────────────────────────────
    llm_provider: str = Field(default="disabled", alias="LLM_PROVIDER")
    llm_model: str = Field(default="", alias="LLM_MODEL")
    llm_api_key: str = Field(default="", alias="LLM_API_KEY")
    llm_base_url: str = Field(
        default="https://api.groq.com/openai/v1", alias="LLM_BASE_URL"
    )
    llm_timeout: int = Field(default=30, alias="LLM_TIMEOUT")

    # ── Forecasting ──────────────────────────────────────────────────────────
    forecasting_model: str = Field(default="baseline", alias="FORECASTING_MODEL")

    # ── Validators ───────────────────────────────────────────────────────────

    @field_validator("llm_provider")
    @classmethod
    def validate_llm_provider(cls, v: str) -> str:
        normalized = v.lower()
        if normalized not in _VALID_LLM_PROVIDERS:
            raise ValueError(
                f"LLM_PROVIDER must be one of {_VALID_LLM_PROVIDERS}, got '{v}'"
            )
        return normalized

    @field_validator("forecasting_model")
    @classmethod
    def validate_forecasting_model(cls, v: str) -> str:
        normalized = v.lower()
        if normalized not in _VALID_FORECASTING_MODELS:
            raise ValueError(
                f"FORECASTING_MODEL must be one of {_VALID_FORECASTING_MODELS}, got '{v}'"
            )
        return normalized

    @field_validator("hindsight_timeout", "llm_timeout")
    @classmethod
    def validate_positive_timeout(cls, v: int) -> int:
        if v <= 0:
            raise ValueError(f"Timeout must be a positive integer, got {v}")
        return v

    def safe_summary(self) -> str:
        """Return a redacted settings summary safe for logging (no secrets)."""
        return (
            f"app_env={self.app_env} "
            f"llm_provider={self.llm_provider} "
            f"llm_model={self.llm_model} "
            f"llm_base_url={self.llm_base_url} "
            f"llm_api_key={'[SET]' if self.llm_api_key else '[NOT SET]'} "
            f"forecasting_model={self.forecasting_model} "
            f"hindsight_base_url={self.hindsight_base_url}"
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached singleton settings instance."""
    return Settings()
