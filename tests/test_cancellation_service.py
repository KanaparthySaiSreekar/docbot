"""Tests for cancellation service."""

import pytest
import pytest_asyncio
from unittest.mock import patch, AsyncMock
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from docbot.cancellation_service import can_cancel_appointment, cancel_appointment


@pytest_asyncio.fixture
async def test_db_with_confirmed_online(test_db):
    """Database with confirmed online appointment."""
    # Future appointment (>1 hour away)
    future_date = (datetime.now(ZoneInfo("Asia/Kolkata")) + timedelta(days=1)).strftime("%Y-%m-%d")

    await test_db.execute(
        """INSERT INTO appointments
           (id, patient_phone, patient_name, patient_age, patient_gender,
            consultation_type, appointment_date, slot_time, status,
            razorpay_payment_id, language, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        ("appt-cancel-test", "+919876543210", "Cancel Test", 30, "Male",
         "online", future_date, "10:00", "CONFIRMED",
         "pay_123", "en", "2026-02-06T10:00:00Z", "2026-02-06T10:00:00Z")
    )
    await test_db.commit()
    return test_db


@pytest.mark.asyncio
async def test_can_cancel_future_appointment(test_db_with_confirmed_online):
    """Test that future appointment can be cancelled."""
    can, reason = await can_cancel_appointment(test_db_with_confirmed_online, "appt-cancel-test")
    assert can is True
    assert reason == "ok"


@pytest.mark.asyncio
async def test_cannot_cancel_imminent_appointment(test_db):
    """Test that appointment <1 hour away cannot be cancelled."""
    # Appointment in 30 minutes
    now = datetime.now(ZoneInfo("Asia/Kolkata"))
    soon = now + timedelta(minutes=30)

    await test_db.execute(
        """INSERT INTO appointments
           (id, patient_phone, patient_name, patient_age, patient_gender,
            consultation_type, appointment_date, slot_time, status,
            language, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        ("appt-soon", "+919876543210", "Soon", 30, "Male",
         "online", soon.strftime("%Y-%m-%d"), soon.strftime("%H:%M"), "CONFIRMED",
         "en", "2026-02-06T10:00:00Z", "2026-02-06T10:00:00Z")
    )
    await test_db.commit()

    can, reason = await can_cancel_appointment(test_db, "appt-soon")
    assert can is False
    assert reason == "too_late"


@pytest.mark.asyncio
async def test_cannot_cancel_already_cancelled(test_db):
    """Test that cancelled appointment cannot be cancelled again."""
    await test_db.execute(
        """INSERT INTO appointments
           (id, patient_phone, patient_name, patient_age, patient_gender,
            consultation_type, appointment_date, slot_time, status,
            language, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        ("appt-already", "+919876543210", "Already", 30, "Male",
         "online", "2026-02-10", "10:00", "CANCELLED",
         "en", "2026-02-06T10:00:00Z", "2026-02-06T10:00:00Z")
    )
    await test_db.commit()

    can, reason = await can_cancel_appointment(test_db, "appt-already")
    assert can is False
    assert reason == "already_cancelled"


@pytest.mark.asyncio
async def test_cancel_appointment_online_with_refund(test_db_with_confirmed_online):
    """Test full cancellation flow with refund."""
    with patch("docbot.cancellation_service.initiate_refund") as mock_refund, \
         patch("docbot.cancellation_service.cancel_appointment_event") as mock_cal:
        mock_refund.return_value = True
        mock_cal.return_value = True

        result = await cancel_appointment(test_db_with_confirmed_online, "appt-cancel-test")

        assert result["status"] == "cancelled"
        assert result["refund_status"] == "processed"
        assert result["calendar_status"] == "deleted"

        mock_refund.assert_called_once()
        mock_cal.assert_called_once()


@pytest.mark.asyncio
async def test_cancel_appointment_offline_no_refund(test_db):
    """Test offline cancellation (no refund needed)."""
    future_date = (datetime.now(ZoneInfo("Asia/Kolkata")) + timedelta(days=1)).strftime("%Y-%m-%d")

    await test_db.execute(
        """INSERT INTO appointments
           (id, patient_phone, patient_name, patient_age, patient_gender,
            consultation_type, appointment_date, slot_time, status,
            language, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        ("appt-offline-cancel", "+919876543210", "Offline Cancel", 30, "Male",
         "offline", future_date, "11:00", "CONFIRMED",
         "en", "2026-02-06T10:00:00Z", "2026-02-06T10:00:00Z")
    )
    await test_db.commit()

    with patch("docbot.cancellation_service.initiate_refund") as mock_refund, \
         patch("docbot.cancellation_service.cancel_appointment_event") as mock_cal:
        mock_cal.return_value = True

        result = await cancel_appointment(test_db, "appt-offline-cancel")

        assert result["status"] == "cancelled"
        assert result["refund_status"] is None  # No refund for offline
        mock_refund.assert_not_called()
