from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    base_url: str = "http://localhost:8000"
    database_url: str = "sqlite:///links.db"

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()