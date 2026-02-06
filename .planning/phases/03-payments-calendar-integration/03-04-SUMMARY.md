---
phase: 03-payments-calendar-integration
plan: 04
subsystem: cancellation-refund
tags: [razorpay, refunds, cancellation, retry-mechanism, exponential-backoff, tdd]

# Dependency graph
requires:
  - phase: 03-03
    provides: Payment webhook processing and calendar event management
  - phase: 03-01
    provides: Razorpay payment service and webhook signature verification
  - phase: 02-04
    provides: Bot conversation handler with menu system
  - phase: 01-02
    provides: State machine with CANCELLED and REFUNDED states

provides:
  - Refund service with Razorpay API integration and exponential backoff retry (1, 2, 4, 8, 16 min)
  - Cancellation service with >1 hour eligibility check
  - Patient-initiated cancellation flow via WhatsApp bot
  - Automatic refund processing for online cancellations
  - Calendar event deletion on cancellation
  - Refund webhook processing (refund.processed events)

affects: [04-admin-dashboard, future-appointment-management, future-automated-retry-job]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - TDD approach for business logic (RED-GREEN-REFACTOR)
    - Exponential backoff retry for transient failures (60s * 2^retry_count)
    - Max retry limit prevents infinite loops (5 attempts)
    - Refund webhook idempotency using razorpay:refund:{refund_id}
    - Time-based cancellation eligibility (>1 hour before appointment)

key-files:
  created:
    - db/003_refund_schema.sql
    - src/docbot/refund_service.py
    - src/docbot/cancellation_service.py
    - tests/test_refund_service.py
    - tests/test_cancellation_service.py
  modified:
    - src/docbot/bot_handler.py
    - src/docbot/i18n.py
    - src/docbot/webhook.py

key-decisions:
  - "Refund retry uses exponential backoff (60, 120, 240, 480, 960 seconds) to handle transient API failures"
  - "Max 5 retry attempts after which refund marked FAILED and alerted"
  - "Cancellation allowed only >1 hour before appointment to prevent abuse"
  - "Online cancellations trigger automatic refund; offline cancellations have no refund"
  - "Calendar event deletion is part of cancellation flow (cleanup)"
  - "Refund webhook processes refund.processed events for async confirmation"

patterns-established:
  - "TDD cycle: failing tests → implementation → passing tests → commit"
  - "Cancellation flow: check eligibility → transition state → initiate refund → delete calendar event"
  - "Refund flow: API call → success: mark PROCESSED + transition to REFUNDED | failure: mark PENDING + schedule retry"
  - "Retry mechanism: fetch PENDING refunds where next_retry_at <= now → retry with backoff"

# Metrics
duration: 7 min
completed: 2026-02-06
---

# Phase 03 Plan 04: Cancellation & Refunds Summary

**Patient cancellation flow with automatic refunds using Razorpay API and exponential backoff retry for reliability**

## Performance

- **Duration:** 7 min
- **Started:** 2026-02-06T15:19:05Z
- **Completed:** 2026-02-06T15:26:23Z
- **Tasks:** 2 (both TDD)
- **Files created:** 5 (schema + 2 services + 2 test files)
- **Files modified:** 3 (bot handler, i18n, webhook)
- **Tests added:** 10 (5 refund + 5 cancellation)
- **Total test suite:** 127 passing, 1 pre-existing failure (unrelated)

## Accomplishments

- Refund service initiates Razorpay refunds via POST /payments/{payment_id}/refund API
- Failed refunds automatically retry with exponential backoff (1, 2, 4, 8, 16 minutes)
- Max 5 retry attempts before marking refund as FAILED and alerting
- Cancellation service validates >1 hour eligibility before allowing cancellation
- Online cancellations trigger automatic refund processing
- Offline cancellations skip refund (no payment to refund)
- Calendar events deleted on successful cancellation
- Refund webhooks process refund.processed events and transition appointment to REFUNDED
- Bot handler updated with cancel menu showing cancellable appointments
- i18n messages added for all cancellation scenarios (en/te/hi)
- All business logic implemented via TDD (RED-GREEN-REFACTOR cycle)

## Task Commits

Each task was committed atomically following TDD cycle:

1. **Task 1: Refund service with retry mechanism (TDD)** - `ab718b4` (feat)
   - RED phase: 5 failing tests for refund scenarios
   - GREEN phase: Refund schema (003_refund_schema.sql) with retry tracking
   - GREEN phase: Refund service with Razorpay API integration and exponential backoff
   - All 5 tests passing (initiate success, API failure creates pending, no payment, retry mechanism, webhook processing)

2. **Task 2: Cancellation service and bot handler integration** - `d08c5a1` (feat)
   - Cancellation service with eligibility checks and orchestration
   - Bot handler cancel menu flow (list appointments → confirm → process)
   - i18n messages for cancellation scenarios
   - Webhook.py updated to route refund events to process_refund_webhook
   - All 5 tests passing (can cancel future, cannot cancel imminent, cannot cancel already cancelled, online with refund, offline no refund)

## Files Created/Modified

**Created:**
- `db/003_refund_schema.sql` - Refund table with retry_count, next_retry_at, status tracking
- `src/docbot/refund_service.py` - Razorpay refund API client with exponential backoff retry
- `src/docbot/cancellation_service.py` - Cancellation orchestration with eligibility checks
- `tests/test_refund_service.py` - TDD tests for refund scenarios (5 tests)
- `tests/test_cancellation_service.py` - TDD tests for cancellation scenarios (5 tests)

**Modified:**
- `src/docbot/bot_handler.py` - Added cancel menu handler and cancellation confirmation flow
- `src/docbot/i18n.py` - Added 8 cancellation messages (no appointments, none cancellable, select, with refund, refund pending, confirmed, too late, failed)
- `src/docbot/webhook.py` - Added refund webhook routing (refund.processed events)

## Decisions Made

1. **Exponential backoff for refund retry** - Rationale: Transient API failures (network, rate limits) resolve over time; exponential backoff prevents overwhelming Razorpay API
   - Base: 60 seconds (1 min, 2 min, 4 min, 8 min, 16 min)
   - Max retries: 5 (prevents infinite loops)
   - After max retries: mark FAILED and log alert for manual intervention

2. **>1 hour cancellation window** - Rationale: Prevents last-minute cancellations that waste doctor time; aligns with typical clinic policies
   - Checked in IST timezone for user-facing correctness
   - User-friendly error message suggests contacting clinic for exceptions

3. **Automatic refund for online, none for offline** - Rationale: Online consultations require payment; offline consultations are pay-at-clinic with no advance payment

4. **Calendar cleanup on cancellation** - Rationale: Cancelled appointments shouldn't show on doctor's calendar; cleanup prevents schedule clutter

5. **Refund webhook idempotency** - Rationale: Razorpay may send duplicate webhooks; idempotency prevents double-processing
   - Event ID format: `razorpay:refund:{refund_id}`
   - Consistent with payment webhook pattern

6. **TDD approach for cancellation/refund logic** - Rationale: Business logic correctness critical for financial transactions; TDD ensures edge cases covered
   - RED: Write failing tests first (5 for refund, 5 for cancellation)
   - GREEN: Implement to pass tests
   - REFACTOR: (None needed - implementation clean on first pass)

## Deviations from Plan

None - plan executed exactly as written. All TDD tests implemented and passing, all services integrated.

## Issues Encountered

**Minor:** Initial test failures due to missing `pytest_asyncio` decorator and deprecated `datetime.utcnow()`. Fixed by:
- Adding `@pytest_asyncio.fixture` decorator to async fixtures
- Replacing `datetime.utcnow()` with `datetime.now(timezone.utc)`

**Impact:** None - fixed in RED phase before GREEN implementation

## User Setup Required

**No additional setup required.** Existing Razorpay configuration from Plan 03-01 includes refund API access.

**Retry mechanism note:** `retry_failed_refunds()` function should be called periodically (e.g., every minute) by a background job or scheduler. Implementation options:
- Add to FastAPI lifespan background task
- Run via cron job calling admin CLI
- Add to future Phase 5 background workers

See `03-USER-SETUP.md` for existing Razorpay configuration verification.

## Next Phase Readiness

**Phase 3 (Payments & Calendar Integration) Complete:**
- Payment link creation (03-01) ✓
- Google Calendar integration with Meet links (03-02) ✓
- Payment webhook → calendar → WhatsApp notification (03-03) ✓
- Cancellation with automatic refunds and retry (03-04) ✓

**All must-have booking flows operational:**
- New booking (online with payment, offline at clinic)
- Payment processing with automatic calendar creation
- Patient-initiated cancellation with refund
- Calendar cleanup on cancellation

**Ready for Phase 4 (Admin Dashboard):**
- All appointment data available for display
- Payment status tracked (PENDING_PAYMENT, CONFIRMED, CANCELLED, REFUNDED)
- Refund tracking for revenue reports
- Calendar events linked for scheduling view
- No blockers

**Future enhancements (Phase 5 candidates):**
- Automated retry job for failed refunds (call retry_failed_refunds() periodically)
- Doctor-initiated cancellations with custom refund policies
- Cancellation analytics (reasons, patterns)
- Automated refund status notifications to patients

---
*Phase: 03-payments-calendar-integration*
*Completed: 2026-02-06*
