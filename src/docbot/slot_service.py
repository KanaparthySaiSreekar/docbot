"""Slot availability service - generates and filters appointment slots."""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from docbot.config import ScheduleConfig, get_settings
from docbot.timezone_utils import utc_now, ist_now


IST = ZoneInfo("Asia/Kolkata")


def generate_slots(schedule: ScheduleConfig) -> list[str]:
    """
    Generate all possible slot times from schedule config.

    Args:
        schedule: Schedule configuration with working hours and breaks

    Returns:
        list[str]: Sorted list of "HH:MM" strings (break period excluded)
    """
    # Parse start and end times
    start_hour, start_minute = map(int, schedule.start_time.split(":"))
    end_hour, end_minute = map(int, schedule.end_time.split(":"))

    # Convert to minutes since midnight
    start_minutes = start_hour * 60 + start_minute
    end_minutes = end_hour * 60 + end_minute

    # Parse break times (if set)
    break_start_minutes = None
    break_end_minutes = None
    if schedule.break_start and schedule.break_end:
        break_start_hour, break_start_minute = map(int, schedule.break_start.split(":"))
        break_end_hour, break_end_minute = map(int, schedule.break_end.split(":"))
        break_start_minutes = break_start_hour * 60 + break_start_minute
        break_end_minutes = break_end_hour * 60 + break_end_minute

    # Generate slots
    slots = []
    current_minutes = start_minutes

    while current_minutes < end_minutes:
        # Check if slot is in break period
        in_break = False
        if break_start_minutes is not None and break_end_minutes is not None:
            if break_start_minutes <= current_minutes < break_end_minutes:
                in_break = True

        # Add slot if not in break
        if not in_break:
            hour = current_minutes // 60
            minute = current_minutes % 60
            slots.append(f"{hour:02d}:{minute:02d}")

        # Move to next slot
        current_minutes += schedule.slot_duration_minutes

    return sorted(slots)


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
    # Use provided schedule or get from settings
    if schedule is None:
        schedule = get_settings().schedule

    # Generate all possible slots
    all_slots = generate_slots(schedule)

    # Check max appointments per day
    cursor = await db.execute(
        """SELECT COUNT(*) FROM appointments
           WHERE appointment_date = ?
           AND status NOT IN ('CANCELLED', 'REFUNDED')""",
        (date_str,)
    )
    row = await cursor.fetchone()
    appointment_count = row[0] if row else 0

    if appointment_count >= schedule.max_appointments_per_day:
        return []

    # Get booked slots
    cursor = await db.execute(
        """SELECT slot_time FROM appointments
           WHERE appointment_date = ?
           AND status NOT IN ('CANCELLED', 'REFUNDED')""",
        (date_str,)
    )
    booked_rows = await cursor.fetchall()
    booked_slots = {row[0] for row in booked_rows}

    # Get locked slots (non-expired)
    now_utc = utc_now()
    cursor = await db.execute(
        """SELECT slot_time FROM slot_locks
           WHERE appointment_date = ?
           AND locked_until > ?""",
        (date_str, now_utc.isoformat())
    )
    locked_rows = await cursor.fetchall()
    locked_slots = {row[0] for row in locked_rows}

    # Filter out booked and locked slots
    available = [slot for slot in all_slots if slot not in booked_slots and slot not in locked_slots]

    # If date is today, filter out past slots (in IST)
    now_ist = ist_now()
    today_str = now_ist.strftime("%Y-%m-%d")

    if date_str == today_str:
        current_time_str = now_ist.strftime("%H:%M")
        available = [slot for slot in available if slot > current_time_str]

    return sorted(available)


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
    # Use provided schedule or get from settings
    if schedule is None:
        schedule = get_settings().schedule

    # Start from today (IST)
    now_ist = ist_now()
    current_date = now_ist.date()

    available_dates = []

    # Check each day
    for i in range(days_ahead):
        check_date = current_date + timedelta(days=i)

        # Check if working day (weekday is 0=Monday, 6=Sunday)
        if check_date.weekday() not in schedule.working_days:
            continue

        # Check if has available slots
        date_str = check_date.strftime("%Y-%m-%d")
        slots = await get_available_slots(db, date_str, schedule)

        if slots:
            available_dates.append(date_str)

    return sorted(available_dates)
