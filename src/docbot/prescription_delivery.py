"""WhatsApp delivery for prescriptions."""
import logging

import aiosqlite

from docbot.config import get_settings
from docbot.i18n import get_message
from docbot.prescription_service import get_prescription, mark_whatsapp_sent, regenerate_token
from docbot.whatsapp_client import send_text

logger = logging.getLogger(__name__)


async def send_prescription_to_patient(
    db: aiosqlite.Connection,
    prescription_id: str,
) -> bool:
    """
    Send prescription download link to patient via WhatsApp.

    Regenerates token before sending to ensure fresh 72-hour expiry.
    Returns True on success, False on failure.
    """
    prescription = await get_prescription(db, prescription_id)
    if not prescription:
        logger.error(f"Prescription not found: {prescription_id}")
        return False

    # Get patient details from appointment
    cursor = await db.execute(
        "SELECT patient_phone, patient_name, language FROM appointments WHERE id = ?",
        (prescription["appointment_id"],)
    )
    row = await cursor.fetchone()
    if not row:
        logger.error(f"Appointment not found for prescription: {prescription_id}")
        return False

    patient_phone, patient_name, language = row

    # Regenerate token for fresh 72-hour window
    new_token = await regenerate_token(db, prescription_id)

    # Build download URL
    settings = get_settings()
    download_url = f"{settings.app.base_url}/prescriptions/download/{new_token}"

    # Send message
    message = get_message(
        "prescription_ready",
        lang=language or "en",
        name=patient_name,
        download_link=download_url
    )

    result = await send_text(patient_phone, message)

    if result:
        await mark_whatsapp_sent(db, prescription_id)
        logger.info(
            "Prescription sent to patient",
            extra={"prescription_id": prescription_id}  # No PII
        )
        return True
    else:
        logger.error(
            "Failed to send prescription to patient",
            extra={"prescription_id": prescription_id}
        )
        return False
