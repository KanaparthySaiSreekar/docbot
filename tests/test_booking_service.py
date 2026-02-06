"""Tests for booking service (TDD)."""

import pytest
from datetime import timedelta
import uuid

from docbot import booking_service
from docbot.timezone_utils import utc_now
from docbot.state_machine import AppointmentStatus


@pytest.mark.asyncio
async def test_lock_slot_success(test_db):
    """lock_slot for an available slot creates entry with 10-min expiry. Returns True."""
    phone = "+911234567890"
    date_str = "2026-02-10"
    slot_time = "09:00"

    result = await booking_service.lock_slot(test_db, phone, date_str, slot_time)

    assert result is True

    # Verify lock exists in database
    cursor = await test_db.execute(
        """SELECT locked_by_phone, locked_until FROM slot_locks
           WHERE appointment_date = ? AND slot_time = ?""",
        (date_str, slot_time)
    )
    row = await cursor.fetchone()
    assert row is not None
    assert row[0] == phone

    # Verify expiry is approximately 10 minutes from now
    from datetime import datetime
    locked_until = datetime.fromisoformat(row[1])
    now = utc_now()
    diff = (locked_until - now).total_seconds()
    assert 590 <= diff <= 610  # Within 10 seconds of 10 minutes


@pytest.mark.asyncio
async def test_lock_slot_already_locked(test_db):
    """lock_slot for a slot already locked by another phone returns False (PRIMARY KEY constraint)."""
    date_str = "2026-02-10"
    slot_time = "09:00"
    phone1 = "+911234567890"
    phone2 = "+911234567891"

    # First lock succeeds
    result1 = await booking_service.lock_slot(test_db, phone1, date_str, slot_time)
    assert result1 is True

    # Second lock by different phone fails
    result2 = await booking_service.lock_slot(test_db, phone2, date_str, slot_time)
    assert result2 is False


@pytest.mark.asyncio
async def test_lock_slot_expired_lock_allows_relock(test_db):
    """If an expired lock exists, lock_slot cleans it up and creates new lock. Returns True."""
    date_str = "2026-02-10"
    slot_time = "09:00"
    phone1 = "+911234567890"
    phone2 = "+911234567891"

    # Create expired lock
    expired_time = (utc_now() - timedelta(minutes=5)).isoformat()
    await test_db.execute(
        """INSERT INTO slot_locks
        (appointment_date, slot_time, locked_by_phone, locked_until)
        VALUES (?, ?, ?, ?)""",
        (date_str, slot_time, phone1, expired_time)
    )
    await test_db.commit()

    # New lock should succeed (expired lock cleaned up)
    result = await booking_service.lock_slot(test_db, phone2, date_str, slot_time)
    assert result is True

    # Verify new lock exists
    cursor = await test_db.execute(
        """SELECT locked_by_phone FROM slot_locks
           WHERE appointment_date = ? AND slot_time = ?""",
        (date_str, slot_time)
    )
    row = await cursor.fetchone()
    assert row[0] == phone2


@pytest.mark.asyncio
async def test_release_lock(test_db):
    """release_lock removes the slot_lock entry for a phone+date+time."""
    phone = "+911234567890"
    date_str = "2026-02-10"
    slot_time = "09:00"

    # Create lock
    locked_until = (utc_now() + timedelta(minutes=10)).isoformat()
    await test_db.execute(
        """INSERT INTO slot_locks
        (appointment_date, slot_time, locked_by_phone, locked_until)
        VALUES (?, ?, ?, ?)""",
        (date_str, slot_time, phone, locked_until)
    )
    await test_db.commit()

    # Release lock
    await booking_service.release_lock(test_db, phone, date_str, slot_time)

    # Verify lock removed
    cursor = await test_db.execute(
        """SELECT * FROM slot_locks
           WHERE appointment_date = ? AND slot_time = ?""",
        (date_str, slot_time)
    )
    row = await cursor.fetchone()
    assert row is None


@pytest.mark.asyncio
async def test_create_appointment_offline(test_db):
    """create_appointment with consultation_type='offline' creates appointment with status 'CONFIRMED'."""
    appointment = await booking_service.create_appointment(
        db=test_db,
        phone="+911234567890",
        name="Test Patient",
        age=30,
        gender="Male",
        consultation_type="offline",
        date_str="2026-02-10",
        slot_time="09:00",
        language="en"
    )

    # Verify returned appointment
    assert appointment["patient_phone"] == "+911234567890"
    assert appointment["patient_name"] == "Test Patient"
    assert appointment["status"] == "CONFIRMED"
    assert appointment["consultation_type"] == "offline"

    # Verify in database
    cursor = await test_db.execute(
        """SELECT status, consultation_type FROM appointments WHERE id = ?""",
        (appointment["id"],)
    )
    row = await cursor.fetchone()
    assert row[0] == "CONFIRMED"
    assert row[1] == "offline"


@pytest.mark.asyncio
async def test_create_appointment_online(test_db):
    """create_appointment with consultation_type='online' creates appointment with status 'PENDING_PAYMENT'."""
    appointment = await booking_service.create_appointment(
        db=test_db,
        phone="+911234567890",
        name="Test Patient",
        age=30,
        gender="Male",
        consultation_type="online",
        date_str="2026-02-10",
        slot_time="09:00",
        language="en"
    )

    # Verify returned appointment
    assert appointment["status"] == "PENDING_PAYMENT"
    assert appointment["consultation_type"] == "online"

    # Verify in database
    cursor = await test_db.execute(
        """SELECT status FROM appointments WHERE id = ?""",
        (appointment["id"],)
    )
    row = await cursor.fetchone()
    assert row[0] == "PENDING_PAYMENT"


@pytest.mark.asyncio
async def test_create_appointment_releases_lock(test_db):
    """After creating appointment, the soft-lock for that slot is released."""
    phone = "+911234567890"
    date_str = "2026-02-10"
    slot_time = "09:00"

    # Create lock
    locked_until = (utc_now() + timedelta(minutes=10)).isoformat()
    await test_db.execute(
        """INSERT INTO slot_locks
        (appointment_date, slot_time, locked_by_phone, locked_until)
        VALUES (?, ?, ?, ?)""",
        (date_str, slot_time, phone, locked_until)
    )
    await test_db.commit()

    # Create appointment
    await booking_service.create_appointment(
        db=test_db,
        phone=phone,
        name="Test",
        age=30,
        gender="Male",
        consultation_type="offline",
        date_str=date_str,
        slot_time=slot_time
    )

    # Verify lock released
    cursor = await test_db.execute(
        """SELECT * FROM slot_locks WHERE appointment_date = ? AND slot_time = ?""",
        (date_str, slot_time)
    )
    row = await cursor.fetchone()
    assert row is None


@pytest.mark.asyncio
async def test_create_appointment_duplicate_slot_fails(test_db):
    """Creating appointment for an already-booked slot raises ValueError."""
    date_str = "2026-02-10"
    slot_time = "09:00"

    # Create first appointment
    await booking_service.create_appointment(
        db=test_db,
        phone="+911234567890",
        name="Test1",
        age=30,
        gender="Male",
        consultation_type="offline",
        date_str=date_str,
        slot_time=slot_time
    )

    # Attempt to create second appointment for same slot
    with pytest.raises(ValueError, match="already booked"):
        await booking_service.create_appointment(
            db=test_db,
            phone="+911234567891",
            name="Test2",
            age=25,
            gender="Female",
            consultation_type="online",
            date_str=date_str,
            slot_time=slot_time
        )


@pytest.mark.asyncio
async def test_cleanup_expired_locks(test_db):
    """cleanup_expired_locks removes locks past their locked_until time. Returns count removed."""
    # Create 2 expired locks and 1 active lock
    date_str = "2026-02-10"
    expired_time = (utc_now() - timedelta(minutes=5)).isoformat()
    active_time = (utc_now() + timedelta(minutes=5)).isoformat()

    await test_db.execute(
        """INSERT INTO slot_locks VALUES (?, ?, ?, ?)""",
        (date_str, "09:00", "+911111111111", expired_time)
    )
    await test_db.execute(
        """INSERT INTO slot_locks VALUES (?, ?, ?, ?)""",
        (date_str, "09:30", "+912222222222", expired_time)
    )
    await test_db.execute(
        """INSERT INTO slot_locks VALUES (?, ?, ?, ?)""",
        (date_str, "10:00", "+913333333333", active_time)
    )
    await test_db.commit()

    # Cleanup
    count = await booking_service.cleanup_expired_locks(test_db)

    # Should remove 2 expired locks
    assert count == 2

    # Verify only active lock remains
    cursor = await test_db.execute("SELECT COUNT(*) FROM slot_locks")
    row = await cursor.fetchone()
    assert row[0] == 1
