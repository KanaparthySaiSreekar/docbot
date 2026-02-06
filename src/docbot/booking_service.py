"""Booking service - slot locking and appointment creation."""


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
    # Stub - will implement in GREEN phase
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
    # Stub - will implement in GREEN phase
    pass


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
    # Stub - will implement in GREEN phase
    return {}


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
    # Stub - will implement in GREEN phase
    return 0
