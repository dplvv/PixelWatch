from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = Field(
        default="postgresql+psycopg://pixelwatch:pixelwatch@db:5432/pixelwatch",
        alias="DATABASE_URL",
    )
    redis_url: str = Field(default="redis://redis:6379/0", alias="REDIS_URL")
    storage_dir: Path = Field(default=Path("storage"), alias="STORAGE_DIR")
    screenshot_timeout_seconds: int = Field(default=30, alias="SCREENSHOT_TIMEOUT_SECONDS")
    visual_diff_threshold: int = Field(default=25, alias="VISUAL_DIFF_THRESHOLD")
    significant_change_percent: float = Field(default=5, alias="SIGNIFICANT_CHANGE_PERCENT")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def screenshots_dir(self) -> Path:
        return self.storage_dir / "screenshots"

    @property
    def diffs_dir(self) -> Path:
        return self.storage_dir / "diffs"


settings = Settings()
