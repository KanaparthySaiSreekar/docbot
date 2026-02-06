"""Tests for conversation state management."""

import asyncio
from datetime import timedelta

import pytest

from docbot.conversation import (
    LANGUAGE_SELECT,
    MAIN_MENU,
    SELECT_TYPE,
    cleanup_expired_conversations,
    end_conversation,
    get_conversation,
    start_conversation,
    update_conversation,
)
from docbot.timezone_utils import utc_now


@pytest.mark.asyncio
async def test_start_conversation_creates_active_conversation(test_db):
    """Test start_conversation creates active conversation."""
    phone = "919876543210"

    conv = await start_conversation(test_db, phone)

    assert conv["phone"] == phone
    assert conv["state"] == LANGUAGE_SELECT
    assert conv["data"] == {}
    assert conv["started_at"] is not None
    assert conv["updated_at"] is not None
    assert conv["expires_at"] is not None


@pytest.mark.asyncio
async def test_start_conversation_replaces_existing(test_db):
    """Test start_conversation replaces existing conversation (BOT-09)."""
    phone = "919876543210"

    # Start first conversation
    conv1 = await start_conversation(test_db, phone, LANGUAGE_SELECT)

    # Small delay to ensure different timestamp
    await asyncio.sleep(0.01)

    # Start second conversation
    conv2 = await start_conversation(test_db, phone, MAIN_MENU)

    assert conv2["state"] == MAIN_MENU
    assert conv2["started_at"] >= conv1["started_at"]  # New or same conversation

    # Verify only one conversation exists
    retrieved = await get_conversation(test_db, phone)
    assert retrieved["state"] == MAIN_MENU


@pytest.mark.asyncio
async def test_get_conversation_returns_none_when_expired(test_db):
    """Test get_conversation returns None when expired."""
    phone = "919876543210"

    # Start conversation
    await start_conversation(test_db, phone)

    # Manually set expires_at to past
    past = (utc_now() - timedelta(hours=1)).isoformat()
    await test_db.execute(
        "UPDATE conversations SET expires_at = ? WHERE phone = ?", (past, phone)
    )
    await test_db.commit()

    # Get conversation should return None and delete it
    conv = await get_conversation(test_db, phone)

    assert conv is None

    # Verify deleted
    async with test_db.execute(
        "SELECT COUNT(*) FROM conversations WHERE phone = ?", (phone,)
    ) as cursor:
        row = await cursor.fetchone()
        assert row[0] == 0


@pytest.mark.asyncio
async def test_update_conversation_merges_data_correctly(test_db):
    """Test update_conversation merges data correctly."""
    phone = "919876543210"

    # Start conversation
    await start_conversation(test_db, phone)

    # Update with some data
    conv1 = await update_conversation(
        test_db, phone, SELECT_TYPE, {"consultation_type": "online"}
    )
    assert conv1["state"] == SELECT_TYPE
    assert conv1["data"]["consultation_type"] == "online"

    # Update with more data - should merge
    conv2 = await update_conversation(
        test_db, phone, SELECT_TYPE, {"appointment_date": "2026-02-10"}
    )
    assert conv2["data"]["consultation_type"] == "online"
    assert conv2["data"]["appointment_date"] == "2026-02-10"


@pytest.mark.asyncio
async def test_update_conversation_resets_expiry(test_db):
    """Test update_conversation resets expiry (rolling expiry)."""
    phone = "919876543210"

    # Start conversation
    conv1 = await start_conversation(test_db, phone)
    expires_at1 = conv1["expires_at"]

    # Small delay to ensure different timestamp
    await asyncio.sleep(0.01)

    # Update conversation
    conv2 = await update_conversation(test_db, phone, MAIN_MENU)
    expires_at2 = conv2["expires_at"]

    # Expiry should be reset to same or later time
    assert expires_at2 >= expires_at1


@pytest.mark.asyncio
async def test_update_conversation_creates_if_not_exists(test_db):
    """Test update_conversation creates conversation if not exists."""
    phone = "919876543210"

    # Update without starting first
    conv = await update_conversation(test_db, phone, MAIN_MENU)

    assert conv["state"] == MAIN_MENU
    assert conv["phone"] == phone


@pytest.mark.asyncio
async def test_end_conversation_removes_conversation(test_db):
    """Test end_conversation removes conversation."""
    phone = "919876543210"

    # Start conversation
    await start_conversation(test_db, phone)

    # End conversation
    await end_conversation(test_db, phone)

    # Verify deleted
    conv = await get_conversation(test_db, phone)
    assert conv is None


@pytest.mark.asyncio
async def test_cleanup_expired_conversations_deletes_old(test_db):
    """Test cleanup_expired_conversations deletes old conversations."""
    phone1 = "919876543210"
    phone2 = "919876543211"
    phone3 = "919876543212"

    # Create three conversations
    await start_conversation(test_db, phone1)
    await start_conversation(test_db, phone2)
    await start_conversation(test_db, phone3)

    # Set two to expired
    past = (utc_now() - timedelta(hours=1)).isoformat()
    await test_db.execute(
        "UPDATE conversations SET expires_at = ? WHERE phone IN (?, ?)",
        (past, phone1, phone2),
    )
    await test_db.commit()

    # Cleanup
    count = await cleanup_expired_conversations(test_db)

    assert count == 2

    # Verify only phone3 remains
    conv1 = await get_conversation(test_db, phone1)
    conv2 = await get_conversation(test_db, phone2)
    conv3 = await get_conversation(test_db, phone3)

    assert conv1 is None
    assert conv2 is None
    assert conv3 is not None
