"""Integration tests for bot conversation handler."""

import pytest
from unittest.mock import AsyncMock, patch

from docbot import bot_handler, patient_store, conversation, booking_service
from docbot.conversation import (
    LANGUAGE_SELECT,
    MAIN_MENU,
    SELECT_TYPE,
    SELECT_DATE,
    SELECT_SLOT,
    ENTER_NAME,
    ENTER_AGE,
    ENTER_GENDER,
    CONFIRM_BOOKING,
)
from docbot.database import get_db


async def simulate_message(phone: str, text: str = None, button_id: str = None, button_title: str = None) -> dict:
    """Helper to construct parsed message dict."""
    return {
        "from": phone,
        "type": "interactive" if button_id else "text",
        "message_id": f"wamid_test_{phone}",
        "timestamp": "1234567890",
        "button_id": button_id,
        "button_title": button_title,
        "text": text,
    }


def mock_get_db(test_db):
    """Helper to create a mock get_db that returns the test database."""
    async def _get_db():
        yield test_db
    return _get_db


@pytest.mark.asyncio
async def test_new_patient_gets_language_selection(test_db):
    """Test that first message from unknown number triggers language selection."""
    phone = "+911234567890"

    with patch("docbot.bot_handler.get_db", mock_get_db(test_db)), \
         patch("docbot.bot_handler.whatsapp_client.send_buttons", new_callable=AsyncMock) as mock_send:
        msg = await simulate_message(phone)
        await bot_handler.handle_message(msg)

        # Verify language selection buttons were sent
        mock_send.assert_called_once()
        args = mock_send.call_args[0]
        assert args[0] == phone  # recipient
        assert "Welcome" in args[1]  # message text

        # Check buttons
        buttons = mock_send.call_args[0][2]
        assert len(buttons) == 3
        assert any(b["id"] == "lang_en" for b in buttons)
        assert any(b["id"] == "lang_te" for b in buttons)
        assert any(b["id"] == "lang_hi" for b in buttons)


@pytest.mark.asyncio
async def test_language_selection_persists(test_db):
    """Test that language selection is persisted and used in next interaction."""
    phone = "+911234567891"

    with patch("docbot.bot_handler.get_db", mock_get_db(test_db)), \
         patch("docbot.bot_handler.whatsapp_client.send_buttons", new_callable=AsyncMock), \
         patch("docbot.bot_handler.whatsapp_client.send_text", new_callable=AsyncMock) as mock_text:

        # First start language selection
        msg = await simulate_message(phone)
        await bot_handler.handle_message(msg)

        # Select Telugu
        msg = await simulate_message(phone, button_id="lang_te")
        await bot_handler.handle_message(msg)

        # Verify language was saved
        lang = await patient_store.get_language(test_db, phone)
        assert lang == "te"

        # Verify confirmation was sent in Telugu
        assert mock_text.call_count >= 1
        # Find the language set confirmation
        for call in mock_text.call_args_list:
            if "సెట్ చేయబడింది" in call[0][1]:  # Telugu confirmation
                break
        else:
            assert False, "Telugu confirmation not found"


@pytest.mark.asyncio
async def test_main_menu_shows_after_language(test_db):
    """Test that main menu is shown after language selection."""
    phone = "+911234567892"

    with patch("docbot.bot_handler.get_db", mock_get_db(test_db)), \
         patch("docbot.bot_handler.whatsapp_client.send_buttons", new_callable=AsyncMock) as mock_send, \
         patch("docbot.bot_handler.whatsapp_client.send_text", new_callable=AsyncMock):

        # Start and select English
        msg = await simulate_message(phone)
        await bot_handler.handle_message(msg)

        msg = await simulate_message(phone, button_id="lang_en")
        await bot_handler.handle_message(msg)

        # Main menu should be sent (second call to send_buttons)
        assert mock_send.call_count == 2
        menu_call = mock_send.call_args_list[1]

        # Check menu buttons
        buttons = menu_call[0][2]
        assert len(buttons) == 3
        assert any(b["id"] == "menu_book" for b in buttons)
        assert any(b["id"] == "menu_cancel" for b in buttons)
        assert any(b["id"] == "menu_contact" for b in buttons)


@pytest.mark.asyncio
async def test_booking_flow_select_type(test_db):
    """Test that booking appointment from menu shows consultation type selection."""
    phone = "+911234567893"

    # Setup: set language first
    await patient_store.set_language(test_db, phone, "en")
    await conversation.start_conversation(test_db, phone, MAIN_MENU)

    with patch("docbot.bot_handler.get_db", mock_get_db(test_db)), \
         patch("docbot.bot_handler.whatsapp_client.send_buttons", new_callable=AsyncMock) as mock_send:
        msg = await simulate_message(phone, button_id="menu_book")
        await bot_handler.handle_message(msg)

        # Verify consultation type selection
        mock_send.assert_called_once()
        buttons = mock_send.call_args[0][2]
        assert len(buttons) == 2
        assert any(b["id"] == "type_online" for b in buttons)
        assert any(b["id"] == "type_offline" for b in buttons)

        # Verify conversation state
        conv = await conversation.get_conversation(test_db, phone)
        assert conv["state"] == SELECT_TYPE


@pytest.mark.asyncio
async def test_booking_flow_select_date(test_db):
    """Test that after selecting type, available dates are shown."""
    phone = "+911234567894"

    # Setup
    await patient_store.set_language(test_db, phone, "en")
    await conversation.start_conversation(test_db, phone, SELECT_TYPE)

    # Mock slot service to return some dates
    with patch("docbot.bot_handler.get_db", mock_get_db(test_db)), \
         patch("docbot.bot_handler.slot_service.get_available_dates") as mock_dates, \
         patch("docbot.bot_handler.slot_service.get_available_slots") as mock_slots, \
         patch("docbot.bot_handler.whatsapp_client.send_list", new_callable=AsyncMock) as mock_list:

        mock_dates.return_value = ["2026-02-10", "2026-02-11"]
        mock_slots.return_value = ["09:00", "10:00", "11:00"]

        msg = await simulate_message(phone, button_id="type_online")
        await bot_handler.handle_message(msg)

        # Verify list message sent
        mock_list.assert_called_once()
        args = mock_list.call_args[0]
        assert args[0] == phone

        # Check sections have date rows
        sections = args[3]
        assert len(sections) > 0
        assert len(sections[0]["rows"]) == 2

        # Verify conversation state
        conv = await conversation.get_conversation(test_db, phone)
        assert conv["state"] == SELECT_DATE
        assert conv["data"]["consultation_type"] == "online"


@pytest.mark.asyncio
async def test_booking_flow_select_slot_and_lock(test_db):
    """Test that selecting date shows slots and selecting slot creates lock."""
    phone = "+911234567895"

    # Setup
    await patient_store.set_language(test_db, phone, "en")
    await conversation.start_conversation(test_db, phone, SELECT_DATE)
    await conversation.update_conversation(
        test_db, phone, SELECT_DATE, {"consultation_type": "offline"}
    )

    # Mock slot service
    with patch("docbot.bot_handler.get_db", mock_get_db(test_db)), \
         patch("docbot.bot_handler.slot_service.get_available_slots") as mock_slots, \
         patch("docbot.bot_handler.whatsapp_client.send_list", new_callable=AsyncMock) as mock_list, \
         patch("docbot.bot_handler.whatsapp_client.send_text", new_callable=AsyncMock):

        mock_slots.return_value = ["09:00", "10:00", "11:00"]

        # Select date
        msg = await simulate_message(phone, button_id="2026-02-10")
        await bot_handler.handle_message(msg)

        # Verify slots list sent
        mock_list.assert_called_once()

        # Verify conversation updated with date
        conv = await conversation.get_conversation(test_db, phone)
        assert conv["state"] == SELECT_SLOT
        assert conv["data"]["appointment_date"] == "2026-02-10"

        # Now select a slot
        msg2 = await simulate_message(phone, button_id="09:00")
        await bot_handler.handle_message(msg2)

        # Verify lock was created
        from docbot.timezone_utils import utc_now
        cursor = await test_db.execute(
            """SELECT locked_by_phone FROM slot_locks
               WHERE appointment_date = ? AND slot_time = ?
               AND locked_until > ?""",
            ("2026-02-10", "09:00", utc_now().isoformat())
        )
        row = await cursor.fetchone()
        assert row is not None
        assert row[0] == phone

        # Verify moved to name entry
        conv = await conversation.get_conversation(test_db, phone)
        assert conv["state"] == ENTER_NAME
        assert conv["data"]["slot_time"] == "09:00"


@pytest.mark.asyncio
async def test_booking_flow_enter_details(test_db):
    """Test name -> age -> gender flow with text and button inputs."""
    phone = "+911234567896"

    # Setup
    await patient_store.set_language(test_db, phone, "en")
    await conversation.start_conversation(test_db, phone, ENTER_NAME)
    await conversation.update_conversation(
        test_db, phone, ENTER_NAME, {
            "consultation_type": "online",
            "appointment_date": "2026-02-10",
            "slot_time": "09:00"
        }
    )

    with patch("docbot.bot_handler.get_db", mock_get_db(test_db)), \
         patch("docbot.bot_handler.whatsapp_client.send_text", new_callable=AsyncMock) as mock_text, \
         patch("docbot.bot_handler.whatsapp_client.send_buttons", new_callable=AsyncMock) as mock_buttons:

        # Enter name
        msg = await simulate_message(phone, text="John Doe")
        await bot_handler.handle_message(msg)

        conv = await conversation.get_conversation(test_db, phone)
        assert conv["state"] == ENTER_AGE
        assert conv["data"]["patient_name"] == "John Doe"

        # Enter age
        msg2 = await simulate_message(phone, text="30")
        await bot_handler.handle_message(msg2)

        conv = await conversation.get_conversation(test_db, phone)
        assert conv["state"] == ENTER_GENDER
        assert conv["data"]["patient_age"] == 30

        # Gender selection buttons should be sent
        mock_buttons.assert_called_once()
        buttons = mock_buttons.call_args[0][2]
        assert len(buttons) == 3

        # Select gender
        msg3 = await simulate_message(phone, button_id="gender_male")
        await bot_handler.handle_message(msg3)

        conv = await conversation.get_conversation(test_db, phone)
        assert conv["state"] == CONFIRM_BOOKING
        assert conv["data"]["patient_gender"] == "Male"


@pytest.mark.asyncio
async def test_booking_flow_confirm_creates_appointment(test_db):
    """Test that confirming booking creates appointment in database."""
    phone = "+911234567897"

    # Setup
    await patient_store.set_language(test_db, phone, "en")
    await conversation.start_conversation(test_db, phone, CONFIRM_BOOKING)
    await conversation.update_conversation(
        test_db, phone, CONFIRM_BOOKING, {
            "consultation_type": "offline",
            "appointment_date": "2026-02-10",
            "slot_time": "10:00",
            "patient_name": "Jane Smith",
            "patient_age": 25,
            "patient_gender": "Female"
        }
    )

    # Create a lock for this slot
    await booking_service.lock_slot(test_db, phone, "2026-02-10", "10:00")

    with patch("docbot.bot_handler.get_db", mock_get_db(test_db)), \
         patch("docbot.bot_handler.slot_service.get_available_slots") as mock_slots, \
         patch("docbot.bot_handler.create_appointment_event") as mock_cal, \
         patch("docbot.bot_handler.whatsapp_client.send_buttons", new_callable=AsyncMock), \
         patch("docbot.bot_handler.whatsapp_client.send_text", new_callable=AsyncMock) as mock_text, \
         patch("docbot.bot_handler.get_settings") as mock_settings:

        # Mock that slot is still available (with our lock)
        mock_slots.return_value = []  # Slot appears taken but we check lock
        mock_cal.return_value = {"event_id": "gcal-123"}
        mock_settings.return_value.clinic.address = "123 Healthcare Street, Medical District, Mumbai, Maharashtra 400001"

        # Confirm booking
        msg = await simulate_message(phone, button_id="confirm_yes")
        await bot_handler.handle_message(msg)

        # Verify appointment was created
        cursor = await test_db.execute(
            """SELECT patient_name, patient_age, patient_gender, status
               FROM appointments
               WHERE patient_phone = ? AND appointment_date = ? AND slot_time = ?""",
            (phone, "2026-02-10", "10:00")
        )
        row = await cursor.fetchone()
        assert row is not None
        assert row[0] == "Jane Smith"
        assert row[1] == 25
        assert row[2] == "Female"
        assert row[3] == "CONFIRMED"  # offline appointments are confirmed

        # Verify confirmation message sent (offline gets clinic address)
        mock_text.assert_called()
        confirmation = mock_text.call_args[0][1]
        assert "confirmed" in confirmation.lower()
        assert "Clinic Address" in confirmation

        # Verify conversation ended
        conv = await conversation.get_conversation(test_db, phone)
        assert conv is None


@pytest.mark.asyncio
async def test_expired_conversation_shows_session_expired(test_db):
    """Test that expired conversation triggers session expired message."""
    phone = "+911234567898"

    # Setup
    await patient_store.set_language(test_db, phone, "en")

    # Create conversation and manually expire it
    conv = await conversation.start_conversation(test_db, phone, SELECT_TYPE)
    from docbot.timezone_utils import utc_now
    from datetime import timedelta

    expired_time = (utc_now() - timedelta(hours=1)).isoformat()
    await test_db.execute(
        "UPDATE conversations SET expires_at = ? WHERE phone = ?",
        (expired_time, phone)
    )
    await test_db.commit()

    with patch("docbot.bot_handler.get_db", mock_get_db(test_db)), \
         patch("docbot.bot_handler.whatsapp_client.send_text", new_callable=AsyncMock) as mock_text, \
         patch("docbot.bot_handler.whatsapp_client.send_buttons", new_callable=AsyncMock):

        msg = await simulate_message(phone, text="hello")
        await bot_handler.handle_message(msg)

        # Verify session expired message sent
        assert mock_text.call_count >= 1
        first_call = mock_text.call_args_list[0]
        assert "expired" in first_call[0][1].lower()


@pytest.mark.asyncio
async def test_invalid_button_shows_retry(test_db):
    """Test that unrecognized button ID triggers invalid input message."""
    phone = "+911234567899"

    # Setup
    await patient_store.set_language(test_db, phone, "en")
    await conversation.start_conversation(test_db, phone, SELECT_TYPE)

    with patch("docbot.bot_handler.get_db", mock_get_db(test_db)), \
         patch("docbot.bot_handler.whatsapp_client.send_text", new_callable=AsyncMock) as mock_text, \
         patch("docbot.bot_handler.whatsapp_client.send_buttons", new_callable=AsyncMock):

        # Send invalid button
        msg = await simulate_message(phone, button_id="invalid_button")
        await bot_handler.handle_message(msg)

        # Verify invalid input message
        mock_text.assert_called_once()
        assert "Invalid" in mock_text.call_args[0][1]

        # Verify state unchanged
        conv = await conversation.get_conversation(test_db, phone)
        assert conv["state"] == SELECT_TYPE


@pytest.mark.asyncio
async def test_slot_taken_during_confirm(test_db):
    """Test that if slot is taken before confirm, user is redirected to slot selection."""
    phone = "+911234567800"
    other_phone = "+919999999999"

    # Setup
    await patient_store.set_language(test_db, phone, "en")
    await conversation.start_conversation(test_db, phone, CONFIRM_BOOKING)
    await conversation.update_conversation(
        test_db, phone, CONFIRM_BOOKING, {
            "consultation_type": "offline",
            "appointment_date": "2026-02-12",
            "slot_time": "11:00",
            "patient_name": "Test User",
            "patient_age": 40,
            "patient_gender": "Male"
        }
    )

    # Another user books the same slot
    await booking_service.create_appointment(
        test_db,
        phone=other_phone,
        name="Other User",
        age=35,
        gender="Female",
        consultation_type="offline",
        date_str="2026-02-12",
        slot_time="11:00"
    )

    with patch("docbot.bot_handler.get_db", mock_get_db(test_db)), \
         patch("docbot.bot_handler.slot_service.get_available_slots") as mock_slots, \
         patch("docbot.bot_handler.whatsapp_client.send_text", new_callable=AsyncMock) as mock_text, \
         patch("docbot.bot_handler.whatsapp_client.send_list", new_callable=AsyncMock):

        mock_slots.return_value = ["09:00", "10:00"]  # Slot 11:00 not available

        # Try to confirm
        msg = await simulate_message(phone, button_id="confirm_yes")
        await bot_handler.handle_message(msg)

        # Verify slot_taken message sent
        mock_text.assert_called()
        assert "no longer available" in mock_text.call_args[0][1]

        # Verify redirected to SELECT_SLOT
        conv = await conversation.get_conversation(test_db, phone)
        assert conv["state"] == SELECT_SLOT


@pytest.mark.asyncio
async def test_contact_clinic_shows_info(test_db):
    """Test that contact clinic button shows clinic info."""
    phone = "+911234567801"

    # Setup
    await patient_store.set_language(test_db, phone, "en")
    await conversation.start_conversation(test_db, phone, MAIN_MENU)

    with patch("docbot.bot_handler.get_db", mock_get_db(test_db)), \
         patch("docbot.bot_handler.whatsapp_client.send_text", new_callable=AsyncMock) as mock_text, \
         patch("docbot.bot_handler.whatsapp_client.send_buttons", new_callable=AsyncMock):

        msg = await simulate_message(phone, button_id="menu_contact")
        await bot_handler.handle_message(msg)

        # Verify contact info sent (might be called multiple times, find the contact info one)
        found_contact = False
        for call in mock_text.call_args_list:
            if "Contact Information" in call[0][1] or "Phone:" in call[0][1]:
                found_contact = True
                break

        assert found_contact, "Contact information not sent"

        # Verify still in main menu
        conv = await conversation.get_conversation(test_db, phone)
        assert conv["state"] == MAIN_MENU


@pytest.mark.asyncio
async def test_booking_flow_online_creates_payment(test_db):
    """Test that online booking creates payment link."""
    phone = "+911234567802"

    # Setup
    await patient_store.set_language(test_db, phone, "en")
    await conversation.start_conversation(test_db, phone, CONFIRM_BOOKING)
    await conversation.update_conversation(
        test_db, phone, CONFIRM_BOOKING, {
            "consultation_type": "online",
            "appointment_date": "2026-02-13",
            "slot_time": "14:00",
            "patient_name": "Online Test",
            "patient_age": 28,
            "patient_gender": "Female"
        }
    )

    # Lock the slot
    await booking_service.lock_slot(test_db, phone, "2026-02-13", "14:00")

    with patch("docbot.bot_handler.get_db", mock_get_db(test_db)), \
         patch("docbot.bot_handler.create_payment_for_appointment") as mock_payment, \
         patch("docbot.bot_handler.whatsapp_client.send_text", new_callable=AsyncMock) as mock_text:

        mock_payment.return_value = {
            "payment_id": "pay-123",
            "short_url": "https://rzp.io/test"
        }

        # Trigger confirmation
        msg = await simulate_message(phone, button_id="confirm_yes")
        await bot_handler.handle_message(msg)

        # Verify payment link creation was called
        mock_payment.assert_called_once()

        # Verify payment link sent in message
        assert mock_text.called
        sent_message = mock_text.call_args[0][1]
        assert "https://rzp.io/test" in sent_message
        assert "₹500" in sent_message


@pytest.mark.asyncio
async def test_booking_flow_offline_creates_calendar(test_db):
    """Test that offline booking creates calendar event immediately."""
    phone = "+911234567803"

    # Setup
    await patient_store.set_language(test_db, phone, "en")
    await conversation.start_conversation(test_db, phone, CONFIRM_BOOKING)
    await conversation.update_conversation(
        test_db, phone, CONFIRM_BOOKING, {
            "consultation_type": "offline",
            "appointment_date": "2026-02-14",
            "slot_time": "15:00",
            "patient_name": "Offline Test",
            "patient_age": 45,
            "patient_gender": "Male"
        }
    )

    # Lock the slot
    await booking_service.lock_slot(test_db, phone, "2026-02-14", "15:00")

    with patch("docbot.bot_handler.get_db", mock_get_db(test_db)), \
         patch("docbot.bot_handler.create_appointment_event") as mock_cal, \
         patch("docbot.bot_handler.whatsapp_client.send_text", new_callable=AsyncMock) as mock_text, \
         patch("docbot.bot_handler.get_settings") as mock_settings:

        mock_cal.return_value = {"event_id": "gcal-123"}
        mock_settings.return_value.clinic.address = "123 Main St, City"

        # Trigger offline booking confirmation
        msg = await simulate_message(phone, button_id="confirm_yes")
        await bot_handler.handle_message(msg)

        # Verify calendar creation was called
        mock_cal.assert_called_once()

        # Verify clinic address sent in message
        assert mock_text.called
        sent_message = mock_text.call_args[0][1]
        assert "123 Main St, City" in sent_message
