"""Tests for slot availability service (TDD)."""

import pytest
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo

from docbot.config import ScheduleConfig
from docbot import slot_service
from docbot.timezone_utils import utc_now, ist_now, to_utc


IST = ZoneInfo("Asia/Kolkata")


@pytest.mark.asyncio
async def test_generate_slots_from_schedule():
    """Generate slots from schedule config (09:00-17:00, break 13:00-14:00, 15-min slots)."""
    schedule = ScheduleConfig(
        start_time="09:00",
        end_time="17:00",
        break_start="13:00",
        break_end="14:00",
        slot_duration_minutes=15
    )

    slots = slot_service.generate_slots(schedule)

    # Should have slots from 09:00 to 16:45
    assert "09:00" in slots
    assert "09:15" in slots
    assert "12:45" in slots  # Last before break
    assert "14:00" in slots  # First after break
    assert "16:45" in slots  # Last slot

    # Should NOT have 13:00-13:45 (break period)
    assert "13:00" not in slots
    assert "13:15" not in slots
    assert "13:30" not in slots
    assert "13:45" not in slots

    # Should NOT have 17:00 (end time is exclusive)
    assert "17:00" not in slots

    # Slots should be sorted
    assert slots == sorted(slots)


@pytest.mark.asyncio
async def test_generate_slots_excludes_break():
    """Verify no slot falls within break_start to break_end range."""
    schedule = ScheduleConfig(
        start_time="10:00",
        end_time="16:00",
        break_start="12:00",
        break_end="13:00",
        slot_duration_minutes=30
    )

    slots = slot_service.generate_slots(schedule)

    # Verify break slots are excluded
    for slot in slots:
        hour, minute = map(int, slot.split(":"))
        slot_minutes = hour * 60 + minute
        break_start_minutes = 12 * 60
        break_end_minutes = 13 * 60

        # Slot should not be in break period
        assert not (break_start_minutes <= slot_minutes < break_end_minutes)


@pytest.mark.asyncio
async def test_get_available_slots_excludes_booked(test_db):
    """Given 2 booked appointments, get_available_slots excludes them."""
    schedule = ScheduleConfig(
        start_time="09:00",
        end_time="12:00",
        break_start="",
        break_end="",
        slot_duration_minutes=30
    )

    # Book 2 appointments
    date_str = "2026-02-10"
    await test_db.execute(
        """INSERT INTO appointments
        (id, patient_phone, patient_name, patient_age, patient_gender,
         consultation_type, appointment_date, slot_time, status,
         created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        ("appt1", "+911234567890", "Test", 30, "Male", "online",
         date_str, "09:00", "CONFIRMED", utc_now().isoformat(), utc_now().isoformat())
    )
    await test_db.execute(
        """INSERT INTO appointments
        (id, patient_phone, patient_name, patient_age, patient_gender,
         consultation_type, appointment_date, slot_time, status,
         created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        ("appt2", "+911234567891", "Test2", 25, "Female", "offline",
         date_str, "10:00", "CONFIRMED", utc_now().isoformat(), utc_now().isoformat())
    )
    await test_db.commit()

    available = await slot_service.get_available_slots(test_db, date_str, schedule)

    # Should have 09:30, 10:30, 11:00, 11:30 but NOT 09:00 or 10:00
    assert "09:00" not in available
    assert "10:00" not in available
    assert "09:30" in available
    assert "10:30" in available
    assert "11:00" in available
    assert "11:30" in available


@pytest.mark.asyncio
async def test_get_available_slots_excludes_locked(test_db):
    """Given a soft-locked slot (non-expired), it's excluded from available slots."""
    schedule = ScheduleConfig(
        start_time="09:00",
        end_time="11:00",
        break_start="",
        break_end="",
        slot_duration_minutes=30
    )

    date_str = "2026-02-10"
    # Lock a slot (expires in 10 minutes)
    locked_until = (utc_now() + timedelta(minutes=10)).isoformat()
    await test_db.execute(
        """INSERT INTO slot_locks
        (appointment_date, slot_time, locked_by_phone, locked_until)
        VALUES (?, ?, ?, ?)""",
        (date_str, "09:30", "+911234567890", locked_until)
    )
    await test_db.commit()

    available = await slot_service.get_available_slots(test_db, date_str, schedule)

    # Should exclude the locked slot
    assert "09:00" in available
    assert "09:30" not in available  # Locked
    assert "10:00" in available
    assert "10:30" in available


@pytest.mark.asyncio
async def test_get_available_slots_includes_expired_locks(test_db):
    """Given an expired soft-lock, that slot IS available (lock expired)."""
    schedule = ScheduleConfig(
        start_time="09:00",
        end_time="11:00",
        break_start="",
        break_end="",
        slot_duration_minutes=30
    )

    date_str = "2026-02-10"
    # Lock a slot but expired (1 minute ago)
    locked_until = (utc_now() - timedelta(minutes=1)).isoformat()
    await test_db.execute(
        """INSERT INTO slot_locks
        (appointment_date, slot_time, locked_by_phone, locked_until)
        VALUES (?, ?, ?, ?)""",
        (date_str, "09:30", "+911234567890", locked_until)
    )
    await test_db.commit()

    available = await slot_service.get_available_slots(test_db, date_str, schedule)

    # Should include the slot since lock expired
    assert "09:30" in available


@pytest.mark.asyncio
async def test_same_day_excludes_past_slots(test_db):
    """For today's date, slots before current IST time are excluded."""
    schedule = ScheduleConfig(
        start_time="00:00",
        end_time="23:59",
        break_start="",
        break_end="",
        slot_duration_minutes=60
    )

    # Get current IST time
    now_ist = ist_now()
    today_str = now_ist.strftime("%Y-%m-%d")
    current_hour = now_ist.hour

    available = await slot_service.get_available_slots(test_db, today_str, schedule)

    # Slots before current hour should be excluded
    if current_hour > 0:
        past_slot = f"{current_hour - 1:02d}:00"
        assert past_slot not in available

    # Current and future slots should be available
    future_slot = f"{min(current_hour + 1, 23):02d}:00"
    assert future_slot in available


@pytest.mark.asyncio
async def test_max_appointments_per_day(test_db):
    """When 50 appointments exist for a date, get_available_slots returns empty list."""
    schedule = ScheduleConfig(
        start_time="09:00",
        end_time="18:00",
        break_start="",
        break_end="",
        slot_duration_minutes=15,
        max_appointments_per_day=50
    )

    date_str = "2026-02-10"

    # Create 50 appointments
    for i in range(50):
        hour = 9 + (i * 15) // 60
        minute = (i * 15) % 60
        slot = f"{hour:02d}:{minute:02d}"

        await test_db.execute(
            """INSERT INTO appointments
            (id, patient_phone, patient_name, patient_age, patient_gender,
             consultation_type, appointment_date, slot_time, status,
             created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (f"appt{i}", f"+9112345678{i:02d}", "Test", 30, "Male",
             "online", date_str, slot, "CONFIRMED",
             utc_now().isoformat(), utc_now().isoformat())
        )
    await test_db.commit()

    available = await slot_service.get_available_slots(test_db, date_str, schedule)

    # Should return empty - max reached
    assert available == []


@pytest.mark.asyncio
async def test_get_available_dates(test_db):
    """Returns list of dates (next 7 days) with at least 1 available slot, excluding non-working days."""
    schedule = ScheduleConfig(
        working_days=[0, 1, 2, 3, 4, 5],  # Monday-Saturday
        start_time="09:00",
        end_time="11:00",
        break_start="",
        break_end="",
        slot_duration_minutes=30
    )

    dates = await slot_service.get_available_dates(test_db, days_ahead=7, schedule=schedule)

    # Should return list of date strings
    assert isinstance(dates, list)
    assert len(dates) > 0

    # Each date should be a valid YYYY-MM-DD string
    for date_str in dates:
        parts = date_str.split("-")
        assert len(parts) == 3
        year, month, day = map(int, parts)
        assert 2020 <= year <= 2030
        assert 1 <= month <= 12
        assert 1 <= day <= 31

    # Dates should be sorted
    assert dates == sorted(dates)

    # Should only include working days (Monday-Saturday, not Sunday)
    for date_str in dates:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
        # Sunday is weekday 6
        assert date_obj.weekday() != 6
