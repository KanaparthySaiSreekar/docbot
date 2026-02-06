"""Dashboard REST API endpoints for appointment management."""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from docbot.auth import require_auth
from docbot.config import get_settings
from docbot.database import get_db
from docbot.timezone_utils import ist_now

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


# Utility functions

def mask_phone(phone: str) -> str:
    """Mask phone number, showing only last 4 digits."""
    if len(phone) <= 4:
        return phone
    return "****" + phone[-4:]


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
