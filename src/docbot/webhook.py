"""WhatsApp webhook endpoints for receiving messages from Meta."""

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import PlainTextResponse

from docbot import bot_handler
from docbot.config import get_settings
from docbot.database import get_db
from docbot.idempotency import check_idempotency, record_event

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
