"""Tests for Google Calendar client."""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
from zoneinfo import ZoneInfo

from docbot.google_calendar_client import create_event, delete_event, get_event


@pytest.fixture
def mock_calendar_service():
    """Mock Google Calendar service."""
    with patch("docbot.google_calendar_client._get_calendar_service") as mock:
        service = MagicMock()
        mock.return_value = service
        yield service


@pytest.mark.asyncio
async def test_create_event_without_meet(mock_calendar_service):
    """Test creating event without Meet link."""
    mock_calendar_service.events().insert().execute.return_value = {
        "id": "event123",
        "summary": "Test Event"
    }

    result = await create_event(
        summary="Test Event",
        description="Test description",
        start_time=datetime(2026, 2, 10, 10, 0, tzinfo=ZoneInfo("Asia/Kolkata")),
        location="Test Clinic"
    )

    assert result is not None
    assert result["event_id"] == "event123"
    assert "meet_link" not in result


@pytest.mark.asyncio
async def test_create_event_with_meet_link(mock_calendar_service):
    """Test creating event with Google Meet link."""
    mock_calendar_service.events().insert().execute.return_value = {
        "id": "event456",
        "summary": "Online Consultation",
        "conferenceData": {
            "entryPoints": [
                {"entryPointType": "video", "uri": "https://meet.google.com/abc-def-ghi"}
            ]
        }
    }

    result = await create_event(
        summary="Online Consultation",
        description="Patient consultation",
        start_time=datetime(2026, 2, 10, 10, 0, tzinfo=ZoneInfo("Asia/Kolkata")),
        add_meet_link=True
    )

    assert result is not None
    assert result["event_id"] == "event456"
    assert result["meet_link"] == "https://meet.google.com/abc-def-ghi"


@pytest.mark.asyncio
async def test_create_event_auth_failure():
    """Test handling of auth failure."""
    with patch("docbot.google_calendar_client._get_calendar_service", return_value=None):
        result = await create_event(
            summary="Test",
            description="Test",
            start_time=datetime.now()
        )
        assert result is None


@pytest.mark.asyncio
async def test_delete_event_success(mock_calendar_service):
    """Test deleting event."""
    mock_calendar_service.events().delete().execute.return_value = None

    result = await delete_event("event123")
    assert result is True


@pytest.mark.asyncio
async def test_delete_event_not_found(mock_calendar_service):
    """Test deleting non-existent event."""
    from googleapiclient.errors import HttpError

    mock_resp = MagicMock()
    mock_resp.status = 404
    mock_calendar_service.events().delete().execute.side_effect = HttpError(
        mock_resp, b"Not Found"
    )

    result = await delete_event("nonexistent")
    assert result is True  # Already deleted = success


@pytest.mark.asyncio
async def test_get_event_success(mock_calendar_service):
    """Test getting event by ID."""
    mock_calendar_service.events().get().execute.return_value = {
        "id": "event123",
        "summary": "Test Event"
    }

    result = await get_event("event123")
    assert result is not None
    assert result["id"] == "event123"
