from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.visual_diff import VisualDiffRead
from app.services.monitor_service import get_monitor, list_monitor_diffs

router = APIRouter(prefix="/api/monitors", tags=["Сравнения"])


@router.get("/{monitor_id}/diffs", response_model=list[VisualDiffRead])
def get_monitor_diffs(
    monitor_id: int,
    db: Session = Depends(get_db),
) -> list[VisualDiffRead]:
    monitor = get_monitor(db, monitor_id)
    if monitor is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Монитор не найден")

    return list_monitor_diffs(db, monitor_id)
