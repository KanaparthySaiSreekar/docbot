"""Prescription creation, storage, and retrieval service."""
import json
import logging
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import aiosqlite

from docbot.config import get_settings
from docbot.prescription_pdf import generate_prescription_pdf
from docbot.timezone_utils import utc_now

logger = logging.getLogger(__name__)

PRESCRIPTION_STORAGE_DIR = Path("prescriptions")


async def create_prescription(
    db: aiosqlite.Connection,
    appointment_id: str,
    medicines: list[dict],
    instructions: str | None = None,
) -> dict:
    """
    Create prescription for appointment.

    Generates PDF and stores in database + filesystem.
    Returns prescription record with secure download token.

    Raises ValueError if prescription already exists for appointment.
    """
    # Check for existing prescription (immutable after creation)
    cursor = await db.execute(
        "SELECT id FROM prescriptions WHERE appointment_id = ?",
        (appointment_id,)
    )
    existing = await cursor.fetchone()
    if existing:
        raise ValueError(f"Prescription already exists for appointment {appointment_id}")

    # Get appointment details for PDF
    cursor = await db.execute(
        """SELECT patient_name, patient_age, patient_gender
           FROM appointments WHERE id = ?""",
        (appointment_id,)
    )
    appt = await cursor.fetchone()
    if not appt:
        raise ValueError(f"Appointment not found: {appointment_id}")

    patient_name, patient_age, patient_gender = appt

    # Generate prescription ID and secure token
    prescription_id = str(uuid.uuid4())
    secure_token = secrets.token_urlsafe(32)
    token_expires_at = (datetime.now(timezone.utc) + timedelta(hours=72)).isoformat()

    # Generate PDF
    pdf_bytes = generate_prescription_pdf(
        prescription_id=prescription_id,
        appointment_id=appointment_id,
        patient_name=patient_name,
        patient_age=patient_age,
        patient_gender=patient_gender,
        medicines=medicines,
        instructions=instructions,
    )

    # Store PDF file
    PRESCRIPTION_STORAGE_DIR.mkdir(exist_ok=True)
    pdf_path = PRESCRIPTION_STORAGE_DIR / f"{prescription_id}.pdf"
    with open(pdf_path, "wb") as f:
        f.write(pdf_bytes)

    # Store in database
    now = utc_now().isoformat()
    await db.execute(
        """INSERT INTO prescriptions
           (id, appointment_id, medicines, instructions, pdf_path, created_at, secure_token, token_expires_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            prescription_id,
            appointment_id,
            json.dumps(medicines),
            instructions,
            str(pdf_path),
            now,
            secure_token,
            token_expires_at,
        )
    )
    await db.commit()

    logger.info(f"Created prescription {prescription_id} for appointment {appointment_id}")

    return {
        "id": prescription_id,
        "appointment_id": appointment_id,
        "secure_token": secure_token,
        "pdf_path": str(pdf_path),
        "created_at": now,
    }


async def get_prescription(db: aiosqlite.Connection, prescription_id: str) -> dict | None:
    """Get prescription by ID."""
    cursor = await db.execute(
        """SELECT id, appointment_id, medicines, instructions, pdf_path, created_at, secure_token, token_expires_at, whatsapp_sent
           FROM prescriptions WHERE id = ?""",
        (prescription_id,)
    )
    row = await cursor.fetchone()
    if not row:
        return None

    return {
        "id": row[0],
        "appointment_id": row[1],
        "medicines": json.loads(row[2]),
        "instructions": row[3],
        "pdf_path": row[4],
        "created_at": row[5],
        "secure_token": row[6],
        "token_expires_at": row[7],
        "whatsapp_sent": row[8] == "true",
    }


async def get_prescription_by_token(db: aiosqlite.Connection, token: str) -> dict | None:
    """Get prescription by secure token (for download URL)."""
    cursor = await db.execute(
        """SELECT id, appointment_id, pdf_path, token_expires_at
           FROM prescriptions WHERE secure_token = ?""",
        (token,)
    )
    row = await cursor.fetchone()
    if not row:
        return None

    # Check expiry
    expires_at = datetime.fromisoformat(row[3])
    if datetime.now(timezone.utc) > expires_at:
        return None

    return {
        "id": row[0],
        "appointment_id": row[1],
        "pdf_path": row[2],
    }


async def regenerate_token(db: aiosqlite.Connection, prescription_id: str) -> str:
    """Regenerate secure token for prescription (extends access)."""
    new_token = secrets.token_urlsafe(32)
    new_expiry = (datetime.now(timezone.utc) + timedelta(hours=72)).isoformat()

    await db.execute(
        "UPDATE prescriptions SET secure_token = ?, token_expires_at = ? WHERE id = ?",
        (new_token, new_expiry, prescription_id)
    )
    await db.commit()

    return new_token


async def mark_whatsapp_sent(db: aiosqlite.Connection, prescription_id: str) -> None:
    """Mark prescription as sent via WhatsApp."""
    await db.execute(
        "UPDATE prescriptions SET whatsapp_sent = 'true' WHERE id = ?",
        (prescription_id,)
    )
    await db.commit()
