"""Calendar service for appointment event management."""

from datetime import datetime
from zoneinfo import ZoneInfo

from docbot import google_calendar_client
from docbot.config import get_settings
from docbot.timezone_utils import IST
from docbot.alerts import log_alert
import logging

logger = logging.getLogger(__name__)


async def create_appointment_event(
    db,
    appointment_id: str,
    retry_count: int = 0
) -> dict | None:
    """
    Create a Google Calendar event for an appointment.

    Args:
        db: Database connection
        appointment_id: Appointment UUID
        retry_count: Number of retry attempts (for failure tracking)

    Returns:
        dict with event_id, meet_link (for online) on success
        None on failure (logs alert for retry)
    """
    # Fetch appointment
    cursor = await db.execute(
        """SELECT id, patient_name, patient_phone, consultation_type,
                  appointment_date, slot_time, status, google_calendar_event_id
           FROM appointments WHERE id = ?""",
        (appointment_id,)
    )
    row = await cursor.fetchone()

    if not row:
        logger.error(f"Appointment not found: {appointment_id}")
        return None

    (appt_id, name, phone, consult_type, date_str, slot_time,
     status, existing_event_id) = row

    # Skip if event already exists
    if existing_event_id:
        logger.info(f"Calendar event already exists for appointment: {appointment_id}")
        cursor = await db.execute(
            "SELECT google_meet_link FROM appointments WHERE id = ?",
            (appointment_id,)
        )
        meet_row = await cursor.fetchone()
        return {
            "event_id": existing_event_id,
            "meet_link": meet_row[0] if meet_row else None
        }

    settings = get_settings()

    # Build event details
    is_online = consult_type == "online"

    summary = f"{'Online' if is_online else 'Offline'} Consultation - {name}"
    description = f"""Patient: {name}
Phone: {phone}
Type: {consult_type.title()}
Appointment ID: {appointment_id}

{'Google Meet link will be available in this event.' if is_online else f'Location: {settings.clinic.address}'}
"""

    # Parse appointment datetime
    hour, minute = map(int, slot_time.split(":"))
    year, month, day = map(int, date_str.split("-"))
    start_time = datetime(year, month, day, hour, minute, tzinfo=IST)

    # Create event
    result = await google_calendar_client.create_event(
        summary=summary,
        description=description,
        start_time=start_time,
        duration_minutes=15,
        location=None if is_online else settings.clinic.address,
        add_meet_link=is_online
    )

    if not result:
        # Log for retry mechanism
        log_alert("ERROR", "calendar_event_creation_failed",
                  "Failed to create calendar event for appointment",
                  {
                      "appointment_id": appointment_id,
                      "retry_count": retry_count
                  })
        return None

    # Update appointment with event details
    meet_link = result.get("meet_link")
    await db.execute(
        """UPDATE appointments
           SET google_calendar_event_id = ?, google_meet_link = ?, updated_at = ?
           WHERE id = ?""",
        (result["event_id"], meet_link, datetime.now(IST).isoformat(), appointment_id)
    )
    await db.commit()

    logger.info(f"Calendar event created for appointment {appointment_id}: {result['event_id']}" +
                (f" with Meet link" if meet_link else ""))

    return result


async def cancel_appointment_event(db, appointment_id: str) -> bool:
    """
    Delete the Google Calendar event for a cancelled appointment.

    Args:
        db: Database connection
        appointment_id: Appointment UUID

    Returns:
        bool: True if event deleted or didn't exist
    """
    cursor = await db.execute(
        "SELECT google_calendar_event_id FROM appointments WHERE id = ?",
        (appointment_id,)
    )
    row = await cursor.fetchone()

    if not row or not row[0]:
        logger.info(f"No calendar event to delete for appointment: {appointment_id}")
        return True

    event_id = row[0]
    success = await google_calendar_client.delete_event(event_id)

    if success:
        # Clear event reference
        await db.execute(
            """UPDATE appointments
               SET google_calendar_event_id = NULL, google_meet_link = NULL
               WHERE id = ?""",
            (appointment_id,)
        )
        await db.commit()

    return success
