"""Booking service - slot locking and appointment creation."""

import uuid
from datetime import timedelta
import aiosqlite

from docbot.timezone_utils import utc_now
from docbot.state_machine import AppointmentStatus


async def cleanup_expired_locks(db, date_str: str | None = None, slot_time: str | None = None) -> int:
    """
    Clean up expired slot locks.

    Args:
        db: Database connection
        date_str: Optional date filter
        slot_time: Optional slot time filter

    Returns:
        int: Number of locks removed
    """
    now_utc = utc_now()

    # Build query with optional filters
    query = "DELETE FROM slot_locks WHERE locked_until < ?"
    params = [now_utc.isoformat()]

    if date_str is not None:
        query += " AND appointment_date = ?"
        params.append(date_str)

    if slot_time is not None:
        query += " AND slot_time = ?"
        params.append(slot_time)

    cursor = await db.execute(query, params)
    await db.commit()

    return cursor.rowcount


async def lock_slot(db, phone: str, date_str: str, slot_time: str, ttl_minutes: int = 10) -> bool:
    """
    Lock a slot for booking.

    Args:
        db: Database connection
        phone: Patient phone number
        date_str: Date in YYYY-MM-DD format
        slot_time: Time in HH:MM format
        ttl_minutes: Lock TTL in minutes (default 10)

    Returns:
        bool: True if lock acquired, False if slot already locked
    """
    # First cleanup expired locks for this specific slot
    await cleanup_expired_locks(db, date_str, slot_time)

    # Calculate lock expiry
    locked_until = (utc_now() + timedelta(minutes=ttl_minutes)).isoformat()

    # Try to insert lock
    try:
        await db.execute(
            """INSERT INTO slot_locks
            (appointment_date, slot_time, locked_by_phone, locked_until)
            VALUES (?, ?, ?, ?)""",
            (date_str, slot_time, phone, locked_until)
        )
        await db.commit()
        return True
    except aiosqlite.IntegrityError:
        # PRIMARY KEY constraint violation - slot already locked
        return False


async def release_lock(db, phone: str, date_str: str, slot_time: str) -> None:
    """
    Release a slot lock.

    Args:
        db: Database connection
        phone: Patient phone number
        date_str: Date in YYYY-MM-DD format
        slot_time: Time in HH:MM format
    """
    await db.execute(
        """DELETE FROM slot_locks
           WHERE appointment_date = ?
           AND slot_time = ?
           AND locked_by_phone = ?""",
        (date_str, slot_time, phone)
    )
    await db.commit()


async def create_appointment(
    db,
    phone: str,
    name: str,
    age: int,
    gender: str,
    consultation_type: str,
    date_str: str,
    slot_time: str,
    language: str = "en"
) -> dict:
    """
    Create an appointment.

    Args:
        db: Database connection
        phone: Patient phone number
        name: Patient name
        age: Patient age
        gender: Patient gender
        consultation_type: 'online' or 'offline'
        date_str: Date in YYYY-MM-DD format
        slot_time: Time in HH:MM format
        language: Language code (default 'en')

    Returns:
        dict: Created appointment

    Raises:
        ValueError: If slot is already booked
    """
    # Check if slot is already booked
    cursor = await db.execute(
        """SELECT id FROM appointments
           WHERE appointment_date = ?
           AND slot_time = ?
           AND status NOT IN ('CANCELLED', 'REFUNDED')""",
        (date_str, slot_time)
    )
    existing = await cursor.fetchone()
    if existing:
        raise ValueError(f"Slot {slot_time} on {date_str} is already booked")

    # Determine initial status
    if consultation_type == "offline":
        status = AppointmentStatus.CONFIRMED.value
    else:  # online
        status = AppointmentStatus.PENDING_PAYMENT.value

    # Generate appointment ID
    appointment_id = str(uuid.uuid4())

    # Get current timestamp
    now = utc_now().isoformat()

    # Insert appointment
    await db.execute(
        """INSERT INTO appointments
        (id, patient_phone, patient_name, patient_age, patient_gender,
         consultation_type, appointment_date, slot_time, status,
         language, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (appointment_id, phone, name, age, gender,
         consultation_type, date_str, slot_time, status,
         language, now, now)
    )

    # Release the soft-lock for this slot
    await release_lock(db, phone, date_str, slot_time)

    await db.commit()

    # Return appointment as dict
    return {
        "id": appointment_id,
        "patient_phone": phone,
        "patient_name": name,
        "patient_age": age,
        "patient_gender": gender,
        "consultation_type": consultation_type,
        "appointment_date": date_str,
        "slot_time": slot_time,
        "status": status,
        "language": language,
        "created_at": now,
        "updated_at": now
    }
