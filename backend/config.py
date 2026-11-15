"""
FINN Backend Configuration
File: backend/config.py
"""
from __future__ import annotations
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    GEMINI_API_KEY: str = Field(default="", description="Google Gemini API key")
    DATABASE_URL: str = Field(default="backend/storage/finn.db", description="SQLite database path")
    YFINANCE_CACHE_TTL_SECONDS: int = Field(default=3600, description="Market data cache TTL in seconds")
    RESEARCH_CACHE_TTL_SECONDS: int = Field(default=86400, description="Research cache TTL in seconds")
    FINANCIAL_STATEMENTS_CACHE_TTL_SECONDS: int = Field(
        default=2592000, description="Yahoo annual statement cache TTL in seconds"
    )
    PORTFOLIO_CACHE_TTL_SECONDS: int = Field(default=300, description="Portfolio response cache TTL in seconds")
    ALERTS_CACHE_TTL_SECONDS: int = Field(default=300, description="Alerts response cache TTL in seconds")
    DIGEST_CACHE_TTL_SECONDS: int = Field(default=900, description="Digest response cache TTL in seconds")
    RESEARCH_RESPONSE_CACHE_TTL_SECONDS: int = Field(
        default=300, description="Research response cache TTL in seconds"
    )
    NARRATIVE_CACHE_TTL_SECONDS: int = Field(default=86400, description="Narrative audit cache TTL in seconds")
    NETWORK_CACHE_TTL_SECONDS: int = Field(default=86400, description="Network response cache TTL in seconds")
    COPILOT_CACHE_TTL_SECONDS: int = Field(default=300, description="Copilot response cache TTL in seconds")
    ENABLE_LIVE_DATA: bool = Field(
        default=False,
        description="Fetch Yahoo Finance data; synthetic seed remains the reliable default",
    )
    ALERT_VOLUME_MULTIPLE_THRESHOLD: float = Field(default=2.0, description="Volume spike alert threshold")
    ALERT_PRICE_CHANGE_PCT_THRESHOLD: float = Field(default=5.0, description="Price change alert threshold %")
    CORS_ORIGINS: list[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"],
        description="Allowed CORS origins",
    )

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
