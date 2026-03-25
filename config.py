# config.py – Centralised settings via pydantic-settings / python-dotenv
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict # type: ignore


class Settings(BaseSettings):
    # Server
    PORT: int = 8000
    HOST: str = "0.0.0.0"
    DEBUG: bool = False

    # JWT
    JWT_SECRET: str = "dev_secret_change_in_production_min_64_chars_xxxxx"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_HOURS: int = 168  # 7 days

    # Email
    SMTP_HOST: str = "smtp.office365.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = "safinjema@outlook.com"
    SMTP_PASS: str = ""
    SMTP_FROM: str = "SaFi Njema Cleaning <safinjema@outlook.com>"

    # Admin seed
    ADMIN_EMAIL: str = "safinjema@outlook.com"
    ADMIN_PASSWORD: str = "SafiNjema@Admin2026"
    ADMIN_NAME: str = "SaFi Admin"

    # CORS
    CORS_ORIGINS: str = "http://localhost:5500,http://127.0.0.1:5500"

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/safinjema.db"

    @property
    def cors_origins_list(self) -> "list[str]":
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
