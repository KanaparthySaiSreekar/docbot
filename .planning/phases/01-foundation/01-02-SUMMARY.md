---
phase: 01-foundation
plan: 02
subsystem: database
tags: [sqlite, aiosqlite, pytest, tdd, state-machine, timezone, idempotency]

# Dependency graph
requires:
  - phase: 01-01
    provides: "FastAPI scaffold with config system and structured logging"
provides:
  - "SQLite schema with appointments, slot_locks, idempotency_keys, prescriptions tables"
  - "State machine for appointment transitions (PENDING_PAYMENT → CONFIRMED → CANCELLED → REFUNDED)"
  - "Timezone utilities for UTC/IST conversions"
  - "Idempotency framework for webhook deduplication"
  - "Database connection management with WAL mode"
  - "Test-driven implementation with 16 passing tests"
affects: [01-03, 01-04, 02-whatsapp, 03-payments, 04-dashboard, all-future-phases]

# Tech tracking
tech-stack:
  added: [tzdata]
  patterns: ["TDD with RED-GREEN-REFACTOR cycle", "State machine with explicit transitions", "UTC storage with IST display", "Database-level locking via PRIMARY KEY constraints", "Idempotency via event IDs", "pytest-asyncio for async test fixtures"]

key-files:
  created:
    - db/001_initial_schema.sql
    - src/docbot/database.py
    - src/docbot/models.py
    - src/docbot/state_machine.py
    - src/docbot/timezone_utils.py
    - src/docbot/idempotency.py
    - tests/conftest.py
    - tests/test_state_machine.py
    - tests/test_timezone_utils.py
    - tests/test_idempotency.py
  modified:
    - src/docbot/main.py
    - pyproject.toml

key-decisions:
  - "TDD approach ensures state machine, timezone, and idempotency correctness before any feature depends on them"
  - "Database-level slot locking via PRIMARY KEY constraint (appointment_date, slot_time) prevents race conditions"
  - "Idempotency event_id is globally unique (not per-source) for complete deduplication"
  - "pytest_asyncio.fixture required for async test fixtures"
  - "tzdata dependency added for Windows timezone support (ZoneInfo requires it)"
  - "Windows-compatible date formatting (no %-I, strip leading zero manually)"

patterns-established:
  - "TDD: Write failing test (RED) → Implement (GREEN) → Refactor if needed"
  - "State machine: Explicit VALID_TRANSITIONS dict, can_transition() for checks, transition() for validation"
  - "Timezone: Always store UTC, convert to IST for display using to_ist()/to_utc()"
  - "Idempotency: check_idempotency() before processing, record_event() after success"
  - "Test fixtures: In-memory SQLite database with schema loaded for each test"
  - "Async test fixtures: Use pytest_asyncio.fixture decorator"

# Metrics
duration: 17min
completed: 2026-02-04
---

# Phase 01 Plan 02: Database & Data Integrity Summary

**SQLite schema with state machine, UTC/IST timezone conversions, and idempotency framework—all test-driven with 16 passing tests**

## Performance

- **Duration:** 17 min
- **Started:** 2026-02-04T18:38:23Z
- **Completed:** 2026-02-04T18:54:54Z
- **Tasks:** 2/2
- **Files modified:** 12 created, 2 modified

## Accomplishments

- SQLite schema with 4 tables (appointments, slot_locks, idempotency_keys, prescriptions) and 7 indexes
- State machine enforces valid appointment transitions (PENDING_PAYMENT → CONFIRMED → CANCELLED → REFUNDED)
- Timezone utilities convert between UTC storage and IST display, handle IST day boundaries
- Idempotency framework prevents duplicate webhook processing
- Database initialization integrated into app lifespan
- 16 tests pass covering all data integrity logic
- Test fixtures provide in-memory database for isolated testing

## Task Commits

Task 1 was committed as a single unit, Task 2 followed TDD with multiple commits:

**Task 1: Database schema and connection management** - `3180ebf` (feat)
- SQLite schema with all tables and indexes
- Database initialization in app lifespan
- Database check added to /ready endpoint
- Test fixtures for in-memory database

**Task 2: TDD - State machine, timezone, idempotency:**

State machine (RED → GREEN):
1. `5f6564a` (test) - Failing tests for state transitions
2. `ea78a19` (feat) - State machine implementation

Timezone utilities (RED → GREEN):
3. `c117511` (test) - Failing tests for UTC/IST conversions
4. `a538ee0` (feat) - Timezone utilities implementation

Idempotency (RED → GREEN):
5. `b58cfb0` (test) - Failing tests for event deduplication
6. `5873de4` (feat) - Idempotency implementation

Fixes:
7. `237d8d4` (fix) - Added tzdata dependency for Windows
8. `d508af7` (fix) - Restored database check in /ready endpoint

## Files Created/Modified

**Created:**
- `db/001_initial_schema.sql` - Complete SQLite schema with appointments, slot_locks, idempotency_keys, prescriptions tables and 7 indexes
- `src/docbot/database.py` - Database connection with WAL mode, init_db() for schema execution
- `src/docbot/models.py` - Pydantic DTOs for Appointment, SlotLock, IdempotencyKey, Prescription
- `src/docbot/state_machine.py` - AppointmentStatus enum, VALID_TRANSITIONS dict, can_transition(), transition()
- `src/docbot/timezone_utils.py` - IST constant, utc_now(), ist_now(), to_ist(), to_utc(), format_ist(), is_same_day_ist(), slot_to_utc()
- `src/docbot/idempotency.py` - check_idempotency(), record_event() for webhook deduplication
- `tests/conftest.py` - pytest_asyncio fixtures for test_db and test_client
- `tests/test_state_machine.py` - 5 tests for state transitions
- `tests/test_timezone_utils.py` - 7 tests for timezone conversions
- `tests/test_idempotency.py` - 4 tests for event deduplication

**Modified:**
- `src/docbot/main.py` - Added init_db() in lifespan, database check in /ready endpoint
- `pyproject.toml` - Added tzdata dependency

## Decisions Made

**1. TDD approach for critical data logic**
- Rationale: State machine, timezone, and idempotency are foundational—errors here affect all features. TDD ensures correctness before any code depends on them.
- Outcome: 16 tests pass, all data integrity logic verified

**2. Database-level slot locking**
- Rationale: SQLite doesn't support row-level locks well. Using PRIMARY KEY (appointment_date, slot_time) on slot_locks table enforces uniqueness at database level.
- Outcome: Race-free slot booking without application-level lock management

**3. Global idempotency event_id**
- Rationale: Event IDs should be globally unique, not per-source. Same event_id from any source should be duplicate.
- Outcome: Simpler deduplication logic, no false positives

**4. Windows timezone support**
- Rationale: Development on Windows requires tzdata package for ZoneInfo to access timezone database.
- Outcome: Added tzdata dependency, all timezone tests pass

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Added tzdata dependency for Windows**
- **Found during:** Task 2 (Timezone utilities tests)
- **Issue:** ZoneInfo("Asia/Kolkata") failed with "No time zone found" on Windows—requires tzdata package
- **Fix:** Ran `uv pip install tzdata`, added to pyproject.toml dependencies
- **Files modified:** pyproject.toml
- **Verification:** All timezone tests pass
- **Committed in:** `237d8d4` (fix)

**2. [Rule 1 - Bug] Fixed strftime format for Windows**
- **Found during:** Task 2 (test_format_ist_display failing)
- **Issue:** `%-I` format (hour without leading zero) not supported on Windows, ValueError raised
- **Fix:** Changed to `%I` with manual leading zero strip for cleaner display
- **Files modified:** src/docbot/timezone_utils.py
- **Verification:** test_format_ist_display passes
- **Committed in:** `a538ee0` (feat - included in GREEN phase)

**3. [Rule 1 - Bug] Fixed pytest_asyncio fixture decorator**
- **Found during:** Task 2 (Idempotency tests failing with fixture error)
- **Issue:** Async fixture test_db used @pytest.fixture instead of @pytest_asyncio.fixture, causing "async fixture with no plugin" error
- **Fix:** Changed to @pytest_asyncio.fixture decorator, added pytest_asyncio import
- **Files modified:** tests/conftest.py
- **Verification:** All idempotency tests pass
- **Committed in:** `b58cfb0` (test - included in RED phase)

---

**Total deviations:** 3 auto-fixed (1 blocking, 2 bugs)
**Impact on plan:** All auto-fixes necessary for Windows compatibility and test execution. No scope creep.

## Issues Encountered

None. All tasks executed smoothly after addressing Windows-specific compatibility issues.

## User Setup Required

None - no external service configuration required.

Users should ensure:
1. Database file will be created automatically on first run (`docbot.db` in project root)
2. All tests pass: `uv run pytest tests/ -v`

## Next Phase Readiness

**Ready for Plan 03 (Google OAuth & Dashboard):**
- ✓ Database schema complete with all tables
- ✓ State machine ready for appointment status transitions
- ✓ Timezone utilities ready for IST display
- ✓ Idempotency framework ready for webhook processing
- ✓ Test fixtures ready for future test suites
- ✓ 16 tests passing confirm data integrity logic correctness

**Blockers:** None

**Foundation strength:**
- All success criteria met
- All verification checks pass
- TDD approach ensures correctness before features depend on this logic
- Database-level constraints prevent race conditions
- Atomic commits enable easy rollback if needed

---
*Phase: 01-foundation*
*Completed: 2026-02-04*
