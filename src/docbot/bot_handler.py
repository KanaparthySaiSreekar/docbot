"""Bot conversation handler for WhatsApp booking flow."""

import logging
from datetime import datetime
from typing import Any

from docbot import (
    booking_service,
    conversation,
    i18n,
    patient_store,
    slot_service,
    whatsapp_client,
)
from docbot.cancellation_service import can_cancel_appointment, cancel_appointment
from docbot.alerts import log_alert
from docbot.calendar_service import create_appointment_event
from docbot.config import get_settings, is_booking_disabled
from docbot.payment_service import create_payment_for_appointment
from docbot.conversation import (
    CONFIRM_BOOKING,
    ENTER_AGE,
    ENTER_GENDER,
    ENTER_NAME,
    LANGUAGE_SELECT,
    MAIN_MENU,
    SELECT_DATE,
    SELECT_SLOT,
    SELECT_TYPE,
)
from docbot.database import get_db

logger = logging.getLogger(__name__)


def format_time_for_display(time_str: str) -> str:
    """
    Format 24-hour time to 12-hour format with AM/PM.

    Args:
        time_str: Time in HH:MM format

    Returns:
        str: Formatted time like "9:00 AM" or "2:30 PM"
    """
    hour, minute = map(int, time_str.split(":"))
    if hour == 0:
        return f"12:{minute:02d} AM"
    elif hour < 12:
        return f"{hour}:{minute:02d} AM"
    elif hour == 12:
        return f"12:{minute:02d} PM"
    else:
        return f"{hour - 12}:{minute:02d} PM"


def format_date_for_display(date_str: str) -> str:
    """
    Format date string to readable format.

    Args:
        date_str: Date in YYYY-MM-DD format

    Returns:
        str: Formatted like "Wed, 12 Feb"
    """
    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    return date_obj.strftime("%a, %d %b")


async def handle_message(parsed_message: dict[str, Any]) -> None:
    """
    Handle incoming WhatsApp message and route through conversation flow.

    Args:
        parsed_message: Parsed message dict with keys:
            - from: phone number
            - type: message type
            - message_id: WhatsApp message ID
            - button_id: button ID if button reply
            - button_title: button title if button reply
            - text: text content if text message
            - timestamp: message timestamp
    """
    phone = parsed_message["from"]
    button_id = parsed_message.get("button_id")
    text = parsed_message.get("text")

    # Handle direct cancel button clicks (outside conversation flow)
    if button_id and button_id.startswith("cancel_"):
        appointment_id = button_id.replace("cancel_", "")
        try:
            async for db in get_db():
                language = await patient_store.get_language(db, phone)
                await _handle_cancel_confirm(db, phone, appointment_id, language)
                return
        except Exception as e:
            logger.error(f"Error handling cancel: {e}", exc_info=True)

    try:
        async for db in get_db():
            # Get patient language
            language = await patient_store.get_language(db, phone)

            # Get active conversation
            conv = await conversation.get_conversation(db, phone)

            # Check if conversation expired and inform user
            if conv is None and parsed_message.get("type") != "first_message":
                # Check if patient exists (returning user vs new user)
                patient = await patient_store.get_or_create_patient(db, phone)

                # If patient has no language set, they're new - start language selection
                if patient["language"] == "en" and not button_id and not text:
                    conv = await conversation.start_conversation(db, phone, LANGUAGE_SELECT)
                else:
                    # Returning user - check if session expired
                    # Send session expired message then restart
                    await whatsapp_client.send_text(
                        phone, i18n.get_message("session_expired", language)
                    )
                    # Start fresh conversation at main menu
                    conv = await conversation.start_conversation(db, phone, MAIN_MENU)

            # If still no conversation (first message ever), start language selection
            if conv is None:
                conv = await conversation.start_conversation(db, phone, LANGUAGE_SELECT)

            state = conv["state"]
            data = conv["data"]

            # Route by conversation state
            if state == LANGUAGE_SELECT:
                await _handle_language_select(db, phone, button_id, language)

            elif state == MAIN_MENU:
                await _handle_main_menu(db, phone, button_id, language)

            elif state == SELECT_TYPE:
                await _handle_select_type(db, phone, button_id, language)

            elif state == SELECT_DATE:
                await _handle_select_date(db, phone, button_id, language)

            elif state == SELECT_SLOT:
                await _handle_select_slot(db, phone, button_id, data, language)

            elif state == ENTER_NAME:
                await _handle_enter_name(db, phone, text, language)

            elif state == ENTER_AGE:
                await _handle_enter_age(db, phone, text, language)

            elif state == ENTER_GENDER:
                await _handle_enter_gender(db, phone, button_id, data, language)

            elif state == CONFIRM_BOOKING:
                await _handle_confirm_booking(db, phone, button_id, data, language)

            else:
                logger.warning(f"Unknown conversation state: {state}", extra={"phone": phone, "state": state})
                await whatsapp_client.send_text(
                    phone, i18n.get_message("error_generic", language)
                )
                await conversation.end_conversation(db, phone)

    except Exception as e:
        logger.error(
            f"Error handling message from {phone}: {e}",
            extra={"phone": phone, "error": str(e)},
            exc_info=True
        )
        log_alert(
            "ERROR",
            "bot_handler_error",
            f"Failed to handle message from {phone}",
            {"phone": phone, "error": str(e)}
        )
        # Send generic error message
        try:
            async for db in get_db():
                language = await patient_store.get_language(db, phone)
                await whatsapp_client.send_text(
                    phone, i18n.get_message("error_generic", language)
                )
                await conversation.end_conversation(db, phone)
        except Exception as inner_e:
            logger.error(f"Failed to send error message: {inner_e}")


async def _handle_language_select(db, phone: str, button_id: str | None, language: str) -> None:
    """Handle language selection state."""
    if button_id is None:
        # First time - send language selection buttons
        settings = get_settings()
        welcome_text = i18n.get_message("welcome", "en", clinic_name=settings.clinic.name)

        buttons = [
            {"id": "lang_en", "title": i18n.get_message("lang_english", "en")},
            {"id": "lang_te", "title": i18n.get_message("lang_telugu", "te")},
            {"id": "lang_hi", "title": i18n.get_message("lang_hindi", "hi")},
        ]

        await whatsapp_client.send_buttons(phone, welcome_text, buttons)
        return

    # Handle button response
    lang_map = {
        "lang_en": "en",
        "lang_te": "te",
        "lang_hi": "hi",
    }

    if button_id not in lang_map:
        # Invalid input - resend buttons
        settings = get_settings()
        welcome_text = i18n.get_message("welcome", "en", clinic_name=settings.clinic.name)
        await whatsapp_client.send_text(phone, i18n.get_message("invalid_input", "en"))

        buttons = [
            {"id": "lang_en", "title": i18n.get_message("lang_english", "en")},
            {"id": "lang_te", "title": i18n.get_message("lang_telugu", "te")},
            {"id": "lang_hi", "title": i18n.get_message("lang_hindi", "hi")},
        ]
        await whatsapp_client.send_buttons(phone, welcome_text, buttons)
        return

    # Valid language selected
    selected_lang = lang_map[button_id]
    await patient_store.set_language(db, phone, selected_lang)

    # Send confirmation
    lang_name = i18n.get_language_name(selected_lang)
    confirmation = i18n.get_message("language_set", selected_lang, language=lang_name)
    await whatsapp_client.send_text(phone, confirmation)

    # Advance to main menu
    await conversation.update_conversation(db, phone, MAIN_MENU)
    await _send_main_menu(phone, selected_lang)


async def _send_main_menu(phone: str, language: str) -> None:
    """Send main menu buttons."""
    menu_text = i18n.get_message("main_menu", language)

    buttons = [
        {"id": "menu_book", "title": i18n.get_message("menu_book", language)},
        {"id": "menu_cancel", "title": i18n.get_message("menu_cancel", language)},
        {"id": "menu_contact", "title": i18n.get_message("menu_contact", language)},
    ]

    await whatsapp_client.send_buttons(phone, menu_text, buttons)


async def _handle_main_menu(db, phone: str, button_id: str | None, language: str) -> None:
    """Handle main menu state."""
    if button_id is None:
        # Send menu
        await _send_main_menu(phone, language)
        return

    if button_id == "menu_book":
        # Check if booking is disabled (emergency mode)
        if is_booking_disabled():
            await whatsapp_client.send_text(phone, i18n.get_message("booking_disabled", language))
            # Stay in main menu
            await _send_main_menu(phone, language)
            return

        # Start booking flow
        await conversation.update_conversation(db, phone, SELECT_TYPE)
        await _send_consultation_type(phone, language)

    elif button_id == "menu_contact":
        # Send contact info
        settings = get_settings()
        hours = f"{settings.schedule.start_time} - {settings.schedule.end_time}"
        contact_text = i18n.get_message(
            "contact_info",
            language,
            phone=settings.clinic.phone,
            address=settings.clinic.address,
            hours=hours
        )
        await whatsapp_client.send_text(phone, contact_text)
        # Stay in main menu
        await _send_main_menu(phone, language)

    elif button_id == "menu_cancel":
        # Show cancellable appointments
        await _handle_cancel_menu(db, phone, language)

    else:
        # Invalid input
        await whatsapp_client.send_text(phone, i18n.get_message("invalid_input", language))
        await _send_main_menu(phone, language)


async def _send_consultation_type(phone: str, language: str) -> None:
    """Send consultation type selection buttons."""
    type_text = i18n.get_message("select_type", language)

    buttons = [
        {"id": "type_online", "title": i18n.get_message("type_online", language)},
        {"id": "type_offline", "title": i18n.get_message("type_offline", language)},
    ]

    await whatsapp_client.send_buttons(phone, type_text, buttons)


async def _handle_select_type(db, phone: str, button_id: str | None, language: str) -> None:
    """Handle consultation type selection state."""
    if button_id is None:
        await _send_consultation_type(phone, language)
        return

    type_map = {
        "type_online": "online",
        "type_offline": "offline",
    }

    if button_id not in type_map:
        # Invalid input
        await whatsapp_client.send_text(phone, i18n.get_message("invalid_input", language))
        await _send_consultation_type(phone, language)
        return

    # Valid type selected
    consultation_type = type_map[button_id]
    await conversation.update_conversation(
        db, phone, SELECT_DATE, {"consultation_type": consultation_type}
    )

    # Send available dates
    await _send_available_dates(db, phone, language)


async def _send_available_dates(db, phone: str, language: str) -> None:
    """Send available dates as list."""
    dates = await slot_service.get_available_dates(db)

    if not dates:
        # No dates available
        await whatsapp_client.send_text(
            phone, i18n.get_message("no_dates_available", language)
        )
        await conversation.end_conversation(db, phone)
        await _send_main_menu(phone, language)
        return

    # Build list message
    date_text = i18n.get_message("select_date", language)

    # Build list rows
    rows = []
    for date_str in dates:
        # Get slot count for this date
        slots = await slot_service.get_available_slots(db, date_str)
        slot_count = len(slots)

        rows.append({
            "id": date_str,
            "title": format_date_for_display(date_str),
            "description": f"{slot_count} slots available"
        })

    sections = [{"title": "Available Dates", "rows": rows}]

    await whatsapp_client.send_list(phone, date_text, "Select Date", sections)


async def _handle_select_date(db, phone: str, button_id: str | None, language: str) -> None:
    """Handle date selection state."""
    if button_id is None:
        await _send_available_dates(db, phone, language)
        return

    # button_id is the date string (YYYY-MM-DD)
    date_str = button_id

    # Validate date format
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        # Invalid date
        await whatsapp_client.send_text(phone, i18n.get_message("invalid_input", language))
        await _send_available_dates(db, phone, language)
        return

    # Store selected date
    await conversation.update_conversation(
        db, phone, SELECT_SLOT, {"appointment_date": date_str}
    )

    # Send available slots
    await _send_available_slots(db, phone, date_str, language)


async def _send_available_slots(db, phone: str, date_str: str, language: str) -> None:
    """Send available slots as list."""
    slots = await slot_service.get_available_slots(db, date_str)

    if not slots:
        # No slots available
        await whatsapp_client.send_text(
            phone, i18n.get_message("no_slots_available", language)
        )
        # Go back to date selection
        await conversation.update_conversation(db, phone, SELECT_DATE, {})
        await _send_available_dates(db, phone, language)
        return

    # Build list message
    formatted_date = format_date_for_display(date_str)
    slot_text = i18n.get_message("select_slot", language, date=formatted_date)

    # Build list rows
    rows = []
    for slot_time in slots:
        rows.append({
            "id": slot_time,
            "title": format_time_for_display(slot_time),
            "description": "Available"
        })

    sections = [{"title": "Available Slots", "rows": rows}]

    await whatsapp_client.send_list(phone, slot_text, "Select Time", sections)


async def _handle_select_slot(
    db, phone: str, button_id: str | None, data: dict, language: str
) -> None:
    """Handle slot selection state."""
    if button_id is None:
        date_str = data.get("appointment_date")
        if date_str:
            await _send_available_slots(db, phone, date_str, language)
        else:
            # No date stored, go back to date selection
            await conversation.update_conversation(db, phone, SELECT_DATE, {})
            await _send_available_dates(db, phone, language)
        return

    # button_id is the slot time (HH:MM)
    slot_time = button_id
    date_str = data.get("appointment_date")

    if not date_str:
        # No date stored, go back
        await conversation.update_conversation(db, phone, SELECT_DATE, {})
        await _send_available_dates(db, phone, language)
        return

    # Try to lock the slot
    lock_acquired = await booking_service.lock_slot(db, phone, date_str, slot_time)

    if not lock_acquired:
        # Slot already taken
        await whatsapp_client.send_text(phone, i18n.get_message("slot_taken", language))
        # Resend slot list
        await _send_available_slots(db, phone, date_str, language)
        return

    # Lock acquired - store slot and advance to name entry
    await conversation.update_conversation(
        db, phone, ENTER_NAME, {"slot_time": slot_time}
    )

    # Prompt for name
    await whatsapp_client.send_text(phone, i18n.get_message("enter_name", language))


async def _handle_enter_name(db, phone: str, text: str | None, language: str) -> None:
    """Handle name entry state."""
    if not text or text.strip() == "":
        # Empty/invalid input
        await whatsapp_client.send_text(phone, i18n.get_message("invalid_input", language))
        await whatsapp_client.send_text(phone, i18n.get_message("enter_name", language))
        return

    # Valid name - store and advance
    await conversation.update_conversation(
        db, phone, ENTER_AGE, {"patient_name": text.strip()}
    )

    # Prompt for age
    await whatsapp_client.send_text(phone, i18n.get_message("enter_age", language))


async def _handle_enter_age(db, phone: str, text: str | None, language: str) -> None:
    """Handle age entry state."""
    if not text or not text.strip().isdigit():
        # Invalid input
        await whatsapp_client.send_text(phone, i18n.get_message("invalid_input", language))
        await whatsapp_client.send_text(phone, i18n.get_message("enter_age", language))
        return

    age = int(text.strip())
    if age < 0 or age > 150:
        # Invalid age range
        await whatsapp_client.send_text(phone, i18n.get_message("invalid_input", language))
        await whatsapp_client.send_text(phone, i18n.get_message("enter_age", language))
        return

    # Valid age - store and advance
    await conversation.update_conversation(
        db, phone, ENTER_GENDER, {"patient_age": age}
    )

    # Send gender selection buttons
    await _send_gender_selection(phone, language)


async def _send_gender_selection(phone: str, language: str) -> None:
    """Send gender selection buttons."""
    gender_text = i18n.get_message("select_gender", language)

    buttons = [
        {"id": "gender_male", "title": i18n.get_message("gender_male", language)},
        {"id": "gender_female", "title": i18n.get_message("gender_female", language)},
        {"id": "gender_other", "title": i18n.get_message("gender_other", language)},
    ]

    await whatsapp_client.send_buttons(phone, gender_text, buttons)


async def _handle_enter_gender(
    db, phone: str, button_id: str | None, data: dict, language: str
) -> None:
    """Handle gender selection state."""
    if button_id is None:
        await _send_gender_selection(phone, language)
        return

    gender_map = {
        "gender_male": "Male",
        "gender_female": "Female",
        "gender_other": "Other",
    }

    if button_id not in gender_map:
        # Invalid input
        await whatsapp_client.send_text(phone, i18n.get_message("invalid_input", language))
        await _send_gender_selection(phone, language)
        return

    # Valid gender - store and advance to confirmation
    gender = gender_map[button_id]
    await conversation.update_conversation(
        db, phone, CONFIRM_BOOKING, {"patient_gender": gender}
    )

    # Send booking confirmation
    await _send_booking_confirmation(db, phone, data, gender, language)


async def _send_booking_confirmation(
    db, phone: str, data: dict, gender: str, language: str
) -> None:
    """Send booking confirmation with summary."""
    # Get booking details from conversation data
    consultation_type = data.get("consultation_type")
    date_str = data.get("appointment_date")
    slot_time = data.get("slot_time")
    name = data.get("patient_name")
    age = data.get("patient_age")

    # Merge newly added gender
    full_data = {**data, "patient_gender": gender}

    # Get updated conversation to ensure data is persisted
    conv = await conversation.get_conversation(db, phone)
    if conv:
        full_data = conv["data"]

    # Format for display
    type_display = i18n.get_message(f"type_{consultation_type}", language)
    date_display = format_date_for_display(date_str)
    time_display = format_time_for_display(slot_time)
    gender_display = i18n.get_message(f"gender_{gender.lower()}", language)

    # Get fee
    settings = get_settings()
    fee = settings.fees.online_consultation

    # Build confirmation message
    confirmation_text = i18n.get_message(
        "confirm_booking",
        language,
        type=type_display,
        date=date_display,
        time=time_display,
        name=name,
        age=age,
        gender=gender_display,
        fee=fee
    )

    # Send confirmation with buttons
    buttons = [
        {"id": "confirm_yes", "title": i18n.get_message("confirm_yes", language)},
        {"id": "confirm_no", "title": i18n.get_message("confirm_no", language)},
    ]

    await whatsapp_client.send_buttons(phone, confirmation_text, buttons)


async def _handle_confirm_booking(
    db, phone: str, button_id: str | None, data: dict, language: str
) -> None:
    """Handle booking confirmation state."""
    if button_id is None:
        # Resend confirmation
        gender = data.get("patient_gender")
        await _send_booking_confirmation(db, phone, data, gender, language)
        return

    if button_id == "confirm_no":
        # Cancel booking
        date_str = data.get("appointment_date")
        slot_time = data.get("slot_time")

        # Release lock
        if date_str and slot_time:
            await booking_service.release_lock(db, phone, date_str, slot_time)

        # Send cancellation message
        await whatsapp_client.send_text(
            phone, i18n.get_message("booking_cancelled_by_user", language)
        )

        # End conversation and return to main menu
        await conversation.end_conversation(db, phone)
        await _send_main_menu(phone, language)
        return

    if button_id != "confirm_yes":
        # Invalid input
        await whatsapp_client.send_text(phone, i18n.get_message("invalid_input", language))
        gender = data.get("patient_gender")
        await _send_booking_confirmation(db, phone, data, gender, language)
        return

    # Confirm booking - re-verify slot availability
    date_str = data.get("appointment_date")
    slot_time = data.get("slot_time")

    # Check if slot still available
    slots = await slot_service.get_available_slots(db, date_str)

    # Also need to check if there's an active lock
    if slot_time not in slots:
        # Check if we have the lock
        from docbot.timezone_utils import utc_now
        cursor = await db.execute(
            """SELECT locked_by_phone FROM slot_locks
               WHERE appointment_date = ? AND slot_time = ?
               AND locked_until > ?""",
            (date_str, slot_time, utc_now().isoformat())
        )
        row = await cursor.fetchone()

        if not row or row[0] != phone:
            # Slot no longer available
            await whatsapp_client.send_text(phone, i18n.get_message("slot_taken", language))
            # Go back to slot selection
            await conversation.update_conversation(db, phone, SELECT_SLOT, {})
            await _send_available_slots(db, phone, date_str, language)
            return

    # Slot still available - create appointment
    try:
        appointment = await booking_service.create_appointment(
            db,
            phone=phone,
            name=data["patient_name"],
            age=data["patient_age"],
            gender=data["patient_gender"],
            consultation_type=data["consultation_type"],
            date_str=date_str,
            slot_time=slot_time,
            language=language
        )

        # Send confirmation message
        date_display = format_date_for_display(date_str)
        time_display = format_time_for_display(slot_time)
        consultation_type = data["consultation_type"]

        if consultation_type == "online":
            # Create payment link
            payment_result = await create_payment_for_appointment(db, appointment["id"])

            if payment_result and "short_url" in payment_result:
                await whatsapp_client.send_text(
                    phone,
                    i18n.get_message(
                        "booking_payment_required",
                        language,
                        date=date_display,
                        time=time_display,
                        amount="500",
                        payment_link=payment_result["short_url"]
                    )
                )
            else:
                # Payment link creation failed - log alert, send fallback message
                log_alert(
                    "ERROR",
                    "payment_link_creation_failed",
                    f"Failed to create payment link for appointment {appointment['id']}",
                    {"appointment_id": appointment["id"], "phone": phone}
                )
                await whatsapp_client.send_text(
                    phone,
                    i18n.get_message("booking_payment_error", language)
                )

        else:  # offline
            # Create calendar event immediately
            cal_result = await create_appointment_event(db, appointment["id"])

            settings = get_settings()
            await whatsapp_client.send_text(
                phone,
                i18n.get_message(
                    "booking_confirmed_offline",
                    language,
                    date=date_display,
                    time=time_display,
                    clinic_address=settings.clinic.address
                )
            )

        # End conversation
        await conversation.end_conversation(db, phone)

        logger.info(
            f"Appointment created successfully: {appointment['id']}",
            extra={"phone": phone, "appointment_id": appointment["id"], "type": consultation_type}
        )

    except ValueError as e:
        # Double-booking or other validation error
        logger.warning(f"Failed to create appointment: {e}", extra={"phone": phone})
        await whatsapp_client.send_text(phone, i18n.get_message("slot_taken", language))

        # Release any locks and go back to slot selection
        await booking_service.release_lock(db, phone, date_str, slot_time)
        await conversation.update_conversation(db, phone, SELECT_SLOT, {})
        await _send_available_slots(db, phone, date_str, language)


async def _handle_cancel_menu(db, phone: str, language: str) -> None:
    """Handle cancel appointment menu."""
    # Find patient's upcoming appointments
    cursor = await db.execute(
        """SELECT id, appointment_date, slot_time, consultation_type
           FROM appointments
           WHERE patient_phone = ?
           AND status IN ('CONFIRMED', 'PENDING_PAYMENT')
           AND appointment_date >= date('now')
           ORDER BY appointment_date, slot_time
           LIMIT 5""",
        (phone,)
    )
    rows = await cursor.fetchall()

    if not rows:
        await whatsapp_client.send_text(phone, i18n.get_message("no_appointments_to_cancel", language))
        await _send_main_menu(phone, language)
        return

    # Build list of cancellable appointments
    sections = []
    rows_list = []
    for row in rows:
        appt_id, date_str, slot_time, consult_type = row
        can, reason = await can_cancel_appointment(db, appt_id)
        if can:
            formatted_date = format_date_for_display(date_str)
            formatted_time = format_time_for_display(slot_time)
            rows_list.append({
                "id": f"cancel_{appt_id}",
                "title": f"{formatted_date} {formatted_time}",
                "description": consult_type.title()
            })

    if not rows_list:
        await whatsapp_client.send_text(phone, i18n.get_message("no_cancellable_appointments", language))
        await _send_main_menu(phone, language)
        return

    sections.append({"title": "Your Appointments", "rows": rows_list})

    await whatsapp_client.send_list(
        phone,
        i18n.get_message("select_appointment_to_cancel", language),
        "Cancel",
        sections
    )


async def _handle_cancel_confirm(db, phone: str, appointment_id: str, language: str) -> None:
    """Process cancellation confirmation."""
    try:
        result = await cancel_appointment(db, appointment_id)

        if result["refund_status"] == "processed":
            await whatsapp_client.send_text(phone, i18n.get_message("cancellation_with_refund", language))
        elif result["refund_status"] == "pending":
            await whatsapp_client.send_text(phone, i18n.get_message("cancellation_refund_pending", language))
        else:
            await whatsapp_client.send_text(phone, i18n.get_message("cancellation_confirmed", language))

        # Return to main menu
        await _send_main_menu(phone, language)

    except ValueError as e:
        if str(e) == "too_late":
            await whatsapp_client.send_text(phone, i18n.get_message("cancellation_too_late", language))
        else:
            await whatsapp_client.send_text(phone, i18n.get_message("cancellation_failed", language))

        # Return to main menu
        await _send_main_menu(phone, language)
