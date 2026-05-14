from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.notification import NotificationRead
from app.services.notification_service import list_notifications, mark_notification_as_read

router = APIRouter(prefix="/api/notifications", tags=["Уведомления"])


@router.get("", response_model=list[NotificationRead])
def get_notifications(
    unread_only: bool = Query(default=False),
    db: Session = Depends(get_db),
) -> list[NotificationRead]:
    return list_notifications(db, unread_only=unread_only)


@router.patch("/{notification_id}/read", response_model=NotificationRead)
def read_notification(notification_id: int, db: Session = Depends(get_db)) -> NotificationRead:
    notification = mark_notification_as_read(db, notification_id)
    if notification is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Уведомление не найдено")

    return notification
