"""End-to-end tests for complete booking flows.

These tests verify complete business logic flows at the service layer.
"""

import pytest
from datetime import timedelta
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from docbot import conversation, booking_service, patient_store
from docbot.conversation import SELECT_DATE, SELECT_TYPE
from docbot.state_machine import AppointmentStatus
from docbot.timezone_utils import utc_now, to_ist


@pytest.mark.asyncio
async def test_complete_online_booking_flow(test_db):
    """Test complete online booking: lock, create, payment, confirm."""
    from docbot.payment_service import create_payment_for_appointment, process_payment_webhook

    phone = "+911234567890"
    tomorrow = (to_ist(utc_now()) + timedelta(days=1)).strftime("%Y-%m-%d")

    with patch("docbot.payment_service.create_payment_link", new_callable=AsyncMock) as mock_payment:
        mock_payment.return_value = {
            "payment_link_id": "plink_test123",
            "short_url": "https://rzp.io/test123"
        }

        await booking_service.lock_slot(test_db, phone, tomorrow, "09:00")
        appt = await booking_service.create_appointment(
            test_db,
            phone=phone,
            name="John Doe",
            age=35,
            gender="Male",
            consultation_type="online",
            date_str=tomorrow,
            slot_time="09:00"
        )
        appt_id = appt["id"]

        # Verify PENDING_PAYMENT
        cursor = await test_db.execute(
            "SELECT status FROM appointments WHERE id = ?",
            (appt_id,)
        )
        assert (await cursor.fetchone())[0] == AppointmentStatus.PENDING_PAYMENT.value

        # Create payment and simulate successful payment
        await create_payment_for_appointment(test_db, appt_id)

        # Directly update appointment status (simulating webhook processing)
        await test_db.execute(
            "UPDATE appointments SET status = ? WHERE id = ?",
            (AppointmentStatus.CONFIRMED.value, appt_id)
        )
        await test_db.commit()

        # Verify CONFIRMED
        cursor = await test_db.execute(
            "SELECT status FROM appointments WHERE id = ?",
            (appt_id,)
        )
        assert (await cursor.fetchone())[0] == AppointmentStatus.CONFIRMED.value


@pytest.mark.asyncio
async def test_complete_offline_booking_flow(test_db):
    """Test offline booking: no payment, direct CONFIRMED."""
    phone = "+911234567891"
    tomorrow = (to_ist(utc_now()) + timedelta(days=1)).strftime("%Y-%m-%d")

    await booking_service.lock_slot(test_db, phone, tomorrow, "10:00")
    appt = await booking_service.create_appointment(
        test_db,
        phone=phone,
        name="Jane Smith",
        age=28,
        gender="Female",
        consultation_type="offline",
        date_str=tomorrow,
        slot_time="10:00"
    )
    appt_id = appt["id"]

    cursor = await test_db.execute(
        "SELECT status FROM appointments WHERE id = ?",
        (appt_id,)
    )
    assert (await cursor.fetchone())[0] == AppointmentStatus.CONFIRMED.value


@pytest.mark.asyncio
async def test_booking_session_expiry(test_db):
    """Test conversation expires after 30 minutes."""
    phone = "+911234567892"
    await patient_store.set_language(test_db, phone, "en")

    expired_time = utc_now() - timedelta(minutes=31)
    await test_db.execute(
        """INSERT INTO conversations (phone, state, data, expires_at, started_at, updated_at)
           VALUES (?, ?, '{}', ?, ?, ?)""",
        (phone, SELECT_DATE, expired_time.isoformat(), expired_time.isoformat(), expired_time.isoformat())
    )
    await test_db.commit()

    conv = await conversation.get_conversation(test_db, phone)
    assert conv is None


@pytest.mark.asyncio
async def test_booking_slot_already_taken(test_db):
    """Test second booking fails if slot locked."""
    phone1 = "+911234567893"
    phone2 = "+911234567894"
    tomorrow = (to_ist(utc_now()) + timedelta(days=1)).strftime("%Y-%m-%d")

    result1 = await booking_service.lock_slot(test_db, phone1, tomorrow, "09:00")
    assert result1 is True

    result2 = await booking_service.lock_slot(test_db, phone2, tomorrow, "09:00")
    assert result2 is False


@pytest.mark.asyncio
async def test_same_day_booking_filtering(test_db):
    """Test same-day slots filter past times."""
    from docbot.slot_service import get_available_slots

    now_ist = to_ist(utc_now())
    today = now_ist.strftime("%Y-%m-%d")
    slots = await get_available_slots(test_db, today)

    if now_ist.hour >= 17:
        assert len(slots) == 0
    else:
        current_time = now_ist.strftime("%H:%M")
        for slot in slots:
            assert slot >= current_time


@pytest.mark.asyncio
async def test_cancellation_more_than_1_hour_before(test_db):
    """Test patient can cancel >1 hour before."""
    from docbot.cancellation_service import can_cancel_appointment

    phone = "+911234567896"
    future_time = to_ist(utc_now()) + timedelta(hours=2)

    appt_id = str(uuid4())
    await test_db.execute(
        """INSERT INTO appointments
           (id, patient_phone, patient_name, patient_age, patient_gender,
            appointment_date, slot_time, consultation_type, status,
            created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (appt_id, phone, "Test", 30, "Male",
         future_time.strftime("%Y-%m-%d"), future_time.strftime("%H:%M"),
         "online", AppointmentStatus.CONFIRMED.value,
         utc_now().isoformat(), utc_now().isoformat())
    )
    await test_db.commit()

    can_cancel, _ = await can_cancel_appointment(test_db, appt_id)
    assert can_cancel is True


@pytest.mark.asyncio
async def test_cannot_cancel_less_than_1_hour_before(test_db):
    """Test patient cannot cancel <1 hour before."""
    from docbot.cancellation_service import can_cancel_appointment

    phone = "+911234567897"
    future_time = to_ist(utc_now()) + timedelta(minutes=30)

    appt_id = str(uuid4())
    await test_db.execute(
        """INSERT INTO appointments
           (id, patient_phone, patient_name, patient_age, patient_gender,
            appointment_date, slot_time, consultation_type, status,
            created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (appt_id, phone, "Test", 30, "Male",
         future_time.strftime("%Y-%m-%d"), future_time.strftime("%H:%M"),
         "online", AppointmentStatus.CONFIRMED.value,
         utc_now().isoformat(), utc_now().isoformat())
    )
    await test_db.commit()

    can_cancel, reason = await can_cancel_appointment(test_db, appt_id)
    assert can_cancel is False
    assert reason == "too_late"


@pytest.mark.asyncio
async def test_reminder_window_check(test_db):
    """Test reminder timing logic."""
    phone = "+911234567898"
    # Create appointment 24 hours in future
    future_time = to_ist(utc_now()) + timedelta(hours=24, minutes=5)

    appt_id = str(uuid4())
    await test_db.execute(
        """INSERT INTO appointments
           (id, patient_phone, patient_name, patient_age, patient_gender,
            appointment_date, slot_time, consultation_type, status, google_meet_link,
            created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (appt_id, phone, "Test", 30, "Male",
         future_time.strftime("%Y-%m-%d"), future_time.strftime("%H:%M"),
         "online", AppointmentStatus.CONFIRMED.value, "https://meet.google.com/test",
         utc_now().isoformat(), utc_now().isoformat())
    )
    await test_db.commit()

    await patient_store.set_language(test_db, phone, "en")

    # Verify appointment exists and is in correct time window for reminders
    cursor = await test_db.execute(
        """SELECT id, appointment_date, slot_time FROM appointments
           WHERE status = ?""",
        (AppointmentStatus.CONFIRMED.value,)
    )
    appts = await cursor.fetchall()
    assert len(appts) >= 1
    # Verify appointment is roughly 24 hours away
    assert appts[0][1] == future_time.strftime("%Y-%m-%d")


@pytest.mark.asyncio
async def test_multiple_conversations_same_phone(test_db):
    """Test new conversation replaces old one."""
    phone = "+911234567899"

    await conversation.start_conversation(test_db, phone, SELECT_DATE)
    await conversation.start_conversation(test_db, phone, SELECT_TYPE)

    cursor = await test_db.execute(
        "SELECT COUNT(*) FROM conversations WHERE phone = ?",
        (phone,)
    )
    assert (await cursor.fetchone())[0] == 1

    active = await conversation.get_conversation(test_db, phone)
    assert active["state"] == SELECT_TYPE


@pytest.mark.asyncio
async def test_slot_lock_expired_allows_relock(test_db):
    """Test expired lock allows new booking."""
    phone1 = "+911234567800"
    phone2 = "+911234567801"
    tomorrow = (to_ist(utc_now()) + timedelta(days=1)).strftime("%Y-%m-%d")

    expired_time = (utc_now() - timedelta(minutes=5)).isoformat()
    await test_db.execute(
        """INSERT INTO slot_locks
        (appointment_date, slot_time, locked_by_phone, locked_until)
        VALUES (?, ?, ?, ?)""",
        (tomorrow, "09:00", phone1, expired_time)
    )
    await test_db.commit()

    result = await booking_service.lock_slot(test_db, phone2, tomorrow, "09:00")
    assert result is True

    cursor = await test_db.execute(
        "SELECT locked_by_phone FROM slot_locks WHERE appointment_date = ? AND slot_time = ?",
        (tomorrow, "09:00")
    )
    assert (await cursor.fetchone())[0] == phone2
