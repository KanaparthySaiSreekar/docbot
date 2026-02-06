"""Tests for payment service."""

import pytest
import pytest_asyncio
import aiosqlite
from unittest.mock import patch, AsyncMock

from docbot.payment_service import create_payment_for_appointment, process_payment_webhook
from docbot.state_machine import AppointmentStatus
from docbot.timezone_utils import utc_now


@pytest_asyncio.fixture
async def test_db():
    """Create an in-memory test database."""
    db = await aiosqlite.connect(":memory:")

    # Create tables
    await db.execute("""
        CREATE TABLE appointments (
            id TEXT PRIMARY KEY,
            patient_name TEXT NOT NULL,
            patient_phone TEXT NOT NULL,
            status TEXT NOT NULL,
            razorpay_payment_id TEXT,
            razorpay_order_id TEXT,
            updated_at TEXT NOT NULL
        )
    """)

    await db.execute("""
        CREATE TABLE payments (
            id TEXT PRIMARY KEY,
            appointment_id TEXT NOT NULL REFERENCES appointments(id),
            razorpay_payment_link_id TEXT,
            razorpay_payment_id TEXT,
            amount_paise INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'PENDING',
            created_at TEXT NOT NULL,
            captured_at TEXT,
            UNIQUE(appointment_id)
        )
    """)

    await db.execute("""
        CREATE TABLE idempotency_keys (
            event_id TEXT PRIMARY KEY,
            source TEXT NOT NULL,
            processed_at TEXT NOT NULL,
            result TEXT
        )
    """)

    await db.commit()
    yield db
    await db.close()


@pytest.mark.asyncio
async def test_create_payment_for_appointment_success(test_db):
    """Test successful payment creation for PENDING_PAYMENT appointment."""
    # Insert appointment
    await test_db.execute(
        """INSERT INTO appointments (id, patient_name, patient_phone, status, updated_at)
           VALUES (?, ?, ?, ?, ?)""",
        ("appt_123", "Test Patient", "+919876543210", AppointmentStatus.PENDING_PAYMENT.value, utc_now().isoformat())
    )
    await test_db.commit()

    # Mock Razorpay client
    with patch("docbot.payment_service.create_payment_link", new_callable=AsyncMock) as mock_create:
        mock_create.return_value = {
            "payment_link_id": "plink_test123",
            "short_url": "https://rzp.io/l/test123"
        }

        result = await create_payment_for_appointment(test_db, "appt_123")

    assert result is not None
    assert result["payment_link_id"] == "plink_test123"
    assert result["short_url"] == "https://rzp.io/l/test123"

    # Verify payment record created
    cursor = await test_db.execute("SELECT * FROM payments WHERE appointment_id = ?", ("appt_123",))
    row = await cursor.fetchone()
    assert row is not None


@pytest.mark.asyncio
async def test_create_payment_for_appointment_already_exists(test_db):
    """Test returns existing payment link if payment already exists."""
    # Insert appointment and payment
    await test_db.execute(
        """INSERT INTO appointments (id, patient_name, patient_phone, status, updated_at)
           VALUES (?, ?, ?, ?, ?)""",
        ("appt_123", "Test Patient", "+919876543210", AppointmentStatus.PENDING_PAYMENT.value, utc_now().isoformat())
    )
    await test_db.execute(
        """INSERT INTO payments (id, appointment_id, razorpay_payment_link_id, amount_paise, status, created_at)
           VALUES (?, ?, ?, ?, ?, ?)""",
        ("pay_123", "appt_123", "plink_existing", 50000, "PENDING", utc_now().isoformat())
    )
    await test_db.commit()

    result = await create_payment_for_appointment(test_db, "appt_123")

    assert result is not None
    assert result["payment_link_id"] == "plink_existing"


@pytest.mark.asyncio
async def test_create_payment_for_appointment_wrong_status(test_db):
    """Test raises ValueError if appointment not in PENDING_PAYMENT status."""
    # Insert CONFIRMED appointment
    await test_db.execute(
        """INSERT INTO appointments (id, patient_name, patient_phone, status, updated_at)
           VALUES (?, ?, ?, ?, ?)""",
        ("appt_123", "Test Patient", "+919876543210", AppointmentStatus.CONFIRMED.value, utc_now().isoformat())
    )
    await test_db.commit()

    with pytest.raises(ValueError, match="expected PENDING_PAYMENT"):
        await create_payment_for_appointment(test_db, "appt_123")


@pytest.mark.asyncio
async def test_process_payment_webhook_success(test_db):
    """Test successful payment webhook processing."""
    # Insert appointment and payment
    await test_db.execute(
        """INSERT INTO appointments (id, patient_name, patient_phone, status, updated_at)
           VALUES (?, ?, ?, ?, ?)""",
        ("appt_123", "Test Patient", "+919876543210", AppointmentStatus.PENDING_PAYMENT.value, utc_now().isoformat())
    )
    await test_db.execute(
        """INSERT INTO payments (id, appointment_id, razorpay_payment_link_id, amount_paise, status, created_at)
           VALUES (?, ?, ?, ?, ?, ?)""",
        ("pay_123", "appt_123", "plink_123", 50000, "PENDING", utc_now().isoformat())
    )
    await test_db.commit()

    payload_body = b'{"event":"payment.captured"}'
    signature = "valid_signature"

    with patch("docbot.payment_service.verify_webhook_signature", return_value=True):
        result = await process_payment_webhook(
            test_db,
            payload_body,
            signature,
            "payment.captured",
            {"id": "pay_razorpay_123", "payment_link_id": "plink_123"}
        )

    assert result is True

    # Verify payment updated to CAPTURED
    cursor = await test_db.execute("SELECT status FROM payments WHERE id = ?", ("pay_123",))
    row = await cursor.fetchone()
    assert row[0] == "CAPTURED"

    # Verify appointment transitioned to CONFIRMED
    cursor = await test_db.execute("SELECT status FROM appointments WHERE id = ?", ("appt_123",))
    row = await cursor.fetchone()
    assert row[0] == AppointmentStatus.CONFIRMED.value


@pytest.mark.asyncio
async def test_process_payment_webhook_idempotent(test_db):
    """Test duplicate webhook only processes once."""
    # Insert appointment and payment
    await test_db.execute(
        """INSERT INTO appointments (id, patient_name, patient_phone, status, updated_at)
           VALUES (?, ?, ?, ?, ?)""",
        ("appt_123", "Test Patient", "+919876543210", AppointmentStatus.PENDING_PAYMENT.value, utc_now().isoformat())
    )
    await test_db.execute(
        """INSERT INTO payments (id, appointment_id, razorpay_payment_link_id, amount_paise, status, created_at)
           VALUES (?, ?, ?, ?, ?, ?)""",
        ("pay_123", "appt_123", "plink_123", 50000, "PENDING", utc_now().isoformat())
    )
    await test_db.commit()

    payload_body = b'{"event":"payment.captured"}'
    signature = "valid_signature"
    payment_data = {"id": "pay_razorpay_123", "payment_link_id": "plink_123"}

    with patch("docbot.payment_service.verify_webhook_signature", return_value=True):
        # First webhook
        result1 = await process_payment_webhook(
            test_db, payload_body, signature, "payment.captured", payment_data
        )
        assert result1 is True

        # Second webhook (duplicate)
        result2 = await process_payment_webhook(
            test_db, payload_body, signature, "payment.captured", payment_data
        )
        assert result2 is True

    # Verify idempotency record exists
    cursor = await test_db.execute(
        "SELECT COUNT(*) FROM idempotency_keys WHERE event_id = ?",
        ("razorpay:pay_razorpay_123:payment.captured",)
    )
    count = (await cursor.fetchone())[0]
    assert count == 1


@pytest.mark.asyncio
async def test_process_payment_webhook_invalid_signature(test_db):
    """Test invalid signature returns False without updating."""
    payload_body = b'{"event":"payment.captured"}'
    signature = "invalid_signature"

    with patch("docbot.payment_service.verify_webhook_signature", return_value=False):
        result = await process_payment_webhook(
            test_db,
            payload_body,
            signature,
            "payment.captured",
            {"id": "pay_123", "payment_link_id": "plink_123"}
        )

    assert result is False


@pytest.mark.asyncio
async def test_process_payment_webhook_payment_not_found(test_db):
    """Test missing payment record returns False."""
    payload_body = b'{"event":"payment.captured"}'
    signature = "valid_signature"

    with patch("docbot.payment_service.verify_webhook_signature", return_value=True):
        result = await process_payment_webhook(
            test_db,
            payload_body,
            signature,
            "payment.captured",
            {"id": "pay_razorpay_123", "payment_link_id": "plink_nonexistent"}
        )

    assert result is False
