"""Cancellation service for patient-initiated cancellations."""

from datetime import datetime
from zoneinfo import ZoneInfo

from docbot.state_machine import transition, AppointmentStatus
from docbot.refund_service import initiate_refund
from docbot.calendar_service import cancel_appointment_event
from docbot.timezone_utils import utc_now, IST
from docbot.alerts import log_alert
import logging

logger = logging.getLogger(__name__)


async def can_cancel_appointment(db, appointment_id: str) -> tuple[bool, str]:
    """
    Check if appointment can be cancelled by patient.

    Args:
        db: Database connection
        appointment_id: Appointment UUID

    Returns:
        (can_cancel: bool, reason: str)
    """
    cursor = await db.execute(
        """SELECT appointment_date, slot_time, status
           FROM appointments WHERE id = ?""",
        (appointment_id,)
    )
    row = await cursor.fetchone()

    if not row:
        return False, "appointment_not_found"

    date_str, slot_time, status = row

    # Only CONFIRMED or PENDING_PAYMENT can be cancelled
    if status not in [AppointmentStatus.CONFIRMED.value, AppointmentStatus.PENDING_PAYMENT.value]:
        return False, "already_cancelled"

    # Check if >1 hour before appointment
    year, month, day = map(int, date_str.split("-"))
    hour, minute = map(int, slot_time.split(":"))
    appt_time = datetime(year, month, day, hour, minute, tzinfo=IST)

    now = datetime.now(IST)
    hours_until = (appt_time - now).total_seconds() / 3600

    if hours_until <= 1:
        return False, "too_late"

    return True, "ok"


async def cancel_appointment(db, appointment_id: str, by_patient: bool = True) -> dict:
    """
    Cancel an appointment with refund and calendar cleanup.

    Args:
        db: Database connection
        appointment_id: Appointment UUID
        by_patient: Whether cancellation is by patient (vs doctor)

    Returns:
        dict with status, refund_status, calendar_status

    Raises:
        ValueError: If cancellation not allowed
    """
    # Check cancellation eligibility
    if by_patient:
        can_cancel, reason = await can_cancel_appointment(db, appointment_id)
        if not can_cancel:
            raise ValueError(reason)

    # Get appointment details
    cursor = await db.execute(
        """SELECT consultation_type, status, razorpay_payment_id
           FROM appointments WHERE id = ?""",
        (appointment_id,)
    )
    row = await cursor.fetchone()

    if not row:
        raise ValueError("appointment_not_found")

    consult_type, current_status, payment_id = row

    # Transition to CANCELLED
    transition(current_status, AppointmentStatus.CANCELLED.value)

    now = utc_now().isoformat()
    await db.execute(
        """UPDATE appointments
           SET status = ?, cancelled_at = ?, updated_at = ?
           WHERE id = ?""",
        (AppointmentStatus.CANCELLED.value, now, now, appointment_id)
    )
    await db.commit()

    result = {
        "status": "cancelled",
        "refund_status": None,
        "calendar_status": None
    }

    # Handle refund for online with payment
    if consult_type == "online" and payment_id:
        refund_success = await initiate_refund(db, appointment_id)
        result["refund_status"] = "processed" if refund_success else "pending"

    # Delete calendar event
    cal_success = await cancel_appointment_event(db, appointment_id)
    result["calendar_status"] = "deleted" if cal_success else "failed"

    logger.info("Appointment cancelled",
                extra={"appointment_id": appointment_id,
                       "by_patient": by_patient,
                       "refund_status": result["refund_status"]})

    return result
