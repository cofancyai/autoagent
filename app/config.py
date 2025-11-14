"""Application configuration using pydantic-settings"""

from typing import List
from pydantic import Field, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )

    # Application
    app_name: str = Field(default="ThinkingAgent", alias="APP_NAME")
    app_version: str = Field(default="0.1.0", alias="APP_VERSION")
    app_env: str = Field(default="development", alias="APP_ENV")
    debug: bool = Field(default=True, alias="DEBUG")

    # Server
    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8000, alias="PORT")

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/thinkingagent",
        alias="DATABASE_URL"
    )
    database_pool_size: int = Field(default=20, alias="DATABASE_POOL_SIZE")
    database_max_overflow: int = Field(default=10, alias="DATABASE_MAX_OVERFLOW")

    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")

    # Anthropic
    anthropic_api_key: str = Field(default="", alias="ANTHROPIC_API_KEY")

    # Security
    secret_key: str = Field(
        default="your_secret_key_here_change_in_production",
        alias="SECRET_KEY"
    )
    algorithm: str = Field(default="HS256", alias="ALGORITHM")
    access_token_expire_minutes: int = Field(
        default=30,
        alias="ACCESS_TOKEN_EXPIRE_MINUTES"
    )

    # LLM Configuration
    llm_default_model: str = Field(default="sonnet", alias="LLM_DEFAULT_MODEL")
    llm_max_tokens: int = Field(default=8192, alias="LLM_MAX_TOKENS")
    llm_temperature: float = Field(default=0.7, alias="LLM_TEMPERATURE")
    llm_enable_prompt_caching: bool = Field(
        default=True,
        alias="LLM_ENABLE_PROMPT_CACHING"
    )

    # Rate Limiting
    rate_limit_requests_per_minute: int = Field(
        default=50,
        alias="RATE_LIMIT_REQUESTS_PER_MINUTE"
    )
    rate_limit_tokens_per_minute: int = Field(
        default=40000,
        alias="RATE_LIMIT_TOKENS_PER_MINUTE"
    )

    # Cost Limits
    daily_cost_limit: float = Field(default=50.00, alias="DAILY_COST_LIMIT")
    monthly_cost_limit: float = Field(default=1000.00, alias="MONTHLY_COST_LIMIT")

    # CORS
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        alias="CORS_ORIGINS"
    )

    @property
    def is_development(self) -> bool:
        """Check if running in development mode"""
        return self.app_env == "development"

    @property
    def is_production(self) -> bool:
        """Check if running in production mode"""
        return self.app_env == "production"


# Global settings instance
settings = Settings()
