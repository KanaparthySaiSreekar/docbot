"""Patient data persistence for language preferences and profile."""

import logging
from typing import Optional

import aiosqlite

from docbot.timezone_utils import utc_now

logger = logging.getLogger(__name__)

VALID_LANGUAGES = {"en", "te", "hi"}


async def get_or_create_patient(db: aiosqlite.Connection, phone: str) -> dict:
    """
    Get patient by phone number, creating if not exists.

    Args:
        db: Database connection
        phone: Phone number in E.164 format

    Returns:
        dict: Patient data with phone, language, name, created_at, updated_at
    """
    # Try to get existing patient
    async with db.execute(
        "SELECT phone, language, name, created_at, updated_at FROM patients WHERE phone = ?",
        (phone,),
    ) as cursor:
        row = await cursor.fetchone()

    if row:
        return {
            "phone": row[0],
            "language": row[1],
            "name": row[2],
            "created_at": row[3],
            "updated_at": row[4],
        }

    # Create new patient with default language
    now = utc_now().isoformat()
    await db.execute(
        "INSERT INTO patients (phone, language, created_at, updated_at) VALUES (?, ?, ?, ?)",
        (phone, "en", now, now),
    )
    await db.commit()

    logger.info(f"Created new patient: {phone}")

    return {
        "phone": phone,
        "language": "en",
        "name": None,
        "created_at": now,
        "updated_at": now,
    }


async def get_language(db: aiosqlite.Connection, phone: str) -> str:
    """
    Get language preference for phone number.

    Args:
        db: Database connection
        phone: Phone number in E.164 format

    Returns:
        str: Language code ('en', 'te', 'hi'), defaults to 'en' if patient not found
    """
    async with db.execute(
        "SELECT language FROM patients WHERE phone = ?", (phone,)
    ) as cursor:
        row = await cursor.fetchone()

    if row:
        return row[0]

    return "en"


async def set_language(db: aiosqlite.Connection, phone: str, language: str) -> None:
    """
    Set language preference for phone number.

    Creates patient if not exists.

    Args:
        db: Database connection
        phone: Phone number in E.164 format
        language: Language code ('en', 'te', 'hi')

    Raises:
        ValueError: If language code is invalid
    """
    if language not in VALID_LANGUAGES:
        raise ValueError(
            f"Invalid language code: {language}. Must be one of {VALID_LANGUAGES}"
        )

    now = utc_now().isoformat()

    # Try to update existing patient
    async with db.execute(
        "UPDATE patients SET language = ?, updated_at = ? WHERE phone = ?",
        (language, now, phone),
    ) as cursor:
        if cursor.rowcount > 0:
            await db.commit()
            logger.info(f"Updated language for {phone} to {language}")
            return

    # Patient doesn't exist, create it
    await db.execute(
        "INSERT INTO patients (phone, language, created_at, updated_at) VALUES (?, ?, ?, ?)",
        (phone, language, now, now),
    )
    await db.commit()

    logger.info(f"Created patient {phone} with language {language}")


async def update_patient_name(
    db: aiosqlite.Connection, phone: str, name: str
) -> None:
    """
    Update patient name.

    Args:
        db: Database connection
        phone: Phone number in E.164 format
        name: Patient name
    """
    now = utc_now().isoformat()

    await db.execute(
        "UPDATE patients SET name = ?, updated_at = ? WHERE phone = ?",
        (name, now, phone),
    )
    await db.commit()

    logger.info(f"Updated name for {phone}")
