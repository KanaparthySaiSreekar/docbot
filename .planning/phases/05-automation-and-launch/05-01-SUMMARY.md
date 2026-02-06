---
phase: 05-automation-and-launch
plan: 01
subsystem: automation
tags: [reminders, whatsapp, cron, notifications, i18n]
requires: [02-01-whatsapp-integration, 03-02-calendar-integration, 01-02-state-management]
provides: [automated-reminders, reminder-tracking, cron-jobs]
affects: [05-03-deployment-automation]
tech-stack:
  added: []
  patterns: [time-window-queries, database-tracking-columns, cron-scheduling]
key-files:
  created:
    - src/docbot/reminder_service.py
    - db/004_reminder_tracking.sql
    - scripts/run_reminders.py
    - tests/test_reminder_service.py
  modified:
    - src/docbot/i18n.py
decisions:
  - id: REMIND-01
    title: 24-hour and 1-hour reminder windows
    rationale: "Two reminder times (24h and 1h before) provide optimal balance between early notice and last-minute reminder without being intrusive"
  - id: REMIND-02
    title: Time window ranges for cron flexibility
    rationale: "24h window is 23-25 hours, 1h window is 50-70 minutes to accommodate cron schedule variations and ensure reminders sent even if job delayed"
  - id: REMIND-03
    title: Database tracking columns for idempotency
    rationale: "reminder_sent_24h and reminder_sent_1h columns in appointments table ensure reminders sent exactly once per type, preventing duplicate messages"
  - id: REMIND-04
    title: Separate cron script invocations for each reminder type
    rationale: "Separate commands (24h vs 1h) allow different cron schedules: hourly for 24h reminders, every 15 minutes for 1h reminders"
  - id: REMIND-05
    title: Optional db parameter for testing
    rationale: "Functions accept optional db connection to support both production (via get_db()) and testing (with in-memory test_db) without code duplication"
duration: 18 min
completed: 2026-02-07
---

# Phase 05 Plan 01: Automated Reminders Summary

**One-liner:** WhatsApp reminder automation with 24h/1h notifications using cron-scheduled jobs, database tracking, and multi-language support

## What Was Built

### Core Functionality

**Reminder Service (`src/docbot/reminder_service.py`)**
- `get_due_reminders(reminder_type, db)`: Queries CONFIRMED appointments within time windows (23-25h for "24h", 50-70min for "1h")
- `send_reminder(phone, reminder_type, appointment)`: Sends localized WhatsApp messages with Meet links (online) or clinic address (offline)
- `mark_reminder_sent(appointment_id, reminder_type, db)`: Updates database tracking columns to prevent duplicate sends
- `run_reminder_job(reminder_type, db)`: Main entry point that queries, sends, tracks, and returns statistics

**Database Schema (`db/004_reminder_tracking.sql`)**
- Added `reminder_sent_24h` and `reminder_sent_1h` TEXT columns to appointments table
- Created indexes on (reminder_sent_24h, appointment_date, status) and (reminder_sent_1h, appointment_date, status) for efficient queries

**Cron Script (`scripts/run_reminders.py`)**
- CLI interface accepting "24h" or "1h" argument
- Logs execution and prints statistics (sent/failed/skipped)
- Example cron schedules provided in docstring

**Localization (`src/docbot/i18n.py`)**
- Added 4 reminder message keys: `reminder_24h_online`, `reminder_24h_offline`, `reminder_1h_online`, `reminder_1h_offline`
- Each message in English, Telugu, and Hindi
- Online messages include Meet link, offline include clinic address

### Testing

**Comprehensive Test Suite (`tests/test_reminder_service.py`)**
- 15 tests covering all reminder service functionality
- `TestGetDueReminders`: Time window detection, exclusion logic (already sent, non-confirmed, outside window)
- `TestSendReminder`: Message content verification, language selection, failure handling
- `TestMarkReminderSent`: Database column updates, subsequent query exclusion
- `TestRunReminderJob`: Statistics accuracy, send failures, idempotency
- All tests use `test_db` fixture with sample appointments at various time offsets

## Technical Decisions

1. **Time Window Design (REMIND-02)**: Windows have buffer ranges rather than exact times
   - 24h reminder: 23-25 hours (2-hour window)
   - 1h reminder: 50-70 minutes (20-minute window)
   - Rationale: Accommodates cron schedule variations, network delays, job execution time

2. **Database Tracking Approach (REMIND-03)**: Separate boolean columns vs. timestamp columns
   - Chose: TEXT columns with 'true'/'false' values
   - Alternative considered: Timestamp columns storing when reminder sent
   - Rationale: Boolean tracking simpler for query logic, timestamps unnecessary for business requirements

3. **Cron Scheduling Strategy (REMIND-04)**: Single script with argument vs. separate scripts
   - Chose: Single script with "24h"/"1h" argument
   - Allows different cron schedules: `0 * * * *` for 24h (hourly), `*/15 * * * *` for 1h (every 15 min)
   - Rationale: Single codebase, flexibility in scheduling without code changes

4. **Testing Database Injection (REMIND-05)**: Context manager modification vs. parameter injection
   - Chose: Optional `db` parameter in all functions
   - Functions use `get_db()` if `db=None`, else use provided connection
   - Rationale: Non-intrusive to production code, explicit in tests, no mocking required

## Deviations from Plan

None - plan executed exactly as written.

## Performance Metrics

- **Task execution:** 3 tasks completed
- **Commits:** 3 atomic commits (1 per task)
- **Tests:** 15/15 passing
- **Duration:** 18 minutes
- **Lines added:** ~450 (service: 250, tests: 483, schema: 11, script: 40, i18n: 16)

## Integration Points

**Depends On:**
- 02-01 (WhatsApp Client): Uses `send_text()` for message delivery
- 03-02 (Calendar Integration): Sends Meet links from appointment records
- 01-02 (State Management): Queries appointments table, updates tracking columns

**Provides For:**
- 05-03 (Deployment Automation): Cron job setup instructions for production
- Future prescription reminders: Pattern established for adding new reminder types

**Affects:**
- WhatsApp quota usage: 2 messages per appointment (24h + 1h)
- Database load: Queries run hourly (24h) and every 15 minutes (1h)

## Next Phase Readiness

**Ready for:**
- Cron job setup in production environment
- Monitoring reminder send statistics
- Adding new reminder types (e.g., 3-day advance notice, day-of reminder)

**Blockers:** None

**Considerations:**
- Cron Job Recommended: Schedule reminders in production using provided script
  - 24h reminders: `0 * * * * cd /app && uv run python scripts/run_reminders.py 24h`
  - 1h reminders: `*/15 * * * * cd /app && uv run python scripts/run_reminders.py 1h`
- WhatsApp rate limits: Current design sends ~2 messages per appointment, monitor Meta Business Suite for quota usage
- Timezone handling: All datetime comparisons use UTC consistently with existing codebase

## Lessons Learned

1. **Time window buffer zones essential**: Initial design used exact time matching, revised to ranges after considering cron schedule reliability
2. **Database tracking simpler than in-memory state**: Using database columns eliminates need for distributed cache or state management
3. **Optional parameters for testing clean pattern**: Allows production and test code paths without mocking frameworks
4. **Comprehensive time-based testing requires careful fixture design**: Sample appointments created at precise time offsets (+24h, +1h, +2h) to verify window logic

## Verification

All verification steps from plan completed successfully:

```bash
✓ pytest tests/test_reminder_service.py -v  # 15/15 tests passing
✓ python scripts/run_reminders.py 24h        # Executes without error, returns stats
✓ python scripts/run_reminders.py 1h         # Executes without error, returns stats
✓ get_message('reminder_24h_online', ...)   # Returns formatted message with Meet link
```

**Cron job testing recommended:** Create test appointment 1 hour in future, verify 1h reminder sent automatically when cron job runs.

---

**Status:** ✅ Complete - All tasks executed, tests passing, ready for cron setup
