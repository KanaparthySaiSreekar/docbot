"""Timezone conversion utilities for UTC/IST handling."""

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

# IST timezone constant
IST = ZoneInfo("Asia/Kolkata")


def utc_now() -> datetime:
    """
    Get current time in UTC.

    Returns:
        datetime: Current time with UTC timezone
    """
    return datetime.now(timezone.utc)


def ist_now() -> datetime:
    """
    Get current time in IST.

    Returns:
        datetime: Current time with IST timezone
    """
    return datetime.now(IST)


def to_ist(utc_dt: datetime) -> datetime:
    """
    Convert UTC datetime to IST.

    Args:
        utc_dt: Datetime in UTC

    Returns:
        datetime: Datetime in IST
    """
    return utc_dt.astimezone(IST)


def utc_to_ist(utc_dt: datetime) -> datetime:
    """
    Convert UTC datetime to IST (alias for to_ist).

    Args:
        utc_dt: Datetime in UTC

    Returns:
        datetime: Datetime in IST
    """
    return to_ist(utc_dt)


def to_utc(ist_dt: datetime) -> datetime:
    """
    Convert IST datetime to UTC.

    Args:
        ist_dt: Datetime in IST

    Returns:
        datetime: Datetime in UTC
    """
    return ist_dt.astimezone(timezone.utc)


def format_ist(utc_dt: datetime) -> str:
    """
    Format UTC datetime as human-readable IST string.

    Args:
        utc_dt: Datetime in UTC

    Returns:
        str: Formatted string like "05 Feb 2026, 8:00 PM IST"
    """
    ist_dt = to_ist(utc_dt)
    # Use %I (with zero-padding) for Windows compatibility
    formatted = ist_dt.strftime("%d %b %Y, %I:%M %p IST")
    # Strip leading zero from hour for cleaner display
    parts = formatted.split(", ")
    time_part = parts[1]
    if time_part[0] == "0":
        time_part = time_part[1:]
    return f"{parts[0]}, {time_part}"


def is_same_day_ist(dt1: datetime, dt2: datetime) -> bool:
    """
    Check if two datetimes fall on the same IST day.

    Args:
        dt1: First datetime
        dt2: Second datetime

    Returns:
        bool: True if both are on same IST day
    """
    ist1 = to_ist(dt1)
    ist2 = to_ist(dt2)
    return ist1.date() == ist2.date()


def slot_to_utc(date_str: str, time_str: str) -> datetime:
    """
    Convert IST slot (date + time) to UTC datetime.

    Args:
        date_str: Date in YYYY-MM-DD format
        time_str: Time in HH:MM format (IST)

    Returns:
        datetime: UTC datetime
    """
    # Parse date and time
    year, month, day = map(int, date_str.split("-"))
    hour, minute = map(int, time_str.split(":"))
    
    # Create IST datetime
    ist_dt = datetime(year, month, day, hour, minute, tzinfo=IST)
    
    # Convert to UTC
    return to_utc(ist_dt)
