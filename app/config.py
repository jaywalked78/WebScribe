from functools import lru_cache

from pydantic import BaseSettings, AnyHttpUrl


class Settings(BaseSettings):
    """Application configuration pulled from environment variables or defaults."""

    HOST: str = "0.0.0.0"
    PORT: int = 8000
    LOG_LEVEL: str = "INFO"
    WEBHOOK_URL: str | None = None
    WEBHOOK_SECRET: str | None = None
    MAX_CONTENT_SIZE: int = 10 * 1024 * 1024  # 10MB
    TIMEOUT_SECONDS: int = 30
    DEBUG: bool = False

    # Airtable Integration
    AIRTABLE_API_KEY: str | None = None  # Legacy support
    AIRTABLE_PERSONAL_ACCESS_TOKEN: str | None = None  # Modern Airtable auth
    AIRTABLE_BASE_ID: str | None = None
    AIRTABLE_TABLE_NAME: str | None = None

    # Comma separated origins or *
    CORS_ALLOW_ORIGINS: str = "*"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @property
    def allowed_origins(self) -> list[str | AnyHttpUrl]:
        """Return list of allowed CORS origins."""
        if self.CORS_ALLOW_ORIGINS.strip() == "*":
            return ["*"]
        return [origin.strip() for origin in self.CORS_ALLOW_ORIGINS.split(",") if origin]


@lru_cache()
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()


settings = get_settings() 