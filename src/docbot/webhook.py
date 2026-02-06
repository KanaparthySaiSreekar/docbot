"""WhatsApp webhook endpoints for receiving messages from Meta."""

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import JSONResponse, PlainTextResponse

from docbot import bot_handler
from docbot.config import get_settings
from docbot.database import get_db
from docbot.idempotency import check_idempotency, record_event
from docbot.payment_service import process_payment_webhook
from docbot.calendar_service import create_appointment_event
from docbot.whatsapp_client import send_text

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/webhook/whatsapp")
async def verify_webhook(request: Request) -> PlainTextResponse:
    """
    Webhook verification endpoint for Meta WhatsApp setup.

    Meta sends GET request with hub.mode, hub.verify_token, hub.challenge.
    If verify_token matches settings, return challenge as plain text.
    Otherwise return 403.
    """
    mode = request.query_params.get("hub.mode")
    verify_token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    settings = get_settings()

    if mode == "subscribe" and verify_token == settings.whatsapp.verify_token:
        logger.info("WhatsApp webhook verified successfully")
        return PlainTextResponse(content=challenge)

    logger.warning(
        "WhatsApp webhook verification failed",
        extra={
            "mode": mode,
            "verify_token_match": verify_token == settings.whatsapp.verify_token
        }
    )
    raise HTTPException(status_code=403, detail="Forbidden")


@router.post("/webhook/whatsapp")
async def receive_message(request: Request) -> dict[str, str]:
    """
    Receive incoming WhatsApp messages from Meta.

    Parses webhook payload, extracts message details, deduplicates via idempotency,
    and returns 200 to Meta (always, even on errors to prevent retry storms).

    Message types supported:
    - text: Plain text messages
    - interactive.button_reply: Button click responses
    - interactive.list_reply: List selection responses
    """
    try:
        body = await request.json()

        # Extract message from webhook structure
        # WhatsApp webhook structure: body.entry[0].changes[0].value.messages[0]
        if not body.get("entry"):
            logger.warning("Webhook received with no entries", extra={"body": body})
            return {"status": "ok"}

        entry = body["entry"][0]
        if not entry.get("changes"):
            logger.warning("Webhook entry has no changes", extra={"entry": entry})
            return {"status": "ok"}

        change = entry["changes"][0]
        value = change.get("value", {})

        # Check if this is a message event
        if not value.get("messages"):
            logger.debug("Webhook received but no messages", extra={"value": value})
            return {"status": "ok"}

        message = value["messages"][0]
        sender = message.get("from")
        message_id = message.get("id")
        timestamp = message.get("timestamp")
        message_type = message.get("type")

        if not message_id:
            logger.warning("Message received without ID", extra={"message": message})
            return {"status": "ok"}

        # Check idempotency
        async for db in get_db():
            if await check_idempotency(db, message_id):
                logger.info(
                    "Duplicate message ignored (idempotency)",
                    extra={"message_id": message_id}
                )
                return {"status": "ok"}

            # Parse message content based on type
            parsed_message: dict[str, Any] = {
                "from": sender,
                "type": message_type,
                "message_id": message_id,
                "timestamp": timestamp,
                "button_id": None,
                "button_title": None,
                "text": None
            }

            if message_type == "text":
                parsed_message["text"] = message.get("text", {}).get("body")

            elif message_type == "interactive":
                interactive = message.get("interactive", {})
                interactive_type = interactive.get("type")

                if interactive_type == "button_reply":
                    button_reply = interactive.get("button_reply", {})
                    parsed_message["button_id"] = button_reply.get("id")
                    parsed_message["button_title"] = button_reply.get("title")

                elif interactive_type == "list_reply":
                    list_reply = interactive.get("list_reply", {})
                    parsed_message["button_id"] = list_reply.get("id")
                    parsed_message["button_title"] = list_reply.get("title")

            # Log the parsed message
            logger.info(
                "WhatsApp message received",
                extra={
                    "message_id": message_id,
                    "from": sender,
                    "type": message_type,
                    "parsed": parsed_message
                }
            )

            # Record the message as processed (idempotency)
            await record_event(db, message_id, "whatsapp", parsed_message)

            # Handle the message through bot handler
            try:
                await bot_handler.handle_message(parsed_message)
            except Exception as handler_error:
                # Log but don't raise - always return 200 to Meta
                logger.error(
                    "Bot handler error",
                    extra={"error": str(handler_error), "message_id": message_id},
                    exc_info=True
                )

            return {"status": "ok"}

    except Exception as e:
        # Always return 200 to Meta to prevent retry storms
        # Log errors internally for monitoring
        logger.error(
            "Error processing WhatsApp webhook",
            extra={"error": str(e)},
            exc_info=True
        )
        return {"status": "ok"}


@router.post("/webhook/razorpay")
async def razorpay_webhook(request: Request) -> JSONResponse:
    """
    Handle Razorpay payment webhooks.

    Always returns 200 to prevent retry storms.
    Signature verification done in payment_service.
    """
    try:
        body = await request.body()
        signature = request.headers.get("X-Razorpay-Signature", "")

        data = await request.json()
        event_type = data.get("event", "")
        payment_entity = data.get("payload", {}).get("payment", {}).get("entity", {})

        async for db in get_db():
            success = await process_payment_webhook(
                db,
                payload_body=body,
                signature=signature,
                event_type=event_type,
                payment_data=payment_entity
            )

            if success and event_type == "payment.captured":
                # Get appointment details for calendar and notification
                payment_link_id = payment_entity.get("payment_link_id")
                cursor = await db.execute(
                    """SELECT a.id, a.patient_phone, a.patient_name,
                              a.appointment_date, a.slot_time, a.language
                       FROM appointments a
                       JOIN payments p ON p.appointment_id = a.id
                       WHERE p.razorpay_payment_link_id = ?""",
                    (payment_link_id,)
                )
                row = await cursor.fetchone()

                if row:
                    appt_id, phone, name, date_str, slot_time, lang = row

                    # Create calendar event (non-blocking - logs alert on failure)
                    cal_result = await create_appointment_event(db, appt_id)

                    # Send confirmation with Meet link
                    if cal_result and cal_result.get("meet_link"):
                        await send_text(
                            phone,
                            f"Payment received! Your online consultation is confirmed.\n\n"
                            f"Date: {date_str}\n"
                            f"Time: {slot_time}\n\n"
                            f"Join here: {cal_result['meet_link']}\n\n"
                            f"Please join 5 minutes before your appointment."
                        )
                    else:
                        # Meet link will be sent when calendar succeeds
                        await send_text(
                            phone,
                            f"Payment received! Your online consultation is confirmed.\n\n"
                            f"Date: {date_str}\n"
                            f"Time: {slot_time}\n\n"
                            f"Your Google Meet link will be sent shortly."
                        )

        return JSONResponse({"status": "ok"})

    except Exception as e:
        logger.error(f"Razorpay webhook error: {str(e)}", exc_info=True)
        return JSONResponse({"status": "error"}, status_code=200)  # Still 200
