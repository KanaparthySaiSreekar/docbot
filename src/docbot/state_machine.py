"""Appointment state machine with transition validation."""

from enum import Enum


class AppointmentStatus(Enum):
    """Appointment status values."""
    PENDING_PAYMENT = "PENDING_PAYMENT"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"
    REFUNDED = "REFUNDED"


# Valid state transitions
VALID_TRANSITIONS = {
    "PENDING_PAYMENT": {"CONFIRMED"},
    "CONFIRMED": {"CANCELLED"},
    "CANCELLED": {"REFUNDED"},
    "REFUNDED": set(),  # Terminal state
}


def can_transition(current: str, target: str) -> bool:
    """
    Check if transition from current to target status is valid.

    Args:
        current: Current appointment status
        target: Target appointment status

    Returns:
        bool: True if transition is valid, False otherwise
    """
    if current not in VALID_TRANSITIONS:
        return False
    return target in VALID_TRANSITIONS.get(current, set())


def transition(current: str, target: str) -> str:
    """
    Perform state transition with validation.

    Args:
        current: Current appointment status
        target: Target appointment status

    Returns:
        str: Target status if transition is valid

    Raises:
        ValueError: If transition is invalid or status is unknown
    """
    # Validate statuses exist
    valid_statuses = {s.value for s in AppointmentStatus}
    if current not in valid_statuses:
        raise ValueError(f"Invalid current status: {current}")
    if target not in valid_statuses:
        raise ValueError(f"Invalid target status: {target}")

    # Check if transition is allowed
    if not can_transition(current, target):
        raise ValueError(
            f"Invalid transition: {current} -> {target}. "
            f"Allowed transitions from {current}: {VALID_TRANSITIONS.get(current, set())}"
        )

    return target
