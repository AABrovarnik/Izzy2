from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = "development"
    app_name: str = "ai-secretary"
    app_port: int = 8000
    database_url: str = "sqlite:///./data/ai_secretary.db"
    api_token: str = ""
    approval_signing_key: str = ""
    telegram_webhook_secret: str = ""
    telegram_owner_user_id: str = ""
    app_timezone: str = "Europe/Moscow"
    approval_ttl_hours: int = Field(default=24, ge=1, le=168)
    execution_enabled: bool = False

    @field_validator("app_env")
    @classmethod
    def normalize_env(cls, value: str) -> str:
        return value.lower().strip()

    def validate_production(self) -> None:
        if self.app_env == "production":
            missing = [
                name
                for name, value in (
                    ("API_TOKEN", self.api_token),
                    ("APPROVAL_SIGNING_KEY", self.approval_signing_key),
                    ("TELEGRAM_WEBHOOK_SECRET", self.telegram_webhook_secret),
                )
                if len(value) < 32
            ]
            if missing:
                raise RuntimeError(
                    "Production secrets must be random strings of at least 32 characters: "
                    + ", ".join(missing)
                )
            if not self.telegram_owner_user_id:
                raise RuntimeError("TELEGRAM_OWNER_USER_ID is required in production")


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.validate_production()
    return settings
