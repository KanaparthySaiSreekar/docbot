"""Tests for prescription service."""
import json
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import pytest_asyncio

from docbot.prescription_service import (
    create_prescription,
    get_prescription,
    get_prescription_by_token,
    mark_whatsapp_sent,
    regenerate_token,
    PRESCRIPTION_STORAGE_DIR,
)


@pytest_asyncio.fixture
async def test_appointment(test_db):
    """Create a test appointment for prescription creation."""
    appointment_id = str(uuid.uuid4())
    await test_db.execute(
        """INSERT INTO appointments
           (id, patient_phone, patient_name, patient_age, patient_gender,
            consultation_type, appointment_date, slot_time, status,
            language, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            appointment_id,
            "1234567890",
            "John Doe",
            35,
            "Male",
            "online",
            "2026-02-15",
            "10:00",
            "CONFIRMED",
            "en",
            datetime.now(timezone.utc).isoformat(),
            datetime.now(timezone.utc).isoformat(),
        ),
    )
    await test_db.commit()
    return appointment_id


@pytest.fixture
def mock_pdf_generation():
    """Mock PDF generation to avoid dependencies."""
    with patch("docbot.prescription_service.generate_prescription_pdf") as mock:
        mock.return_value = b"fake_pdf_content"
        yield mock


@pytest.mark.asyncio
async def test_create_prescription_success(test_db, test_appointment, mock_pdf_generation):
    """Test successful prescription creation."""
    # Prepare test data
    medicines = [
        {
            "name": "Paracetamol",
            "dosage": "500mg",
            "frequency": "3 times daily",
            "duration": "5 days",
            "notes": "After meals",
        },
        {
            "name": "Vitamin D",
            "dosage": "60000 IU",
            "frequency": "Once weekly",
            "duration": "8 weeks",
            "notes": "",
        },
    ]
    instructions = "Take plenty of rest and drink lots of fluids."

    # Create prescription
    result = await create_prescription(
        test_db, test_appointment, medicines, instructions
    )

    # Verify return value
    assert "id" in result
    assert result["appointment_id"] == test_appointment
    assert "secure_token" in result
    assert "pdf_path" in result
    assert "created_at" in result

    # Verify database record
    cursor = await test_db.execute(
        "SELECT id, appointment_id, medicines, instructions, pdf_path, secure_token, token_expires_at FROM prescriptions WHERE id = ?",
        (result["id"],),
    )
    row = await cursor.fetchone()
    assert row is not None
    assert row[0] == result["id"]
    assert row[1] == test_appointment
    assert json.loads(row[2]) == medicines
    assert row[3] == instructions
    assert row[4] == result["pdf_path"]
    assert row[5] == result["secure_token"]
    assert row[6] is not None  # token_expires_at

    # Verify PDF file created
    pdf_path = Path(result["pdf_path"])
    assert pdf_path.exists()
    assert pdf_path.read_bytes() == b"fake_pdf_content"

    # Verify PDF generation was called with correct args
    mock_pdf_generation.assert_called_once()
    call_args = mock_pdf_generation.call_args[1]
    assert call_args["prescription_id"] == result["id"]
    assert call_args["appointment_id"] == test_appointment
    assert call_args["patient_name"] == "John Doe"
    assert call_args["patient_age"] == 35
    assert call_args["patient_gender"] == "Male"
    assert call_args["medicines"] == medicines
    assert call_args["instructions"] == instructions

    # Cleanup
    pdf_path.unlink()


@pytest.mark.asyncio
async def test_create_prescription_appointment_not_found(test_db, mock_pdf_generation):
    """Test prescription creation fails for non-existent appointment."""
    medicines = [{"name": "Test", "dosage": "1mg", "frequency": "daily", "duration": "5 days", "notes": ""}]

    with pytest.raises(ValueError, match="Appointment not found"):
        await create_prescription(test_db, "non_existent_id", medicines, None)


@pytest.mark.asyncio
async def test_create_prescription_duplicate(test_db, test_appointment, mock_pdf_generation):
    """Test prescription immutability - cannot create duplicate."""
    medicines = [{"name": "Test", "dosage": "1mg", "frequency": "daily", "duration": "5 days", "notes": ""}]

    # Create first prescription
    result1 = await create_prescription(test_db, test_appointment, medicines, None)

    # Attempt to create second prescription for same appointment
    with pytest.raises(ValueError, match="Prescription already exists"):
        await create_prescription(test_db, test_appointment, medicines, None)

    # Cleanup
    Path(result1["pdf_path"]).unlink()


@pytest.mark.asyncio
async def test_get_prescription(test_db, test_appointment, mock_pdf_generation):
    """Test retrieving prescription by ID."""
    medicines = [{"name": "Test", "dosage": "1mg", "frequency": "daily", "duration": "5 days", "notes": "Note"}]
    instructions = "Test instructions"

    # Create prescription
    created = await create_prescription(test_db, test_appointment, medicines, instructions)

    # Retrieve prescription
    result = await get_prescription(test_db, created["id"])

    # Verify
    assert result is not None
    assert result["id"] == created["id"]
    assert result["appointment_id"] == test_appointment
    assert result["medicines"] == medicines
    assert result["instructions"] == instructions
    assert result["pdf_path"] == created["pdf_path"]
    assert result["secure_token"] == created["secure_token"]
    assert result["whatsapp_sent"] is False

    # Cleanup
    Path(created["pdf_path"]).unlink()


@pytest.mark.asyncio
async def test_get_prescription_not_found(test_db):
    """Test get_prescription returns None for non-existent ID."""
    result = await get_prescription(test_db, "non_existent_id")
    assert result is None


@pytest.mark.asyncio
async def test_get_prescription_by_token_valid(test_db, test_appointment, mock_pdf_generation):
    """Test retrieving prescription by valid token."""
    medicines = [{"name": "Test", "dosage": "1mg", "frequency": "daily", "duration": "5 days", "notes": ""}]

    # Create prescription
    created = await create_prescription(test_db, test_appointment, medicines, None)

    # Retrieve by token
    result = await get_prescription_by_token(test_db, created["secure_token"])

    # Verify
    assert result is not None
    assert result["id"] == created["id"]
    assert result["appointment_id"] == test_appointment
    assert result["pdf_path"] == created["pdf_path"]

    # Cleanup
    Path(created["pdf_path"]).unlink()


@pytest.mark.asyncio
async def test_get_prescription_by_token_expired(test_db, test_appointment, mock_pdf_generation):
    """Test expired token returns None."""
    medicines = [{"name": "Test", "dosage": "1mg", "frequency": "daily", "duration": "5 days", "notes": ""}]

    # Create prescription
    created = await create_prescription(test_db, test_appointment, medicines, None)

    # Manually expire the token
    expired_time = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    await test_db.execute(
        "UPDATE prescriptions SET token_expires_at = ? WHERE id = ?",
        (expired_time, created["id"]),
    )
    await test_db.commit()

    # Try to retrieve with expired token
    result = await get_prescription_by_token(test_db, created["secure_token"])
    assert result is None

    # Cleanup
    Path(created["pdf_path"]).unlink()


@pytest.mark.asyncio
async def test_get_prescription_by_token_invalid(test_db):
    """Test invalid token returns None."""
    result = await get_prescription_by_token(test_db, "invalid_token_xyz")
    assert result is None


@pytest.mark.asyncio
async def test_regenerate_token(test_db, test_appointment, mock_pdf_generation):
    """Test token regeneration extends access."""
    medicines = [{"name": "Test", "dosage": "1mg", "frequency": "daily", "duration": "5 days", "notes": ""}]

    # Create prescription
    created = await create_prescription(test_db, test_appointment, medicines, None)
    old_token = created["secure_token"]

    # Regenerate token
    new_token = await regenerate_token(test_db, created["id"])

    # Verify new token is different
    assert new_token != old_token

    # Verify old token no longer works
    result_old = await get_prescription_by_token(test_db, old_token)
    assert result_old is None

    # Verify new token works
    result_new = await get_prescription_by_token(test_db, new_token)
    assert result_new is not None
    assert result_new["id"] == created["id"]

    # Verify expiry time was updated (should be ~72 hours from now)
    cursor = await test_db.execute(
        "SELECT token_expires_at FROM prescriptions WHERE id = ?",
        (created["id"],),
    )
    row = await cursor.fetchone()
    expires_at = datetime.fromisoformat(row[0])
    time_until_expiry = expires_at - datetime.now(timezone.utc)
    assert 71 <= time_until_expiry.total_seconds() / 3600 <= 73  # ~72 hours

    # Cleanup
    Path(created["pdf_path"]).unlink()


@pytest.mark.asyncio
async def test_mark_whatsapp_sent(test_db, test_appointment, mock_pdf_generation):
    """Test marking prescription as sent via WhatsApp."""
    medicines = [{"name": "Test", "dosage": "1mg", "frequency": "daily", "duration": "5 days", "notes": ""}]

    # Create prescription
    created = await create_prescription(test_db, test_appointment, medicines, None)

    # Verify initially not sent
    result = await get_prescription(test_db, created["id"])
    assert result["whatsapp_sent"] is False

    # Mark as sent
    await mark_whatsapp_sent(test_db, created["id"])

    # Verify flag updated
    result = await get_prescription(test_db, created["id"])
    assert result["whatsapp_sent"] is True

    # Cleanup
    Path(created["pdf_path"]).unlink()


@pytest.mark.asyncio
async def test_prescription_storage_directory_created(test_db, test_appointment, mock_pdf_generation):
    """Test that prescription storage directory is created automatically."""
    # Remove directory if it exists
    if PRESCRIPTION_STORAGE_DIR.exists():
        for file in PRESCRIPTION_STORAGE_DIR.glob("*"):
            file.unlink()
        PRESCRIPTION_STORAGE_DIR.rmdir()

    medicines = [{"name": "Test", "dosage": "1mg", "frequency": "daily", "duration": "5 days", "notes": ""}]

    # Create prescription (should create directory)
    result = await create_prescription(test_db, test_appointment, medicines, None)

    # Verify directory exists
    assert PRESCRIPTION_STORAGE_DIR.exists()
    assert PRESCRIPTION_STORAGE_DIR.is_dir()

    # Cleanup
    Path(result["pdf_path"]).unlink()
