"""Pydantic models for data transfer objects (DTOs)."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class Appointment(BaseModel):
    """Appointment data transfer object."""

    id: str
    patient_phone: str
    patient_name: str
    patient_age: int
    patient_gender: str  # 'Male', 'Female', 'Other'
    consultation_type: str  # 'online', 'offline'
    appointment_date: str  # ISO date YYYY-MM-DD
    slot_time: str  # HH:MM format
    status: str = "PENDING_PAYMENT"
    razorpay_payment_id: Optional[str] = None
    razorpay_order_id: Optional[str] = None
    razorpay_refund_id: Optional[str] = None
    google_calendar_event_id: Optional[str] = None
    google_meet_link: Optional[str] = None
    language: str = "en"
    created_at: str  # ISO 8601 UTC
    updated_at: str  # ISO 8601 UTC
    cancelled_at: Optional[str] = None
    refunded_at: Optional[str] = None


class SlotLock(BaseModel):
    """Slot lock data transfer object."""

    appointment_date: str  # YYYY-MM-DD
    slot_time: str  # HH:MM
    locked_by_phone: str
    locked_until: str  # UTC timestamp


class IdempotencyKey(BaseModel):
    """Idempotency key data transfer object."""

    event_id: str
    source: str  # 'razorpay', 'whatsapp', etc.
    processed_at: str  # UTC timestamp
    result: Optional[str] = None  # JSON string


class Prescription(BaseModel):
    """Prescription data transfer object."""

    id: str
    appointment_id: str
    medicines: str  # JSON string
    instructions: Optional[str] = None
    pdf_path: Optional[str] = None
    created_at: str  # UTC timestamp
