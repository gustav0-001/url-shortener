from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator

class Settings(BaseSettings):
    base_url: str = "http://localhost:8000"
    database_url: str = "sqlite:///links.db"
    admin_token: str = ""
    create_rate_limit: int = 10
    create_rate_window: int = 60
    log_level: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env")

    @field_validator("database_url")
    @classmethod
    def normalize_database_url(cls, value: str) -> str:
        for prefix in ("postgres://", "postgresql://"):
            if value.startswith(prefix):
                return "postgresql+psycopg://" + value[len(prefix):]
        return value


settings = Settings()