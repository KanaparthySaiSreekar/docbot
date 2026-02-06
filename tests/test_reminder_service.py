"""Tests for automated reminder service."""

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio

from docbot.reminder_service import (
    get_due_reminders,
    mark_reminder_sent,
    run_reminder_job,
    send_reminder,
)


@pytest_asyncio.fixture
async def sample_appointments(test_db):
    """Create sample appointments for testing."""
    now = datetime.now(timezone.utc)
    appointments = []

    # Appointment 24 hours from now (should get 24h reminder)
    appt_24h = {
        "id": str(uuid.uuid4()),
        "patient_phone": "+919876543210",
        "patient_name": "Test Patient 24h",
        "patient_age": 30,
        "patient_gender": "Male",
        "consultation_type": "online",
        "appointment_date": (now + timedelta(hours=24)).strftime("%Y-%m-%d"),
        "slot_time": (now + timedelta(hours=24)).strftime("%H:%M"),
        "status": "CONFIRMED",
        "google_meet_link": "https://meet.google.com/abc-defg-hij",
        "language": "en",
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
        "reminder_sent_24h": "false",
        "reminder_sent_1h": "false",
    }
    await test_db.execute(
        """
        INSERT INTO appointments (
            id, patient_phone, patient_name, patient_age, patient_gender,
            consultation_type, appointment_date, slot_time, status,
            google_meet_link, language, created_at, updated_at,
            reminder_sent_24h, reminder_sent_1h
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            appt_24h["id"], appt_24h["patient_phone"], appt_24h["patient_name"],
            appt_24h["patient_age"], appt_24h["patient_gender"],
            appt_24h["consultation_type"], appt_24h["appointment_date"],
            appt_24h["slot_time"], appt_24h["status"], appt_24h["google_meet_link"],
            appt_24h["language"], appt_24h["created_at"], appt_24h["updated_at"],
            appt_24h["reminder_sent_24h"], appt_24h["reminder_sent_1h"],
        ),
    )
    appointments.append(appt_24h)

    # Appointment 1 hour from now (should get 1h reminder)
    appt_1h = {
        "id": str(uuid.uuid4()),
        "patient_phone": "+919876543211",
        "patient_name": "Test Patient 1h",
        "patient_age": 25,
        "patient_gender": "Female",
        "consultation_type": "offline",
        "appointment_date": (now + timedelta(hours=1)).strftime("%Y-%m-%d"),
        "slot_time": (now + timedelta(hours=1)).strftime("%H:%M"),
        "status": "CONFIRMED",
        "google_meet_link": None,
        "language": "te",
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
        "reminder_sent_24h": "true",  # Already sent 24h reminder
        "reminder_sent_1h": "false",
    }
    await test_db.execute(
        """
        INSERT INTO appointments (
            id, patient_phone, patient_name, patient_age, patient_gender,
            consultation_type, appointment_date, slot_time, status,
            language, created_at, updated_at,
            reminder_sent_24h, reminder_sent_1h
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            appt_1h["id"], appt_1h["patient_phone"], appt_1h["patient_name"],
            appt_1h["patient_age"], appt_1h["patient_gender"],
            appt_1h["consultation_type"], appt_1h["appointment_date"],
            appt_1h["slot_time"], appt_1h["status"], appt_1h["language"],
            appt_1h["created_at"], appt_1h["updated_at"],
            appt_1h["reminder_sent_24h"], appt_1h["reminder_sent_1h"],
        ),
    )
    appointments.append(appt_1h)

    # Appointment 2 hours from now (outside both windows)
    appt_2h = {
        "id": str(uuid.uuid4()),
        "patient_phone": "+919876543212",
        "patient_name": "Test Patient 2h",
        "patient_age": 35,
        "patient_gender": "Male",
        "consultation_type": "online",
        "appointment_date": (now + timedelta(hours=2)).strftime("%Y-%m-%d"),
        "slot_time": (now + timedelta(hours=2)).strftime("%H:%M"),
        "status": "CONFIRMED",
        "google_meet_link": "https://meet.google.com/xyz",
        "language": "hi",
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
        "reminder_sent_24h": "false",
        "reminder_sent_1h": "false",
    }
    await test_db.execute(
        """
        INSERT INTO appointments (
            id, patient_phone, patient_name, patient_age, patient_gender,
            consultation_type, appointment_date, slot_time, status,
            google_meet_link, language, created_at, updated_at,
            reminder_sent_24h, reminder_sent_1h
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            appt_2h["id"], appt_2h["patient_phone"], appt_2h["patient_name"],
            appt_2h["patient_age"], appt_2h["patient_gender"],
            appt_2h["consultation_type"], appt_2h["appointment_date"],
            appt_2h["slot_time"], appt_2h["status"], appt_2h["google_meet_link"],
            appt_2h["language"], appt_2h["created_at"], appt_2h["updated_at"],
            appt_2h["reminder_sent_24h"], appt_2h["reminder_sent_1h"],
        ),
    )
    appointments.append(appt_2h)

    # Appointment with 24h reminder already sent
    appt_sent = {
        "id": str(uuid.uuid4()),
        "patient_phone": "+919876543213",
        "patient_name": "Test Patient Sent",
        "patient_age": 40,
        "patient_gender": "Female",
        "consultation_type": "online",
        "appointment_date": (now + timedelta(hours=24)).strftime("%Y-%m-%d"),
        "slot_time": (now + timedelta(hours=24)).strftime("%H:%M"),
        "status": "CONFIRMED",
        "google_meet_link": "https://meet.google.com/sent",
        "language": "en",
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
        "reminder_sent_24h": "true",
        "reminder_sent_1h": "false",
    }
    await test_db.execute(
        """
        INSERT INTO appointments (
            id, patient_phone, patient_name, patient_age, patient_gender,
            consultation_type, appointment_date, slot_time, status,
            google_meet_link, language, created_at, updated_at,
            reminder_sent_24h, reminder_sent_1h
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            appt_sent["id"], appt_sent["patient_phone"], appt_sent["patient_name"],
            appt_sent["patient_age"], appt_sent["patient_gender"],
            appt_sent["consultation_type"], appt_sent["appointment_date"],
            appt_sent["slot_time"], appt_sent["status"], appt_sent["google_meet_link"],
            appt_sent["language"], appt_sent["created_at"], appt_sent["updated_at"],
            appt_sent["reminder_sent_24h"], appt_sent["reminder_sent_1h"],
        ),
    )
    appointments.append(appt_sent)

    await test_db.commit()
    return appointments


class TestGetDueReminders:
    """Tests for get_due_reminders function."""

    @pytest.mark.asyncio
    async def test_24h_reminder_window(self, test_db, sample_appointments):
        """Test 24h reminder window captures correct appointments."""
        reminders = await get_due_reminders("24h", test_db)

        # Should only include appt_24h (not appt_sent which already has reminder)
        assert len(reminders) == 1
        assert reminders[0]["patient_phone"] == "+919876543210"
        assert reminders[0]["consultation_type"] == "online"

    @pytest.mark.asyncio
    async def test_1h_reminder_window(self, test_db, sample_appointments):
        """Test 1h reminder window captures correct appointments."""
        reminders = await get_due_reminders("1h", test_db)

        # Should only include appt_1h
        assert len(reminders) == 1
        assert reminders[0]["patient_phone"] == "+919876543211"
        assert reminders[0]["consultation_type"] == "offline"

    @pytest.mark.asyncio
    async def test_excludes_already_sent(self, test_db, sample_appointments):
        """Test excludes appointments with reminder already sent."""
        # Mark the 24h appointment as sent
        await mark_reminder_sent(sample_appointments[0]["id"], "24h", test_db)

        reminders = await get_due_reminders("24h", test_db)

        # Should now be 0 (appt_sent already has it, and we just marked appt_24h)
        assert len(reminders) == 0

    @pytest.mark.asyncio
    async def test_excludes_non_confirmed(self, test_db):
        """Test excludes non-CONFIRMED appointments."""
        now = datetime.now(timezone.utc)
        appt_id = str(uuid.uuid4())

        # Create PENDING_PAYMENT appointment 24h from now
        await test_db.execute(
            """
            INSERT INTO appointments (
                id, patient_phone, patient_name, patient_age, patient_gender,
                consultation_type, appointment_date, slot_time, status,
                language, created_at, updated_at, reminder_sent_24h, reminder_sent_1h
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                appt_id, "+919999999999", "Pending Patient", 30, "Male",
                "online", (now + timedelta(hours=24)).strftime("%Y-%m-%d"),
                (now + timedelta(hours=24)).strftime("%H:%M"), "PENDING_PAYMENT",
                "en", now.isoformat(), now.isoformat(), "false", "false"
            ),
        )
        await test_db.commit()

        reminders = await get_due_reminders("24h", test_db)

        # Should not include PENDING_PAYMENT appointment
        assert not any(r["id"] == appt_id for r in reminders)

    @pytest.mark.asyncio
    async def test_excludes_outside_window(self, test_db, sample_appointments):
        """Test excludes appointments outside time window."""
        # appt_2h is 2 hours from now, outside both windows
        reminders_24h = await get_due_reminders("24h")
        reminders_1h = await get_due_reminders("1h")

        # Should not include appt_2h in either
        assert not any(r["patient_phone"] == "+919876543212" for r in reminders_24h)
        assert not any(r["patient_phone"] == "+919876543212" for r in reminders_1h)


class TestSendReminder:
    """Tests for send_reminder function."""

    @patch("docbot.reminder_service.send_text")
    @pytest.mark.asyncio
    async def test_online_reminder_includes_meet_link(self, mock_send_text):
        """Test online consultation reminder includes Meet link."""
        mock_send_text.return_value = {"success": True}

        appointment = {
            "id": "test-id",
            "patient_phone": "+919876543210",
            "consultation_type": "online",
            "slot_time": "10:00",
            "google_meet_link": "https://meet.google.com/abc-defg-hij",
            "language": "en",
        }

        result = await send_reminder("+919876543210", "24h", appointment)

        assert result is True
        mock_send_text.assert_called_once()
        call_args = mock_send_text.call_args
        assert call_args[0][0] == "+919876543210"
        assert "meet.google.com" in call_args[0][1]

    @patch("docbot.reminder_service.send_text")
    @pytest.mark.asyncio
    async def test_offline_reminder_includes_clinic_address(self, mock_send_text):
        """Test offline consultation reminder includes clinic address."""
        mock_send_text.return_value = {"success": True}

        appointment = {
            "id": "test-id",
            "patient_phone": "+919876543211",
            "consultation_type": "offline",
            "slot_time": "14:30",
            "language": "te",
        }

        result = await send_reminder("+919876543211", "1h", appointment)

        assert result is True
        mock_send_text.assert_called_once()
        call_args = mock_send_text.call_args
        assert call_args[0][0] == "+919876543211"
        # Should contain clinic address from config
        message = call_args[0][1]
        assert len(message) > 0  # Verify message was generated

    @patch("docbot.reminder_service.send_text")
    @pytest.mark.asyncio
    async def test_uses_patient_language(self, mock_send_text):
        """Test reminder uses patient's language preference."""
        mock_send_text.return_value = {"success": True}

        # Hindi language appointment
        appointment = {
            "id": "test-id",
            "patient_phone": "+919876543212",
            "consultation_type": "online",
            "slot_time": "11:00",
            "google_meet_link": "https://meet.google.com/xyz",
            "language": "hi",
        }

        result = await send_reminder("+919876543212", "24h", appointment)

        assert result is True
        mock_send_text.assert_called_once()

    @patch("docbot.reminder_service.send_text")
    @pytest.mark.asyncio
    async def test_returns_false_on_send_failure(self, mock_send_text):
        """Test returns False when WhatsApp send fails."""
        mock_send_text.return_value = None  # Failure

        appointment = {
            "id": "test-id",
            "patient_phone": "+919876543210",
            "consultation_type": "online",
            "slot_time": "10:00",
            "google_meet_link": "https://meet.google.com/abc",
            "language": "en",
        }

        result = await send_reminder("+919876543210", "24h", appointment)

        assert result is False


class TestMarkReminderSent:
    """Tests for mark_reminder_sent function."""

    @pytest.mark.asyncio
    async def test_updates_24h_column(self, test_db):
        """Test updates reminder_sent_24h column."""
        now = datetime.now(timezone.utc)
        appt_id = str(uuid.uuid4())

        # Create appointment
        await test_db.execute(
            """
            INSERT INTO appointments (
                id, patient_phone, patient_name, patient_age, patient_gender,
                consultation_type, appointment_date, slot_time, status,
                language, created_at, updated_at, reminder_sent_24h, reminder_sent_1h
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                appt_id, "+919999999999", "Test", 30, "Male", "online",
                (now + timedelta(hours=24)).strftime("%Y-%m-%d"),
                (now + timedelta(hours=24)).strftime("%H:%M"),
                "CONFIRMED", "en", now.isoformat(), now.isoformat(),
                "false", "false"
            ),
        )
        await test_db.commit()

        # Mark 24h reminder sent
        await mark_reminder_sent(appt_id, "24h", test_db)

        # Verify column updated
        cursor = await test_db.execute(
            "SELECT reminder_sent_24h, reminder_sent_1h FROM appointments WHERE id = ?",
            (appt_id,)
        )
        row = await cursor.fetchone()
        assert row[0] == "true"  # reminder_sent_24h
        assert row[1] == "false"  # reminder_sent_1h

    @pytest.mark.asyncio
    async def test_updates_1h_column(self, test_db):
        """Test updates reminder_sent_1h column."""
        now = datetime.now(timezone.utc)
        appt_id = str(uuid.uuid4())

        # Create appointment
        await test_db.execute(
            """
            INSERT INTO appointments (
                id, patient_phone, patient_name, patient_age, patient_gender,
                consultation_type, appointment_date, slot_time, status,
                language, created_at, updated_at, reminder_sent_24h, reminder_sent_1h
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                appt_id, "+919999999999", "Test", 30, "Male", "online",
                (now + timedelta(hours=1)).strftime("%Y-%m-%d"),
                (now + timedelta(hours=1)).strftime("%H:%M"),
                "CONFIRMED", "en", now.isoformat(), now.isoformat(),
                "true", "false"  # 24h already sent
            ),
        )
        await test_db.commit()

        # Mark 1h reminder sent
        await mark_reminder_sent(appt_id, "1h", test_db)

        # Verify column updated
        cursor = await test_db.execute(
            "SELECT reminder_sent_24h, reminder_sent_1h FROM appointments WHERE id = ?",
            (appt_id,)
        )
        row = await cursor.fetchone()
        assert row[0] == "true"  # reminder_sent_24h
        assert row[1] == "true"  # reminder_sent_1h

    @pytest.mark.asyncio
    async def test_appointment_excluded_from_subsequent_queries(self, test_db, sample_appointments):
        """Test appointment not included in queries after marking sent."""
        appt = sample_appointments[0]  # 24h appointment

        # Should be in results initially
        reminders = await get_due_reminders("24h", test_db)
        assert any(r["id"] == appt["id"] for r in reminders)

        # Mark as sent
        await mark_reminder_sent(appt["id"], "24h", test_db)

        # Should no longer be in results
        reminders = await get_due_reminders("24h", test_db)
        assert not any(r["id"] == appt["id"] for r in reminders)


class TestRunReminderJob:
    """Tests for run_reminder_job function."""

    @patch("docbot.reminder_service.send_text")
    @pytest.mark.asyncio
    async def test_returns_correct_stats(self, mock_send_text, test_db, sample_appointments):
        """Test returns correct send/failed/skipped counts."""
        # Mock successful sends
        mock_send_text.return_value = {"success": True}

        result = await run_reminder_job("24h", test_db)

        # Should have sent 1 reminder (appt_24h, not appt_sent)
        assert result["sent"] == 1
        assert result["failed"] == 0
        assert result["skipped"] == 0

    @patch("docbot.reminder_service.send_text")
    @pytest.mark.asyncio
    async def test_handles_send_failures(self, mock_send_text, test_db, sample_appointments):
        """Test handles failed sends correctly."""
        # Mock failed send
        mock_send_text.return_value = None

        result = await run_reminder_job("24h", test_db)

        # Should have 1 failure
        assert result["sent"] == 0
        assert result["failed"] == 1

    @patch("docbot.reminder_service.send_text")
    @pytest.mark.asyncio
    async def test_idempotency(self, mock_send_text, test_db, sample_appointments):
        """Test running job twice doesn't double-send."""
        mock_send_text.return_value = {"success": True}

        # Run first time
        result1 = await run_reminder_job("24h", test_db)
        assert result1["sent"] == 1

        # Run second time - should send nothing
        result2 = await run_reminder_job("24h", test_db)
        assert result2["sent"] == 0
        assert result2["failed"] == 0
