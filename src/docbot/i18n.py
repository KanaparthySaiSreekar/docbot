"""Multi-language message catalog for WhatsApp bot."""

import logging

logger = logging.getLogger(__name__)

# Message catalog for all bot interactions in English, Telugu, and Hindi
MESSAGES = {
    # Welcome & Language Selection
    "welcome": {
        "en": "Welcome to {clinic_name}! Please select your language:",
        "te": "{clinic_name} కు స్వాగతం! దయచేసి మీ భాషను ఎంచుకోండి:",
        "hi": "{clinic_name} में आपका स्वागत है! कृपया अपनी भाषा चुनें:",
    },
    "lang_english": {
        "en": "English",
        "te": "English",
        "hi": "English",
    },
    "lang_telugu": {
        "en": "Telugu",
        "te": "తెలుగు",
        "hi": "Telugu",
    },
    "lang_hindi": {
        "en": "Hindi",
        "te": "Hindi",
        "hi": "हिंदी",
    },
    "language_set": {
        "en": "Language set to {language}",
        "te": "భాష {language} కు సెట్ చేయబడింది",
        "hi": "भाषा {language} पर सेट की गई",
    },
    # Main Menu
    "main_menu": {
        "en": "What would you like to do?",
        "te": "మీరు ఏమి చేయాలనుకుంటున్నారు?",
        "hi": "आप क्या करना चाहते हैं?",
    },
    "menu_book": {
        "en": "📅 Book Appointment",
        "te": "📅 అపాయింట్‌మెంట్ బుక్ చేయండి",
        "hi": "📅 अपॉइंटमेंट बुक करें",
    },
    "menu_view": {
        "en": "👁️ View Appointment",
        "te": "👁️ అపాయింట్‌మెంట్ చూడండి",
        "hi": "👁️ अपॉइंटमेंट देखें",
    },
    "menu_cancel": {
        "en": "❌ Cancel Appointment",
        "te": "❌ అపాయింట్‌మెంట్ రద్దు చేయండి",
        "hi": "❌ अपॉइंटमेंट रद्द करें",
    },
    "menu_contact": {
        "en": "📞 Contact Clinic",
        "te": "📞 క్లినిక్‌ను సంప్రదించండి",
        "hi": "📞 क्लिनिक से संपर्क करें",
    },
    # Contact Info
    "contact_info": {
        "en": "📞 Contact Information:\n\nPhone: {phone}\nAddress: {address}\n\nClinic Hours:\n{hours}",
        "te": "📞 సంప్రదింపు సమాచారం:\n\nఫోన్: {phone}\nచిరునామా: {address}\n\nక్లినిక్ సమయాలు:\n{hours}",
        "hi": "📞 संपर्क जानकारी:\n\nफ़ोन: {phone}\nपता: {address}\n\nक्लिनिक के घंटे:\n{hours}",
    },
    # Booking Flow
    "select_type": {
        "en": "Select consultation type:",
        "te": "కన్సల్టేషన్ రకాన్ని ఆఏర్చుకోండి:",
        "hi": "परामर्श प्रकार चुनें:",
    },
    "type_online": {
        "en": "💻 Online Consultation",
        "te": "💻 ఆన్‌లైన్ కన్సల్టేషన్",
        "hi": "💻 ऑनलाइन परामर्श",
    },
    "type_offline": {
        "en": "🏥 Offline Consultation",
        "te": "🏥 ఆఫ్‌లైన్ కన్సల్టేషన్",
        "hi": "🏥 ऑफलाइन परामर्श",
    },
    "select_date": {
        "en": "Select appointment date:",
        "te": "అపాయింట్‌మెంట్ తేదీని ఎంచుకోండి:",
        "hi": "अपॉइंटमेंट तारीख चुनें:",
    },
    "no_dates_available": {
        "en": "No dates available at this time. Please try again later.",
        "te": "ఈ సమయంలో తేదీలు అందుబాటులో లేవు. దయచేసి తర్వాత మళ్లీ ప్రయత్నించండి.",
        "hi": "इस समय कोई तारीख उपलब्ध नहीं है। कृपया बाद में पुनः प्रयास करें।",
    },
    "select_slot": {
        "en": "Select time slot for {date}:",
        "te": "{date} కోసం సమయ స్లాట్‌ను ఎంచుకోండి:",
        "hi": "{date} के लिए समय स्लॉट चुनें:",
    },
    "no_slots_available": {
        "en": "No slots available for this date. Please select another date.",
        "te": "ఈ తేదీకి స్లాట్‌లు అందుబాటులో లేవు. దయచేసి మరొక తేదీని ఎంచుకోండి.",
        "hi": "इस तारीख के लिए कोई स्लॉट उपलब्ध नहीं है। कृपया दूसरी तारीख चुनें।",
    },
    "enter_name": {
        "en": "Please enter your full name:",
        "te": "దయచేసి మీ పూర్తి పేరు నమోదు చేయండి:",
        "hi": "कृपया अपना पूरा नाम दर्ज करें:",
    },
    "enter_age": {
        "en": "Please enter your age:",
        "te": "దయచేసి మీ వయస్సు నమోదు చేయండి:",
        "hi": "कृपया अपनी आयु दर्ज करें:",
    },
    "select_gender": {
        "en": "Select your gender:",
        "te": "మీ లింగాన్ని ఎంచుకోండి:",
        "hi": "अपना लिंग चुनें:",
    },
    "gender_male": {
        "en": "Male",
        "te": "పురుషుడు",
        "hi": "पुरुष",
    },
    "gender_female": {
        "en": "Female",
        "te": "స్త్రీ",
        "hi": "महिला",
    },
    "gender_other": {
        "en": "Other",
        "te": "ఇతర",
        "hi": "अन्य",
    },
    # Booking Confirmation
    "confirm_booking": {
        "en": "Please confirm your booking:\n\n"
        "Type: {type}\n"
        "Date: {date}\n"
        "Time: {time}\n"
        "Name: {name}\n"
        "Age: {age}\n"
        "Gender: {gender}\n\n"
        "Consultation Fee: ₹{fee}",
        "te": "దయచేసి మీ బుకింగ్‌ను నిర్ధారించండి:\n\n"
        "రకం: {type}\n"
        "తేదీ: {date}\n"
        "సమయం: {time}\n"
        "పేరు: {name}\n"
        "వయస్సు: {age}\n"
        "లింగం: {gender}\n\n"
        "కన్సల్టేషన్ ఫీజు: ₹{fee}",
        "hi": "कृपया अपनी बुकिंग की पुष्टि करें:\n\n"
        "प्रकार: {type}\n"
        "तारीख: {date}\n"
        "समय: {time}\n"
        "नाम: {name}\n"
        "आयु: {age}\n"
        "लिंग: {gender}\n\n"
        "परामर्श शुल्क: ₹{fee}",
    },
    "confirm_yes": {
        "en": "✅ Confirm & Pay",
        "te": "✅ నిర్ధారించండి & చెల్లించండి",
        "hi": "✅ पुष्टि करें और भुगतान करें",
    },
    "confirm_no": {
        "en": "❌ Cancel",
        "te": "❌ రద్దు చేయి",
        "hi": "❌ रद्द करें",
    },
    "booking_confirmed": {
        "en": "✅ Appointment booked successfully!\n\n"
        "Appointment ID: {appointment_id}\n"
        "Date: {date}\n"
        "Time: {time}\n\n"
        "{meet_link}"
        "Please complete payment to confirm.",
        "te": "✅ అపాయింట్‌మెంట్ విజయవంతంగా బుక్ చేయబడింది!\n\n"
        "అపాయింట్‌మెంట్ ID: {appointment_id}\n"
        "తేదీ: {date}\n"
        "సమయం: {time}\n\n"
        "{meet_link}"
        "దయచేసి నిర్ధారించడానికి చెల్లింపును పూర్తి చేయండి.",
        "hi": "✅ अपॉइंटमेंट सफलतापूर्वक बुक किया गया!\n\n"
        "अपॉइंटमेंट ID: {appointment_id}\n"
        "तारीख: {date}\n"
        "समय: {time}\n\n"
        "{meet_link}"
        "कृपया पुष्टि करने के लिए भुगतान पूरा करें।",
    },
    "booking_cancelled_by_user": {
        "en": "Booking cancelled. Returning to main menu.",
        "te": "బుకింగ్ రద్దు చేయబడింది. ప్రధాన మెను కు తిరిగి వెళ్తోంది.",
        "hi": "बुकिंग रद्द की गई। मुख्य मेनू पर वापस जा रहे हैं।",
    },
    # Errors & Session
    "session_expired": {
        "en": "⏱️ Your session has expired. Please start again.",
        "te": "⏱️ మీ సెషన్ గడువు ముగిసింది. దయచేసి మళ్లీ ప్రారంభించండి.",
        "hi": "⏱️ आपका सत्र समाप्त हो गया है। कृपया फिर से शुरू करें।",
    },
    "invalid_input": {
        "en": "❌ Invalid selection. Please try again.",
        "te": "❌ చెల్లని ఎంపిక. దయచేసి మళ్లీ ప్రయత్నించండి.",
        "hi": "❌ अमान्य चयन। कृपया पुनः प्रयास करें।",
    },
    "already_booking": {
        "en": "⚠️ You already have a booking in progress. Please complete or cancel it first.",
        "te": "⚠️ మీరు ఇప్పటికే బుకింగ్ ప్రక్రియలో ఉన్నారు. దయచేసి ముందుగా దాన్ని పూర్తి చేయండి లేదా రద్దు చేయండి.",
        "hi": "⚠️ आपकी पहले से ही एक बुकिंग प्रक्रिया में है। कृपया पहले उसे पूरा करें या रद्द करें।",
    },
    "error_generic": {
        "en": "❌ Something went wrong. Please try again or contact the clinic.",
        "te": "❌ ఏదో తప్పు జరిగింది. దయచేసి మళ్లీ ప్రయత్నించండి లేదా క్లినిక్‌ను సంప్రదించండి.",
        "hi": "❌ कुछ गलत हो गया। कृपया पुनः प्रयास करें या क्लिनिक से संपर्क करें।",
    },
    "slot_taken": {
        "en": "⚠️ This slot is no longer available. Please select another.",
        "te": "⚠️ ఈ స్లాట్ ఇకపై అందుబాటులో లేదు. దయచేసి మరొకటి ఎంచుకోండి.",
        "hi": "⚠️ यह स्लॉट अब उपलब्ध नहीं है। कृपया दूसरा चुनें।",
    },
}


def get_message(key: str, lang: str = "en", **kwargs) -> str:
    """
    Get localized message with template substitution.

    Falls back to English if translation missing.

    Args:
        key: Message key
        lang: Language code ('en', 'te', 'hi')
        **kwargs: Template variables for .format()

    Returns:
        str: Localized message with substitutions applied

    Raises:
        KeyError: If message key doesn't exist in any language
    """
    if key not in MESSAGES:
        logger.error(f"Unknown message key: {key}")
        raise KeyError(f"Unknown message key: {key}")

    messages_for_key = MESSAGES[key]

    # Get message in requested language, fallback to English
    message = messages_for_key.get(lang, messages_for_key.get("en"))

    if message is None:
        logger.error(f"No translation found for key {key} in any language")
        raise KeyError(f"No translation found for key {key}")

    # Apply template substitution
    try:
        return message.format(**kwargs)
    except KeyError as e:
        logger.error(f"Missing template variable for message {key}: {e}")
        raise


def get_supported_languages() -> list[str]:
    """
    Get list of supported language codes.

    Returns:
        list[str]: Supported language codes
    """
    return ["en", "te", "hi"]


def get_language_name(code: str) -> str:
    """
    Get human-readable language name.

    Args:
        code: Language code ('en', 'te', 'hi')

    Returns:
        str: Human-readable language name
    """
    names = {
        "en": "English",
        "te": "Telugu",
        "hi": "Hindi",
    }
    return names.get(code, code)
