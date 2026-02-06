"""Payment service for appointment payment processing."""

import logging
import uuid
from docbot.razorpay_client import create_payment_link, verify_webhook_signature
from docbot.idempotency import check_idempotency, record_event
from docbot.state_machine import transition, AppointmentStatus
from docbot.timezone_utils import utc_now
from docbot.config import get_settings
from docbot.alerts import log_alert

logger = logging.getLogger(__name__)

CONSULTATION_FEE_PAISE = 50000  # ₹500


async def create_payment_for_appointment(db, appointment_id: str) -> dict | None:
    """
    Create a payment link for a PENDING_PAYMENT appointment.

    Args:
        db: Database connection
        appointment_id: Appointment UUID

    Returns:
        dict with payment_link_id, short_url on success
        None on failure

    Raises:
        ValueError: If appointment not found or not in PENDING_PAYMENT status
    """
    # Fetch appointment
    cursor = await db.execute(
        "SELECT id, patient_name, patient_phone, status FROM appointments WHERE id = ?",
        (appointment_id,)
    )
    row = await cursor.fetchone()

    if not row:
        raise ValueError(f"Appointment {appointment_id} not found")

    appt_id, name, phone, status = row

    if status != AppointmentStatus.PENDING_PAYMENT.value:
        raise ValueError(f"Appointment {appointment_id} is {status}, expected PENDING_PAYMENT")

    # Check for existing payment
    cursor = await db.execute(
        "SELECT razorpay_payment_link_id, id FROM payments WHERE appointment_id = ?",
        (appointment_id,)
    )
    existing = await cursor.fetchone()

    if existing and existing[0]:
        # Return existing payment link ID for re-fetch
        logger.info(f"Payment already exists for appointment {appointment_id}")
        return {"payment_link_id": existing[0], "payment_id": existing[1]}

    # Create payment link via Razorpay
    settings = get_settings()
    callback_url = f"{settings.app.base_url}/payment/callback"

    # Clean phone number (remove +91 if present)
    clean_phone = phone.lstrip("+").replace("91", "", 1) if phone.startswith("+91") else phone

    result = await create_payment_link(
        amount_paise=CONSULTATION_FEE_PAISE,
        receipt=appointment_id,
        description="Online Consultation - DocBot",
        customer_name=name,
        customer_phone=clean_phone,
        callback_url=callback_url
    )

    if not result:
        return None

    # Store payment record
    payment_id = str(uuid.uuid4())
    now = utc_now().isoformat()

    await db.execute(
        """INSERT INTO payments
           (id, appointment_id, razorpay_payment_link_id, amount_paise, status, created_at)
           VALUES (?, ?, ?, ?, 'PENDING', ?)""",
        (payment_id, appointment_id, result["payment_link_id"], CONSULTATION_FEE_PAISE, now)
    )
    await db.commit()

    return {
        "payment_id": payment_id,
        "payment_link_id": result["payment_link_id"],
        "short_url": result["short_url"]
    }


async def process_payment_webhook(
    db,
    payload_body: bytes,
    signature: str,
    event_type: str,
    payment_data: dict
) -> bool:
    """
    Process Razorpay payment webhook.

    Args:
        db: Database connection
        payload_body: Raw webhook body for signature verification
        signature: X-Razorpay-Signature header
        event_type: Razorpay event type (e.g., 'payment.captured')
        payment_data: Parsed payment entity from webhook

    Returns:
        bool: True if processed successfully
    """
    # Verify signature
    if not verify_webhook_signature(payload_body, signature):
        logger.warning("Invalid Razorpay webhook signature")
        return False

    # Extract payment link ID from notes or payment_link_id field
    payment_link_id = payment_data.get("payment_link_id")
    razorpay_payment_id = payment_data.get("id")

    if not payment_link_id:
        logger.warning(f"Missing payment_link_id in webhook (payment_id={razorpay_payment_id})")
        return False

    # Check idempotency
    event_id = f"razorpay:{razorpay_payment_id}:{event_type}"
    if await check_idempotency(db, event_id):
        logger.info(f"Duplicate webhook, skipping (event_id={event_id})")
        return True  # Already processed

    # Find payment record
    cursor = await db.execute(
        "SELECT id, appointment_id FROM payments WHERE razorpay_payment_link_id = ?",
        (payment_link_id,)
    )
    payment_row = await cursor.fetchone()

    if not payment_row:
        logger.warning(f"Payment record not found (payment_link_id={payment_link_id})")
        return False

    payment_id, appointment_id = payment_row

    # Handle payment.captured event
    if event_type == "payment.captured":
        now = utc_now().isoformat()

        # Update payment record
        await db.execute(
            """UPDATE payments
               SET status = 'CAPTURED', razorpay_payment_id = ?, captured_at = ?
               WHERE id = ?""",
            (razorpay_payment_id, now, payment_id)
        )

        # Transition appointment to CONFIRMED
        await db.execute(
            """UPDATE appointments
               SET status = ?, razorpay_payment_id = ?, updated_at = ?
               WHERE id = ? AND status = ?""",
            (AppointmentStatus.CONFIRMED.value, razorpay_payment_id, now,
             appointment_id, AppointmentStatus.PENDING_PAYMENT.value)
        )

        await db.commit()

        # Record idempotency
        await record_event(db, event_id, "razorpay", {"appointment_id": appointment_id})

        logger.info(f"Payment captured (appointment_id={appointment_id}, payment_id={razorpay_payment_id})")
        return True

    return False
