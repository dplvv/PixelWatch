from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.screenshot import ScreenshotRead
from app.services.monitor_service import get_monitor, list_monitor_screenshots

router = APIRouter(prefix="/api/monitors", tags=["Скриншоты"])


@router.get("/{monitor_id}/screenshots", response_model=list[ScreenshotRead])
def get_monitor_screenshots(
    monitor_id: int,
    db: Session = Depends(get_db),
) -> list[ScreenshotRead]:
    monitor = get_monitor(db, monitor_id)
    if monitor is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Монитор не найден")

    return list_monitor_screenshots(db, monitor_id)
