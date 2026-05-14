from __future__ import annotations

from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery_app = Celery(
    "pixelwatch",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.tasks.monitor_tasks"],
)

celery_app.conf.update(
    timezone="Europe/Moscow",
    enable_utc=True,
    beat_schedule={
        "check-active-monitors-every-minute": {
            "task": "app.tasks.monitor_tasks.check_all_active_monitors",
            "schedule": crontab(minute="*"),
        }
    },
)
