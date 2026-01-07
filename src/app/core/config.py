"""Application configuration using pydantic-settings."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # OpenAI Configuration
    openai_api_key: str = ""
    openai_embedding_model: str = "text-embedding-3-small"
    openai_chat_model: str = "gpt-4o"

    # Database Configuration
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/manufacturing_rag"

    # Retrieval Parameters
    chunk_size: int = 512
    chunk_overlap: int = 50
    top_k_retrieval: int = 5
    similarity_threshold: float = 0.3

    # Application Settings
    log_level: str = "INFO"
    environment: str = "development"

    # Security Settings
    api_key_enabled: bool = True
    api_keys: list[str] = []

    # Rate Limiting
    rate_limit_enabled: bool = True
    rate_limit_default: str = "100/minute"
    rate_limit_query: str = "30/minute"
    rate_limit_ingest: str = "10/minute"
    rate_limit_threads: str = "60/minute"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
