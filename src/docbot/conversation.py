"""Conversation state management for booking flow tracking."""

import json
import logging
from datetime import timedelta
from typing import Optional

import aiosqlite

from docbot.timezone_utils import utc_now

logger = logging.getLogger(__name__)

# Conversation states for the booking flow
IDLE = "IDLE"
LANGUAGE_SELECT = "LANGUAGE_SELECT"
MAIN_MENU = "MAIN_MENU"
SELECT_TYPE = "SELECT_TYPE"
SELECT_DATE = "SELECT_DATE"
SELECT_SLOT = "SELECT_SLOT"
ENTER_NAME = "ENTER_NAME"
ENTER_AGE = "ENTER_AGE"
ENTER_GENDER = "ENTER_GENDER"
CONFIRM_BOOKING = "CONFIRM_BOOKING"

# Conversation timeout (30 minutes)
CONVERSATION_TIMEOUT = timedelta(minutes=30)


async def get_conversation(
    db: aiosqlite.Connection, phone: str
) -> Optional[dict]:
    """
    Get active conversation for phone number.

    Returns None if no conversation exists or if expired.
    Automatically deletes expired conversations.

    Args:
        db: Database connection
        phone: Phone number in E.164 format

    Returns:
        dict or None: Conversation data if active, None otherwise
    """
    async with db.execute(
        "SELECT phone, state, data, started_at, updated_at, expires_at FROM conversations WHERE phone = ?",
        (phone,),
    ) as cursor:
        row = await cursor.fetchone()

    if not row:
        return None

    # Check if expired
    expires_at = row[5]
    now = utc_now().isoformat()

    if expires_at <= now:
        # Expired - delete it
        await db.execute("DELETE FROM conversations WHERE phone = ?", (phone,))
        await db.commit()
        logger.info(f"Deleted expired conversation for {phone}")
        return None

    # Parse data JSON
    data_json = row[2]
    data = json.loads(data_json) if data_json else {}

    return {
        "phone": row[0],
        "state": row[1],
        "data": data,
        "started_at": row[3],
        "updated_at": row[4],
        "expires_at": row[5],
    }


async def start_conversation(
    db: aiosqlite.Connection, phone: str, state: str = LANGUAGE_SELECT
) -> dict:
    """
    Start new conversation.

    If conversation already exists for this phone, deletes it first (BOT-09).

    Args:
        db: Database connection
        phone: Phone number in E.164 format
        state: Initial conversation state

    Returns:
        dict: New conversation data
    """
    # Delete existing conversation if any
    await db.execute("DELETE FROM conversations WHERE phone = ?", (phone,))

    now = utc_now()
    now_iso = now.isoformat()
    expires_at = (now + CONVERSATION_TIMEOUT).isoformat()

    # Create new conversation
    await db.execute(
        "INSERT INTO conversations (phone, state, data, started_at, updated_at, expires_at) VALUES (?, ?, ?, ?, ?, ?)",
        (phone, state, "{}", now_iso, now_iso, expires_at),
    )
    await db.commit()

    logger.info(f"Started conversation for {phone} in state {state}")

    return {
        "phone": phone,
        "state": state,
        "data": {},
        "started_at": now_iso,
        "updated_at": now_iso,
        "expires_at": expires_at,
    }


async def update_conversation(
    db: aiosqlite.Connection, phone: str, state: str, data: Optional[dict] = None
) -> dict:
    """
    Update conversation state and optionally merge new data.

    Resets expiry to 30 minutes from now (rolling expiry).

    Args:
        db: Database connection
        phone: Phone number in E.164 format
        state: New conversation state
        data: Optional data to merge into existing data blob

    Returns:
        dict: Updated conversation data
    """
    # Get existing conversation to merge data
    existing = await get_conversation(db, phone)

    if not existing:
        # No existing conversation - create new one
        return await start_conversation(db, phone, state)

    # Merge data
    merged_data = existing["data"].copy()
    if data:
        merged_data.update(data)

    data_json = json.dumps(merged_data)

    now = utc_now()
    now_iso = now.isoformat()
    expires_at = (now + CONVERSATION_TIMEOUT).isoformat()

    # Update conversation
    await db.execute(
        "UPDATE conversations SET state = ?, data = ?, updated_at = ?, expires_at = ? WHERE phone = ?",
        (state, data_json, now_iso, expires_at, phone),
    )
    await db.commit()

    logger.info(f"Updated conversation for {phone} to state {state}")

    return {
        "phone": phone,
        "state": state,
        "data": merged_data,
        "started_at": existing["started_at"],
        "updated_at": now_iso,
        "expires_at": expires_at,
    }


async def end_conversation(db: aiosqlite.Connection, phone: str) -> None:
    """
    End conversation for phone number.

    Deletes the conversation (booking complete or cancelled).

    Args:
        db: Database connection
        phone: Phone number in E.164 format
    """
    await db.execute("DELETE FROM conversations WHERE phone = ?", (phone,))
    await db.commit()

    logger.info(f"Ended conversation for {phone}")


async def cleanup_expired_conversations(db: aiosqlite.Connection) -> int:
    """
    Delete all expired conversations.

    Args:
        db: Database connection

    Returns:
        int: Number of conversations deleted
    """
    now = utc_now().isoformat()

    async with db.execute(
        "DELETE FROM conversations WHERE expires_at <= ? RETURNING phone", (now,)
    ) as cursor:
        deleted = await cursor.fetchall()

    await db.commit()

    count = len(deleted)
    if count > 0:
        logger.info(f"Cleaned up {count} expired conversations")

    return count
