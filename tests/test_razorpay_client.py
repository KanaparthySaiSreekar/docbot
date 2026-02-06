"""Tests for Razorpay API client."""

import hashlib
import hmac
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from docbot.razorpay_client import create_payment_link, verify_webhook_signature


@pytest.mark.asyncio
async def test_create_payment_link_success():
    """Test successful payment link creation."""
    from unittest.mock import Mock

    mock_response = Mock()
    mock_response.json.return_value = {
        "id": "plink_test123",
        "short_url": "https://rzp.io/l/test123"
    }
    mock_response.raise_for_status = Mock()

    mock_post = AsyncMock(return_value=mock_response)
    mock_client = AsyncMock()
    mock_client.__aenter__.return_value.post = mock_post

    with patch("httpx.AsyncClient", return_value=mock_client):
        result = await create_payment_link(
            amount_paise=50000,
            receipt="appt_123",
            description="Test consultation",
            customer_name="Test Patient",
            customer_phone="9876543210"
        )

    assert result is not None
    assert result["payment_link_id"] == "plink_test123"
    assert result["short_url"] == "https://rzp.io/l/test123"


@pytest.mark.asyncio
async def test_create_payment_link_with_appointment_reference():
    """Test payment link contains appointment_id in receipt."""
    from unittest.mock import Mock

    appointment_id = "appt_unique_123"

    mock_response = Mock()
    mock_response.json.return_value = {
        "id": "plink_test123",
        "short_url": "https://rzp.io/l/test123"
    }
    mock_response.raise_for_status = Mock()

    mock_post = AsyncMock(return_value=mock_response)
    mock_client = AsyncMock()
    mock_client.__aenter__.return_value.post = mock_post

    with patch("httpx.AsyncClient", return_value=mock_client):
        await create_payment_link(
            amount_paise=50000,
            receipt=appointment_id,
            description="Test consultation",
            customer_name="Test Patient",
            customer_phone="9876543210"
        )

        # Verify the receipt was passed in the request
        call_kwargs = mock_post.call_args[1]
        assert call_kwargs["json"]["receipt"] == appointment_id


@pytest.mark.asyncio
async def test_create_payment_link_network_error():
    """Test payment link creation handles network errors gracefully."""
    mock_post = AsyncMock(side_effect=httpx.NetworkError("Connection failed"))
    mock_client = AsyncMock()
    mock_client.__aenter__.return_value.post = mock_post

    with patch("httpx.AsyncClient", return_value=mock_client):
        result = await create_payment_link(
            amount_paise=50000,
            receipt="appt_123",
            description="Test consultation",
            customer_name="Test Patient",
            customer_phone="9876543210"
        )

    assert result is None


def test_verify_webhook_signature_valid():
    """Test valid webhook signature verification."""
    webhook_secret = "test_secret_key"
    payload_body = b'{"event":"payment.captured","payload":{"payment":{"id":"pay_123"}}}'

    # Calculate expected signature
    expected_signature = hmac.new(
        webhook_secret.encode(),
        payload_body,
        hashlib.sha256
    ).hexdigest()

    with patch("docbot.razorpay_client.get_settings") as mock_settings:
        mock_settings.return_value.razorpay.webhook_secret = webhook_secret

        result = verify_webhook_signature(payload_body, expected_signature)

    assert result is True


def test_verify_webhook_signature_invalid():
    """Test tampered payload returns False."""
    webhook_secret = "test_secret_key"
    payload_body = b'{"event":"payment.captured","payload":{"payment":{"id":"pay_123"}}}'
    tampered_signature = "invalid_signature_hash"

    with patch("docbot.razorpay_client.get_settings") as mock_settings:
        mock_settings.return_value.razorpay.webhook_secret = webhook_secret

        result = verify_webhook_signature(payload_body, tampered_signature)

    assert result is False


def test_verify_webhook_signature_missing_header():
    """Test missing signature header returns False."""
    payload_body = b'{"event":"payment.captured","payload":{"payment":{"id":"pay_123"}}}'

    with patch("docbot.razorpay_client.get_settings") as mock_settings:
        mock_settings.return_value.razorpay.webhook_secret = "test_secret"

        result = verify_webhook_signature(payload_body, "")

    assert result is False
