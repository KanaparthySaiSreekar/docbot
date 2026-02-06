---
phase: 03-payments-calendar-integration
plan: 01
subsystem: payments
tags: [razorpay, payment-gateway, webhooks, tdd, idempotency]

# Dependency graph
requires:
  - phase: 01-foundation
    provides: Configuration system (RazorpayConfig), idempotency framework, state machine
  - phase: 02-whatsapp-bot-booking-flow
    provides: Appointment booking with PENDING_PAYMENT status for online consultations

provides:
  - Razorpay API client with payment link creation and webhook verification
  - Payment service for online consultation fee collection (₹500)
  - Idempotent webhook processing preventing duplicate confirmations
  - Payment tracking table for reconciliation

affects: [03-02-calendar-sync, 04-admin-dashboard, future-refund-handling]

# Tech tracking
tech-stack:
  added: [httpx (already present), razorpay-api-integration]
  patterns:
    - TDD with RED-GREEN-REFACTOR cycle for payment critical code
    - HMAC-SHA256 webhook signature verification
    - Idempotent event processing with globally unique event IDs

key-files:
  created:
    - db/002_payment_schema.sql
    - src/docbot/razorpay_client.py
    - src/docbot/payment_service.py
    - tests/test_razorpay_client.py
    - tests/test_payment_service.py
  modified: []

key-decisions:
  - "TDD approach for payment integration ensures correctness before production"
  - "Payment link expiry handled via slot soft-lock (not Razorpay expire_by) for consistent UX"
  - "Phone numbers cleaned (+91 prefix removed) before sending to Razorpay for compatibility"
  - "Webhook idempotency uses razorpay:{payment_id}:{event_type} as globally unique event_id"
  - "Payment confirmation transitions appointment PENDING_PAYMENT → CONFIRMED atomically"

patterns-established:
  - "Alert logging for payment failures with structured details"
  - "Network error handling returns None and logs alert (non-blocking)"
  - "Async fixtures with pytest_asyncio for database tests"

# Metrics
duration: 10 min
completed: 2026-02-06
---

# Phase 3 Plan 1: Razorpay Payment Integration Summary

**TDD-developed Razorpay client and payment service with ₹500 fixed fee, HMAC-SHA256 webhook verification, and idempotent payment confirmation**

## Performance

- **Duration:** 10 min
- **Started:** 2026-02-06T14:45:56Z
- **Completed:** 2026-02-06T14:56:16Z
- **Tasks:** 2 (TDD tasks with RED-GREEN phases)
- **Files modified:** 5 created
- **Tests added:** 13 (6 client + 7 service)
- **Total test suite:** 105 passing

## Accomplishments

- Razorpay API client creates payment links with customer details, receipt tracking, and callback URLs
- Webhook signature verification using HMAC-SHA256 prevents tampered payloads
- Payment service creates ₹50000 (₹500) payment links for PENDING_PAYMENT appointments
- Idempotent webhook processing prevents duplicate payment confirmations via event_id deduplication
- Payment confirmation atomically transitions appointments to CONFIRMED with razorpay_payment_id stored
- Network errors handled gracefully (returns None, logs alerts, doesn't crash)
- Full test coverage with mocked HTTP calls (no real API dependency in tests)

## Task Commits

Each task followed TDD RED-GREEN cycle:

1. **Task 1: Payment schema and Razorpay client with TDD** - `93e3850` (test)
   - RED: Created 6 failing tests for payment link creation and webhook verification
   - GREEN: Implemented `razorpay_client.py` with HMAC-SHA256 signature validation
   - Created `002_payment_schema.sql` for payment tracking
   - All tests passing

2. **Task 2: Payment service with idempotent webhook handling** - `9968b2e` (feat)
   - RED: Created 7 failing tests for payment creation and webhook processing
   - GREEN: Implemented `payment_service.py` with idempotency checks
   - Full suite: 105 tests passing

**Plan metadata:** (to be committed separately)

## Files Created/Modified

- `db/002_payment_schema.sql` - Payment tracking table with appointment link, amount, status
- `src/docbot/razorpay_client.py` - Razorpay API client (create_payment_link, verify_webhook_signature)
- `src/docbot/payment_service.py` - Payment business logic (create_payment_for_appointment, process_payment_webhook)
- `tests/test_razorpay_client.py` - 6 tests covering API client functionality
- `tests/test_payment_service.py` - 7 tests covering service logic and webhooks
- `.planning/phases/03-payments-calendar-integration/03-USER-SETUP.md` - Razorpay account setup guide

## Decisions Made

1. **TDD for payment integration** - Rationale: Payment bugs cause customer trust issues and financial disputes; TDD ensures correctness upfront

2. **Phone number cleaning (+91 removal)** - Rationale: Razorpay expects numeric phone without country code prefix; defensive cleaning prevents API errors

3. **Payment link expiry via soft-lock, not Razorpay** - Rationale: Consistent expiry behavior across booking flow; slot lock already implements 15-minute timeout

4. **Event ID format: `razorpay:{payment_id}:{event_type}`** - Rationale: Globally unique across all webhook sources; prevents cross-event collisions

5. **Standard logging not structlog** - Rationale: Project uses standard Python logging; consistency over feature richness

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Fixed logging import mismatch**
- **Found during:** Task 1 GREEN phase (test execution)
- **Issue:** Plan specified `import structlog` but project uses standard `logging` module
- **Fix:** Changed to `import logging` and `logger = logging.getLogger(__name__)`
- **Files modified:** src/docbot/razorpay_client.py
- **Verification:** Tests import successfully, no ModuleNotFoundError
- **Committed in:** 93e3850 (Task 1 commit)

**2. [Rule 3 - Blocking] Fixed logger.error() keyword arguments**
- **Found during:** Task 1 GREEN phase (test failure)
- **Issue:** Standard logging doesn't support keyword args like `logger.error("msg", key=value)`; only structlog does
- **Fix:** Changed to f-string formatting: `logger.error(f"Failed: {error} (receipt={receipt})")`
- **Files modified:** src/docbot/razorpay_client.py
- **Verification:** Network error test passes without TypeError
- **Committed in:** 93e3850 (Task 1 commit)

**3. [Rule 3 - Blocking] Fixed async mock configuration**
- **Found during:** Task 1 GREEN phase (test failures)
- **Issue:** AsyncMock for httpx response.json() was configured as async but httpx.Response.json() is synchronous
- **Fix:** Used regular Mock() for response object while keeping AsyncMock for client.post()
- **Files modified:** tests/test_razorpay_client.py
- **Verification:** All 6 client tests pass
- **Committed in:** 93e3850 (Task 1 commit)

**4. [Rule 3 - Blocking] Fixed pytest async fixture decorator**
- **Found during:** Task 2 RED phase (test collection)
- **Issue:** `@pytest.fixture` doesn't support async fixtures; pytest-asyncio requires `@pytest_asyncio.fixture`
- **Fix:** Changed `@pytest.fixture` to `@pytest_asyncio.fixture` and added import
- **Files modified:** tests/test_payment_service.py
- **Verification:** All 7 service tests execute and pass
- **Committed in:** 9968b2e (Task 2 commit)

---

**Total deviations:** 4 auto-fixed (all Rule 3 - Blocking)
**Impact on plan:** All fixes were necessary to unblock test execution. No scope creep - purely environment compatibility fixes.

## Issues Encountered

None - all deviations were blocking issues auto-fixed during TDD phases.

## User Setup Required

**External services require manual configuration.** See [03-USER-SETUP.md](./03-USER-SETUP.md) for:

- Razorpay account creation and KYC verification
- API key generation (test and live modes)
- Webhook endpoint configuration with event subscriptions
- Environment variable configuration in config.prod.json
- Verification commands and test card details

**Note:** Payment integration will not function until Razorpay account is configured and keys are added to config.

## Next Phase Readiness

**Ready for Plan 03-02 (Google Calendar Integration):**
- Payment flow complete; appointments transition to CONFIRMED after payment
- CONFIRMED appointments are ready for calendar event creation
- Payment tracking table provides audit trail for appointment-payment linkage

**No blockers** - Payment integration is self-contained. Calendar sync can proceed independently.

**Future enhancement opportunities:**
- Refund processing (webhook already monitors refund.processed event)
- Payment failure handling (send retry link via WhatsApp)
- Payment analytics dashboard

---
*Phase: 03-payments-calendar-integration*
*Completed: 2026-02-06*
