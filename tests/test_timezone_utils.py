"""Tests for timezone conversion utilities."""

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import pytest

from docbot.timezone_utils import (
    IST,
    format_ist,
    ist_now,
    is_same_day_ist,
    slot_to_utc,
    to_ist,
    to_utc,
    utc_now,
)


def test_utc_now_returns_utc():
    """Test utc_now() returns datetime with UTC timezone."""
    now = utc_now()
    assert now.tzinfo == timezone.utc


def test_to_ist_converts_correctly():
    """Test UTC to IST conversion adds 5:30."""
    # Known UTC time: 2026-02-05 00:00:00 UTC
    utc_dt = datetime(2026, 2, 5, 0, 0, 0, tzinfo=timezone.utc)
    ist_dt = to_ist(utc_dt)
    
    # Should be 2026-02-05 05:30:00 IST
    assert ist_dt.year == 2026
    assert ist_dt.month == 2
    assert ist_dt.day == 5
    assert ist_dt.hour == 5
    assert ist_dt.minute == 30
    assert ist_dt.tzinfo == ZoneInfo("Asia/Kolkata")


def test_to_utc_converts_correctly():
    """Test IST to UTC conversion subtracts 5:30."""
    # Known IST time: 2026-02-05 05:30:00 IST
    ist_dt = datetime(2026, 2, 5, 5, 30, 0, tzinfo=ZoneInfo("Asia/Kolkata"))
    utc_dt = to_utc(ist_dt)
    
    # Should be 2026-02-05 00:00:00 UTC
    assert utc_dt.year == 2026
    assert utc_dt.month == 2
    assert utc_dt.day == 5
    assert utc_dt.hour == 0
    assert utc_dt.minute == 0
    assert utc_dt.tzinfo == timezone.utc


def test_ist_now_returns_ist():
    """Test ist_now() returns datetime with IST timezone."""
    now = ist_now()
    assert now.tzinfo == ZoneInfo("Asia/Kolkata")


def test_format_ist_display():
    """Test format_ist() returns human-readable IST string."""
    # UTC time: 2026-02-05 14:30:00 UTC
    utc_dt = datetime(2026, 2, 5, 14, 30, 0, tzinfo=timezone.utc)
    formatted = format_ist(utc_dt)
    
    # Should convert to IST (20:00) and format nicely
    assert "05 Feb 2026" in formatted
    assert "08:00 PM" in formatted or "8:00 PM" in formatted
    assert "IST" in formatted


def test_is_same_day_ist():
    """Test is_same_day_ist() correctly checks IST day boundaries."""
    # Two UTC times on different UTC days but same IST day
    # 2026-02-04 23:00:00 UTC = 2026-02-05 04:30:00 IST
    # 2026-02-05 01:00:00 UTC = 2026-02-05 06:30:00 IST
    dt1 = datetime(2026, 2, 4, 23, 0, 0, tzinfo=timezone.utc)
    dt2 = datetime(2026, 2, 5, 1, 0, 0, tzinfo=timezone.utc)
    
    assert is_same_day_ist(dt1, dt2) is True
    
    # Two UTC times on different IST days
    # 2026-02-04 18:00:00 UTC = 2026-02-04 23:30:00 IST
    # 2026-02-04 23:00:00 UTC = 2026-02-05 04:30:00 IST
    dt3 = datetime(2026, 2, 4, 18, 0, 0, tzinfo=timezone.utc)
    dt4 = datetime(2026, 2, 4, 23, 0, 0, tzinfo=timezone.utc)
    
    assert is_same_day_ist(dt3, dt4) is False


def test_slot_time_to_utc():
    """Test slot_to_utc() converts IST slot to UTC datetime."""
    # Date: 2026-02-05, Time: 14:30 IST
    # Should become: 2026-02-05 09:00:00 UTC
    utc_dt = slot_to_utc("2026-02-05", "14:30")
    
    assert utc_dt.year == 2026
    assert utc_dt.month == 2
    assert utc_dt.day == 5
    assert utc_dt.hour == 9
    assert utc_dt.minute == 0
    assert utc_dt.tzinfo == timezone.utc
