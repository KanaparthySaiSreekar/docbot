"""Database connection and initialization for SQLite with WAL mode."""

import logging
import sqlite3
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
    Initialize database by executing all schema SQL scripts.

    Loads all .sql files from db/ directory in sorted order.
    Tracks applied migrations in schema_migrations table to ensure
    each file is only executed once.
    """
    settings = get_settings()
    db_path = Path(settings.database.path)
    schema_dir = Path("db")

    if not schema_dir.exists():
        logger.error(f"Schema directory not found: {schema_dir}")
        raise FileNotFoundError(f"Schema directory not found: {schema_dir}")

    # Get all .sql files in sorted order
    schema_files = sorted(schema_dir.glob("*.sql"))

    if not schema_files:
        logger.error(f"No schema files found in {schema_dir}")
        raise FileNotFoundError(f"No schema files found in {schema_dir}")

    logger.info(f"Initializing database at {db_path}")

    async with aiosqlite.connect(str(db_path)) as conn:
        # Create migration tracking table if it doesn't exist
        await conn.executescript(
            "CREATE TABLE IF NOT EXISTS schema_migrations "
            "(filename TEXT PRIMARY KEY, applied_at TEXT DEFAULT (datetime('now')));"
        )
        await conn.commit()

        # Get already-applied migrations
        cursor = await conn.execute("SELECT filename FROM schema_migrations")
        applied = {row[0] for row in await cursor.fetchall()}

        # Execute each schema file in order, skipping already-applied ones
        for schema_path in schema_files:
            if schema_path.name in applied:
                logger.info(f"Skipping already-applied schema: {schema_path.name}")
                continue
            logger.info(f"Executing schema: {schema_path.name}")
            with open(schema_path, "r", encoding="utf-8") as f:
                schema_sql = f.read()
            try:
                await conn.executescript(schema_sql)
            except sqlite3.OperationalError as e:
                # "duplicate column name" means this migration was already applied
                # before migration tracking was introduced — treat as applied.
                if "duplicate column name" in str(e):
                    logger.info(
                        f"Schema {schema_path.name} already applied (columns exist), marking as done"
                    )
                else:
                    raise
            await conn.execute(
                "INSERT INTO schema_migrations (filename) VALUES (?)",
                (schema_path.name,),
            )
            await conn.commit()

    logger.info(f"Database initialized successfully at {db_path}")
