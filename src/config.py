"""
Application configuration via Pydantic Settings.

All configuration is loaded from environment variables (or .env file).
Pydantic Settings validates types at startup — a missing or malformed env var
fails fast with a clear error rather than silently breaking at runtime.

Interview talking points:
- Why Pydantic Settings over os.getenv()? Type safety, validation, defaults,
  and documentation in one place. You never get a None where you expected a string.
- Why a single Settings class? One source of truth for all config. Easy to mock
  in tests. Easy to see what the app needs at a glance.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database
    database_url: str = (
        "postgresql+asyncpg://workshop:workshop_dev@localhost:5432/workshop"
    )

    # Anthropic (Claude)
    anthropic_api_key: str = ""

    # Voyage AI (Embeddings)
    voyage_api_key: str = ""

    # Langfuse (Observability)
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = "https://cloud.langfuse.com"

    # Application
    app_env: str = "development"
    log_level: str = "INFO"

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"


settings = Settings()
