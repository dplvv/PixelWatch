from __future__ import annotations

from sqlalchemy import select

from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.core.statuses import (
    MONITOR_STATUS_FAILED,
    MONITOR_STATUS_SUCCESS,
    SCREENSHOT_STATUS_SUCCESS,
    TASK_STATUS_BASELINE_CREATED,
    TASK_STATUS_ERROR,
    TASK_STATUS_FAILED,
    TASK_STATUS_NOT_FOUND,
    TASK_STATUS_SUCCESS,
)
from app.core.timezone import now_moscow
from app.models.page_monitor import PageMonitor
from app.services.diff_service import create_visual_diff
from app.services.monitor_service import should_run_monitor
from app.services.notification_service import (
    create_change_notification_if_needed,
    create_check_error_notification,
)
from app.services.screenshot_service import capture_screenshot, get_previous_success_screenshot


@celery_app.task(name="app.tasks.monitor_tasks.check_page_monitor")
def check_page_monitor(page_monitor_id: int) -> dict[str, str | int | float | None]:
    db = SessionLocal()
    try:
        monitor = db.get(PageMonitor, page_monitor_id)
        if monitor is None:
            return {"status": TASK_STATUS_NOT_FOUND, "page_monitor_id": page_monitor_id}

        screenshot = capture_screenshot(db, monitor)
        monitor.last_checked_at = now_moscow()

        if screenshot.status != SCREENSHOT_STATUS_SUCCESS:
            monitor.last_status = MONITOR_STATUS_FAILED
            create_check_error_notification(
                db,
                monitor,
                screenshot.error_message or "Неизвестная ошибка создания скриншота",
            )
            db.add(monitor)
            db.commit()
            db.refresh(monitor)
            return {
                "status": TASK_STATUS_FAILED,
                "page_monitor_id": page_monitor_id,
                "error": screenshot.error_message,
            }

        previous_success = get_previous_success_screenshot(
            db,
            monitor_id=monitor.id,
            exclude_screenshot_id=screenshot.id,
        )

        monitor.last_status = MONITOR_STATUS_SUCCESS

        if previous_success is None:
            monitor.last_change_percent = None
            db.add(monitor)
            db.commit()
            db.refresh(monitor)
            return {
                "status": TASK_STATUS_BASELINE_CREATED,
                "page_monitor_id": page_monitor_id,
                "screenshot_id": screenshot.id,
            }

        visual_diff = create_visual_diff(db, monitor, previous_success, screenshot)
        if visual_diff is not None:
            monitor.last_change_percent = visual_diff.hybrid_change_percent
            create_change_notification_if_needed(
                db,
                monitor,
                visual_diff.hybrid_change_percent,
            )

        db.add(monitor)
        db.commit()
        db.refresh(monitor)

        return {
            "status": TASK_STATUS_SUCCESS,
            "page_monitor_id": page_monitor_id,
            "screenshot_id": screenshot.id,
            "change_percent": monitor.last_change_percent,
        }
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        return {
            "status": TASK_STATUS_ERROR,
            "page_monitor_id": page_monitor_id,
            "error": str(exc),
        }
    finally:
        db.close()


@celery_app.task(name="app.tasks.monitor_tasks.check_all_active_monitors")
def check_all_active_monitors() -> dict[str, int]:
    db = SessionLocal()
    try:
        active_stmt = select(PageMonitor).where(PageMonitor.is_active.is_(True))
        active_monitors = list(db.scalars(active_stmt).all())

        now = now_moscow()
        enqueued = 0
        for monitor in active_monitors:
            if should_run_monitor(monitor, now=now):
                check_page_monitor.delay(monitor.id)
                enqueued += 1

        return {"checked_active_monitors": len(active_monitors), "enqueued_checks": enqueued}
    finally:
        db.close()
