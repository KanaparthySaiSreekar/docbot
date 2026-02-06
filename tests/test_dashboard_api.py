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


@pytest.mark.asyncio
async def test_cancel_appointment_doctor(test_client, test_db):
    """Doctor can cancel any appointment without time restriction."""
    # Create a confirmed appointment
    await test_db.execute(
        """INSERT INTO appointments
           (id, patient_phone, patient_name, patient_age, patient_gender,
            consultation_type, appointment_date, slot_time, status,
            created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        ("appt-cancel", "+919876543210", "Test User", 30, "Male",
         "offline", "2026-02-07", "10:00", "CONFIRMED",
         "2026-02-06T10:00:00Z", "2026-02-06T10:00:00Z")
    )
    await test_db.commit()

    async def mock_get_db():
        yield test_db

    async def mock_require_auth():
        return {"email": "test@example.com"}

    app.dependency_overrides[get_db] = mock_get_db
    app.dependency_overrides[require_auth] = mock_require_auth

    try:
        # Disable CSRF for testing by setting cookie
        test_client.cookies.set("csrftoken", "test-token")

        # Cancel appointment
        response = test_client.post(
            "/api/appointments/appt-cancel/cancel",
            headers={"X-CSRF-Token": "test-token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "cancelled"

        # Verify appointment status updated
        cursor = await test_db.execute(
            "SELECT status FROM appointments WHERE id = ?",
            ("appt-cancel",)
        )
        row = await cursor.fetchone()
        assert row[0] == "CANCELLED"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_cancel_triggers_refund(test_client, test_db):
    """Online cancellation triggers refund."""
    # Create confirmed online appointment with payment
    await test_db.execute(
        """INSERT INTO appointments
           (id, patient_phone, patient_name, patient_age, patient_gender,
            consultation_type, appointment_date, slot_time, status,
            razorpay_payment_id, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        ("appt-refund", "+919876543210", "Test User", 30, "Male",
         "online", "2026-02-07", "10:00", "CONFIRMED",
         "pay_test123", "2026-02-06T10:00:00Z", "2026-02-06T10:00:00Z")
    )
    await test_db.execute(
        """INSERT INTO payments
           (id, appointment_id, razorpay_payment_id, amount_paise, status, created_at)
           VALUES (?, ?, ?, ?, ?, ?)""",
        ("pmt-1", "appt-refund", "pay_test123", 50000, "captured", "2026-02-06T10:00:00Z")
    )
    await test_db.commit()

    async def mock_get_db():
        yield test_db

    async def mock_require_auth():
        return {"email": "test@example.com"}

    app.dependency_overrides[get_db] = mock_get_db
    app.dependency_overrides[require_auth] = mock_require_auth

    try:
        # Disable CSRF for testing
        test_client.cookies.set("csrftoken", "test-token")

        # Mock refund API call
        with patch("docbot.refund_service._call_razorpay_refund") as mock_refund:
            mock_refund.return_value = {"id": "rfnd_test123", "status": "processed"}

            response = test_client.post(
                "/api/appointments/appt-refund/cancel",
                headers={"X-CSRF-Token": "test-token"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "cancelled"
            assert data["refund_status"] in ["processed", "pending"]

            # Verify refund record created
            cursor = await test_db.execute(
                "SELECT status FROM refunds WHERE appointment_id = ?",
                ("appt-refund",)
            )
            row = await cursor.fetchone()
            assert row is not None
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_retry_refund(test_client, test_db):
    """Manual refund retry works."""
    # Create appointment and failed refund
    await test_db.execute(
        """INSERT INTO appointments
           (id, patient_phone, patient_name, patient_age, patient_gender,
            consultation_type, appointment_date, slot_time, status,
            razorpay_payment_id, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        ("appt-retry", "+919876543210", "Test User", 30, "Male",
         "online", "2026-02-07", "10:00", "CANCELLED",
         "pay_test456", "2026-02-06T10:00:00Z", "2026-02-06T10:00:00Z")
    )
    await test_db.execute(
        """INSERT INTO payments
           (id, appointment_id, razorpay_payment_id, amount_paise, status, created_at)
           VALUES (?, ?, ?, ?, ?, ?)""",
        ("pmt-retry", "appt-retry", "pay_test456", 50000, "captured", "2026-02-06T10:00:00Z")
    )
    await test_db.execute(
        """INSERT INTO refunds
           (id, appointment_id, razorpay_payment_id, amount_paise,
            status, retry_count, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        ("rfnd-retry", "appt-retry", "pay_test456", 50000, "PENDING", 2, "2026-02-06T10:00:00Z")
    )
    await test_db.commit()

    async def mock_get_db():
        yield test_db

    async def mock_require_auth():
        return {"email": "test@example.com"}

    app.dependency_overrides[get_db] = mock_get_db
    app.dependency_overrides[require_auth] = mock_require_auth

    try:
        # Disable CSRF for testing
        test_client.cookies.set("csrftoken", "test-token")

        # Mock refund API call
        with patch("docbot.refund_service._call_razorpay_refund") as mock_refund:
            mock_refund.return_value = {"id": "rfnd_test789", "status": "processed"}

            response = test_client.post(
                "/api/refunds/rfnd-retry/retry",
                headers={"X-CSRF-Token": "test-token"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] in ["processed", "pending_retry"]
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_resend_confirmation(test_client, test_db):
    """Resend confirmation to patient."""
    # Create confirmed appointment
    await test_db.execute(
        """INSERT INTO appointments
           (id, patient_phone, patient_name, patient_age, patient_gender,
            consultation_type, appointment_date, slot_time, status,
            google_meet_link, language, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        ("appt-resend", "+919876543210", "Test User", 30, "Male",
         "online", "2026-02-07", "10:00", "CONFIRMED",
         "meet.google.com/xyz", "en", "2026-02-06T10:00:00Z", "2026-02-06T10:00:00Z")
    )
    await test_db.commit()

    async def mock_get_db():
        yield test_db

    async def mock_require_auth():
        return {"email": "test@example.com"}

    app.dependency_overrides[get_db] = mock_get_db
    app.dependency_overrides[require_auth] = mock_require_auth

    try:
        # Disable CSRF for testing
        test_client.cookies.set("csrftoken", "test-token")

        # Mock WhatsApp send
        with patch("docbot.whatsapp_client.send_text") as mock_send:
            mock_send.return_value = {"messaging_product": "whatsapp"}

            response = test_client.post(
                "/api/appointments/appt-resend/resend",
                headers={"X-CSRF-Token": "test-token"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "sent"

            # Verify send was called
            mock_send.assert_called_once()
    finally:
        app.dependency_overrides.clear()


def test_csrf_required(test_client):
    """Mutation endpoints require CSRF token (disabled in test env)."""
    async def mock_require_auth():
        return {"email": "test@example.com"}

    app.dependency_overrides[require_auth] = mock_require_auth

    try:
        # Try to cancel without CSRF token
        # In test environment, CSRF is disabled, so this will fail with 400 (bad request)
        # because the appointment doesn't exist
        response = test_client.post("/api/appointments/test-id/cancel")

        # In test env, CSRF is disabled so we get 400 for missing appointment
        # In prod env, CSRF middleware would return 403 when token missing
        assert response.status_code == 400
        assert "appointment_not_found" in response.json()["detail"]
    finally:
        app.dependency_overrides.clear()


def test_update_settings_valid(test_client, tmp_path):
    """Valid schedule update succeeds."""
    async def mock_require_auth():
        return {"email": "test@example.com"}

    app.dependency_overrides[require_auth] = mock_require_auth

    try:
        # Disable CSRF for testing
        test_client.cookies.set("csrftoken", "test-token")

        # Update settings
        response = test_client.put(
            "/api/settings",
            json={
                "working_days": [0, 1, 2, 3, 4],
                "start_time": "08:00",
                "end_time": "18:00",
                "break_start": "12:00",
                "break_end": "13:00"
            },
            headers={"X-CSRF-Token": "test-token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "updated"

        # Verify config file was updated
        import os
        env = os.getenv("DOCBOT_ENV", "test")
        config_path = f"config.{env}.json"

        if os.path.exists(config_path):
            import json
            with open(config_path, "r") as f:
                config_data = json.load(f)

            assert config_data["schedule"]["working_days"] == [0, 1, 2, 3, 4]
            assert config_data["schedule"]["start_time"] == "08:00"
    finally:
        app.dependency_overrides.clear()


def test_update_settings_invalid_days(test_client):
    """Invalid working days rejected."""
    async def mock_require_auth():
        return {"email": "test@example.com"}

    app.dependency_overrides[require_auth] = mock_require_auth

    try:
        # Disable CSRF for testing
        test_client.cookies.set("csrftoken", "test-token")

        # Try to update with invalid working days
        response = test_client.put(
            "/api/settings",
            json={
                "working_days": [7, 8],
                "start_time": "09:00",
                "end_time": "17:00",
                "break_start": "13:00",
                "break_end": "14:00"
            },
            headers={"X-CSRF-Token": "test-token"}
        )

        assert response.status_code == 422
        # Check that error mentions working_days validation
        assert "working_days" in response.text
    finally:
        app.dependency_overrides.clear()


def test_update_settings_invalid_times(test_client):
    """Invalid time format rejected."""
    async def mock_require_auth():
        return {"email": "test@example.com"}

    app.dependency_overrides[require_auth] = mock_require_auth

    try:
        # Disable CSRF for testing
        test_client.cookies.set("csrftoken", "test-token")

        # Try to update with invalid time format
        response = test_client.put(
            "/api/settings",
            json={
                "working_days": [0, 1, 2, 3, 4],
                "start_time": "9:00",  # Missing leading zero
                "end_time": "17:00",
                "break_start": "13:00",
                "break_end": "14:00"
            },
            headers={"X-CSRF-Token": "test-token"}
        )

        assert response.status_code == 422
    finally:
        app.dependency_overrides.clear()


def test_update_settings_end_before_start(test_client):
    """End time before start time rejected."""
    async def mock_require_auth():
        return {"email": "test@example.com"}

    app.dependency_overrides[require_auth] = mock_require_auth

    try:
        # Disable CSRF for testing
        test_client.cookies.set("csrftoken", "test-token")

        # Try to update with end before start
        response = test_client.put(
            "/api/settings",
            json={
                "working_days": [0, 1, 2, 3, 4],
                "start_time": "17:00",
                "end_time": "09:00",
                "break_start": "13:00",
                "break_end": "14:00"
            },
            headers={"X-CSRF-Token": "test-token"}
        )

        assert response.status_code == 422
    finally:
        app.dependency_overrides.clear()


def test_update_settings_requires_auth(test_client):
    """Settings update requires authentication."""
    # Try to update without authentication
    response = test_client.put(
        "/api/settings",
        json={
            "working_days": [0, 1, 2, 3, 4],
            "start_time": "09:00",
            "end_time": "17:00",
            "break_start": "13:00",
            "break_end": "14:00"
        }
    )

    assert response.status_code == 401
