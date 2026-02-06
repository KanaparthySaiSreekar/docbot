"""Tests for refund service."""

import pytest
import pytest_asyncio
from unittest.mock import patch, AsyncMock
from datetime import datetime, timedelta, timezone

from docbot.refund_service import initiate_refund, process_refund_webhook, retry_failed_refunds


@pytest_asyncio.fixture
async def test_db_with_paid_appointment(test_db):
    """Database with a confirmed paid appointment."""
    await test_db.execute(
        """INSERT INTO appointments
           (id, patient_phone, patient_name, patient_age, patient_gender,
            consultation_type, appointment_date, slot_time, status,
            razorpay_payment_id, language, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        ("appt-paid", "+919876543210", "Paid Patient", 30, "Male",
         "online", "2026-02-10", "10:00", "CONFIRMED",
         "pay_razorpay123", "en", "2026-02-06T10:00:00Z", "2026-02-06T10:00:00Z")
    )
    await test_db.execute(
        """INSERT INTO payments
           (id, appointment_id, razorpay_payment_link_id, razorpay_payment_id,
            amount_paise, status, created_at, captured_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        ("pay-db-123", "appt-paid", "plink_123", "pay_razorpay123",
         50000, "CAPTURED", "2026-02-06T10:00:00Z", "2026-02-06T10:05:00Z")
    )
    await test_db.commit()
    return test_db


@pytest.mark.asyncio
async def test_initiate_refund_success(test_db_with_paid_appointment):
    """Test successful refund initiation."""
    with patch("docbot.refund_service._call_razorpay_refund") as mock_refund:
        mock_refund.return_value = {"id": "rfnd_123", "status": "processed"}

        result = await initiate_refund(test_db_with_paid_appointment, "appt-paid")

        assert result is True

        # Verify refund record created
        cursor = await test_db_with_paid_appointment.execute(
            "SELECT status FROM refunds WHERE appointment_id = ?",
            ("appt-paid",)
        )
        row = await cursor.fetchone()
        assert row[0] == "PROCESSED"


@pytest.mark.asyncio
async def test_initiate_refund_api_failure_creates_pending(test_db_with_paid_appointment):
    """Test that API failure creates pending refund for retry."""
    with patch("docbot.refund_service._call_razorpay_refund") as mock_refund:
        mock_refund.return_value = None  # API failed

        result = await initiate_refund(test_db_with_paid_appointment, "appt-paid")

        assert result is False

        # Verify pending refund record created
        cursor = await test_db_with_paid_appointment.execute(
            "SELECT status, retry_count FROM refunds WHERE appointment_id = ?",
            ("appt-paid",)
        )
        row = await cursor.fetchone()
        assert row[0] == "PENDING"
        assert row[1] == 1


@pytest.mark.asyncio
async def test_initiate_refund_no_payment(test_db):
    """Test refund for appointment without payment."""
    await test_db.execute(
        """INSERT INTO appointments
           (id, patient_phone, patient_name, patient_age, patient_gender,
            consultation_type, appointment_date, slot_time, status,
            language, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        ("appt-no-pay", "+919876543210", "No Pay", 30, "Male",
         "offline", "2026-02-10", "11:00", "CONFIRMED",
         "en", "2026-02-06T10:00:00Z", "2026-02-06T10:00:00Z")
    )
    await test_db.commit()

    result = await initiate_refund(test_db, "appt-no-pay")

    # Should succeed (nothing to refund)
    assert result is True


@pytest.mark.asyncio
async def test_retry_failed_refunds(test_db):
    """Test retry mechanism for failed refunds."""
    # Create failed refund
    await test_db.execute(
        """INSERT INTO appointments
           (id, patient_phone, patient_name, patient_age, patient_gender,
            consultation_type, appointment_date, slot_time, status,
            razorpay_payment_id, language, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        ("appt-retry", "+919876543210", "Retry Patient", 30, "Male",
         "online", "2026-02-10", "12:00", "CANCELLED",
         "pay_retry123", "en", "2026-02-06T10:00:00Z", "2026-02-06T10:00:00Z")
    )
    await test_db.execute(
        """INSERT INTO refunds
           (id, appointment_id, razorpay_payment_id, amount_paise,
            status, retry_count, next_retry_at, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        ("rfnd-pending", "appt-retry", "pay_retry123", 50000,
         "PENDING", 1, datetime.now(timezone.utc).isoformat(), "2026-02-06T10:00:00Z")
    )
    await test_db.commit()

    with patch("docbot.refund_service._call_razorpay_refund") as mock_refund:
        mock_refund.return_value = {"id": "rfnd_success", "status": "processed"}

        count = await retry_failed_refunds(test_db)

        assert count == 1

        # Verify refund now processed
        cursor = await test_db.execute(
            "SELECT status FROM refunds WHERE id = ?",
            ("rfnd-pending",)
        )
        row = await cursor.fetchone()
        assert row[0] == "PROCESSED"


@pytest.mark.asyncio
async def test_process_refund_webhook(test_db):
    """Test processing refund.processed webhook."""
    await test_db.execute(
        """INSERT INTO appointments
           (id, patient_phone, patient_name, patient_age, patient_gender,
            consultation_type, appointment_date, slot_time, status,
            razorpay_payment_id, language, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        ("appt-refund-wh", "+919876543210", "Webhook Patient", 30, "Male",
         "online", "2026-02-10", "13:00", "CANCELLED",
         "pay_wh123", "en", "2026-02-06T10:00:00Z", "2026-02-06T10:00:00Z")
    )
    await test_db.execute(
        """INSERT INTO refunds
           (id, appointment_id, razorpay_payment_id, amount_paise,
            status, retry_count, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        ("rfnd-wh", "appt-refund-wh", "pay_wh123", 50000,
         "PENDING", 0, "2026-02-06T10:00:00Z")
    )
    await test_db.commit()

    with patch("docbot.refund_service.verify_webhook_signature", return_value=True):
        result = await process_refund_webhook(
            test_db,
            payload_body=b"{}",
            signature="valid",
            event_type="refund.processed",
            refund_data={"id": "rfnd_api_123", "payment_id": "pay_wh123"}
        )

        assert result is True

        # Verify appointment transitioned to REFUNDED
        cursor = await test_db.execute(
            "SELECT status, razorpay_refund_id FROM appointments WHERE id = ?",
            ("appt-refund-wh",)
        )
        row = await cursor.fetchone()
        assert row[0] == "REFUNDED"
        assert row[1] == "rfnd_api_123"
