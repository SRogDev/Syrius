"""Syrius API settings (Phase 0).

Configuration comes from the environment (or a ``.env`` file next to the
app / at the repo root). No secrets are committed; ``.env.example`` lists
the placeholders.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings for the Syrius API."""

    model_config = SettingsConfigDict(
        env_file=(".env", "../../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "postgresql+psycopg://syrius:syrius@localhost:5432/syrius"
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
    environment: str = "development"


settings = Settings()
