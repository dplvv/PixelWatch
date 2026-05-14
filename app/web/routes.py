from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.statuses import (
    monitor_status_label,
    notification_type_label,
    screenshot_status_label,
)
from app.core.timezone import format_moscow_datetime
from app.schemas.page_monitor import PageMonitorCreate
from app.services.monitor_service import (
    create_monitor,
    delete_monitor,
    get_latest_diff,
    get_latest_screenshot,
    get_monitor,
    list_monitor_diffs,
    list_monitor_screenshots,
    list_monitors,
)
from app.services.notification_service import list_notifications, mark_notification_as_read
from app.tasks.monitor_tasks import check_page_monitor

router = APIRouter(tags=["Веб"])

templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent / "templates"))
templates.env.globals["monitor_status_label"] = monitor_status_label
templates.env.globals["screenshot_status_label"] = screenshot_status_label
templates.env.globals["notification_type_label"] = notification_type_label
templates.env.globals["format_moscow_datetime"] = format_moscow_datetime


def _redirect(url: str) -> RedirectResponse:
    return RedirectResponse(url=url, status_code=status.HTTP_303_SEE_OTHER)


def _template_response(
    request: Request,
    template_name: str,
    context: dict,
    status_code: int = status.HTTP_200_OK,
):
    shared_context = {
        "format_moscow_datetime": format_moscow_datetime,
        "monitor_status_label": monitor_status_label,
        "screenshot_status_label": screenshot_status_label,
        "notification_type_label": notification_type_label,
    }
    shared_context.update(context)
    return templates.TemplateResponse(
        request,
        template_name,
        shared_context,
        status_code=status_code,
    )


@router.get("/", name="web_index")
def web_index(
    request: Request,
    db: Session = Depends(get_db),
    message: str | None = Query(default=None),
):
    monitors = list_monitors(db)
    unread_notifications = list_notifications(db, unread_only=True, limit=5)
    return _template_response(
        request,
        "index.html",
        {
            "monitors": monitors,
            "message": message,
            "unread_count": len(unread_notifications),
        },
    )


@router.get("/monitors/new", name="web_monitor_form")
def web_monitor_form(request: Request):
    return _template_response(request, "monitor_form.html", {"error": None, "form": {}})


@router.post("/monitors/new", name="web_monitor_create")
def web_monitor_create(
    request: Request,
    title: str = Form(...),
    url: str = Form(...),
    check_interval_minutes: int = Form(...),
    is_active: str | None = Form(default=None),
    db: Session = Depends(get_db),
):
    try:
        payload = PageMonitorCreate(
            title=title,
            url=url,
            check_interval_minutes=check_interval_minutes,
            is_active=is_active is not None,
        )
    except ValidationError:
        return _template_response(
            request,
            "monitor_form.html",
            {
                "error": "Проверьте корректность данных формы.",
                "form": {
                    "title": title,
                    "url": url,
                    "check_interval_minutes": check_interval_minutes,
                    "is_active": is_active is not None,
                },
            },
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    monitor = create_monitor(db, payload)
    return _redirect(str(request.url_for("web_monitor_detail", monitor_id=monitor.id)))


@router.get("/monitors/{monitor_id}", name="web_monitor_detail")
def web_monitor_detail(monitor_id: int, request: Request, db: Session = Depends(get_db)):
    monitor = get_monitor(db, monitor_id)
    if monitor is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Монитор не найден")

    latest_screenshot = get_latest_screenshot(db, monitor_id)
    latest_diff = get_latest_diff(db, monitor_id)

    screenshot_history = list_monitor_screenshots(db, monitor_id, limit=10)
    diff_history = list_monitor_diffs(db, monitor_id, limit=20)

    return _template_response(
        request,
        "monitor_detail.html",
        {
            "monitor": monitor,
            "latest_screenshot": latest_screenshot,
            "latest_diff": latest_diff,
            "screenshot_history": screenshot_history,
            "diff_history": diff_history,
        },
    )


@router.post("/monitors/{monitor_id}/check", name="web_monitor_check")
def web_monitor_check(monitor_id: int, request: Request, db: Session = Depends(get_db)):
    monitor = get_monitor(db, monitor_id)
    if monitor is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Монитор не найден")

    check_page_monitor.delay(monitor_id)
    target = str(request.url_for("web_monitor_detail", monitor_id=monitor_id))
    return _redirect(f"{target}?queued=1")


@router.post("/monitors/{monitor_id}/toggle", name="web_monitor_toggle")
def web_monitor_toggle(monitor_id: int, request: Request, db: Session = Depends(get_db)):
    monitor = get_monitor(db, monitor_id)
    if monitor is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Монитор не найден")

    monitor.is_active = not monitor.is_active
    db.add(monitor)
    db.commit()

    return _redirect(str(request.url_for("web_monitor_detail", monitor_id=monitor_id)))


@router.post("/monitors/{monitor_id}/delete", name="web_monitor_delete")
def web_monitor_delete(monitor_id: int, request: Request, db: Session = Depends(get_db)):
    monitor = get_monitor(db, monitor_id)
    if monitor is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Монитор не найден")

    delete_monitor(db, monitor)
    return _redirect(str(request.url_for("web_index")))


@router.get("/notifications", name="web_notifications")
def web_notifications(request: Request, db: Session = Depends(get_db)):
    notifications = list_notifications(db, unread_only=False, limit=200)
    return _template_response(
        request,
        "notifications.html",
        {
            "notifications": notifications,
        },
    )


@router.post("/notifications/{notification_id}/read", name="web_notification_read")
def web_notification_read(notification_id: int, request: Request, db: Session = Depends(get_db)):
    notification = mark_notification_as_read(db, notification_id)
    if notification is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Уведомление не найдено")

    return _redirect(str(request.url_for("web_notifications")))
