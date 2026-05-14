from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ScreenshotRead(BaseModel):
    id: int
    page_monitor_id: int
    file_path: str | None
    created_at: datetime
    width: int | None
    height: int | None
    status: str
    error_message: str | None
    http_status: int | None
    dom_hash: str | None
    text_hash: str | None
    text_length: int | None

    model_config = ConfigDict(from_attributes=True)
