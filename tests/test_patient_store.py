"""Tests for patient data persistence."""

import pytest

from docbot.patient_store import (
    get_language,
    get_or_create_patient,
    set_language,
    update_patient_name,
)


@pytest.mark.asyncio
async def test_get_or_create_patient_creates_new(test_db):
    """Test get_or_create_patient creates new patient with default language."""
    phone = "919876543210"

    patient = await get_or_create_patient(test_db, phone)

    assert patient["phone"] == phone
    assert patient["language"] == "en"
    assert patient["name"] is None
    assert patient["created_at"] is not None
    assert patient["updated_at"] is not None


@pytest.mark.asyncio
async def test_get_or_create_patient_returns_existing(test_db):
    """Test get_or_create_patient returns existing patient."""
    phone = "919876543210"

    # Create patient
    patient1 = await get_or_create_patient(test_db, phone)
    created_at1 = patient1["created_at"]

    # Get again
    patient2 = await get_or_create_patient(test_db, phone)

    assert patient2["phone"] == phone
    assert patient2["created_at"] == created_at1  # Same creation time


@pytest.mark.asyncio
async def test_get_language_returns_en_for_unknown_phone(test_db):
    """Test get_language returns 'en' for unknown phone."""
    phone = "919876543210"

    language = await get_language(test_db, phone)

    assert language == "en"


@pytest.mark.asyncio
async def test_get_language_returns_stored_preference(test_db):
    """Test get_language returns stored language preference."""
    phone = "919876543210"

    # Set language
    await set_language(test_db, phone, "te")

    # Get language
    language = await get_language(test_db, phone)

    assert language == "te"


@pytest.mark.asyncio
async def test_set_language_updates_existing_patient(test_db):
    """Test set_language updates and persists preference."""
    phone = "919876543210"

    # Create patient
    await get_or_create_patient(test_db, phone)

    # Update language
    await set_language(test_db, phone, "hi")

    # Verify
    language = await get_language(test_db, phone)
    assert language == "hi"


@pytest.mark.asyncio
async def test_set_language_creates_patient_if_not_exists(test_db):
    """Test set_language creates patient if not exists."""
    phone = "919876543210"

    # Set language without creating patient first
    await set_language(test_db, phone, "te")

    # Verify patient exists with correct language
    patient = await get_or_create_patient(test_db, phone)
    assert patient["language"] == "te"


@pytest.mark.asyncio
async def test_set_language_rejects_invalid_language(test_db):
    """Test set_language rejects invalid language code."""
    phone = "919876543210"

    with pytest.raises(ValueError, match="Invalid language code"):
        await set_language(test_db, phone, "fr")


@pytest.mark.asyncio
async def test_update_patient_name(test_db):
    """Test update_patient_name stores patient name."""
    phone = "919876543210"
    name = "John Doe"

    # Create patient
    await get_or_create_patient(test_db, phone)

    # Update name
    await update_patient_name(test_db, phone, name)

    # Verify
    patient = await get_or_create_patient(test_db, phone)
    assert patient["name"] == name
