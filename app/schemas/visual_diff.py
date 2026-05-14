from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class VisualDiffRead(BaseModel):
    id: int
    page_monitor_id: int
    old_screenshot_id: int
    new_screenshot_id: int
    diff_file_path: str
    change_percent: float
    text_change_percent: float | None
    hybrid_change_percent: float
    dom_changed: bool
    changed_pixels_count: int
    total_pixels_count: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
