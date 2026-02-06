"""Tests for dashboard API endpoints."""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio

from docbot.main import app
from docbot.auth import require_auth
from docbot.database import get_db
from docbot.timezone_utils import ist_now


@pytest.fixture
def test_client():
    """Create FastAPI test client."""
    from fastapi.testclient import TestClient
    return TestClient(app)


@pytest_asyncio.fixture
async def db_with_appointments(test_db):
    """Create test database with sample appointments."""
    today = ist_now().strftime("%Y-%m-%d")
    tomorrow = (ist_now() + timedelta(days=1)).strftime("%Y-%m-%d")
    yesterday = (ist_now() - timedelta(days=1)).strftime("%Y-%m-%d")

    # Insert test appointments
    appointments = [
        ("appt-1", "+919876543210", "John Doe", 30, "Male", "online",
         today, "09:00", "CONFIRMED", "meet.google.com/xyz",
         "2026-02-06T10:00:00Z", "2026-02-06T10:00:00Z"),
        ("appt-2", "+919876543211", "Jane Smith", 25, "Female", "offline",
         tomorrow, "10:00", "PENDING_PAYMENT", None,
         "2026-02-06T10:00:00Z", "2026-02-06T10:00:00Z"),
        ("appt-3", "+919876543212", "Bob Johnson", 40, "Male", "online",
         yesterday, "11:00", "COMPLETED", "meet.google.com/abc",
         "2026-02-05T10:00:00Z", "2026-02-05T10:00:00Z"),
        ("appt-4", "+919876543213", "Alice Brown", 35, "Female", "offline",
         today, "14:00", "CANCELLED", None,
         "2026-02-06T10:00:00Z", "2026-02-06T10:00:00Z"),
    ]

    for appt in appointments:
        await test_db.execute(
            """INSERT INTO appointments
               (id, patient_phone, patient_name, patient_age, patient_gender,
                consultation_type, appointment_date, slot_time, status,
                google_meet_link, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            appt
        )

    # Insert refund for cancelled appointment
    await test_db.execute(
        """INSERT INTO refunds
           (id, appointment_id, razorpay_payment_id, amount_paise,
            status, retry_count, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        ("rfnd-1", "appt-4", "pay_123", 50000, "PENDING", 2, "2026-02-06T10:00:00Z")
    )

    await test_db.commit()

    return test_db


def test_appointments_requires_auth(test_client):
    """Test that GET /api/appointments returns 401 without authentication."""
    response = test_client.get("/api/appointments")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_appointments_returns_list(test_client, db_with_appointments):
    """Test that GET /api/appointments returns JSON array with authentication."""
    # Mock get_db to return test database
    async def mock_get_db():
        yield db_with_appointments

    # Mock require_auth to return mock user
    async def mock_require_auth():
        return {"email": "test@example.com", "name": "Test User"}

    # Override dependencies
    app.dependency_overrides[get_db] = mock_get_db
    app.dependency_overrides[require_auth] = mock_require_auth

    try:
        response = test_client.get("/api/appointments")

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        # Should return today's and future appointments (not yesterday's)
        assert len(data) >= 2

        # Verify structure of first appointment
        if len(data) > 0:
            appt = data[0]
            assert "id" in appt
            assert "patient_name" in appt
            assert "patient_age" in appt
            assert "patient_gender" in appt
            assert "patient_phone" in appt
            assert "consultation_type" in appt
            assert "appointment_date" in appt
            assert "slot_time" in appt
            assert "status" in appt
    finally:
        # Clean up overrides
        app.dependency_overrides.clear()


def test_appointments_filters_by_date(test_client, db_with_appointments):
    """Test that date_from/date_to parameters filter appointments correctly."""
    tomorrow = (ist_now() + timedelta(days=1)).strftime("%Y-%m-%d")

    async def mock_get_db():
        yield db_with_appointments

    async def mock_require_auth():
        return {"email": "test@example.com"}

    app.dependency_overrides[get_db] = mock_get_db
    app.dependency_overrides[require_auth] = mock_require_auth

    try:
        response = test_client.get(
            f"/api/appointments?date_from={tomorrow}&date_to={tomorrow}"
        )

        assert response.status_code == 200
        data = response.json()

        # Should only return tomorrow's appointment
        assert len(data) == 1
        assert data[0]["appointment_date"] == tomorrow
    finally:
        app.dependency_overrides.clear()


def test_appointments_history_returns_past(test_client, db_with_appointments):
    """Test that GET /api/appointments/history returns only past appointments."""
    async def mock_get_db():
        yield db_with_appointments

    async def mock_require_auth():
        return {"email": "test@example.com"}

    app.dependency_overrides[get_db] = mock_get_db
    app.dependency_overrides[require_auth] = mock_require_auth

    try:
        response = test_client.get("/api/appointments/history")

        assert response.status_code == 200
        data = response.json()

        # Should only return yesterday's appointment
        assert len(data) == 1
        assert data[0]["status"] == "COMPLETED"

        # Verify it's a past date
        today = ist_now().strftime("%Y-%m-%d")
        assert data[0]["appointment_date"] < today
    finally:
        app.dependency_overrides.clear()


def test_refunds_failed_returns_pending(test_client, db_with_appointments):
    """Test that GET /api/refunds/failed returns only PENDING/FAILED refunds."""
    async def mock_get_db():
        yield db_with_appointments

    async def mock_require_auth():
        return {"email": "test@example.com"}

    app.dependency_overrides[get_db] = mock_get_db
    app.dependency_overrides[require_auth] = mock_require_auth

    try:
        response = test_client.get("/api/refunds/failed")

        assert response.status_code == 200
        data = response.json()

        # Should return the pending refund
        assert len(data) == 1
        assert data[0]["status"] == "PENDING"
        assert data[0]["patient_name"] == "Alice Brown"
        assert data[0]["retry_count"] == 2
        assert data[0]["amount_paise"] == 50000
    finally:
        app.dependency_overrides.clear()


def test_settings_returns_schedule(test_client):
    """Test that GET /api/settings returns ScheduleConfig fields."""
    async def mock_require_auth():
        return {"email": "test@example.com"}

    app.dependency_overrides[require_auth] = mock_require_auth

    try:
        response = test_client.get("/api/settings")

        assert response.status_code == 200
        data = response.json()

        # Verify all required fields present
        assert "working_days" in data
        assert "start_time" in data
        assert "end_time" in data
        assert "break_start" in data
        assert "break_end" in data
        assert "slot_duration_minutes" in data

        # Verify types
        assert isinstance(data["working_days"], list)
        assert isinstance(data["start_time"], str)
        assert isinstance(data["slot_duration_minutes"], int)
    finally:
        app.dependency_overrides.clear()


def test_phone_masking(test_client, db_with_appointments):
    """Test that patient phone numbers are masked in responses."""
    async def mock_get_db():
        yield db_with_appointments

    async def mock_require_auth():
        return {"email": "test@example.com"}

    app.dependency_overrides[get_db] = mock_get_db
    app.dependency_overrides[require_auth] = mock_require_auth

    try:
        response = test_client.get("/api/appointments")

        assert response.status_code == 200
        data = response.json()

        # Check that phone numbers are masked
        for appt in data:
            phone = appt["patient_phone"]
            # Should start with **** and end with 4 digits
            assert phone.startswith("****")
            assert len(phone) == 8  # ****XXXX
            assert phone[4:].isdigit()
    finally:
        app.dependency_overrides.clear()
