import os
from functools import lru_cache
from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Central application configuration loaded from environment variables and .env file.
    Using pydantic-settings guarantees type safety, validation at startup, and centralized access.
    """
    GEMINI_API_KEY: str = Field(
        default="",
        description="Official Google Gemini API key used by the provider layer"
    )
    GEMINI_MODEL: str = Field(
        default="gemini-3.6-flash",
        description="Target Gemini foundational model identifier"
    )
    ENVIRONMENT: str = Field(
        default="development",
        description="Runtime environment: development, staging, or production"
    )
    APP_NAME: str = Field(
        default="AI Assistant API",
        description="Application title for OpenAPI docs and logging"
    )
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:3001"],
        description="Allowed origins for frontend CORS communication"
    )
    REQUEST_TIMEOUT_SECONDS: float = Field(
        default=30.0,
        description="Maximum seconds to wait for an upstream LLM response before timing out"
    )

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(__file__), "..", "..", ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )


@lru_cache()
def get_settings() -> Settings:
    """
    Cached settings instance to avoid reading files or re-parsing environment variables per request.
    """
    return Settings()
