---
phase: 03-payments-calendar-integration
plan: 03
subsystem: integration
tags: [razorpay, google-calendar, whatsapp, payment-webhook, calendar-events, booking-flow]

# Dependency graph
requires:
  - phase: 03-01
    provides: Razorpay payment service (create_payment_for_appointment, process_payment_webhook)
  - phase: 03-02
    provides: Google Calendar service (create_appointment_event)
  - phase: 02-04
    provides: Bot conversation handler with booking confirmation flow

provides:
  - Razorpay webhook endpoint processing payment.captured events
  - Calendar event creation after payment confirmation
  - WhatsApp notifications with Meet link after payment
  - Bot handler integration for online payment links and offline calendar events
  - Complete end-to-end booking flow (online and offline)

affects: [03-04-cancellation-refund, 04-admin-dashboard, future-appointment-management]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Webhook always returns 200 to prevent retry storms (Razorpay)
    - Non-blocking calendar creation (logs alert on failure, doesn't block payment)
    - i18n message template variables passed as kwargs to get_message()

key-files:
  created: []
  modified:
    - src/docbot/webhook.py
    - src/docbot/bot_handler.py
    - src/docbot/i18n.py
    - tests/test_webhook.py
    - tests/test_bot_handler.py

key-decisions:
  - "Webhook always returns 200 to prevent Razorpay retry storms"
  - "Calendar creation is non-blocking - logs alert on failure without blocking payment confirmation"
  - "Online bookings send payment link immediately, calendar created after payment"
  - "Offline bookings create calendar event immediately with clinic address"

patterns-established:
  - "Payment webhook → process_payment_webhook → create_appointment_event → send WhatsApp notification"
  - "Online flow: booking → payment link → webhook → calendar → Meet link"
  - "Offline flow: booking → calendar event → clinic address"

# Metrics
duration: 8 min
completed: 2026-02-06
---

# Phase 03 Plan 03: Payment & Calendar Integration Summary

**Razorpay webhook processes payments, creates calendar events with Meet links, and sends WhatsApp confirmations for complete online/offline booking flows**

## Performance

- **Duration:** 8 min
- **Started:** 2026-02-06T15:05:30Z
- **Completed:** 2026-02-06T15:13:51Z
- **Tasks:** 2
- **Files modified:** 5
- **Tests added:** 4 (2 webhook + 2 bot handler)
- **Total test suite:** 114 passing

## Accomplishments

- Razorpay webhook endpoint validates signatures and processes payment.captured events
- Payment confirmation triggers calendar event creation with automatic Meet link generation
- WhatsApp notifications sent to patients with Meet link (or pending message if calendar fails)
- Bot handler updated for online bookings (payment link flow) and offline bookings (calendar + clinic address)
- Complete end-to-end booking flow operational for both consultation types
- All flows tested with mocked external services (Razorpay, Google Calendar, WhatsApp)

## Task Commits

Each task was committed atomically:

1. **Task 1: Razorpay webhook endpoint** - `cea60c9` (feat)
   - POST /webhook/razorpay endpoint with signature verification
   - Calendar event creation after payment.captured
   - WhatsApp notification with Meet link or pending message
   - Tests for payment processing and invalid signatures

2. **Task 2: Update bot handler with payment and calendar flow** - `ab66b6f` (feat)
   - Online bookings create payment link via create_payment_for_appointment
   - Offline bookings create calendar event immediately
   - i18n messages for payment required, payment error, offline confirmation
   - Tests for online and offline booking flows
   - Updated existing tests to mock calendar service

## Files Created/Modified

- `src/docbot/webhook.py` - Added Razorpay webhook endpoint with payment processing and calendar integration
- `src/docbot/bot_handler.py` - Updated booking confirmation to call payment/calendar services based on consultation type
- `src/docbot/i18n.py` - Added payment and offline confirmation messages in English, Telugu, and Hindi
- `tests/test_webhook.py` - Added Razorpay webhook tests (payment captured, invalid signature)
- `tests/test_bot_handler.py` - Added online/offline booking flow tests, updated existing tests

## Decisions Made

1. **Webhook always returns 200** - Rationale: Prevents Razorpay retry storms on internal errors; errors logged for monitoring

2. **Calendar creation is non-blocking** - Rationale: Failed calendar shouldn't block payment confirmation; logs alert for retry mechanism

3. **i18n template variables via kwargs** - Rationale: Consistent with existing i18n.get_message() API; cleaner than .format() chaining

4. **Offline bookings create calendar immediately** - Rationale: No payment required, so calendar event can be created and address sent right away

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - all planned work completed successfully with no blockers.

## User Setup Required

**External services already configured in prior plans.** Users should have completed:
- Razorpay webhook configuration (Plan 03-01)
- Google Calendar OAuth and credentials (Plan 03-02)
- WhatsApp Cloud API configuration (Plan 02-01)

See `03-USER-SETUP.md` for verification commands.

## Next Phase Readiness

**Complete online and offline booking flows operational:**
- Online: Patient books → receives payment link → pays → appointment confirmed → calendar event created → Meet link sent
- Offline: Patient books → appointment confirmed → calendar event created → clinic address sent
- Both flows tested end-to-end with mocked external services

**Ready for Plan 03-04 (Cancellation & Refund):**
- Appointment cancellation can now trigger calendar event deletion (cancel_appointment_event already exists)
- Refund processing can build on process_payment_webhook pattern
- No blockers

**Admin Dashboard (Phase 4) Ready:**
- All appointment data available for display
- Payment status tracked for revenue reporting
- Calendar events linked for scheduling view

---
*Phase: 03-payments-calendar-integration*
*Completed: 2026-02-06*
