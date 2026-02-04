"""Tests for idempotency key checking and recording."""

import pytest

from docbot.idempotency import check_idempotency, record_event


@pytest.mark.asyncio
async def test_new_event_not_duplicate(test_db):
    """Test new event ID is not considered duplicate."""
    is_duplicate = await check_idempotency(test_db, "event_123")
    assert is_duplicate is False


@pytest.mark.asyncio
async def test_recorded_event_is_duplicate(test_db):
    """Test recorded event ID is detected as duplicate."""
    # Record an event
    await record_event(test_db, "event_456", "razorpay")
    
    # Check should return True
    is_duplicate = await check_idempotency(test_db, "event_456")
    assert is_duplicate is True


@pytest.mark.asyncio
async def test_record_stores_result(test_db):
    """Test recorded event stores result data."""
    result_data = {"status": "success", "amount": 500}
    
    await record_event(test_db, "event_789", "razorpay", result_data)
    
    # Verify stored
    cursor = await test_db.execute(
        "SELECT result FROM idempotency_keys WHERE event_id = ?",
        ("event_789",)
    )
    row = await cursor.fetchone()
    assert row is not None
    
    import json
    stored_result = json.loads(row[0])
    assert stored_result["status"] == "success"
    assert stored_result["amount"] == 500


@pytest.mark.asyncio
async def test_same_event_id_always_duplicate(test_db):
    """Test same event_id is duplicate regardless of source."""
    # Record from razorpay
    await record_event(test_db, "event_global", "razorpay")
    
    # Check should be duplicate even if checking from whatsapp context
    is_duplicate = await check_idempotency(test_db, "event_global")
    assert is_duplicate is True
