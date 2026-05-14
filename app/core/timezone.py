from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

MOSCOW_TZ = ZoneInfo("Europe/Moscow")


def now_moscow() -> datetime:
    return datetime.now(MOSCOW_TZ)


def to_moscow(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None

    if dt.tzinfo is None:
        return dt.replace(tzinfo=MOSCOW_TZ)

    return dt.astimezone(MOSCOW_TZ)


def format_moscow_datetime(dt: datetime | None) -> str:
    localized = to_moscow(dt)
    if localized is None:
        return "-"

    return localized.strftime("%d.%m.%Y %H:%M:%S")
