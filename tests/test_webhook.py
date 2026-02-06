"""Tests for WhatsApp webhook endpoints."""

from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio

from docbot.main import app


@pytest.fixture
def test_client():
    """Create FastAPI test client."""
    from fastapi.testclient import TestClient
    return TestClient(app)


def test_webhook_verification_with_correct_token(test_client):
    """Test that GET webhook verification returns challenge with correct token."""
    with patch("docbot.webhook.get_settings") as mock_settings:
        mock_settings.return_value.whatsapp.verify_token = "test_verify_token_123"

        response = test_client.get(
            "/webhook/whatsapp",
            params={
                "hub.mode": "subscribe",
                "hub.verify_token": "test_verify_token_123",
                "hub.challenge": "1234567890"
            }
        )

        assert response.status_code == 200
        assert response.text == "1234567890"
        assert response.headers["content-type"] == "text/plain; charset=utf-8"


def test_webhook_verification_with_wrong_token(test_client):
    """Test that GET webhook verification returns 403 with wrong token."""
    with patch("docbot.webhook.get_settings") as mock_settings:
        mock_settings.return_value.whatsapp.verify_token = "test_verify_token_123"

        response = test_client.get(
            "/webhook/whatsapp",
            params={
                "hub.mode": "subscribe",
                "hub.verify_token": "wrong_token",
                "hub.challenge": "1234567890"
            }
        )

        assert response.status_code == 403


def test_webhook_verification_with_wrong_mode(test_client):
    """Test that GET webhook verification returns 403 with wrong mode."""
    with patch("docbot.webhook.get_settings") as mock_settings:
        mock_settings.return_value.whatsapp.verify_token = "test_verify_token_123"

        response = test_client.get(
            "/webhook/whatsapp",
            params={
                "hub.mode": "invalid",
                "hub.verify_token": "test_verify_token_123",
                "hub.challenge": "1234567890"
            }
        )

        assert response.status_code == 403


@pytest.mark.asyncio
async def test_webhook_text_message_extraction(test_client):
    """Test that POST webhook extracts sender and text from text message."""
    payload = {
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "messages": [
                                {
                                    "from": "+919876543210",
                                    "id": "wamid.test123",
                                    "timestamp": "1234567890",
                                    "type": "text",
                                    "text": {
                                        "body": "Hello, I need help"
                                    }
                                }
                            ]
                        }
                    }
                ]
            }
        ]
    }

    # Mock database and idempotency
    with patch("docbot.webhook.get_db") as mock_get_db:
        with patch("docbot.webhook.check_idempotency", new_callable=AsyncMock) as mock_check:
            with patch("docbot.webhook.record_event", new_callable=AsyncMock) as mock_record:
                mock_check.return_value = False  # Not a duplicate

                # Mock database context manager
                mock_db = AsyncMock()
                mock_get_db.return_value.__aiter__.return_value = [mock_db]

                response = test_client.post("/webhook/whatsapp", json=payload)

                assert response.status_code == 200
                assert response.json() == {"status": "ok"}

                # Verify idempotency check was called
                mock_check.assert_called_once_with(mock_db, "wamid.test123")

                # Verify event was recorded
                mock_record.assert_called_once()
                call_args = mock_record.call_args
                assert call_args[0][0] == mock_db
                assert call_args[0][1] == "wamid.test123"
                assert call_args[0][2] == "whatsapp"

                # Verify parsed message structure
                parsed = call_args[0][3]
                assert parsed["from"] == "+919876543210"
                assert parsed["type"] == "text"
                assert parsed["text"] == "Hello, I need help"
                assert parsed["button_id"] is None


@pytest.mark.asyncio
async def test_webhook_button_reply_extraction(test_client):
    """Test that POST webhook extracts button_id from button reply."""
    payload = {
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "messages": [
                                {
                                    "from": "+919876543210",
                                    "id": "wamid.test456",
                                    "timestamp": "1234567890",
                                    "type": "interactive",
                                    "interactive": {
                                        "type": "button_reply",
                                        "button_reply": {
                                            "id": "btn_confirm",
                                            "title": "Confirm"
                                        }
                                    }
                                }
                            ]
                        }
                    }
                ]
            }
        ]
    }

    with patch("docbot.webhook.get_db") as mock_get_db:
        with patch("docbot.webhook.check_idempotency", new_callable=AsyncMock) as mock_check:
            with patch("docbot.webhook.record_event", new_callable=AsyncMock) as mock_record:
                mock_check.return_value = False

                mock_db = AsyncMock()
                mock_get_db.return_value.__aiter__.return_value = [mock_db]

                response = test_client.post("/webhook/whatsapp", json=payload)

                assert response.status_code == 200
                assert response.json() == {"status": "ok"}

                # Verify parsed message
                parsed = mock_record.call_args[0][3]
                assert parsed["from"] == "+919876543210"
                assert parsed["type"] == "interactive"
                assert parsed["button_id"] == "btn_confirm"
                assert parsed["button_title"] == "Confirm"
                assert parsed["text"] is None


@pytest.mark.asyncio
async def test_webhook_list_reply_extraction(test_client):
    """Test that POST webhook extracts list selection from list reply."""
    payload = {
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "messages": [
                                {
                                    "from": "+919876543210",
                                    "id": "wamid.test789",
                                    "timestamp": "1234567890",
                                    "type": "interactive",
                                    "interactive": {
                                        "type": "list_reply",
                                        "list_reply": {
                                            "id": "slot_09",
                                            "title": "09:00 AM"
                                        }
                                    }
                                }
                            ]
                        }
                    }
                ]
            }
        ]
    }

    with patch("docbot.webhook.get_db") as mock_get_db:
        with patch("docbot.webhook.check_idempotency", new_callable=AsyncMock) as mock_check:
            with patch("docbot.webhook.record_event", new_callable=AsyncMock) as mock_record:
                mock_check.return_value = False

                mock_db = AsyncMock()
                mock_get_db.return_value.__aiter__.return_value = [mock_db]

                response = test_client.post("/webhook/whatsapp", json=payload)

                assert response.status_code == 200
                assert response.json() == {"status": "ok"}

                # Verify parsed message
                parsed = mock_record.call_args[0][3]
                assert parsed["button_id"] == "slot_09"
                assert parsed["button_title"] == "09:00 AM"


@pytest.mark.asyncio
async def test_webhook_duplicate_message_idempotency(test_client):
    """Test that POST webhook returns 200 without reprocessing for duplicate message_id."""
    payload = {
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "messages": [
                                {
                                    "from": "+919876543210",
                                    "id": "wamid.duplicate",
                                    "timestamp": "1234567890",
                                    "type": "text",
                                    "text": {
                                        "body": "Test message"
                                    }
                                }
                            ]
                        }
                    }
                ]
            }
        ]
    }

    with patch("docbot.webhook.get_db") as mock_get_db:
        with patch("docbot.webhook.check_idempotency", new_callable=AsyncMock) as mock_check:
            with patch("docbot.webhook.record_event", new_callable=AsyncMock) as mock_record:
                # Simulate duplicate message (already processed)
                mock_check.return_value = True

                mock_db = AsyncMock()
                mock_get_db.return_value.__aiter__.return_value = [mock_db]

                response = test_client.post("/webhook/whatsapp", json=payload)

                assert response.status_code == 200
                assert response.json() == {"status": "ok"}

                # Verify idempotency check was called
                mock_check.assert_called_once_with(mock_db, "wamid.duplicate")

                # Verify event was NOT recorded (duplicate)
                mock_record.assert_not_called()


@pytest.mark.asyncio
async def test_webhook_malformed_body_returns_200(test_client):
    """Test that POST webhook returns 200 without crashing on malformed body."""
    # Missing entry
    payload = {"invalid": "structure"}

    response = test_client.post("/webhook/whatsapp", json=payload)

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

    # Empty payload
    response = test_client.post("/webhook/whatsapp", json={})

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_webhook_no_messages_returns_200(test_client):
    """Test that POST webhook returns 200 when webhook has no messages."""
    payload = {
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "statuses": [{"id": "status_update"}]
                        }
                    }
                ]
            }
        ]
    }

    response = test_client.post("/webhook/whatsapp", json=payload)

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_razorpay_webhook_payment_captured(test_client, test_db):
    """Test Razorpay payment.captured webhook processing."""
    # Setup: Create appointment and payment
    await test_db.execute(
        """INSERT INTO appointments
           (id, patient_phone, patient_name, patient_age, patient_gender,
            consultation_type, appointment_date, slot_time, status,
            language, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        ("appt-pay-test", "+919876543210", "Payment Test", 30, "Male",
         "online", "2026-02-10", "10:00", "PENDING_PAYMENT",
         "en", "2026-02-06T10:00:00Z", "2026-02-06T10:00:00Z")
    )
    await test_db.execute(
        """INSERT INTO payments
           (id, appointment_id, razorpay_payment_link_id, amount_paise, status, created_at)
           VALUES (?, ?, ?, ?, ?, ?)""",
        ("pay-123", "appt-pay-test", "plink_test123", 50000, "PENDING", "2026-02-06T10:00:00Z")
    )
    await test_db.commit()

    # Create mock for get_db that yields test_db
    async def mock_get_db():
        yield test_db

    # Mock signature verification and calendar
    with patch("docbot.webhook.get_db", mock_get_db), \
         patch("docbot.payment_service.verify_webhook_signature", return_value=True), \
         patch("docbot.calendar_service.google_calendar_client") as mock_cal, \
         patch("docbot.webhook.send_text", new_callable=AsyncMock) as mock_send:

        mock_cal.create_event = AsyncMock(return_value={
            "event_id": "gcal-123",
            "meet_link": "https://meet.google.com/test"
        })

        webhook_payload = {
            "event": "payment.captured",
            "payload": {
                "payment": {
                    "entity": {
                        "id": "pay_razorpay123",
                        "payment_link_id": "plink_test123",
                        "amount": 50000,
                        "status": "captured"
                    }
                }
            }
        }

        response = test_client.post(
            "/webhook/razorpay",
            json=webhook_payload,
            headers={"X-Razorpay-Signature": "valid_signature"}
        )

        assert response.status_code == 200

        # Verify appointment status updated
        cursor = await test_db.execute(
            "SELECT status FROM appointments WHERE id = ?",
            ("appt-pay-test",)
        )
        row = await cursor.fetchone()
        assert row[0] == "CONFIRMED"

        # Verify WhatsApp message sent
        mock_send.assert_called()


@pytest.mark.asyncio
async def test_razorpay_webhook_invalid_signature(test_client):
    """Test webhook rejection with invalid signature."""
    with patch("docbot.payment_service.verify_webhook_signature", return_value=False):
        response = test_client.post(
            "/webhook/razorpay",
            json={"event": "payment.captured", "payload": {}},
            headers={"X-Razorpay-Signature": "invalid"}
        )

        # Should still return 200 to prevent retries
        assert response.status_code == 200
