"""Slot availability service - generates and filters appointment slots."""

from docbot.config import ScheduleConfig


def generate_slots(schedule: ScheduleConfig) -> list[str]:
    """
    Generate all possible slot times from schedule config.

    Args:
        schedule: Schedule configuration with working hours and breaks

    Returns:
        list[str]: Sorted list of "HH:MM" strings (break period excluded)
    """
    # Stub - will implement in GREEN phase
    return []


async def get_available_slots(db, date_str: str, schedule: ScheduleConfig | None = None) -> list[str]:
    """
    Get available slots for a specific date.

    Args:
        db: Database connection
        date_str: Date in YYYY-MM-DD format
        schedule: Optional schedule config (uses default if None)

    Returns:
        list[str]: Sorted list of available slot times
    """
    # Stub - will implement in GREEN phase
    return []


async def get_available_dates(db, days_ahead: int = 7, schedule: ScheduleConfig | None = None) -> list[str]:
    """
    Get dates with available slots.

    Args:
        db: Database connection
        days_ahead: Number of days to look ahead
        schedule: Optional schedule config (uses default if None)

    Returns:
        list[str]: Sorted list of "YYYY-MM-DD" strings
    """
    # Stub - will implement in GREEN phase
    return []
