from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.statuses import TASK_STATUS_QUEUED
from app.schemas.page_monitor import PageMonitorCreate, PageMonitorRead, PageMonitorUpdate
from app.services.monitor_service import (
    create_monitor,
    delete_monitor,
    get_monitor,
    list_monitors,
    update_monitor,
)
from app.tasks.monitor_tasks import check_page_monitor

router = APIRouter(prefix="/api/monitors", tags=["Мониторы"])


@router.get("", response_model=list[PageMonitorRead])
def get_monitors(db: Session = Depends(get_db)) -> list[PageMonitorRead]:
    return list_monitors(db)


@router.post("", response_model=PageMonitorRead, status_code=status.HTTP_201_CREATED)
def create_new_monitor(payload: PageMonitorCreate, db: Session = Depends(get_db)) -> PageMonitorRead:
    return create_monitor(db, payload)


@router.get("/{monitor_id}", response_model=PageMonitorRead)
def get_monitor_by_id(monitor_id: int, db: Session = Depends(get_db)) -> PageMonitorRead:
    monitor = get_monitor(db, monitor_id)
    if monitor is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Монитор не найден")
    return monitor


@router.patch("/{monitor_id}", response_model=PageMonitorRead)
def patch_monitor(
    monitor_id: int,
    payload: PageMonitorUpdate,
    db: Session = Depends(get_db),
) -> PageMonitorRead:
    monitor = get_monitor(db, monitor_id)
    if monitor is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Монитор не найден")

    return update_monitor(db, monitor, payload)


@router.delete("/{monitor_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_monitor(monitor_id: int, db: Session = Depends(get_db)) -> Response:
    monitor = get_monitor(db, monitor_id)
    if monitor is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Монитор не найден")

    delete_monitor(db, monitor)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{monitor_id}/check", status_code=status.HTTP_202_ACCEPTED)
def run_monitor_check(monitor_id: int, db: Session = Depends(get_db)) -> dict[str, str | int]:
    monitor = get_monitor(db, monitor_id)
    if monitor is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Монитор не найден")

    task = check_page_monitor.delay(monitor_id)
    return {"status": TASK_STATUS_QUEUED, "task_id": task.id, "monitor_id": monitor_id}
