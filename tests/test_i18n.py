"""Tests for i18n multi-language message catalog."""

import pytest

from docbot.i18n import (
    MESSAGES,
    get_language_name,
    get_message,
    get_supported_languages,
)


def test_get_message_returns_english_by_default():
    """Test get_message returns English by default."""
    msg = get_message("welcome", clinic_name="Test Clinic")
    assert "Welcome to Test Clinic!" in msg
    assert "Please select your language:" in msg


def test_get_message_returns_telugu():
    """Test get_message returns Telugu when lang='te'."""
    msg = get_message("main_menu", lang="te")
    assert "మీరు ఏమి చేయాలనుకుంటున్నారు?" in msg


def test_get_message_returns_hindi():
    """Test get_message returns Hindi when lang='hi'."""
    msg = get_message("main_menu", lang="hi")
    assert "आप क्या करना चाहते हैं?" in msg


def test_get_message_with_format_kwargs():
    """Test get_message with format kwargs substitutes correctly."""
    msg = get_message(
        "confirm_booking",
        lang="en",
        type="Online",
        date="2026-02-10",
        time="10:00 AM",
        name="John Doe",
        age=30,
        gender="Male",
        fee=500,
    )
    assert "Type: Online" in msg
    assert "Date: 2026-02-10" in msg
    assert "Time: 10:00 AM" in msg
    assert "Name: John Doe" in msg
    assert "Age: 30" in msg
    assert "Gender: Male" in msg
    assert "₹500" in msg


def test_get_message_falls_back_to_english():
    """Test get_message falls back to English for missing translation."""
    # Add a temporary message with only English
    MESSAGES["test_fallback"] = {"en": "English only"}

    try:
        msg = get_message("test_fallback", lang="te")
        assert msg == "English only"
    finally:
        # Clean up
        del MESSAGES["test_fallback"]


def test_get_message_raises_keyerror_for_unknown_key():
    """Test get_message raises KeyError for unknown key."""
    with pytest.raises(KeyError, match="Unknown message key"):
        get_message("nonexistent_key")


def test_all_message_keys_have_all_translations():
    """Test all required message keys exist in all 3 languages."""
    required_languages = {"en", "te", "hi"}
    missing = []

    for key, translations in MESSAGES.items():
        for lang in required_languages:
            if lang not in translations:
                missing.append((key, lang))

    if missing:
        missing_str = "\n".join([f"  {key}: missing {lang}" for key, lang in missing])
        pytest.fail(f"Missing translations:\n{missing_str}")


def test_get_supported_languages():
    """Test get_supported_languages returns correct list."""
    langs = get_supported_languages()
    assert langs == ["en", "te", "hi"]


def test_get_language_name():
    """Test get_language_name returns human-readable names."""
    assert get_language_name("en") == "English"
    assert get_language_name("te") == "Telugu"
    assert get_language_name("hi") == "Hindi"
    assert get_language_name("unknown") == "unknown"  # Fallback
