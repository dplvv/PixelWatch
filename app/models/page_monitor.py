from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class PageMonitor(Base):
    __tablename__ = "page_monitors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    check_interval_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=60)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    last_change_percent: Mapped[float | None] = mapped_column(Float, nullable=True)

    screenshots = relationship(
        "Screenshot",
        back_populates="page_monitor",
        cascade="all, delete-orphan",
    )
    visual_diffs = relationship(
        "VisualDiff",
        back_populates="page_monitor",
        cascade="all, delete-orphan",
    )
    notifications = relationship(
        "Notification",
        back_populates="page_monitor",
        cascade="all, delete-orphan",
    )
