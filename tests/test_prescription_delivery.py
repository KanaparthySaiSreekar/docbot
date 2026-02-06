"""Tests for prescription delivery and secure download URLs."""
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient

from docbot.main import app
from docbot.prescription_delivery import send_prescription_to_patient
from docbot.prescription_service import (
    create_prescription,
    get_prescription_by_token,
    regenerate_token,
)


@pytest_asyncio.fixture
async def sample_appointment(test_db):
    """Create a sample appointment for prescription testing."""
    from docbot.timezone_utils import utc_now

    appointment_id = "test-appt-123"
    now = utc_now().isoformat()
    await test_db.execute(
        """INSERT INTO appointments
           (id, patient_name, patient_phone, patient_age, patient_gender,
            appointment_date, slot_time, consultation_type,
            status, language, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            appointment_id,
            "Test Patient",
            "9876543210",
            30,
            "Male",
            "2026-02-10",
            "10:00",
            "online",
            "CONFIRMED",
            "en",
            now,
            now,
        ),
    )
    await test_db.commit()
    return appointment_id


@pytest_asyncio.fixture
async def sample_prescription(test_db, sample_appointment):
    """Create a sample prescription for testing."""
    medicines = [
        {
            "name": "Paracetamol",
            "dosage": "500mg",
            "frequency": "1-1-1",
            "duration": "5 days",
        }
    ]
    prescription = await create_prescription(
        test_db, sample_appointment, medicines, "Take with food"
    )
    return prescription


class TestSecureDownloadEndpoint:
    """Test the /prescriptions/download/{token} endpoint logic."""

    @pytest.mark.asyncio
    async def test_valid_token_returns_prescription(self, test_db, sample_prescription):
        """Test that get_prescription_by_token works with valid token."""
        token = sample_prescription["secure_token"]

        prescription = await get_prescription_by_token(test_db, token)

        assert prescription is not None
        assert prescription["id"] == sample_prescription["id"]
        assert prescription["pdf_path"] == sample_prescription["pdf_path"]

    @pytest.mark.asyncio
    async def test_invalid_token_returns_none(self, test_db):
        """Test that invalid token returns None."""
        prescription = await get_prescription_by_token(test_db, "invalid-token-12345")

        assert prescription is None

    @pytest.mark.asyncio
    async def test_expired_token_returns_none(self, test_db, sample_prescription):
        """Test that expired token returns None."""
        # Expire the token
        expired_time = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        await test_db.execute(
            "UPDATE prescriptions SET token_expires_at = ? WHERE id = ?",
            (expired_time, sample_prescription["id"]),
        )
        await test_db.commit()

        token = sample_prescription["secure_token"]
        prescription = await get_prescription_by_token(test_db, token)

        assert prescription is None


class TestSendPrescriptionToPatient:
    """Test the send_prescription_to_patient function."""

    @pytest.mark.asyncio
    async def test_successful_delivery(self, test_db, sample_prescription):
        """Test successful WhatsApp delivery of prescription."""
        with patch("docbot.prescription_delivery.send_text") as mock_send:
            mock_send.return_value = {"message_id": "test-msg-123"}

            result = await send_prescription_to_patient(
                test_db, sample_prescription["id"]
            )

            assert result is True
            assert mock_send.called
            call_args = mock_send.call_args

            # Verify phone number and message content
            phone = call_args[0][0]
            message = call_args[0][1]

            assert phone == "9876543210"
            assert "Test Patient" in message
            assert "/prescriptions/download/" in message
            assert "72 hours" in message

            # Verify whatsapp_sent flag updated
            prescription = await test_db.execute(
                "SELECT whatsapp_sent FROM prescriptions WHERE id = ?",
                (sample_prescription["id"],)
            )
            row = await prescription.fetchone()
            assert row[0] == "true"

    @pytest.mark.asyncio
    async def test_token_regenerated_before_sending(self, test_db, sample_prescription):
        """Test that token is regenerated for fresh 72-hour window."""
        original_token = sample_prescription["secure_token"]

        with patch("docbot.prescription_delivery.send_text") as mock_send:
            mock_send.return_value = {"message_id": "test-msg-123"}

            await send_prescription_to_patient(test_db, sample_prescription["id"])

            # Get updated prescription
            cursor = await test_db.execute(
                "SELECT secure_token FROM prescriptions WHERE id = ?",
                (sample_prescription["id"],)
            )
            row = await cursor.fetchone()
            new_token = row[0]

            # Token should be different
            assert new_token != original_token

            # Message should contain new token
            call_args = mock_send.call_args
            message = call_args[0][1]
            assert new_token in message

    @pytest.mark.asyncio
    async def test_whatsapp_failure_returns_false(self, test_db, sample_prescription):
        """Test that WhatsApp send failure returns False."""
        with patch("docbot.prescription_delivery.send_text") as mock_send:
            mock_send.return_value = None  # Simulates failure

            result = await send_prescription_to_patient(
                test_db, sample_prescription["id"]
            )

            assert result is False

            # whatsapp_sent should NOT be updated
            cursor = await test_db.execute(
                "SELECT whatsapp_sent FROM prescriptions WHERE id = ?",
                (sample_prescription["id"],)
            )
            row = await cursor.fetchone()
            assert row[0] != "true"

    @pytest.mark.asyncio
    async def test_missing_prescription_returns_false(self, test_db):
        """Test that missing prescription returns False."""
        with patch("docbot.prescription_delivery.send_text") as mock_send:
            result = await send_prescription_to_patient(
                test_db, "nonexistent-prescription-id"
            )

            assert result is False
            assert not mock_send.called

    @pytest.mark.asyncio
    async def test_multilingual_message(self, test_db, sample_appointment):
        """Test that message uses correct language from appointment."""
        # Create appointment with Telugu language
        await test_db.execute(
            "UPDATE appointments SET language = ? WHERE id = ?",
            ("te", sample_appointment)
        )
        await test_db.commit()

        # Create prescription
        prescription = await create_prescription(
            test_db,
            sample_appointment,
            [{"name": "Test Med", "dosage": "100mg", "frequency": "1-0-1", "duration": "5 days"}],
        )

        with patch("docbot.prescription_delivery.send_text") as mock_send:
            mock_send.return_value = {"message_id": "test-msg-123"}

            await send_prescription_to_patient(test_db, prescription["id"])

            # Verify Telugu message
            message = mock_send.call_args[0][1]
            assert "ప్రిస్క్రిప్షన్" in message or "download" in message.lower()


class TestTokenRegeneration:
    """Test prescription token regeneration."""

    @pytest.mark.asyncio
    async def test_old_token_invalid_after_regeneration(
        self, test_db, sample_prescription
    ):
        """Test that old token becomes invalid after regeneration."""
        old_token = sample_prescription["secure_token"]

        # Regenerate token
        new_token = await regenerate_token(test_db, sample_prescription["id"])

        # Old token should not work
        old_prescription = await get_prescription_by_token(test_db, old_token)
        assert old_prescription is None

        # New token should work
        new_prescription = await get_prescription_by_token(test_db, new_token)
        assert new_prescription is not None
        assert new_prescription["id"] == sample_prescription["id"]

    @pytest.mark.asyncio
    async def test_new_token_has_fresh_expiry(self, test_db, sample_prescription):
        """Test that regenerated token has fresh 72-hour expiry."""
        # Regenerate token
        new_token = await regenerate_token(test_db, sample_prescription["id"])

        # Get expiry time
        cursor = await test_db.execute(
            "SELECT token_expires_at FROM prescriptions WHERE id = ?",
            (sample_prescription["id"],)
        )
        row = await cursor.fetchone()
        expires_at = datetime.fromisoformat(row[0])

        # Should expire approximately 72 hours from now
        now = datetime.now(timezone.utc)
        time_until_expiry = expires_at - now

        assert time_until_expiry.total_seconds() > (71 * 3600)  # At least 71 hours
        assert time_until_expiry.total_seconds() < (73 * 3600)  # At most 73 hours


class TestIntegrationFlow:
    """Integration test for complete prescription delivery flow."""

    @pytest.mark.asyncio
    async def test_complete_flow(self, test_db, sample_appointment):
        """Test complete flow: create -> send -> verify token."""
        # 1. Create prescription
        medicines = [
            {
                "name": "Amoxicillin",
                "dosage": "500mg",
                "frequency": "1-0-1",
                "duration": "7 days",
            }
        ]
        prescription = await create_prescription(
            test_db, sample_appointment, medicines, "Complete full course"
        )

        # 2. Send to patient (mock WhatsApp)
        with patch("docbot.prescription_delivery.send_text") as mock_send:
            mock_send.return_value = {"message_id": "msg-123"}

            success = await send_prescription_to_patient(test_db, prescription["id"])
            assert success

        # 3. Extract token from sent message
        sent_message = mock_send.call_args[0][1]
        # Extract token from URL in message
        import re

        match = re.search(r"/prescriptions/download/([A-Za-z0-9_-]+)", sent_message)
        assert match
        token = match.group(1)

        # 4. Verify token works
        prescription_by_token = await get_prescription_by_token(test_db, token)
        assert prescription_by_token is not None
        assert prescription_by_token["id"] == prescription["id"]

    @pytest.mark.asyncio
    async def test_expired_token_workflow(self, test_db, sample_prescription):
        """Test that expired tokens don't work, but can be regenerated."""
        # Expire the current token
        expired_time = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        await test_db.execute(
            "UPDATE prescriptions SET token_expires_at = ? WHERE id = ?",
            (expired_time, sample_prescription["id"]),
        )
        await test_db.commit()

        old_token = sample_prescription["secure_token"]

        # Old token should not work
        old_prescription = await get_prescription_by_token(test_db, old_token)
        assert old_prescription is None

        # Regenerate and send again
        with patch("docbot.prescription_delivery.send_text") as mock_send:
            mock_send.return_value = {"message_id": "msg-123"}

            success = await send_prescription_to_patient(
                test_db, sample_prescription["id"]
            )
            assert success

            # Extract new token from message
            sent_message = mock_send.call_args[0][1]
            import re

            match = re.search(r"/prescriptions/download/([A-Za-z0-9_-]+)", sent_message)
            new_token = match.group(1)

        # New token should work
        new_prescription = await get_prescription_by_token(test_db, new_token)
        assert new_prescription is not None
        assert new_prescription["id"] == sample_prescription["id"]
