"""Razorpay API client for payment processing."""

import hashlib
import hmac
import logging
import httpx
from docbot.config import get_settings
from docbot.alerts import log_alert

logger = logging.getLogger(__name__)

RAZORPAY_API_BASE = "https://api.razorpay.com/v1"

async def create_payment_link(
    amount_paise: int,
    receipt: str,
    description: str,
    customer_name: str,
    customer_phone: str,
    callback_url: str | None = None
) -> dict | None:
    """
    Create a Razorpay payment link.

    Args:
        amount_paise: Amount in paise (50000 = ₹500)
        receipt: Unique receipt ID (use appointment_id)
        description: Payment description
        customer_name: Patient name
        customer_phone: Patient phone (without +91)
        callback_url: Optional redirect URL after payment

    Returns:
        dict with payment_link_id, short_url on success
        None on failure (logs alert)
    """
    settings = get_settings()

    payload = {
        "amount": amount_paise,
        "currency": "INR",
        "accept_partial": False,
        "description": description,
        "customer": {
            "name": customer_name,
            "contact": customer_phone
        },
        "notify": {
            "sms": False,  # We send via WhatsApp
            "email": False
        },
        "receipt": receipt,
        "expire_by": None  # No expiry - we handle via soft-lock
    }

    if callback_url:
        payload["callback_url"] = callback_url
        payload["callback_method"] = "get"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{RAZORPAY_API_BASE}/payment_links",
                json=payload,
                auth=(settings.razorpay.key_id, settings.razorpay.key_secret),
                timeout=30.0
            )
            response.raise_for_status()
            data = response.json()
            return {
                "payment_link_id": data["id"],
                "short_url": data["short_url"]
            }
    except httpx.HTTPError as e:
        log_alert("ERROR", "payment_link_creation_failed",
                  "Failed to create Razorpay payment link", {
            "receipt": receipt,
            "error": str(e)
        })
        logger.error(f"Failed to create payment link: {str(e)} (receipt={receipt})")
        return None


def verify_webhook_signature(payload_body: bytes, signature: str) -> bool:
    """
    Verify Razorpay webhook signature using HMAC-SHA256.

    Args:
        payload_body: Raw request body bytes
        signature: X-Razorpay-Signature header value

    Returns:
        bool: True if signature is valid
    """
    if not signature:
        return False

    settings = get_settings()
    expected = hmac.new(
        settings.razorpay.webhook_secret.encode(),
        payload_body,
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(expected, signature)
