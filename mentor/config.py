"""
Configuration management for Mentor platform.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field, PostgresDsn, RedisDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application
    app_name: str = "Mentor"
    app_env: Literal["development", "staging", "production"] = "development"
    debug: bool = False
    secret_key: str = Field(default="change-me-in-production")
    api_v1_prefix: str = "/api/v1"

    # Database
    database_url: PostgresDsn = Field(
        default="postgresql+asyncpg://mentor:mentor@localhost:5432/mentor"
    )
    database_pool_size: int = 20
    database_max_overflow: int = 10

    # Redis
    redis_url: RedisDsn = Field(default="redis://localhost:6379/0")

    # Authentication
    jwt_secret_key: str = Field(default="change-me-in-production")
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # OAuth
    oauth_enabled: bool = False
    oauth_provider: str | None = None
    oauth_client_id: str | None = None
    oauth_client_secret: str | None = None
    oauth_redirect_uri: str | None = None

    # LLM Configuration
    llm_provider: Literal["ollama", "together", "openrouter", "openai", "anthropic"] = "ollama"
    ollama_base_url: str = "http://localhost:11434"
    ollama_default_model: str = "llama3.1:8b"

    # Cloud LLM providers
    together_api_key: str | None = None
    openrouter_api_key: str | None = None
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None

    # Embeddings
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_dimension: int = 384

    # File Storage
    upload_dir: str = "./uploads"
    max_upload_size_mb: int = 50

    # Gaming Detection Thresholds
    gaming_min_response_time_ms: int = 3000
    gaming_min_coherence: float = 0.4
    gaming_max_competence_jump: float = 0.4
    gaming_ai_detection_threshold: float = 0.7

    # Research
    research_mode: bool = False
    enable_data_export: bool = False

    # Logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    log_format: Literal["json", "text"] = "json"

    # CORS
    cors_origins: list[str] = Field(default=["http://localhost:3000", "http://localhost:5173"])

    # Frontend URL
    frontend_url: str = "http://localhost:5173"

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
