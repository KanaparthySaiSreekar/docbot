"""Tests for calendar service."""

import pytest
import pytest_asyncio
from unittest.mock import patch, AsyncMock
from datetime import datetime

from docbot.calendar_service import create_appointment_event, cancel_appointment_event


@pytest_asyncio.fixture
async def test_db_with_appointment(test_db):
    """Test database with an appointment."""
    await test_db.execute(
        """INSERT INTO appointments
           (id, patient_phone, patient_name, patient_age, patient_gender,
            consultation_type, appointment_date, slot_time, status,
            language, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        ("appt-123", "+919876543210", "Test Patient", 30, "Male",
         "online", "2026-02-10", "10:00", "CONFIRMED",
         "en", "2026-02-06T10:00:00Z", "2026-02-06T10:00:00Z")
    )
    await test_db.commit()
    return test_db


@pytest.mark.asyncio
async def test_create_appointment_event_online(test_db_with_appointment):
    """Test creating event for online appointment."""
    with patch("docbot.calendar_service.google_calendar_client") as mock_client:
        mock_client.create_event = AsyncMock(return_value={
            "event_id": "gcal-event-123",
            "meet_link": "https://meet.google.com/abc-def"
        })

        result = await create_appointment_event(test_db_with_appointment, "appt-123")

        assert result is not None
        assert result["event_id"] == "gcal-event-123"
        assert result["meet_link"] == "https://meet.google.com/abc-def"

        # Verify database updated
        cursor = await test_db_with_appointment.execute(
            "SELECT google_calendar_event_id, google_meet_link FROM appointments WHERE id = ?",
            ("appt-123",)
        )
        row = await cursor.fetchone()
        assert row[0] == "gcal-event-123"
        assert row[1] == "https://meet.google.com/abc-def"


@pytest.mark.asyncio
async def test_create_appointment_event_offline(test_db):
    """Test creating event for offline appointment (no Meet link)."""
    await test_db.execute(
        """INSERT INTO appointments
           (id, patient_phone, patient_name, patient_age, patient_gender,
            consultation_type, appointment_date, slot_time, status,
            language, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        ("appt-offline", "+919876543210", "Offline Patient", 25, "Female",
         "offline", "2026-02-10", "11:00", "CONFIRMED",
         "en", "2026-02-06T10:00:00Z", "2026-02-06T10:00:00Z")
    )
    await test_db.commit()

    with patch("docbot.calendar_service.google_calendar_client") as mock_client:
        mock_client.create_event = AsyncMock(return_value={
            "event_id": "gcal-event-456"
        })

        result = await create_appointment_event(test_db, "appt-offline")

        assert result is not None
        assert result["event_id"] == "gcal-event-456"
        assert "meet_link" not in result or result.get("meet_link") is None

        # Verify create_event was called without meet link
        call_args = mock_client.create_event.call_args
        assert call_args.kwargs["add_meet_link"] is False


@pytest.mark.asyncio
async def test_create_appointment_event_already_exists(test_db):
    """Test skipping creation when event already exists."""
    await test_db.execute(
        """INSERT INTO appointments
           (id, patient_phone, patient_name, patient_age, patient_gender,
            consultation_type, appointment_date, slot_time, status,
            google_calendar_event_id, google_meet_link,
            language, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        ("appt-existing", "+919876543210", "Existing", 40, "Male",
         "online", "2026-02-10", "12:00", "CONFIRMED",
         "existing-event-id", "https://meet.google.com/existing",
         "en", "2026-02-06T10:00:00Z", "2026-02-06T10:00:00Z")
    )
    await test_db.commit()

    with patch("docbot.calendar_service.google_calendar_client") as mock_client:
        result = await create_appointment_event(test_db, "appt-existing")

        assert result is not None
        assert result["event_id"] == "existing-event-id"
        mock_client.create_event.assert_not_called()


@pytest.mark.asyncio
async def test_cancel_appointment_event(test_db):
    """Test deleting calendar event on cancellation."""
    await test_db.execute(
        """INSERT INTO appointments
           (id, patient_phone, patient_name, patient_age, patient_gender,
            consultation_type, appointment_date, slot_time, status,
            google_calendar_event_id,
            language, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        ("appt-cancel", "+919876543210", "Cancel Me", 35, "Male",
         "online", "2026-02-10", "14:00", "CANCELLED",
         "event-to-delete",
         "en", "2026-02-06T10:00:00Z", "2026-02-06T10:00:00Z")
    )
    await test_db.commit()

    with patch("docbot.calendar_service.google_calendar_client") as mock_client:
        mock_client.delete_event = AsyncMock(return_value=True)

        result = await cancel_appointment_event(test_db, "appt-cancel")

        assert result is True
        mock_client.delete_event.assert_called_once_with("event-to-delete")

        # Verify database cleared
        cursor = await test_db.execute(
            "SELECT google_calendar_event_id FROM appointments WHERE id = ?",
            ("appt-cancel",)
        )
        row = await cursor.fetchone()
        assert row[0] is None


@pytest.mark.asyncio
async def test_cancel_appointment_event_no_event(test_db):
    """Test cancellation when no calendar event exists."""
    await test_db.execute(
        """INSERT INTO appointments
           (id, patient_phone, patient_name, patient_age, patient_gender,
            consultation_type, appointment_date, slot_time, status,
            language, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        ("appt-no-event", "+919876543210", "No Event", 28, "Female",
         "offline", "2026-02-10", "15:00", "CANCELLED",
         "en", "2026-02-06T10:00:00Z", "2026-02-06T10:00:00Z")
    )
    await test_db.commit()

    with patch("docbot.calendar_service.google_calendar_client") as mock_client:
        result = await cancel_appointment_event(test_db, "appt-no-event")

        assert result is True
        mock_client.delete_event.assert_not_called()
