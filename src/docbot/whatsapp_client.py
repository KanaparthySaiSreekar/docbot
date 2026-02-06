"""WhatsApp Cloud API client for sending messages with retry logic."""

import asyncio
import logging
from typing import Any

import httpx

from docbot.alerts import log_alert
from docbot.config import get_settings

logger = logging.getLogger(__name__)


async def send_text(to: str, text: str) -> dict[str, Any] | None:
    """
    Send plain text message via WhatsApp Cloud API.

    Args:
        to: Recipient phone number (including country code)
        text: Message text

    Returns:
        dict | None: API response on success, None on complete failure
    """
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text}
    }
    return await _send_message(payload)


async def send_buttons(to: str, body_text: str, buttons: list[dict]) -> dict[str, Any] | None:
    """
    Send interactive reply button message via WhatsApp Cloud API.

    Args:
        to: Recipient phone number (including country code)
        body_text: Message body text
        buttons: List of button dicts with 'id' and 'title' keys (max 3 buttons)

    Returns:
        dict | None: API response on success, None on complete failure
    """
    # Format buttons for WhatsApp API
    formatted_buttons = [
        {
            "type": "reply",
            "reply": {
                "id": btn["id"],
                "title": btn["title"]
            }
        }
        for btn in buttons
    ]

    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {"text": body_text},
            "action": {"buttons": formatted_buttons}
        }
    }
    return await _send_message(payload)


async def send_list(to: str, body_text: str, button_text: str, sections: list[dict]) -> dict[str, Any] | None:
    """
    Send interactive list message via WhatsApp Cloud API.

    Args:
        to: Recipient phone number (including country code)
        body_text: Message body text
        button_text: Text for list button
        sections: List sections with rows (WhatsApp format)

    Returns:
        dict | None: API response on success, None on complete failure
    """
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "list",
            "body": {"text": body_text},
            "action": {
                "button": button_text,
                "sections": sections
            }
        }
    }
    return await _send_message(payload)


async def _send_message(payload: dict[str, Any]) -> dict[str, Any] | None:
    """
    Internal helper to send WhatsApp message with retry logic.

    Retries on 5xx or network errors with exponential backoff: 1s, 2s, 4s (3 attempts max).
    Logs failures but does not raise exceptions.

    Args:
        payload: WhatsApp API message payload

    Returns:
        dict | None: API response JSON on success, None on complete failure
    """
    settings = get_settings()
    api_version = settings.whatsapp.api_version
    phone_number_id = settings.whatsapp.phone_number_id
    access_token = settings.whatsapp.access_token

    url = f"https://graph.facebook.com/{api_version}/{phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    # Retry configuration
    max_attempts = 3
    backoff_delays = [1, 2, 4]  # seconds

    async with httpx.AsyncClient() as client:
        for attempt in range(max_attempts):
            try:
                response = await client.post(url, json=payload, headers=headers, timeout=10.0)

                # Success - return response
                if 200 <= response.status_code < 300:
                    return response.json()

                # Server error - retry
                if response.status_code >= 500:
                    if attempt < max_attempts - 1:
                        delay = backoff_delays[attempt]
                        logger.warning(
                            f"WhatsApp API returned {response.status_code}, retrying in {delay}s (attempt {attempt + 1}/{max_attempts})",
                            extra={
                                "status_code": response.status_code,
                                "attempt": attempt + 1,
                                "retry_delay": delay
                            }
                        )
                        await asyncio.sleep(delay)
                        continue
                    else:
                        # Final attempt failed
                        logger.error(
                            f"WhatsApp API failed after {max_attempts} attempts: {response.status_code}",
                            extra={
                                "status_code": response.status_code,
                                "response_text": response.text
                            }
                        )
                        log_alert(
                            "ERROR",
                            "whatsapp_send_failure",
                            f"Failed to send WhatsApp message after {max_attempts} attempts",
                            {
                                "status_code": response.status_code,
                                "response": response.text,
                                "to": payload.get("to")
                            }
                        )
                        return None

                # Client error (4xx) - don't retry
                logger.error(
                    f"WhatsApp API client error: {response.status_code}",
                    extra={
                        "status_code": response.status_code,
                        "response_text": response.text
                    }
                )
                log_alert(
                    "ERROR",
                    "whatsapp_send_failure",
                    f"WhatsApp API client error: {response.status_code}",
                    {
                        "status_code": response.status_code,
                        "response": response.text,
                        "to": payload.get("to")
                    }
                )
                return None

            except (httpx.RequestError, httpx.TimeoutException) as e:
                # Network error - retry
                if attempt < max_attempts - 1:
                    delay = backoff_delays[attempt]
                    logger.warning(
                        f"WhatsApp API network error, retrying in {delay}s (attempt {attempt + 1}/{max_attempts}): {e}",
                        extra={
                            "error": str(e),
                            "attempt": attempt + 1,
                            "retry_delay": delay
                        }
                    )
                    await asyncio.sleep(delay)
                    continue
                else:
                    # Final attempt failed
                    logger.error(
                        f"WhatsApp API network error after {max_attempts} attempts: {e}",
                        extra={"error": str(e)}
                    )
                    log_alert(
                        "ERROR",
                        "whatsapp_send_failure",
                        f"WhatsApp API network error after {max_attempts} attempts",
                        {
                            "error": str(e),
                            "to": payload.get("to")
                        }
                    )
                    return None

    return None
