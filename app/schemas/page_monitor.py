from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class PageMonitorCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    url: HttpUrl
    check_interval_minutes: int = Field(default=60, ge=1, le=10080)
    is_active: bool = True


class PageMonitorUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    url: HttpUrl | None = None
    check_interval_minutes: int | None = Field(default=None, ge=1, le=10080)
    is_active: bool | None = None


class PageMonitorRead(BaseModel):
    id: int
    title: str
    url: str
    check_interval_minutes: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_checked_at: datetime | None
    last_status: str | None
    last_change_percent: float | None

    model_config = ConfigDict(from_attributes=True)
