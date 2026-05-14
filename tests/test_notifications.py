from __future__ import annotations

from app.schemas.page_monitor import PageMonitorCreate
from app.services.monitor_service import create_monitor
from app.services.notification_service import create_change_notification_if_needed


def test_create_notification_when_threshold_exceeded(db_session):
    monitor = create_monitor(
        db_session,
        PageMonitorCreate(
            title="Marketing page",
            url="https://example.com",
            check_interval_minutes=5,
            is_active=True,
        ),
    )

    notification = create_change_notification_if_needed(db_session, monitor, change_percent=10.2)

    assert notification is not None
    assert notification.id is not None
    assert notification.page_monitor_id == monitor.id
    assert "обнаружены изменения" in notification.message
