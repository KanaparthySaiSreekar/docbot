"""Database connection and initialization for SQLite with WAL mode."""

import logging
from pathlib import Path
from typing import AsyncGenerator

import aiosqlite

from docbot.config import get_settings

logger = logging.getLogger(__name__)


async def get_db() -> AsyncGenerator[aiosqlite.Connection, None]:
    """
    Get async database connection with proper configuration.

    Yields:
        aiosqlite.Connection: Configured SQLite connection
    """
    settings = get_settings()
    db_path = settings.database.path

    conn = await aiosqlite.connect(db_path)

    # Enable foreign keys
    await conn.execute("PRAGMA foreign_keys = ON")

    # Use WAL mode for better concurrent read performance
    await conn.execute("PRAGMA journal_mode = WAL")

    # Use BEGIN IMMEDIATE for write transactions (prevents lock escalation issues)
    conn.isolation_level = "IMMEDIATE"

    try:
        yield conn
    finally:
        await conn.close()


async def init_db() -> None:
    """
    Initialize database by executing schema SQL script.

    Creates all tables, indexes, and constraints defined in db/001_initial_schema.sql.
    Safe to run multiple times - uses CREATE TABLE IF NOT EXISTS.
    """
    settings = get_settings()
    db_path = Path(settings.database.path)
    schema_path = Path("db/001_initial_schema.sql")

    if not schema_path.exists():
        logger.error(f"Schema file not found: {schema_path}")
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    logger.info(f"Initializing database at {db_path}")

    # Read schema SQL
    with open(schema_path, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    # Execute schema
    async with aiosqlite.connect(str(db_path)) as conn:
        await conn.executescript(schema_sql)
        await conn.commit()

    logger.info(f"Database initialized successfully at {db_path}")
