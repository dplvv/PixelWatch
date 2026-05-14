from __future__ import annotations

MONITOR_STATUS_NEVER_CHECKED = "не_проверялась"
MONITOR_STATUS_SUCCESS = "успешно"
MONITOR_STATUS_FAILED = "ошибка"

SCREENSHOT_STATUS_SUCCESS = "успешно"
SCREENSHOT_STATUS_FAILED = "ошибка"

NOTIFICATION_TYPE_CHANGE_DETECTED = "обнаружены_изменения"
NOTIFICATION_TYPE_CHECK_FAILED = "ошибка_проверки"

TASK_STATUS_NOT_FOUND = "не_найден"
TASK_STATUS_FAILED = "ошибка"
TASK_STATUS_BASELINE_CREATED = "базовый_скриншот_создан"
TASK_STATUS_SUCCESS = "успешно"
TASK_STATUS_ERROR = "внутренняя_ошибка"
TASK_STATUS_QUEUED = "в_очереди"

MONITOR_STATUS_LABELS = {
    MONITOR_STATUS_NEVER_CHECKED: "Не проверялась",
    MONITOR_STATUS_SUCCESS: "Успешно",
    MONITOR_STATUS_FAILED: "Ошибка",
}

SCREENSHOT_STATUS_LABELS = {
    SCREENSHOT_STATUS_SUCCESS: "Успешно",
    SCREENSHOT_STATUS_FAILED: "Ошибка",
}

NOTIFICATION_TYPE_LABELS = {
    NOTIFICATION_TYPE_CHANGE_DETECTED: "Обнаружены изменения",
    NOTIFICATION_TYPE_CHECK_FAILED: "Ошибка проверки",
}


def monitor_status_label(value: str | None) -> str:
    if not value:
        return "-"
    return MONITOR_STATUS_LABELS.get(value, value)


def screenshot_status_label(value: str | None) -> str:
    if not value:
        return "-"
    return SCREENSHOT_STATUS_LABELS.get(value, value)


def notification_type_label(value: str | None) -> str:
    if not value:
        return "-"
    return NOTIFICATION_TYPE_LABELS.get(value, value)
