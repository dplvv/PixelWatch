from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.core.statuses import MONITOR_STATUS_NEVER_CHECKED
from app.core.timezone import MOSCOW_TZ, now_moscow
from app.models.page_monitor import PageMonitor
from app.models.screenshot import Screenshot
from app.models.visual_diff import VisualDiff
from app.schemas.page_monitor import PageMonitorCreate, PageMonitorUpdate


def list_monitors(db: Session) -> list[PageMonitor]:
    stmt = select(PageMonitor).order_by(desc(PageMonitor.created_at))
    return list(db.scalars(stmt).all())


def get_monitor(db: Session, monitor_id: int) -> PageMonitor | None:
    return db.get(PageMonitor, monitor_id)


def create_monitor(db: Session, payload: PageMonitorCreate) -> PageMonitor:
    monitor = PageMonitor(
        title=payload.title,
        url=str(payload.url),
        check_interval_minutes=payload.check_interval_minutes,
        is_active=payload.is_active,
        last_status=MONITOR_STATUS_NEVER_CHECKED,
    )
    db.add(monitor)
    db.commit()
    db.refresh(monitor)
    return monitor


def update_monitor(db: Session, monitor: PageMonitor, payload: PageMonitorUpdate) -> PageMonitor:
    changes = payload.model_dump(exclude_unset=True)

    if "title" in changes:
        monitor.title = changes["title"]
    if "url" in changes:
        monitor.url = str(changes["url"])
    if "check_interval_minutes" in changes:
        monitor.check_interval_minutes = changes["check_interval_minutes"]
    if "is_active" in changes:
        monitor.is_active = changes["is_active"]

    db.add(monitor)
    db.commit()
    db.refresh(monitor)
    return monitor


def delete_monitor(db: Session, monitor: PageMonitor) -> None:
    db.delete(monitor)
    db.commit()


def should_run_monitor(monitor: PageMonitor, now: datetime | None = None) -> bool:
    if not monitor.is_active:
        return False

    current_time = now or now_moscow()
    if monitor.last_checked_at is None:
        return True

    last_checked_at = monitor.last_checked_at
    if last_checked_at.tzinfo is None:
        last_checked_at = last_checked_at.replace(tzinfo=MOSCOW_TZ)

    next_check_at = last_checked_at + timedelta(minutes=monitor.check_interval_minutes)
    return current_time >= next_check_at


def list_monitor_screenshots(db: Session, monitor_id: int, limit: int = 50) -> list[Screenshot]:
    stmt = (
        select(Screenshot)
        .where(Screenshot.page_monitor_id == monitor_id)
        .order_by(desc(Screenshot.created_at), desc(Screenshot.id))
        .limit(limit)
    )
    return list(db.scalars(stmt).all())


def list_monitor_diffs(db: Session, monitor_id: int, limit: int = 50) -> list[VisualDiff]:
    stmt = (
        select(VisualDiff)
        .where(VisualDiff.page_monitor_id == monitor_id)
        .order_by(desc(VisualDiff.created_at), desc(VisualDiff.id))
        .limit(limit)
    )
    return list(db.scalars(stmt).all())


def get_latest_screenshot(db: Session, monitor_id: int) -> Screenshot | None:
    stmt = (
        select(Screenshot)
        .where(Screenshot.page_monitor_id == monitor_id)
        .order_by(desc(Screenshot.created_at), desc(Screenshot.id))
        .limit(1)
    )
    return db.scalars(stmt).first()


def get_latest_diff(db: Session, monitor_id: int) -> VisualDiff | None:
    stmt = (
        select(VisualDiff)
        .where(VisualDiff.page_monitor_id == monitor_id)
        .order_by(desc(VisualDiff.created_at), desc(VisualDiff.id))
        .limit(1)
    )
    return db.scalars(stmt).first()
