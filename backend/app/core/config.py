from functools import lru_cache
from secrets import token_urlsafe

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AegisPTR"
    app_env: str = "development"
    app_debug: bool = True
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    frontend_url: str = "http://localhost:3000"
    database_url: str = "postgresql+psycopg://aegis:aegis_password@localhost:5432/aegis_ptr"
    redis_host: str = "localhost"
    redis_port: int = 6379
    ai_provider: str = "disabled"
    ai_model: str = "llama3.2"
    ai_base_url: str = "http://localhost:11434"
    ai_api_key: str = ""
    ai_timeout_seconds: int = 25
    secret_key: str = token_urlsafe(48)
    jwt_secret_key: str = token_urlsafe(48)
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
