"""Dashboard REST API endpoints for appointment management."""

import json
import logging
import os
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query, HTTPException, Request
from pydantic import BaseModel, field_validator

from docbot.auth import require_auth
from docbot.config import get_settings, is_readonly_mode, is_booking_disabled, set_emergency_mode
from docbot.database import get_db
from docbot.timezone_utils import ist_now, utc_now

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["dashboard"])


# Response models

class AppointmentListItem(BaseModel):
    """Appointment list item with masked phone."""
    id: str
    patient_name: str
    patient_age: int
    patient_gender: str
    patient_phone: str  # Masked
    consultation_type: str
    appointment_date: str
    slot_time: str
    status: str
    google_meet_link: Optional[str] = None
    refund_status: Optional[str] = None


class RefundListItem(BaseModel):
    """Failed refund list item."""
    id: str
    appointment_id: str
    patient_name: str
    appointment_date: str
    amount_paise: int
    status: str
    retry_count: int
    created_at: str


class SettingsResponse(BaseModel):
    """Schedule settings response."""
    working_days: list[int]
    start_time: str
    end_time: str
    break_start: str
    break_end: str
    slot_duration_minutes: int


class CancelResponse(BaseModel):
    """Response for cancellation."""
    status: str
    refund_status: Optional[str] = None
    calendar_status: Optional[str] = None


class RetryRefundResponse(BaseModel):
    """Response for refund retry."""
    status: str


class ResendResponse(BaseModel):
    """Response for resend confirmation."""
    status: str


class ScheduleUpdateRequest(BaseModel):
    """Request body for schedule update."""
    working_days: list[int]  # 0=Monday, 6=Sunday
    start_time: str  # HH:MM
    end_time: str  # HH:MM
    break_start: str  # HH:MM
    break_end: str  # HH:MM

    @field_validator('working_days')
    @classmethod
    def validate_working_days(cls, v):
        if not v:
            raise ValueError('At least one working day required')
        if not all(0 <= d <= 6 for d in v):
            raise ValueError('Working days must be 0-6')
        return sorted(set(v))

    @field_validator('start_time', 'end_time', 'break_start', 'break_end')
    @classmethod
    def validate_time_format(cls, v):
        if not re.match(r'^([01]\d|2[0-3]):[0-5]\d$', v):
            raise ValueError('Time must be HH:MM format')
        return v

    @field_validator('end_time')
    @classmethod
    def validate_end_after_start(cls, v, info):
        if 'start_time' in info.data and v <= info.data['start_time']:
            raise ValueError('End time must be after start time')
        return v

    @field_validator('break_end')
    @classmethod
    def validate_break_within_hours(cls, v, info):
        if 'break_start' in info.data and v <= info.data['break_start']:
            raise ValueError('Break end must be after break start')
        if 'start_time' in info.data and info.data.get('break_start', '') < info.data['start_time']:
            raise ValueError('Break must be within working hours')
        if 'end_time' in info.data and v > info.data['end_time']:
            raise ValueError('Break must be within working hours')
        return v


class EmergencyStatusResponse(BaseModel):
    """Emergency mode status response."""
    booking_disabled: bool
    readonly_dashboard: bool


class MedicineItem(BaseModel):
    """Medicine item for prescription."""
    name: str
    dosage: str
    frequency: str  # e.g., "1-0-1" or "Once daily"
    duration: str  # e.g., "5 days"
    notes: str | None = None


class CreatePrescriptionRequest(BaseModel):
    """Request body for creating prescription."""
    appointment_id: str
    medicines: list[MedicineItem]
    instructions: str | None = None


class PrescriptionResponse(BaseModel):
    """Prescription response with download URL."""
    id: str
    appointment_id: str
    patient_name: str
    created_at: str
    whatsapp_sent: bool
    download_url: str


# Utility functions

def mask_phone(phone: str) -> str:
    """Mask phone number, showing only last 4 digits."""
    if len(phone) <= 4:
        return phone
    return "****" + phone[-4:]


def check_readonly() -> None:
    """Check if dashboard is in read-only mode and raise exception if so."""
    if is_readonly_mode():
        raise HTTPException(
            status_code=403,
            detail="Dashboard is in read-only mode during incident response"
        )


# Endpoints

@router.get("/appointments")
async def get_appointments(
    date_from: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    status: Optional[str] = Query(None, description="Filter by status"),
    user: dict = Depends(require_auth),
    db = Depends(get_db)
) -> list[AppointmentListItem]:
    """
    Get list of upcoming appointments.

    Default: today's date to 7 days ahead.
    Returns appointments with patient details, status, and meet links.
    """
    # Default date range: today to 7 days ahead
    if not date_from:
        date_from = ist_now().strftime("%Y-%m-%d")

    if not date_to:
        from_date = datetime.strptime(date_from, "%Y-%m-%d")
        to_date = from_date + timedelta(days=7)
        date_to = to_date.strftime("%Y-%m-%d")

    # Build query
    query = """
        SELECT
            a.id, a.patient_name, a.patient_age, a.patient_gender, a.patient_phone,
            a.consultation_type, a.appointment_date, a.slot_time, a.status,
            a.google_meet_link, r.status as refund_status
        FROM appointments a
        LEFT JOIN refunds r ON a.id = r.appointment_id
        WHERE a.appointment_date >= ? AND a.appointment_date <= ?
    """
    params = [date_from, date_to]

    if status:
        query += " AND a.status = ?"
        params.append(status)

    query += " ORDER BY a.appointment_date ASC, a.slot_time ASC"

    cursor = await db.execute(query, params)
    rows = await cursor.fetchall()

    appointments = []
    for row in rows:
        appointments.append(AppointmentListItem(
            id=row[0],
            patient_name=row[1],
            patient_age=row[2],
            patient_gender=row[3],
            patient_phone=mask_phone(row[4]),
            consultation_type=row[5],
            appointment_date=row[6],
            slot_time=row[7],
            status=row[8],
            google_meet_link=row[9],
            refund_status=row[10]
        ))

    logger.info(
        "Appointments fetched",
        extra={
            "user_email": user.get("email"),
            "date_from": date_from,
            "date_to": date_to,
            "count": len(appointments)
        }
    )

    return appointments


@router.get("/appointments/history")
async def get_appointments_history(
    limit: int = Query(50, description="Number of appointments to return"),
    offset: int = Query(0, description="Offset for pagination"),
    user: dict = Depends(require_auth),
    db = Depends(get_db)
) -> list[AppointmentListItem]:
    """
    Get past appointments (historical data).

    Returns appointments before today in reverse chronological order.
    """
    today = ist_now().strftime("%Y-%m-%d")

    query = """
        SELECT
            a.id, a.patient_name, a.patient_age, a.patient_gender, a.patient_phone,
            a.consultation_type, a.appointment_date, a.slot_time, a.status,
            a.google_meet_link, r.status as refund_status
        FROM appointments a
        LEFT JOIN refunds r ON a.id = r.appointment_id
        WHERE a.appointment_date < ?
        ORDER BY a.appointment_date DESC, a.slot_time DESC
        LIMIT ? OFFSET ?
    """

    cursor = await db.execute(query, [today, limit, offset])
    rows = await cursor.fetchall()

    appointments = []
    for row in rows:
        appointments.append(AppointmentListItem(
            id=row[0],
            patient_name=row[1],
            patient_age=row[2],
            patient_gender=row[3],
            patient_phone=mask_phone(row[4]),
            consultation_type=row[5],
            appointment_date=row[6],
            slot_time=row[7],
            status=row[8],
            google_meet_link=row[9],
            refund_status=row[10]
        ))

    logger.info(
        "Appointment history fetched",
        extra={
            "user_email": user.get("email"),
            "limit": limit,
            "offset": offset,
            "count": len(appointments)
        }
    )

    return appointments


@router.get("/refunds/failed")
async def get_failed_refunds(
    user: dict = Depends(require_auth),
    db = Depends(get_db)
) -> list[RefundListItem]:
    """
    Get list of failed/pending refunds that need attention.

    Returns refunds with status PENDING or FAILED.
    """
    query = """
        SELECT
            r.id, r.appointment_id, a.patient_name, a.appointment_date,
            r.amount_paise, r.status, r.retry_count, r.created_at
        FROM refunds r
        JOIN appointments a ON r.appointment_id = a.id
        WHERE r.status IN ('PENDING', 'FAILED')
        ORDER BY r.created_at DESC
    """

    cursor = await db.execute(query)
    rows = await cursor.fetchall()

    refunds = []
    for row in rows:
        refunds.append(RefundListItem(
            id=row[0],
            appointment_id=row[1],
            patient_name=row[2],
            appointment_date=row[3],
            amount_paise=row[4],
            status=row[5],
            retry_count=row[6],
            created_at=row[7]
        ))

    logger.info(
        "Failed refunds fetched",
        extra={
            "user_email": user.get("email"),
            "count": len(refunds)
        }
    )

    return refunds


@router.get("/settings")
async def get_settings_endpoint(
    user: dict = Depends(require_auth)
) -> SettingsResponse:
    """
    Get current schedule configuration settings.

    Returns working hours, break times, and slot duration.
    """
    settings = get_settings()
    schedule = settings.schedule

    logger.info(
        "Settings fetched",
        extra={"user_email": user.get("email")}
    )

    return SettingsResponse(
        working_days=schedule.working_days,
        start_time=schedule.start_time,
        end_time=schedule.end_time,
        break_start=schedule.break_start,
        break_end=schedule.break_end,
        slot_duration_minutes=schedule.slot_duration_minutes
    )


@router.put("/settings")
async def update_settings_endpoint(
    schedule: ScheduleUpdateRequest,
    request: Request,
    user: dict = Depends(require_auth),
):
    """
    Update working hours configuration.

    Persists to config.{env}.json file.
    """
    check_readonly()

    settings = get_settings()
    env = os.getenv("DOCBOT_ENV", "test")
    config_path = Path(f"config.{env}.json")

    # Read current config
    if config_path.exists():
        with open(config_path, "r") as f:
            config_data = json.load(f)
    else:
        config_data = {}

    # Update schedule section
    if "schedule" not in config_data:
        config_data["schedule"] = {}

    config_data["schedule"]["working_days"] = schedule.working_days
    config_data["schedule"]["start_time"] = schedule.start_time
    config_data["schedule"]["end_time"] = schedule.end_time
    config_data["schedule"]["break_start"] = schedule.break_start
    config_data["schedule"]["break_end"] = schedule.break_end

    # Write back
    with open(config_path, "w") as f:
        json.dump(config_data, f, indent=2)

    # Clear config cache to reload
    get_settings.cache_clear()

    logger.info("Schedule settings updated", extra={
        "user": user.get("email"),
        "working_days": schedule.working_days
    })

    return {"status": "updated"}


@router.get("/emergency", response_model=EmergencyStatusResponse)
async def get_emergency_status(user: dict = Depends(require_auth)) -> EmergencyStatusResponse:
    """Get current emergency mode status."""
    return EmergencyStatusResponse(
        booking_disabled=is_booking_disabled(),
        readonly_dashboard=is_readonly_mode(),
    )


@router.post("/emergency")
async def set_emergency_status(
    booking_disabled: Optional[bool] = None,
    readonly_dashboard: Optional[bool] = None,
    user: dict = Depends(require_auth)
) -> dict:
    """Set emergency mode flags. Requires authentication."""
    set_emergency_mode(booking_disabled, readonly_dashboard)

    logger.info(
        "Emergency mode updated",
        extra={
            "user_email": user.get("email"),
            "booking_disabled": booking_disabled,
            "readonly_dashboard": readonly_dashboard
        }
    )

    return {"status": "updated"}


@router.post("/appointments/{appointment_id}/cancel", response_model=CancelResponse)
async def cancel_appointment_endpoint(
    appointment_id: str,
    request: Request,
    user: dict = Depends(require_auth),
    db = Depends(get_db)
):
    """
    Cancel an appointment (doctor-initiated, no time restriction).

    Triggers automatic refund for online appointments.
    Deletes calendar event.
    """
    check_readonly()

    from docbot.cancellation_service import cancel_appointment

    try:
        # by_patient=False skips the >1 hour check
        result = await cancel_appointment(db, appointment_id, by_patient=False)

        logger.info(
            "Appointment cancelled by doctor",
            extra={
                "user_email": user.get("email"),
                "appointment_id": appointment_id,
                "refund_status": result.get("refund_status")
            }
        )

        return CancelResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/refunds/{refund_id}/retry", response_model=RetryRefundResponse)
async def retry_refund_endpoint(
    refund_id: str,
    user: dict = Depends(require_auth),
    db = Depends(get_db)
):
    """
    Manually retry a failed refund.
    """
    check_readonly()

    # Get refund record
    cursor = await db.execute(
        "SELECT appointment_id, status FROM refunds WHERE id = ?",
        (refund_id,)
    )
    row = await cursor.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Refund not found")

    appointment_id, status = row
    if status == "PROCESSED":
        logger.info(
            "Refund already processed",
            extra={"user_email": user.get("email"), "refund_id": refund_id}
        )
        return RetryRefundResponse(status="already_processed")

    # Reset retry count and trigger immediate retry
    from docbot.refund_service import initiate_refund

    await db.execute("DELETE FROM refunds WHERE id = ?", (refund_id,))
    await db.commit()

    success = await initiate_refund(db, appointment_id)

    logger.info(
        "Manual refund retry",
        extra={
            "user_email": user.get("email"),
            "refund_id": refund_id,
            "appointment_id": appointment_id,
            "success": success
        }
    )

    return RetryRefundResponse(status="processed" if success else "pending_retry")


@router.post("/appointments/{appointment_id}/resend", response_model=ResendResponse)
async def resend_confirmation_endpoint(
    appointment_id: str,
    user: dict = Depends(require_auth),
    db = Depends(get_db)
):
    """
    Resend confirmation message (and Meet link for online) to patient.
    """
    check_readonly()

    cursor = await db.execute(
        """SELECT patient_phone, patient_name, consultation_type, appointment_date,
                  slot_time, google_meet_link, language, status
           FROM appointments WHERE id = ?""",
        (appointment_id,)
    )
    row = await cursor.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Appointment not found")

    phone, name, consult_type, date_str, slot_time, meet_link, lang, status = row

    if status not in ['CONFIRMED', 'PENDING_PAYMENT']:
        raise HTTPException(status_code=400, detail="Cannot resend for cancelled appointments")

    # Build and send message
    from docbot.whatsapp_client import send_text
    from docbot.i18n import get_message

    if consult_type == "online" and meet_link:
        message = get_message("payment_received_meet_link", lang=lang,
                             date=date_str, time=slot_time, meet_link=meet_link)
    else:
        settings = get_settings()
        message = get_message("booking_confirmed_offline", lang=lang,
                             name=name, date=date_str, time=slot_time,
                             clinic_address=settings.clinic.address)

    result = await send_text(phone, message)

    logger.info(
        "Confirmation resent",
        extra={
            "user_email": user.get("email"),
            "appointment_id": appointment_id,
            "sent": result is not None
        }
    )

    return ResendResponse(status="sent" if result else "failed")


@router.get("/appointments/completed")
async def get_completed_appointments(
    user: dict = Depends(require_auth),
    db = Depends(get_db)
) -> list[AppointmentListItem]:
    """
    Get completed appointments without prescriptions for prescription creation.

    Returns appointments with status=CONFIRMED, date < today, and no existing prescription.
    """
    today = ist_now().strftime("%Y-%m-%d")

    query = """
        SELECT
            a.id, a.patient_name, a.patient_age, a.patient_gender, a.patient_phone,
            a.consultation_type, a.appointment_date, a.slot_time, a.status,
            a.google_meet_link, r.status as refund_status
        FROM appointments a
        LEFT JOIN refunds r ON a.id = r.appointment_id
        LEFT JOIN prescriptions p ON a.id = p.appointment_id
        WHERE a.status = 'CONFIRMED'
          AND a.appointment_date < ?
          AND p.id IS NULL
        ORDER BY a.appointment_date DESC, a.slot_time DESC
    """

    cursor = await db.execute(query, [today])
    rows = await cursor.fetchall()

    appointments = []
    for row in rows:
        appointments.append(AppointmentListItem(
            id=row[0],
            patient_name=row[1],
            patient_age=row[2],
            patient_gender=row[3],
            patient_phone=mask_phone(row[4]),
            consultation_type=row[5],
            appointment_date=row[6],
            slot_time=row[7],
            status=row[8],
            google_meet_link=row[9],
            refund_status=row[10]
        ))

    logger.info(
        "Completed appointments fetched",
        extra={
            "user_email": user.get("email"),
            "count": len(appointments)
        }
    )

    return appointments


@router.post("/prescriptions", response_model=PrescriptionResponse)
async def create_prescription_endpoint(
    request_data: CreatePrescriptionRequest,
    user: dict = Depends(require_auth),
    db = Depends(get_db)
):
    """
    Create prescription for an appointment.

    Generates PDF and sends to patient via WhatsApp with secure download link.
    """
    check_readonly()

    from docbot.prescription_service import create_prescription, mark_whatsapp_sent
    from docbot.whatsapp_client import send_text
    from docbot.i18n import get_message

    try:
        # Convert Pydantic models to dicts
        medicines = [med.model_dump() for med in request_data.medicines]

        # Create prescription (generates PDF)
        prescription = await create_prescription(
            db,
            request_data.appointment_id,
            medicines,
            request_data.instructions
        )

        # Get appointment details for WhatsApp message
        cursor = await db.execute(
            "SELECT patient_phone, patient_name, language FROM appointments WHERE id = ?",
            (request_data.appointment_id,)
        )
        appt_row = await cursor.fetchone()
        if appt_row:
            phone, patient_name, lang = appt_row

            # Generate download URL
            settings = get_settings()
            base_url = settings.app.base_url or "http://localhost:8000"
            download_url = f"{base_url}/prescriptions/download/{prescription['secure_token']}"

            # Send prescription via WhatsApp
            message = get_message("prescription_ready", lang=lang,
                                 name=patient_name, download_link=download_url)
            result = await send_text(phone, message)

            if result:
                await mark_whatsapp_sent(db, prescription['id'])

        logger.info(
            "Prescription created",
            extra={
                "user_email": user.get("email"),
                "prescription_id": prescription['id'],
                "appointment_id": request_data.appointment_id
            }
        )

        return PrescriptionResponse(
            id=prescription['id'],
            appointment_id=prescription['appointment_id'],
            patient_name=patient_name,
            created_at=prescription['created_at'],
            whatsapp_sent=result is not None,
            download_url=download_url
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/prescriptions")
async def get_prescriptions(
    user: dict = Depends(require_auth),
    db = Depends(get_db)
) -> list[PrescriptionResponse]:
    """
    Get all prescriptions with patient names.

    Returns prescription history sorted by creation date.
    """
    query = """
        SELECT
            p.id, p.appointment_id, a.patient_name, p.created_at,
            p.whatsapp_sent, p.secure_token
        FROM prescriptions p
        JOIN appointments a ON p.appointment_id = a.id
        ORDER BY p.created_at DESC
    """

    cursor = await db.execute(query)
    rows = await cursor.fetchall()

    settings = get_settings()
    base_url = settings.app.base_url or "http://localhost:8000"

    prescriptions = []
    for row in rows:
        prescriptions.append(PrescriptionResponse(
            id=row[0],
            appointment_id=row[1],
            patient_name=row[2],
            created_at=row[3],
            whatsapp_sent=row[4] == "true",
            download_url=f"{base_url}/prescriptions/download/{row[5]}"
        ))

    logger.info(
        "Prescriptions fetched",
        extra={
            "user_email": user.get("email"),
            "count": len(prescriptions)
        }
    )

    return prescriptions


@router.get("/prescriptions/{prescription_id}/download")
async def regenerate_prescription_token(
    prescription_id: str,
    user: dict = Depends(require_auth),
    db = Depends(get_db)
) -> dict:
    """
    Regenerate secure token for prescription download.

    Extends access for 72 hours from regeneration.
    """
    from docbot.prescription_service import regenerate_token

    new_token = await regenerate_token(db, prescription_id)

    settings = get_settings()
    base_url = settings.app.base_url or "http://localhost:8000"
    download_url = f"{base_url}/prescriptions/download/{new_token}"

    logger.info(
        "Prescription token regenerated",
        extra={
            "user_email": user.get("email"),
            "prescription_id": prescription_id
        }
    )

    return {"download_url": download_url}
