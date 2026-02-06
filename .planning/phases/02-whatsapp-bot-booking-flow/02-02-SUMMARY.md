---
phase: 02-whatsapp-bot-booking-flow
plan: 02
subsystem: database
tags: [sqlite, aiosqlite, i18n, state-machine, conversation-flow]

# Dependency graph
requires:
  - phase: 01-foundation
    provides: Database infrastructure, timezone utilities, logging
provides:
  - Patient language preference persistence (BOT-03)
  - Conversation state tracking for booking flow (BOT-09)
  - Multi-language message catalog (English, Telugu, Hindi) (BOT-06)
  - 30-minute rolling conversation expiry
  - One active conversation per phone enforcement
affects: [02-03, 02-04, bot-handler, payment-integration]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Conversation state machine with JSON data blob for accumulated booking info
    - Language preference persistence per phone number
    - Rolling expiry for conversation timeout
    - Message catalog with fallback to English

key-files:
  created:
    - db/002_patients_conversations.sql
    - src/docbot/patient_store.py
    - src/docbot/conversation.py
    - src/docbot/i18n.py
    - tests/test_patient_store.py
    - tests/test_conversation.py
    - tests/test_i18n.py
  modified:
    - src/docbot/database.py
    - tests/conftest.py

key-decisions:
  - "Auto-discovery of schema files: database.py loads all .sql files in sorted order for automatic migration management"
  - "Conversation data stored as JSON blob for flexibility in tracking booking flow progress"
  - "30-minute rolling expiry for conversations to prevent stale bookings"
  - "One active conversation per phone enforced at database level (PRIMARY KEY on phone)"
  - "Message catalog structure supports template substitution via .format()"

patterns-established:
  - "Patient store pattern: language preference persistence with get/set operations"
  - "Conversation state pattern: start/update/end lifecycle with automatic expiry cleanup"
  - "i18n pattern: message catalog with language fallback and template variable substitution"

# Metrics
duration: 10min
completed: 2026-02-06
---

# Phase 02 Plan 02: Patient Data Layer Summary

**Patient language persistence, conversation state machine with 30-min rolling expiry, and tri-lingual message catalog (English/Telugu/Hindi)**

## Performance

- **Duration:** 10 min
- **Started:** 2026-02-06T05:11:28Z
- **Completed:** 2026-02-06T05:21:00Z
- **Tasks:** 2
- **Files modified:** 9

## Accomplishments
- Patient language preferences persist per phone number with get/set operations
- Conversation state machine tracks booking flow steps with JSON data blob
- Multi-language message catalog covers all Phase 2 bot interactions in 3 languages
- 30-minute rolling expiry prevents stale conversations
- One active conversation per phone enforced (BOT-09)

## Task Commits

Each task was committed atomically:

1. **Task 1: Patient storage and conversation state with schema migration** - Already completed in previous session (fd58347)
2. **Task 2: Multi-language message catalog (i18n)** - `9655e63` (feat)

**Note:** Task 1 was already implemented in commit fd58347 which was labeled as 02-01 but contained all the patient_store, conversation, and schema work specified in this plan.

## Files Created/Modified
- `db/002_patients_conversations.sql` - Schema for patients and conversations tables
- `src/docbot/patient_store.py` - CRUD for patient language preferences and profile
- `src/docbot/conversation.py` - Conversation state machine for booking flow
- `src/docbot/i18n.py` - Multi-language message catalog with 3 languages
- `src/docbot/database.py` - Auto-discovery of all schema files in db/ directory
- `tests/conftest.py` - Load all schema files for test database
- `tests/test_patient_store.py` - Tests for patient CRUD operations
- `tests/test_conversation.py` - Tests for conversation state management
- `tests/test_i18n.py` - Tests for message translation lookup

## Decisions Made

**Auto-discovery of schema files:**
- Modified `database.py` to load all `.sql` files in sorted order instead of hardcoding specific files
- Future schema migrations will be auto-discovered by adding numbered files to db/ directory
- Simplifies adding new schema migrations without code changes

**Conversation data as JSON blob:**
- Stores accumulated booking data (consultation_type, date, slot, patient info) as JSON
- Flexible structure supports future booking flow changes without schema migration
- Uses json.dumps/json.loads for serialization

**30-minute rolling expiry:**
- Each conversation update resets expires_at to 30 minutes from now
- Prevents timeout during active booking flow
- Expired conversations auto-deleted on access or via cleanup function

**One active conversation enforcement:**
- PRIMARY KEY on phone in conversations table prevents concurrent bookings
- start_conversation deletes existing conversation before creating new one
- Prevents booking conflicts per BOT-09 requirement

**Message catalog structure:**
- Nested dict: {message_key: {lang_code: message_string}}
- Template substitution via .format(**kwargs)
- Fallback to English if translation missing
- All 25 message keys have all 3 translations

## Deviations from Plan

None - plan executed exactly as written.

**Note:** Task 1 artifacts were created in a previous execution session, but all implementation matches the plan specification.

## Issues Encountered

**Test timing flakiness:**
- Initial test failures in test_start_conversation_replaces_existing and test_update_conversation_resets_expiry
- Issue: Operations happening too fast, timestamps identical
- Fix: Added 0.01s asyncio.sleep delays and changed assertions from > to >=
- All tests now pass reliably

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

**Ready for bot handler implementation (02-03, 02-04):**
- Patient language preferences can be retrieved and set
- Conversation state tracks where user is in booking flow
- All bot messages available in 3 languages
- Conversation expiry prevents stale bookings

**Database schema complete for Phase 2:**
- patients table stores language and name per phone
- conversations table tracks active booking flows
- Both tables integrated into auto-loading schema system

**No blockers or concerns.**

---
*Phase: 02-whatsapp-bot-booking-flow*
*Completed: 2026-02-06*
