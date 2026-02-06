"""End-to-end tests for prescription flows."""

import pytest
from datetime import timedelta, datetime
from unittest.mock import AsyncMock, patch
from uuid import uuid4
from pathlib import Path

from docbot.state_machine import AppointmentStatus
from docbot.timezone_utils import utc_now, to_ist, IST


@pytest.mark.asyncio
async def test_prescription_creation_flow(test_db):
    """Test complete prescription creation flow."""
    from docbot.prescription_service import create_prescription

    phone = "+911234567890"
    yesterday = (to_ist(utc_now()) - timedelta(days=1)).strftime("%Y-%m-%d")

    with patch("docbot.prescription_service.generate_prescription_pdf") as mock_pdf, \
         patch("docbot.prescription_delivery.send_prescription_to_patient", new_callable=AsyncMock) as mock_send:

        mock_pdf.return_value = b"PDF content here"  # Return bytes
        mock_send.return_value = True

        # Create completed appointment
        appt_id = str(uuid4())
        await test_db.execute(
            """INSERT INTO appointments
               (id, patient_phone, patient_name, patient_age, patient_gender,
                appointment_date, slot_time, consultation_type, status, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (appt_id, phone, "Test Patient", 30, "Male", yesterday, "10:00",
             "online", AppointmentStatus.CONFIRMED.value,
             utc_now().isoformat(), utc_now().isoformat())
        )
        await test_db.commit()

        # Create prescription
        medicines = [
            {"name": "Paracetamol 500mg", "dosage": "1-0-1", "duration": "3 days"},
            {"name": "Amoxicillin 250mg", "dosage": "1-1-1", "duration": "5 days"}
        ]
        instructions = "Take after meals. Complete the course."

        prescription = await create_prescription(
            test_db,
            appointment_id=appt_id,
            medicines=medicines,
            instructions=instructions
        )

        assert prescription is not None
        assert prescription["appointment_id"] == appt_id
        # Prescription created successfully

        # Verify prescription record in database
        cursor = await test_db.execute(
            "SELECT id, appointment_id, pdf_path FROM prescriptions WHERE appointment_id = ?",
            (appt_id,)
        )
        record = await cursor.fetchone()
        assert record is not None
        assert record[1] == appt_id

        # WhatsApp delivery is handled separately in production
        # (mocked in test environment)


@pytest.mark.asyncio
async def test_prescription_immutability(test_db):
    """Test that only one prescription per appointment."""
    from docbot.prescription_service import create_prescription

    phone = "+911234567891"
    yesterday = (to_ist(utc_now()) - timedelta(days=1)).strftime("%Y-%m-%d")

    with patch("docbot.prescription_service.generate_prescription_pdf") as mock_pdf, \
         patch("docbot.prescription_delivery.send_prescription_to_patient", new_callable=AsyncMock):

        mock_pdf.return_value = b"PDF content here"

        # Create completed appointment
        appt_id = str(uuid4())
        await test_db.execute(
            """INSERT INTO appointments
               (id, patient_phone, patient_name, patient_age, patient_gender,
                appointment_date, slot_time, consultation_type, status, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (appt_id, phone, "Test Patient", 30, "Male", yesterday, "11:00",
             "online", AppointmentStatus.CONFIRMED.value,
             utc_now().isoformat(), utc_now().isoformat())
        )
        await test_db.commit()

        medicines = [{"name": "Test Medicine", "dosage": "1-0-0", "duration": "1 day"}]

        # Create first prescription - should succeed
        prescription1 = await create_prescription(
            test_db,
            appointment_id=appt_id,
            medicines=medicines,
            instructions="First prescription"
        )
        assert prescription1 is not None

        # Try to create second prescription - should fail
        with pytest.raises(Exception):  # UNIQUE constraint violation
            await create_prescription(
                test_db,
                appointment_id=appt_id,
                medicines=medicines,
                instructions="Second prescription"
            )


@pytest.mark.asyncio
async def test_prescription_token_expiry(test_db):
    """Test prescription download token expiry."""
    phone = "+911234567892"

    # Create prescription with expired token
    appt_id = str(uuid4())
    prescription_id = str(uuid4())
    token = str(uuid4())

    # Set token expiry to 73 hours ago
    expired_time = utc_now() - timedelta(hours=73)

    await test_db.execute(
        """INSERT INTO appointments
           (id, patient_phone, patient_name, patient_age, patient_gender,
            appointment_date, slot_time, consultation_type, status, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (appt_id, phone, "Test Patient", 30, "Male", "2026-01-01", "10:00",
         "online", AppointmentStatus.CONFIRMED.value,
         utc_now().isoformat(), utc_now().isoformat())
    )

    await test_db.execute(
        """INSERT INTO prescriptions
           (id, appointment_id, medicines, instructions, pdf_path, secure_token,
            token_expires_at, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (prescription_id, appt_id, '[]', "Test", "prescriptions/test.pdf",
         token, expired_time.isoformat(), utc_now().isoformat())
    )
    await test_db.commit()

    # Query for valid tokens
    cursor = await test_db.execute(
        """SELECT id FROM prescriptions
           WHERE secure_token = ? AND datetime(token_expires_at) > datetime('now')""",
        (token,)
    )
    valid_prescription = await cursor.fetchone()

    # Should return None (token expired)
    assert valid_prescription is None


@pytest.mark.asyncio
async def test_prescription_token_regeneration(test_db):
    """Test prescription token can be regenerated."""
    from docbot.prescription_service import regenerate_token

    phone = "+911234567893"

    # Create prescription
    appt_id = str(uuid4())
    prescription_id = str(uuid4())
    old_token = str(uuid4())

    await test_db.execute(
        """INSERT INTO appointments
           (id, patient_phone, patient_name, patient_age, patient_gender,
            appointment_date, slot_time, consultation_type, status, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (appt_id, phone, "Test Patient", 30, "Male", "2026-01-01", "10:00",
         "online", AppointmentStatus.CONFIRMED.value,
         utc_now().isoformat(), utc_now().isoformat())
    )

    await test_db.execute(
        """INSERT INTO prescriptions
           (id, appointment_id, medicines, instructions, pdf_path, secure_token,
            token_expires_at, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (prescription_id, appt_id, '[]', "Test", "prescriptions/test.pdf",
         old_token, (utc_now() + timedelta(hours=72)).isoformat(), utc_now().isoformat())
    )
    await test_db.commit()

    # Regenerate token
    new_token = await regenerate_token(test_db, prescription_id)
    assert new_token != old_token

    # Verify old token invalid
    cursor = await test_db.execute(
        "SELECT secure_token FROM prescriptions WHERE id = ?",
        (prescription_id,)
    )
    current_token = (await cursor.fetchone())[0]
    assert current_token == new_token
    assert current_token != old_token


@pytest.mark.asyncio
async def test_prescription_for_completed_appointments_only(test_db):
    """Test prescription filtering for completed appointments."""
    phone = "+911234567894"

    # Create future appointment (not completed yet)
    future_appt_id = str(uuid4())
    future_time = to_ist(utc_now()) + timedelta(days=1)
    await test_db.execute(
        """INSERT INTO appointments
           (id, patient_phone, patient_name, patient_age, patient_gender,
            appointment_date, slot_time, consultation_type, status, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (future_appt_id, phone, "Future Patient", 30, "Male",
         future_time.strftime("%Y-%m-%d"), "10:00",
         "online", AppointmentStatus.CONFIRMED.value,
         utc_now().isoformat(), utc_now().isoformat())
    )

    # Create past appointment (completed)
    past_appt_id = str(uuid4())
    past_time = to_ist(utc_now()) - timedelta(days=1)
    await test_db.execute(
        """INSERT INTO appointments
           (id, patient_phone, patient_name, patient_age, patient_gender,
            appointment_date, slot_time, consultation_type, status, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (past_appt_id, phone, "Past Patient", 30, "Male",
         past_time.strftime("%Y-%m-%d"), "10:00",
         "online", AppointmentStatus.CONFIRMED.value,
         utc_now().isoformat(), utc_now().isoformat())
    )
    await test_db.commit()

    # Query completed appointments (past only)
    now_ist = datetime.now(IST)
    cursor = await test_db.execute(
        """SELECT id FROM appointments
           WHERE status = ? AND datetime(appointment_date || ' ' || slot_time) < ?""",
        (AppointmentStatus.CONFIRMED.value, now_ist.strftime("%Y-%m-%d %H:%M"))
    )
    completed = await cursor.fetchall()
    completed_ids = [row[0] for row in completed]

    # Only past appointment should be in completed list
    assert past_appt_id in completed_ids
    assert future_appt_id not in completed_ids
