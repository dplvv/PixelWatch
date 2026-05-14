from __future__ import annotations

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.statuses import (
    NOTIFICATION_TYPE_CHANGE_DETECTED,
    NOTIFICATION_TYPE_CHECK_FAILED,
)
from app.models.notification import Notification
from app.models.page_monitor import PageMonitor


def create_notification(
    db: Session,
    page_monitor_id: int,
    notification_type: str,
    message: str,
) -> Notification:
    notification = Notification(
        page_monitor_id=page_monitor_id,
        type=notification_type,
        message=message,
    )
    db.add(notification)
    db.flush()
    db.refresh(notification)
    return notification


def create_change_notification_if_needed(
    db: Session,
    monitor: PageMonitor,
    change_percent: float,
) -> Notification | None:
    if change_percent < settings.significant_change_percent:
        return None

    message = (
        f"На странице {monitor.title} обнаружены изменения: "
        f"{round(change_percent, 2)}%."
    )
    return create_notification(db, monitor.id, NOTIFICATION_TYPE_CHANGE_DETECTED, message)


def create_check_error_notification(
    db: Session,
    monitor: PageMonitor,
    error_message: str,
) -> Notification:
    message = f"Ошибка проверки страницы {monitor.title}: {error_message}"
    return create_notification(db, monitor.id, NOTIFICATION_TYPE_CHECK_FAILED, message)


def list_notifications(db: Session, unread_only: bool = False, limit: int = 100) -> list[Notification]:
    stmt = select(Notification)
    if unread_only:
        stmt = stmt.where(Notification.is_read.is_(False))

    stmt = stmt.order_by(desc(Notification.created_at), desc(Notification.id)).limit(limit)
    return list(db.scalars(stmt).all())


def mark_notification_as_read(db: Session, notification_id: int) -> Notification | None:
    notification = db.get(Notification, notification_id)
    if notification is None:
        return None

    notification.is_read = True
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification
