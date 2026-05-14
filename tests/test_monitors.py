from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.schemas.page_monitor import PageMonitorCreate
from app.services.monitor_service import create_monitor


def test_create_monitor_record(db_session):
    payload = PageMonitorCreate(
        title="Example homepage",
        url="https://example.com",
        check_interval_minutes=15,
        is_active=True,
    )

    monitor = create_monitor(db_session, payload)

    assert monitor.id is not None
    assert monitor.title == "Example homepage"
    assert monitor.url == "https://example.com/"
    assert monitor.check_interval_minutes == 15
    assert monitor.is_active is True


def test_url_validation():
    with pytest.raises(ValidationError):
        PageMonitorCreate(
            title="Broken URL monitor",
            url="this-is-not-a-url",
            check_interval_minutes=10,
            is_active=True,
        )
