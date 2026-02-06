---
phase: 02-whatsapp-bot-booking-flow
plan: 03
subsystem: business-logic
tags: [tdd, slots, booking, locking, availability, scheduling]

# Dependency graph
requires:
  - phase: 01-foundation
    provides: Database schema, timezone utils, state machine, config system
provides:
  - Slot generation from schedule config with break exclusion
  - Available slot filtering (excludes booked and locked slots)
  - Soft-lock mechanism with 10-min TTL
  - Appointment creation with correct initial status
  - Double-booking prevention
affects: [02-04-whatsapp-booking-flow, 03-payment-integration]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - TDD with RED-GREEN-REFACTOR cycle
    - Pure functions for slot generation (testable without DB)
    - Database-level locking via PRIMARY KEY constraint
    - Automatic expired lock cleanup before new locks

key-files:
  created:
    - src/docbot/slot_service.py
    - src/docbot/booking_service.py
    - tests/test_slot_service.py
    - tests/test_booking_service.py
  modified: []

key-decisions:
  - "TDD approach ensures slot generation and booking logic correctness before bot integration"
  - "Slot at break_start excluded, slot at break_end included (break period is half-open interval)"
  - "Same-day filtering uses IST time comparison (not UTC) for user-facing correctness"
  - "Expired locks automatically cleaned up before acquiring new locks (no separate cleanup job needed)"
  - "create_appointment releases soft-lock (transition from reservation to booking)"

patterns-established:
  - "generate_slots is pure function (no DB access) for easy testing and reuse"
  - "get_available_slots uses schedule config parameter (injectable for testing)"
  - "Double-booking prevented at both application (ValueError) and database level (UNIQUE constraint on date+slot)"

# Metrics
duration: 5 min
completed: 2026-02-06
---

# Phase 02 Plan 03: Slot Availability and Booking Service Summary

**Slot generation and booking service built with TDD - pure business logic tested before bot integration**

## Performance

- **Duration:** 5 min
- **Started:** 2026-02-06T10:12:21Z
- **Completed:** 2026-02-06T10:17:11Z
- **Tasks:** 2 (TDD)
- **Files created:** 4
- **Tests:** 17 (all passing)

## Accomplishments

- Slot generation from schedule config with break period exclusion
- Available slot filtering excludes booked appointments and soft-locked slots
- Same-day booking automatically filters past IST slots
- Soft-lock mechanism with 10-min TTL prevents race conditions
- Appointment creation with correct initial status (CONFIRMED for offline, PENDING_PAYMENT for online)
- Double-booking prevention at application and database level
- Expired lock automatic cleanup on lock acquisition

## Task Commits

Each TDD task followed RED-GREEN-REFACTOR cycle:

### Task 1: Slot Availability Service

1. **RED:** `621b08b` - test(02-03): add failing tests for slot availability service
2. **GREEN:** `ab66eab` - feat(02-03): implement slot availability service

### Task 2: Booking Service

3. **RED:** `48f39f7` - test(02-03): add failing tests for booking service
4. **GREEN:** `2e05c03` - feat(02-03): implement booking service

**Total:** 4 commits (2 RED, 2 GREEN, 0 REFACTOR - code was clean from start)

## Files Created/Modified

**Created:**
- `src/docbot/slot_service.py` - Slot generation and availability checking (pure functions + DB queries)
- `src/docbot/booking_service.py` - Slot locking and appointment creation (stateful operations)
- `tests/test_slot_service.py` - 8 tests for slot service
- `tests/test_booking_service.py` - 9 tests for booking service

## Decisions Made

1. **TDD approach for business logic** - Critical booking logic tested before bot integration. Ensures correctness and prevents race conditions.

2. **Break period is half-open interval** - Slot at break_start excluded, slot at break_end included. Example: break 13:00-14:00 excludes 13:00-13:45, includes 14:00+.

3. **Same-day filtering uses IST** - For today's date, compare slot times against current IST time (not UTC). User sees "9:00 AM" as past/future based on IST clock.

4. **Automatic expired lock cleanup** - lock_slot calls cleanup_expired_locks before acquiring. No separate cron job needed.

5. **Appointment creation releases lock** - Soft-lock transitions to real booking. Lock entry removed after appointment created.

6. **Double-booking prevention layers** - Application checks before insert (ValueError), database has UNIQUE constraint on (date, slot) as last resort.

## Deviations from Plan

None - plan executed exactly as written. TDD cycle followed strictly (RED → GREEN → REFACTOR).

## Issues Encountered

None. All tests passed on first GREEN implementation.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

**Ready for 02-04 (WhatsApp booking flow):**
- Slot service provides `get_available_dates` and `get_available_slots` for bot to present to users
- Booking service provides `lock_slot`, `create_appointment`, and `release_lock` for bot to manage booking flow
- All business logic tested and verified
- Double-booking prevention ensures data integrity

**Critical for bot flow:**
- Bot must call `lock_slot` when user selects a slot
- Bot has 10 minutes to complete booking before lock expires
- Bot must call `release_lock` if user cancels or times out
- Bot must call `create_appointment` to finalize booking (automatically releases lock)

**Testing complete:**
- Slot generation with break exclusion ✓
- Booked and locked slot filtering ✓
- Same-day past slot filtering ✓
- Max appointments per day enforcement ✓
- Soft-lock TTL and expiry ✓
- Appointment status determination ✓
- Double-booking prevention ✓

---
*Phase: 02-whatsapp-bot-booking-flow*
*Completed: 2026-02-06*
