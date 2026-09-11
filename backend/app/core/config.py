from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AegisPTR"
    app_env: str = "development"
    app_debug: bool = True
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    database_url: str = "postgresql+psycopg://aegis:aegis_password@localhost:5432/aegis_ptr"
    redis_host: str = "localhost"
    redis_port: int = 6379
    secret_key: str = "change-me-in-production"
    jwt_secret_key: str = "aegisptr_super_secret_change_this_in_prod_2026_09_11_!@#0123456789abcd"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
