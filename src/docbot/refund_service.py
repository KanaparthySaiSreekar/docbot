"""Refund service with exponential backoff retry."""

import uuid
import httpx
from datetime import timedelta

from docbot.config import get_settings
from docbot.razorpay_client import verify_webhook_signature
from docbot.idempotency import check_idempotency, record_event
from docbot.state_machine import transition, AppointmentStatus
from docbot.timezone_utils import utc_now
from docbot.alerts import log_alert
import logging

logger = logging.getLogger(__name__)

RAZORPAY_API_BASE = "https://api.razorpay.com/v1"
MAX_RETRY_COUNT = 5
BACKOFF_BASE_SECONDS = 60  # 1 min, 2 min, 4 min, 8 min, 16 min


async def _call_razorpay_refund(payment_id: str, amount_paise: int) -> dict | None:
    """
    Call Razorpay refund API.

    Args:
        payment_id: Razorpay payment ID
        amount_paise: Amount to refund in paise

    Returns:
        Refund response dict or None on failure
    """
    settings = get_settings()

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{RAZORPAY_API_BASE}/payments/{payment_id}/refund",
                json={"amount": amount_paise},
                auth=(settings.razorpay.key_id, settings.razorpay.key_secret),
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        logger.error("Razorpay refund API failed", payment_id=payment_id, error=str(e))
        return None


async def initiate_refund(db, appointment_id: str) -> bool:
    """
    Initiate refund for a cancelled appointment.

    Args:
        db: Database connection
        appointment_id: Appointment UUID

    Returns:
        bool: True if refund processed or not needed, False if pending retry
    """
    # Get payment info
    cursor = await db.execute(
        """SELECT a.razorpay_payment_id, p.amount_paise
           FROM appointments a
           LEFT JOIN payments p ON p.appointment_id = a.id
           WHERE a.id = ?""",
        (appointment_id,)
    )
    row = await cursor.fetchone()

    if not row or not row[0]:
        # No payment to refund (offline appointment)
        logger.info("No payment to refund", appointment_id=appointment_id)
        return True

    payment_id, amount = row

    # Check if refund already exists
    cursor = await db.execute(
        "SELECT id, status FROM refunds WHERE appointment_id = ?",
        (appointment_id,)
    )
    existing = await cursor.fetchone()
    if existing:
        logger.info("Refund already exists", appointment_id=appointment_id, status=existing[1])
        return existing[1] == "PROCESSED"

    # Try to process refund
    result = await _call_razorpay_refund(payment_id, amount)
    now = utc_now().isoformat()
    refund_id = str(uuid.uuid4())

    if result:
        # Refund successful
        await db.execute(
            """INSERT INTO refunds
               (id, appointment_id, razorpay_payment_id, razorpay_refund_id,
                amount_paise, status, retry_count, created_at, processed_at)
               VALUES (?, ?, ?, ?, ?, 'PROCESSED', 0, ?, ?)""",
            (refund_id, appointment_id, payment_id, result["id"], amount, now, now)
        )

        # Update appointment
        await db.execute(
            """UPDATE appointments
               SET status = ?, razorpay_refund_id = ?, refunded_at = ?, updated_at = ?
               WHERE id = ?""",
            (AppointmentStatus.REFUNDED.value, result["id"], now, now, appointment_id)
        )
        await db.commit()

        logger.info("Refund processed", appointment_id=appointment_id, refund_id=result["id"])
        return True
    else:
        # Refund failed - create pending for retry
        next_retry = (utc_now() + timedelta(seconds=BACKOFF_BASE_SECONDS)).isoformat()

        await db.execute(
            """INSERT INTO refunds
               (id, appointment_id, razorpay_payment_id, amount_paise,
                status, retry_count, next_retry_at, created_at)
               VALUES (?, ?, ?, ?, 'PENDING', 1, ?, ?)""",
            (refund_id, appointment_id, payment_id, amount, next_retry, now)
        )
        await db.commit()

        log_alert("WARNING", "refund_failed_pending_retry", "Refund failed, pending retry", {
            "appointment_id": appointment_id,
            "payment_id": payment_id
        })

        return False


async def retry_failed_refunds(db) -> int:
    """
    Retry pending refunds that are due.

    Should be called periodically (e.g., every minute).

    Returns:
        int: Number of refunds successfully processed
    """
    now = utc_now().isoformat()

    cursor = await db.execute(
        """SELECT id, appointment_id, razorpay_payment_id, amount_paise, retry_count
           FROM refunds
           WHERE status = 'PENDING' AND next_retry_at <= ?
           ORDER BY next_retry_at
           LIMIT 10""",
        (now,)
    )
    rows = await cursor.fetchall()

    processed = 0

    for row in rows:
        refund_id, appt_id, payment_id, amount, retry_count = row

        if retry_count >= MAX_RETRY_COUNT:
            # Mark as failed
            await db.execute(
                "UPDATE refunds SET status = 'FAILED' WHERE id = ?",
                (refund_id,)
            )
            await db.commit()
            log_alert("ERROR", "refund_max_retries_exceeded", "Refund max retries exceeded", {
                "appointment_id": appt_id,
                "refund_id": refund_id
            })
            continue

        result = await _call_razorpay_refund(payment_id, amount)
        now_ts = utc_now().isoformat()

        if result:
            await db.execute(
                """UPDATE refunds
                   SET status = 'PROCESSED', razorpay_refund_id = ?, processed_at = ?
                   WHERE id = ?""",
                (result["id"], now_ts, refund_id)
            )
            await db.execute(
                """UPDATE appointments
                   SET status = ?, razorpay_refund_id = ?, refunded_at = ?, updated_at = ?
                   WHERE id = ?""",
                (AppointmentStatus.REFUNDED.value, result["id"], now_ts, now_ts, appt_id)
            )
            await db.commit()
            processed += 1
            logger.info("Refund retry successful", appointment_id=appt_id)
        else:
            # Schedule next retry with exponential backoff
            next_retry = (utc_now() + timedelta(
                seconds=BACKOFF_BASE_SECONDS * (2 ** retry_count)
            )).isoformat()

            await db.execute(
                """UPDATE refunds
                   SET retry_count = ?, next_retry_at = ?
                   WHERE id = ?""",
                (retry_count + 1, next_retry, refund_id)
            )
            await db.commit()

    return processed


async def process_refund_webhook(
    db,
    payload_body: bytes,
    signature: str,
    event_type: str,
    refund_data: dict
) -> bool:
    """
    Process Razorpay refund webhook.

    Args:
        db: Database connection
        payload_body: Raw webhook body
        signature: X-Razorpay-Signature header
        event_type: Event type
        refund_data: Refund entity from webhook

    Returns:
        bool: True if processed successfully
    """
    if not verify_webhook_signature(payload_body, signature):
        logger.warning("Invalid refund webhook signature")
        return False

    payment_id = refund_data.get("payment_id")
    refund_id = refund_data.get("id")

    if not payment_id:
        return False

    # Check idempotency
    event_id = f"razorpay:refund:{refund_id}"
    if await check_idempotency(db, event_id):
        return True

    # Find refund record
    cursor = await db.execute(
        "SELECT id, appointment_id FROM refunds WHERE razorpay_payment_id = ?",
        (payment_id,)
    )
    row = await cursor.fetchone()

    if not row:
        logger.warning("Refund record not found", payment_id=payment_id)
        return False

    db_refund_id, appointment_id = row
    now = utc_now().isoformat()

    if event_type == "refund.processed":
        await db.execute(
            """UPDATE refunds
               SET status = 'PROCESSED', razorpay_refund_id = ?, processed_at = ?
               WHERE id = ?""",
            (refund_id, now, db_refund_id)
        )
        await db.execute(
            """UPDATE appointments
               SET status = ?, razorpay_refund_id = ?, refunded_at = ?, updated_at = ?
               WHERE id = ?""",
            (AppointmentStatus.REFUNDED.value, refund_id, now, now, appointment_id)
        )
        await db.commit()
        await record_event(db, event_id, "razorpay", {"appointment_id": appointment_id})

        logger.info("Refund webhook processed", appointment_id=appointment_id)
        return True

    return False
