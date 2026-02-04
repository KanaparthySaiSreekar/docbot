"""Idempotency key checking and recording for webhook deduplication."""

import json
from typing import Any, Optional

import aiosqlite

from docbot.timezone_utils import utc_now


async def check_idempotency(db: aiosqlite.Connection, event_id: str) -> bool:
    """
    Check if event ID has already been processed.

    Args:
        db: Database connection
        event_id: Unique event identifier

    Returns:
        bool: True if event was already processed, False otherwise
    """
    cursor = await db.execute(
        "SELECT 1 FROM idempotency_keys WHERE event_id = ?",
        (event_id,)
    )
    row = await cursor.fetchone()
    return row is not None


async def record_event(
    db: aiosqlite.Connection,
    event_id: str,
    source: str,
    result: Optional[dict[str, Any]] = None
) -> None:
    """
    Record event as processed with optional result data.

    Args:
        db: Database connection
        event_id: Unique event identifier
        source: Event source (e.g., 'razorpay', 'whatsapp')
        result: Optional result data to store as JSON
    """
    processed_at = utc_now().isoformat()
    result_json = json.dumps(result) if result else None

    await db.execute(
        "INSERT INTO idempotency_keys (event_id, source, processed_at, result) VALUES (?, ?, ?, ?)",
        (event_id, source, processed_at, result_json)
    )
    await db.commit()
