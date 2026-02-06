"""Reconciliation service for calendar and payment sync.

Designed to run as nightly cron job. Database is authoritative.
Google Calendar is synced as a projection of database state.
"""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from docbot import google_calendar_client
from docbot.calendar_service import create_appointment_event
from docbot.state_machine import AppointmentStatus
from docbot.timezone_utils import IST
from docbot.alerts import log_alert
import logging

logger = logging.getLogger(__name__)


async def retry_failed_calendar_events(db) -> dict:
    """
    Retry creating calendar events for confirmed appointments without events.

    Returns:
        dict with counts of retried and failed
    """
    # Find confirmed appointments without calendar events
    cursor = await db.execute(
        """SELECT id FROM appointments
           WHERE status = ?
           AND google_calendar_event_id IS NULL
           AND appointment_date >= date('now')
           LIMIT 20""",
        (AppointmentStatus.CONFIRMED.value,)
    )
    rows = await cursor.fetchall()

    retried = 0
    failed = 0

    for row in rows:
        appointment_id = row[0]
        result = await create_appointment_event(db, appointment_id, retry_count=1)

        if result:
            retried += 1
            logger.info("Calendar event created on retry", appointment_id=appointment_id)
        else:
            failed += 1
            logger.warning("Calendar event retry failed", appointment_id=appointment_id)

    return {"retried": retried, "failed": failed}


async def check_calendar_drift(db) -> list[dict]:
    """
    Check for mismatches between database and Google Calendar.

    Compares upcoming confirmed appointments with their calendar events.
    Database is authoritative - calendar drift is flagged for correction.

    Returns:
        List of drift records with appointment_id and drift_type
    """
    drifts = []

    # Get confirmed appointments with calendar events for next 7 days
    cursor = await db.execute(
        """SELECT id, google_calendar_event_id, appointment_date, slot_time
           FROM appointments
           WHERE status = ?
           AND google_calendar_event_id IS NOT NULL
           AND appointment_date BETWEEN date('now') AND date('now', '+7 days')""",
        (AppointmentStatus.CONFIRMED.value,)
    )
    rows = await cursor.fetchall()

    for row in rows:
        appointment_id, event_id, date_str, slot_time = row

        # Fetch event from Google Calendar
        event = await google_calendar_client.get_event(event_id)

        if not event:
            drifts.append({
                "appointment_id": appointment_id,
                "event_id": event_id,
                "drift_type": "event_missing",
                "details": "Calendar event deleted but appointment exists"
            })
            continue

        # Check if event time matches
        event_start = event.get("start", {}).get("dateTime", "")
        if event_start:
            # Parse event time and compare
            # Event time format: 2026-02-10T10:00:00+05:30
            try:
                event_dt = datetime.fromisoformat(event_start)
                expected_hour, expected_min = map(int, slot_time.split(":"))
                expected_year, expected_month, expected_day = map(int, date_str.split("-"))

                if (event_dt.hour != expected_hour or
                    event_dt.minute != expected_min or
                    event_dt.day != expected_day):
                    drifts.append({
                        "appointment_id": appointment_id,
                        "event_id": event_id,
                        "drift_type": "time_mismatch",
                        "details": f"DB: {date_str} {slot_time}, Cal: {event_start}"
                    })
            except ValueError:
                logger.warning("Failed to parse event time", event_id=event_id)

    return drifts


async def check_orphaned_cancelled(db) -> list[dict]:
    """
    Find cancelled appointments that still have calendar events.

    These should have been deleted but might have failed.

    Returns:
        List of orphaned records
    """
    cursor = await db.execute(
        """SELECT id, google_calendar_event_id
           FROM appointments
           WHERE status IN (?, ?)
           AND google_calendar_event_id IS NOT NULL""",
        (AppointmentStatus.CANCELLED.value, AppointmentStatus.REFUNDED.value)
    )
    rows = await cursor.fetchall()

    orphans = []
    for row in rows:
        appointment_id, event_id = row
        orphans.append({
            "appointment_id": appointment_id,
            "event_id": event_id,
            "issue": "Cancelled/refunded appointment still has calendar event"
        })

    return orphans


async def run_reconciliation(db) -> dict:
    """
    Run full reconciliation job.

    Steps:
    1. Retry failed calendar event creations
    2. Retry failed refunds
    3. Check for calendar drift
    4. Check for orphaned cancelled events
    5. Alert on any issues found

    Returns:
        dict with reconciliation results
    """
    logger.info("Starting reconciliation job")
    results = {
        "calendar_retries": {"retried": 0, "failed": 0},
        "refund_retries": 0,
        "calendar_drifts": [],
        "orphaned_cancelled": [],
        "alerts_raised": 0
    }

    # 1. Retry failed calendar creations
    cal_result = await retry_failed_calendar_events(db)
    results["calendar_retries"] = cal_result

    # 2. Retry failed refunds (stub for now - will import when refund_service exists)
    try:
        from docbot.refund_service import retry_failed_refunds
        refund_count = await retry_failed_refunds(db)
        results["refund_retries"] = refund_count
    except ImportError:
        logger.warning("refund_service not yet available, skipping refund retries")
        results["refund_retries"] = 0

    # 3. Check calendar drift
    drifts = await check_calendar_drift(db)
    results["calendar_drifts"] = drifts

    # 4. Check orphaned cancelled
    orphans = await check_orphaned_cancelled(db)
    results["orphaned_cancelled"] = orphans

    # 5. Alert on issues
    if drifts:
        log_alert("ERROR", "calendar_drift_detected", "Calendar drift detected",
                  {
                      "count": len(drifts),
                      "drifts": drifts[:5]  # Limit for alert size
                  })
        results["alerts_raised"] += 1

    if orphans:
        log_alert("ERROR", "orphaned_calendar_events", "Orphaned calendar events found",
                  {
                      "count": len(orphans),
                      "orphans": orphans[:5]
                  })
        results["alerts_raised"] += 1

    if cal_result["failed"] > 0:
        log_alert("ERROR", "calendar_creation_failures", "Calendar creation failures",
                  {
                      "failed": cal_result["failed"]
                  })
        results["alerts_raised"] += 1

    logger.info("Reconciliation complete", results=results)
    return results
