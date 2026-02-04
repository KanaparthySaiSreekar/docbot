"""Pytest configuration and shared fixtures."""

import asyncio
from pathlib import Path
from typing import AsyncGenerator

import aiosqlite
import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def test_db() -> AsyncGenerator[aiosqlite.Connection, None]:
    """
    Create in-memory SQLite database for testing.

    Yields:
        aiosqlite.Connection: In-memory test database
    """
    conn = await aiosqlite.connect(":memory:")

    # Enable foreign keys
    await conn.execute("PRAGMA foreign_keys = ON")

    # Use WAL mode
    await conn.execute("PRAGMA journal_mode = WAL")

    # Load schema
    schema_path = Path("db/001_initial_schema.sql")
    if schema_path.exists():
        with open(schema_path, "r", encoding="utf-8") as f:
            schema_sql = f.read()
        await conn.executescript(schema_sql)
        await conn.commit()

    yield conn

    await conn.close()


@pytest.fixture
def test_client():
    """
    Create FastAPI test client.

    Returns:
        TestClient: FastAPI test client
    """
    from docbot.main import app

    return TestClient(app)
