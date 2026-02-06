"""Tests for reconciliation service."""

import pytest
import pytest_asyncio
from unittest.mock import patch, AsyncMock
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from docbot.reconciliation import (
    retry_failed_calendar_events,
    check_calendar_drift,
    check_orphaned_cancelled,
    run_reconciliation
)


@pytest_asyncio.fixture
async def test_db_with_appointments(test_db):
    """Database with various appointment states for reconciliation testing."""
    future_date = (datetime.now(ZoneInfo("Asia/Kolkata")) + timedelta(days=2)).strftime("%Y-%m-%d")

    # Confirmed without calendar event (needs retry)
    await test_db.execute(
        """INSERT INTO appointments
           (id, patient_phone, patient_name, patient_age, patient_gender,
            consultation_type, appointment_date, slot_time, status,
            language, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        ("appt-no-cal", "+919876543210", "No Calendar", 30, "Male",
         "online", future_date, "10:00", "CONFIRMED",
         "en", "2026-02-06T10:00:00Z", "2026-02-06T10:00:00Z")
    )

    # Confirmed with calendar event (should be in sync)
    await test_db.execute(
        """INSERT INTO appointments
           (id, patient_phone, patient_name, patient_age, patient_gender,
            consultation_type, appointment_date, slot_time, status,
            google_calendar_event_id, language, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        ("appt-with-cal", "+919876543210", "With Calendar", 25, "Female",
         "online", future_date, "11:00", "CONFIRMED",
         "gcal-event-123", "en", "2026-02-06T10:00:00Z", "2026-02-06T10:00:00Z")
    )

    # Cancelled but still has calendar event (orphan)
    await test_db.execute(
        """INSERT INTO appointments
           (id, patient_phone, patient_name, patient_age, patient_gender,
            consultation_type, appointment_date, slot_time, status,
            google_calendar_event_id, language, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        ("appt-orphan", "+919876543210", "Orphan", 35, "Male",
         "online", future_date, "12:00", "CANCELLED",
         "gcal-orphan-456", "en", "2026-02-06T10:00:00Z", "2026-02-06T10:00:00Z")
    )

    await test_db.commit()
    return test_db


@pytest.mark.asyncio
async def test_retry_failed_calendar_events(test_db_with_appointments):
    """Test retry of calendar event creation."""
    with patch("docbot.reconciliation.create_appointment_event") as mock_create:
        mock_create.return_value = {"event_id": "new-event-123"}

        result = await retry_failed_calendar_events(test_db_with_appointments)

        assert result["retried"] == 1
        assert result["failed"] == 0
        mock_create.assert_called_once()


@pytest.mark.asyncio
async def test_check_calendar_drift_missing_event(test_db_with_appointments):
    """Test detection of missing calendar event."""
    with patch("docbot.reconciliation.google_calendar_client") as mock_client:
        # First call returns None (event missing), second returns event
        mock_client.get_event = AsyncMock(side_effect=[None, {"id": "exists"}])

        drifts = await check_calendar_drift(test_db_with_appointments)

        # Should find one drift (missing event)
        assert len(drifts) >= 1
        assert any(d["drift_type"] == "event_missing" for d in drifts)


@pytest.mark.asyncio
async def test_check_orphaned_cancelled(test_db_with_appointments):
    """Test detection of orphaned cancelled appointments."""
    orphans = await check_orphaned_cancelled(test_db_with_appointments)

    assert len(orphans) == 1
    assert orphans[0]["appointment_id"] == "appt-orphan"


@pytest.mark.asyncio
async def test_run_reconciliation_full(test_db_with_appointments):
    """Test full reconciliation run."""
    with patch("docbot.reconciliation.create_appointment_event") as mock_cal, \
         patch("docbot.reconciliation.google_calendar_client") as mock_client, \
         patch("docbot.reconciliation.log_alert") as mock_alert:

        mock_cal.return_value = {"event_id": "new-123"}
        mock_client.get_event = AsyncMock(return_value={"id": "exists", "start": {"dateTime": ""}})

        result = await run_reconciliation(test_db_with_appointments)

        assert result["calendar_retries"]["retried"] == 1
        assert result["refund_retries"] == 0  # Stub returns 0
        assert len(result["orphaned_cancelled"]) == 1

        # Alert should be raised for orphaned events
        assert mock_alert.called
