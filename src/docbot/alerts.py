"""
Alert logging stub for operational monitoring.

This module provides structured alert logging for critical failures.
Phase 1: Logs alerts as structured JSON with ERROR level.
Future phases: Will integrate email, webhook, or other notification channels.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


def log_alert(level: str, category: str, message: str, details: dict[str, Any] | None = None):
    """
    Log an alert with structured data for future notification integration.

    Args:
        level: Alert severity level (INFO, WARNING, ERROR, CRITICAL)
        category: Alert category for filtering (payment_failure, calendar_failure, refund_failure)
        message: Human-readable alert message
        details: Additional structured data about the alert

    Categories:
        - payment_failure: Razorpay payment processing errors
        - calendar_failure: Google Calendar API failures
        - refund_failure: Payment refund processing errors
        - booking_failure: Appointment booking system errors
        - auth_failure: Authentication/authorization errors

    Future integration:
        - Email notifications to admin
        - Webhook to monitoring service
        - SMS alerts for critical failures
    """
    log_level = getattr(logging, level.upper(), logging.ERROR)

    extra_data = {
        "alert_category": category,
        "alert_details": details or {}
    }

    logger.log(
        log_level,
        f"[ALERT] {message}",
        extra=extra_data
    )
