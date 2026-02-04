"""Tests for appointment state machine transitions."""

import pytest

from docbot.state_machine import AppointmentStatus, can_transition, transition


def test_valid_transitions():
    """Test valid state transitions."""
    # PENDING_PAYMENT -> CONFIRMED
    assert transition("PENDING_PAYMENT", "CONFIRMED") == "CONFIRMED"
    
    # CONFIRMED -> CANCELLED
    assert transition("CONFIRMED", "CANCELLED") == "CANCELLED"
    
    # CANCELLED -> REFUNDED
    assert transition("CANCELLED", "REFUNDED") == "REFUNDED"


def test_invalid_transitions():
    """Test invalid state transitions that should raise ValueError."""
    # PENDING_PAYMENT cannot skip to CANCELLED
    with pytest.raises(ValueError):
        transition("PENDING_PAYMENT", "CANCELLED")
    
    # PENDING_PAYMENT cannot skip to REFUNDED
    with pytest.raises(ValueError):
        transition("PENDING_PAYMENT", "REFUNDED")
    
    # Cannot go backward: CONFIRMED -> PENDING_PAYMENT
    with pytest.raises(ValueError):
        transition("CONFIRMED", "PENDING_PAYMENT")
    
    # Cannot go backward: REFUNDED -> CONFIRMED
    with pytest.raises(ValueError):
        transition("REFUNDED", "CONFIRMED")


def test_can_transition_returns_bool():
    """Test can_transition returns boolean without raising."""
    # Valid transitions
    assert can_transition("CONFIRMED", "CANCELLED") is True
    
    # Invalid transitions
    assert can_transition("CONFIRMED", "REFUNDED") is False
    assert can_transition("PENDING_PAYMENT", "CANCELLED") is False


def test_all_statuses_defined():
    """Test AppointmentStatus enum has exactly 4 values."""
    assert len(AppointmentStatus) == 4
    assert "PENDING_PAYMENT" in [s.value for s in AppointmentStatus]
    assert "CONFIRMED" in [s.value for s in AppointmentStatus]
    assert "CANCELLED" in [s.value for s in AppointmentStatus]
    assert "REFUNDED" in [s.value for s in AppointmentStatus]


def test_transition_raises_on_invalid_status():
    """Test transition raises ValueError for unknown statuses."""
    with pytest.raises(ValueError):
        transition("INVALID_STATUS", "CONFIRMED")
    
    with pytest.raises(ValueError):
        transition("CONFIRMED", "INVALID_TARGET")
