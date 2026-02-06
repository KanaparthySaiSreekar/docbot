"""Automated reminder service for appointment notifications via WhatsApp."""

import logging
from datetime import datetime, timedelta, timezone

from docbot.config import get_settings
from docbot.database import get_db
from docbot.i18n import get_message
from docbot.whatsapp_client import send_text

logger = logging.getLogger(__name__)


async def get_due_reminders(reminder_type: str, db=None) -> list[dict]:
    """
    Query appointments that need reminders sent.

    Args:
        reminder_type: "24h" for 24-hour reminders, "1h" for 1-hour reminders
        db: Optional database connection (for testing)

    Returns:
        list[dict]: Appointments needing reminders with all necessary data
    """
    now = datetime.now(timezone.utc)

    # Define time windows for each reminder type
    if reminder_type == "24h":
        # 24 hours = 1440 minutes, window: 23-25 hours (1380-1500 minutes)
        window_start = now + timedelta(minutes=1380)  # 23 hours
        window_end = now + timedelta(minutes=1500)  # 25 hours
        reminder_sent_column = "reminder_sent_24h"
    elif reminder_type == "1h":
        # 1 hour = 60 minutes, window: 50-70 minutes
        window_start = now + timedelta(minutes=50)
        window_end = now + timedelta(minutes=70)
        reminder_sent_column = "reminder_sent_1h"
    else:
        logger.error(f"Invalid reminder type: {reminder_type}")
        return []

    # Query appointments in the time window that haven't been reminded yet
    query = f"""
        SELECT
            id,
            patient_phone,
            patient_name,
            consultation_type,
            appointment_date,
            slot_time,
            google_meet_link,
            language
        FROM appointments
        WHERE status = 'CONFIRMED'
        AND {reminder_sent_column} != 'true'
        AND datetime(appointment_date || ' ' || slot_time) >= ?
        AND datetime(appointment_date || ' ' || slot_time) < ?
        ORDER BY appointment_date, slot_time
    """

    # Use provided db or get from connection pool
    if db is not None:
        cursor = await db.execute(
            query,
            (
                window_start.strftime("%Y-%m-%d %H:%M"),
                window_end.strftime("%Y-%m-%d %H:%M"),
            ),
        )
        rows = await cursor.fetchall()

        reminders = []
        for row in rows:
            reminders.append({
                "id": row[0],
                "patient_phone": row[1],
                "patient_name": row[2],
                "consultation_type": row[3],
                "appointment_date": row[4],
                "slot_time": row[5],
                "google_meet_link": row[6],
                "language": row[7],
            })

        logger.info(
            f"Found {len(reminders)} appointments for {reminder_type} reminders",
            extra={"reminder_type": reminder_type, "count": len(reminders)}
        )
        return reminders
    else:
        async for db in get_db():
            cursor = await db.execute(
                query,
                (
                    window_start.strftime("%Y-%m-%d %H:%M"),
                    window_end.strftime("%Y-%m-%d %H:%M"),
                ),
            )
            rows = await cursor.fetchall()

            reminders = []
            for row in rows:
                reminders.append({
                    "id": row[0],
                    "patient_phone": row[1],
                    "patient_name": row[2],
                    "consultation_type": row[3],
                    "appointment_date": row[4],
                    "slot_time": row[5],
                    "google_meet_link": row[6],
                    "language": row[7],
                })

            logger.info(
                f"Found {len(reminders)} appointments for {reminder_type} reminders",
                extra={"reminder_type": reminder_type, "count": len(reminders)}
            )
            return reminders


async def send_reminder(phone: str, reminder_type: str, appointment: dict) -> bool:
    """
    Send reminder message via WhatsApp.

    Args:
        phone: Patient phone number
        reminder_type: "24h" or "1h"
        appointment: Appointment data dict

    Returns:
        bool: True if sent successfully, False otherwise
    """
    settings = get_settings()
    language = appointment.get("language", "en")
    consultation_type = appointment["consultation_type"]
    slot_time = appointment["slot_time"]

    # Determine message key based on reminder type and consultation type
    if reminder_type == "24h":
        if consultation_type == "online":
            message_key = "reminder_24h_online"
        else:
            message_key = "reminder_24h_offline"
    else:  # 1h
        if consultation_type == "online":
            message_key = "reminder_1h_online"
        else:
            message_key = "reminder_1h_offline"

    # Prepare message template variables
    kwargs = {"time": slot_time}

    if consultation_type == "online":
        kwargs["meet_link"] = appointment.get("google_meet_link", "[Link pending]")
    else:
        kwargs["clinic_address"] = settings.clinic.address

    # Get localized message
    try:
        message = get_message(message_key, language, **kwargs)
    except KeyError as e:
        logger.error(
            f"Failed to get reminder message: {e}",
            extra={
                "message_key": message_key,
                "language": language,
                "appointment_id": appointment["id"]
            }
        )
        return False

    # Send via WhatsApp
    result = await send_text(phone, message)

    if result:
        logger.info(
            f"Reminder sent successfully",
            extra={
                "appointment_id": appointment["id"],
                "reminder_type": reminder_type,
                "phone": phone[-4:]  # Last 4 digits for privacy
            }
        )
        return True
    else:
        logger.error(
            f"Failed to send reminder",
            extra={
                "appointment_id": appointment["id"],
                "reminder_type": reminder_type,
                "phone": phone[-4:]
            }
        )
        return False


async def mark_reminder_sent(appointment_id: str, reminder_type: str, db=None) -> None:
    """
    Mark reminder as sent in database.

    Args:
        appointment_id: Appointment ID
        reminder_type: "24h" or "1h"
        db: Optional database connection (for testing)
    """
    column = "reminder_sent_24h" if reminder_type == "24h" else "reminder_sent_1h"

    query = f"""
        UPDATE appointments
        SET {column} = 'true',
            updated_at = ?
        WHERE id = ?
    """

    # Use provided db or get from connection pool
    if db is not None:
        await db.execute(
            query,
            (datetime.now(timezone.utc).isoformat(), appointment_id)
        )
        await db.commit()

        logger.debug(
            f"Marked reminder as sent",
            extra={
                "appointment_id": appointment_id,
                "reminder_type": reminder_type
            }
        )
    else:
        async for db in get_db():
            await db.execute(
                query,
                (datetime.now(timezone.utc).isoformat(), appointment_id)
            )
            await db.commit()

            logger.debug(
                f"Marked reminder as sent",
                extra={
                    "appointment_id": appointment_id,
                    "reminder_type": reminder_type
                }
            )


async def run_reminder_job(reminder_type: str, db=None) -> dict:
    """
    Main entry point for reminder cron job.

    Queries due reminders, sends each, marks as sent, returns statistics.

    Args:
        reminder_type: "24h" or "1h"
        db: Optional database connection (for testing)

    Returns:
        dict: Statistics with keys "sent", "failed", "skipped"
    """
    logger.info(f"Starting {reminder_type} reminder job")

    stats = {"sent": 0, "failed": 0, "skipped": 0}

    # Get appointments needing reminders
    reminders = await get_due_reminders(reminder_type, db)

    for appointment in reminders:
        phone = appointment["patient_phone"]
        appointment_id = appointment["id"]

        # Send reminder
        success = await send_reminder(phone, reminder_type, appointment)

        if success:
            # Mark as sent
            await mark_reminder_sent(appointment_id, reminder_type, db)
            stats["sent"] += 1
        else:
            stats["failed"] += 1

    logger.info(
        f"Reminder job complete",
        extra={
            "reminder_type": reminder_type,
            "stats": stats
        }
    )

    return stats
