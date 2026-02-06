---
phase: 03-payments-calendar-integration
plan: 05
subsystem: maintenance
tags: [reconciliation, calendar-sync, refund-webhook, cron-job, data-integrity]

# Dependency graph
requires:
  - phase: 03-03
    provides: Razorpay webhook endpoint, calendar event creation, WhatsApp notifications
  - phase: 03-04
    provides: Refund service with retry mechanism

provides:
  - Nightly reconciliation job for calendar and payment sync
  - Calendar drift detection (database vs Google Calendar)
  - Orphaned calendar event detection for cancelled appointments
  - Failed calendar creation retry mechanism
  - Refund webhook processing (refund.processed events)
  - Refund completion notifications via WhatsApp
  - Cron-ready reconciliation script

affects: [04-admin-dashboard, future-monitoring-integration]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Database is authoritative source of truth (calendar synced as projection)
    - Reconciliation limits to 20 calendar retries per run to avoid overwhelming API
    - Calendar drift checks only next 7 days (performance optimization)
    - Webhook handles multiple event types (payment.captured, refund.processed)
    - i18n template variables passed as kwargs for cleaner code

key-files:
  created:
    - src/docbot/reconciliation.py
    - tests/test_reconciliation.py
    - scripts/run_reconciliation.py
  modified:
    - src/docbot/webhook.py
    - src/docbot/i18n.py
    - tests/test_webhook.py

key-decisions:
  - "Database is authoritative; calendar events synced as projection"
  - "Reconciliation retries limited to 20 per run to prevent API quota issues"
  - "Calendar drift checks only upcoming 7 days for performance"
  - "Refund webhook integrated into existing Razorpay webhook endpoint"
  - "i18n messages use kwargs pattern for consistency with existing API"

patterns-established:
  - "Reconciliation flow: retry calendar → retry refunds → check drift → check orphans → alert"
  - "Calendar drift detection: fetch event, compare time/date, flag mismatches"
  - "Orphaned detection: find CANCELLED/REFUNDED with non-null calendar event ID"
  - "Webhook routing: if/elif by event_type for different Razorpay events"

# Metrics
duration: 11 min
completed: 2026-02-06
---

# Phase 03 Plan 05: Reconciliation Job Summary

**Nightly reconciliation ensures calendar/payment sync with drift detection, failed operation retry, and refund webhook completion**

## Performance

- **Duration:** 11 min
- **Started:** 2026-02-06T15:17:53Z
- **Completed:** 2026-02-06T15:29:13Z
- **Tasks:** 2
- **Files created:** 3
- **Files modified:** 3
- **Tests added:** 5 (4 reconciliation + 1 refund webhook)
- **Total test suite:** 129 passing

## Accomplishments

- Reconciliation service retries failed calendar creations (limit 20 per run)
- Calendar drift detection compares database appointments vs Google Calendar events
- Orphaned calendar event detection finds cancelled appointments with lingering events
- Refund webhook endpoint processes refund.processed events from Razorpay
- Patient notifications sent via WhatsApp when refund completes
- Reconciliation script ready for cron scheduling (exits 1 on critical failures)
- i18n messages added for payment confirmation and refund completion
- Database established as authoritative source (calendar as projection)

## Task Commits

Each task was committed atomically:

1. **Task 1: Reconciliation service for calendar sync** - `949f18a` (feat)
   - Calendar drift detection (missing events, time mismatches)
   - Orphaned cancelled appointment detection
   - Failed calendar creation retry mechanism
   - Integration with refund retry service
   - Structured alert logging for monitoring

2. **Task 2: Refund webhook and cron script** - `363ea52` (feat)
   - Razorpay webhook handles refund.processed events
   - Patient notification on refund completion
   - i18n messages for payment/refund confirmations
   - Cron-ready reconciliation script with exit codes
   - Tests for refund webhook processing

## Files Created/Modified

**Created:**
- `src/docbot/reconciliation.py` - Reconciliation service with drift detection
- `tests/test_reconciliation.py` - Reconciliation service tests (4 tests)
- `scripts/run_reconciliation.py` - Cron-ready reconciliation script

**Modified:**
- `src/docbot/webhook.py` - Added refund.processed event handling
- `src/docbot/i18n.py` - Added payment confirmation and refund messages
- `tests/test_webhook.py` - Added refund webhook test

## Decisions Made

1. **Database is authoritative source** - Rationale: Calendar is a projection; database state is truth; drift flagged for correction

2. **Retry limit of 20 per run** - Rationale: Prevents API quota exhaustion; failed creations will retry next night

3. **7-day drift check window** - Rationale: Performance optimization; most relevant for upcoming appointments

4. **Unified webhook endpoint** - Rationale: Single Razorpay endpoint handles all event types (payment, refund) with if/elif routing

5. **i18n kwargs pattern** - Rationale: Consistent with existing get_message() API; cleaner than .format() chaining

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed logging import in reconciliation.py**
- **Found during:** Task 1 test execution
- **Issue:** Plan specified `structlog` but project uses standard `logging` library
- **Fix:** Changed `import structlog` to `import logging` and updated logger initialization
- **Files modified:** src/docbot/reconciliation.py, src/docbot/refund_service.py
- **Commit:** Included in 949f18a

**2. [Rule 1 - Bug] Fixed i18n.get_message() call signature**
- **Found during:** Task 2 test execution
- **Issue:** Used .format() chaining instead of kwargs pattern
- **Fix:** Changed to pass template variables as kwargs to get_message()
- **Files modified:** src/docbot/webhook.py
- **Commit:** Included in 363ea52

**3. [Rule 2 - Missing Critical] Added pytest_asyncio import**
- **Found during:** Task 1 test execution
- **Issue:** Async fixture missing @pytest_asyncio.fixture decorator
- **Fix:** Added import and decorator to test fixture
- **Files modified:** tests/test_reconciliation.py
- **Commit:** Included in 949f18a

## Issues Encountered

None - all blockers auto-fixed per deviation rules.

## User Setup Required

**No additional setup required.** This plan builds on existing integrations:
- Razorpay webhook already configured (Plan 03-01)
- Google Calendar API credentials already set up (Plan 03-02)
- Refund service already implemented (Plan 03-04)

**Cron job scheduling (optional):**
```bash
# Add to crontab for nightly reconciliation at 2 AM
0 2 * * * cd /app && uv run python scripts/run_reconciliation.py
```

## Next Phase Readiness

**Complete payment and calendar integration with automated reconciliation:**
- Online bookings: book → pay → calendar → Meet link → refund on cancel
- Offline bookings: book → calendar → clinic address → cancel cleanup
- Nightly reconciliation ensures data integrity
- Failed operations retry automatically

**Ready for Phase 4 (Admin Dashboard):**
- All appointment/payment/calendar data available for display
- Reconciliation metrics can be shown in admin dashboard
- Calendar sync status visible to doctor
- Refund tracking available for revenue reporting

**Maintenance patterns established:**
- Reconciliation job design (retry + drift detection + alerting)
- Database-as-truth pattern for external system sync
- Webhook routing pattern for multiple event types

---
*Phase: 03-payments-calendar-integration*
*Completed: 2026-02-06*
