"""Tests for WhatsApp Cloud API client."""

from unittest import mock
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from docbot import whatsapp_client


@pytest.mark.asyncio
async def test_send_text_constructs_correct_payload():
    """Test that send_text creates the correct payload for WhatsApp API."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"messages": [{"id": "wamid.test123"}]}

    with patch("docbot.whatsapp_client.httpx.AsyncClient") as mock_client_class:
        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client

        result = await whatsapp_client.send_text("+919876543210", "Hello, this is a test message")

        # Verify correct payload structure
        mock_client.post.assert_called_once()
        call_kwargs = mock_client.post.call_args.kwargs
        payload = call_kwargs["json"]

        assert payload["messaging_product"] == "whatsapp"
        assert payload["to"] == "+919876543210"
        assert payload["type"] == "text"
        assert payload["text"]["body"] == "Hello, this is a test message"

        # Verify result
        assert result == {"messages": [{"id": "wamid.test123"}]}


@pytest.mark.asyncio
async def test_send_buttons_constructs_correct_interactive_payload():
    """Test that send_buttons creates the correct interactive button payload."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"messages": [{"id": "wamid.test456"}]}

    with patch("docbot.whatsapp_client.httpx.AsyncClient") as mock_client_class:
        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client

        buttons = [
            {"id": "btn_yes", "title": "Yes"},
            {"id": "btn_no", "title": "No"}
        ]

        result = await whatsapp_client.send_buttons("+919876543210", "Do you confirm?", buttons)

        # Verify correct payload structure
        mock_client.post.assert_called_once()
        call_kwargs = mock_client.post.call_args.kwargs
        payload = call_kwargs["json"]

        assert payload["messaging_product"] == "whatsapp"
        assert payload["to"] == "+919876543210"
        assert payload["type"] == "interactive"
        assert payload["interactive"]["type"] == "button"
        assert payload["interactive"]["body"]["text"] == "Do you confirm?"
        assert len(payload["interactive"]["action"]["buttons"]) == 2
        assert payload["interactive"]["action"]["buttons"][0]["type"] == "reply"
        assert payload["interactive"]["action"]["buttons"][0]["reply"]["id"] == "btn_yes"
        assert payload["interactive"]["action"]["buttons"][0]["reply"]["title"] == "Yes"

        # Verify result
        assert result == {"messages": [{"id": "wamid.test456"}]}


@pytest.mark.asyncio
async def test_send_list_constructs_correct_list_payload():
    """Test that send_list creates the correct interactive list payload."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"messages": [{"id": "wamid.test789"}]}

    with patch("docbot.whatsapp_client.httpx.AsyncClient") as mock_client_class:
        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client

        sections = [
            {
                "title": "Morning Slots",
                "rows": [
                    {"id": "slot_09", "title": "09:00 AM"},
                    {"id": "slot_10", "title": "10:00 AM"}
                ]
            }
        ]

        result = await whatsapp_client.send_list(
            "+919876543210",
            "Please select a time slot",
            "View Slots",
            sections
        )

        # Verify correct payload structure
        mock_client.post.assert_called_once()
        call_kwargs = mock_client.post.call_args.kwargs
        payload = call_kwargs["json"]

        assert payload["messaging_product"] == "whatsapp"
        assert payload["to"] == "+919876543210"
        assert payload["type"] == "interactive"
        assert payload["interactive"]["type"] == "list"
        assert payload["interactive"]["body"]["text"] == "Please select a time slot"
        assert payload["interactive"]["action"]["button"] == "View Slots"
        assert payload["interactive"]["action"]["sections"] == sections

        # Verify result
        assert result == {"messages": [{"id": "wamid.test789"}]}


@pytest.mark.asyncio
async def test_retry_on_500_response():
    """Test that _send_message retries on 500 server error and succeeds on retry."""
    # First call returns 500, second call returns 200
    mock_response_500 = MagicMock()
    mock_response_500.status_code = 500
    mock_response_500.text = "Internal Server Error"

    mock_response_200 = MagicMock()
    mock_response_200.status_code = 200
    mock_response_200.json.return_value = {"messages": [{"id": "wamid.retry"}]}

    with patch("docbot.whatsapp_client.httpx.AsyncClient") as mock_client_class:
        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()

        # First call returns 500, second call returns 200
        mock_client.post = AsyncMock(side_effect=[mock_response_500, mock_response_200])

        mock_client_class.return_value = mock_client

        with patch("docbot.whatsapp_client.asyncio.sleep", new_callable=AsyncMock):
            result = await whatsapp_client.send_text("+919876543210", "Test message")

        # Should have called post twice (first attempt + one retry)
        assert mock_client.post.call_count == 2

        # Should return success result from second attempt
        assert result == {"messages": [{"id": "wamid.retry"}]}


@pytest.mark.asyncio
async def test_final_failure_returns_none_after_max_retries():
    """Test that _send_message returns None after all retry attempts fail."""
    mock_response_500 = MagicMock()
    mock_response_500.status_code = 503
    mock_response_500.text = "Service Unavailable"

    with patch("docbot.whatsapp_client.httpx.AsyncClient") as mock_client_class:
        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()

        # All attempts return 503
        mock_client.post = AsyncMock(return_value=mock_response_500)

        mock_client_class.return_value = mock_client

        with patch("docbot.whatsapp_client.asyncio.sleep", new_callable=AsyncMock):
            with patch("docbot.whatsapp_client.log_alert") as mock_alert:
                result = await whatsapp_client.send_text("+919876543210", "Test message")

        # Should have called post 3 times (max attempts)
        assert mock_client.post.call_count == 3

        # Should return None on complete failure
        assert result is None

        # Should have logged alert
        mock_alert.assert_called_once()
        assert mock_alert.call_args[0][1] == "whatsapp_send_failure"


@pytest.mark.asyncio
async def test_network_error_retries():
    """Test that network errors trigger retry logic."""
    # First attempt raises network error, second succeeds
    mock_response_200 = MagicMock()
    mock_response_200.status_code = 200
    mock_response_200.json.return_value = {"messages": [{"id": "wamid.network"}]}

    with patch("docbot.whatsapp_client.httpx.AsyncClient") as mock_client_class:
        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()

        # First call raises network error, second call succeeds
        mock_client.post = AsyncMock(side_effect=[
            httpx.RequestError("Connection failed"),
            mock_response_200
        ])

        mock_client_class.return_value = mock_client

        with patch("docbot.whatsapp_client.asyncio.sleep", new_callable=AsyncMock):
            result = await whatsapp_client.send_text("+919876543210", "Test message")

        # Should have called post twice
        assert mock_client.post.call_count == 2

        # Should return success result from retry
        assert result == {"messages": [{"id": "wamid.network"}]}


@pytest.mark.asyncio
async def test_client_error_does_not_retry():
    """Test that 4xx client errors do not trigger retry."""
    mock_response_400 = MagicMock()
    mock_response_400.status_code = 400
    mock_response_400.text = "Bad Request"

    with patch("docbot.whatsapp_client.httpx.AsyncClient") as mock_client_class:
        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response_400)
        mock_client_class.return_value = mock_client

        with patch("docbot.whatsapp_client.log_alert") as mock_alert:
            result = await whatsapp_client.send_text("+919876543210", "Test message")

        # Should have called post only once (no retry)
        assert mock_client.post.call_count == 1

        # Should return None
        assert result is None

        # Should have logged alert
        mock_alert.assert_called_once()
