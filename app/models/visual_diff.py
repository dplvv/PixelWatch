from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class VisualDiff(Base):
    __tablename__ = "visual_diffs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    page_monitor_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("page_monitors.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    old_screenshot_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("screenshots.id", ondelete="CASCADE"),
        nullable=False,
    )
    new_screenshot_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("screenshots.id", ondelete="CASCADE"),
        nullable=False,
    )
    diff_file_path: Mapped[str] = mapped_column(String(4096), nullable=False)
    change_percent: Mapped[float] = mapped_column(Float, nullable=False)
    text_change_percent: Mapped[float | None] = mapped_column(Float, nullable=True)
    hybrid_change_percent: Mapped[float] = mapped_column(Float, nullable=False)
    dom_changed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    changed_pixels_count: Mapped[int] = mapped_column(Integer, nullable=False)
    total_pixels_count: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    page_monitor = relationship("PageMonitor", back_populates="visual_diffs")
    old_screenshot = relationship("Screenshot", foreign_keys=[old_screenshot_id], back_populates="old_diffs")
    new_screenshot = relationship("Screenshot", foreign_keys=[new_screenshot_id], back_populates="new_diffs")
