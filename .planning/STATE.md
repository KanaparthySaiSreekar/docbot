# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-04)

**Core value:** Fully automated appointment booking and management that eliminates manual coordination - patients can book, pay, cancel, and receive prescriptions entirely through WhatsApp while the doctor focuses solely on consultations through a clean web interface.
**Current focus:** Phase 2 - WhatsApp Bot & Booking Flow

## Current Position

Phase: 2 of 5 (WhatsApp Bot & Booking Flow)
Plan: 3 of 4 in current phase
Status: In progress
Last activity: 2026-02-06 — Completed 02-03-PLAN.md

Progress: [██████░░░░] 2 of 4 Phase 2 plans complete

## Performance Metrics

**Velocity:**
- Total plans completed: 7
- Average duration: 9 min
- Total execution time: 1.1 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01-foundation | 5/5 | 55 min | 11 min |
| 02-whatsapp-bot-booking-flow | 2/4 | 10 min | 5 min |

**Recent Trend:**
- Last 5 plans: 01-03 (13min), 01-04 (6min), 01-05 (7min), 02-01 (5min), 02-03 (5min)
- Trend: Exceptional velocity maintained (5 min average for Phase 2 plans)

*Updated after each plan completion*

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- **Foundation Phase**: SQLite chosen for single-doctor deployment simplicity
- **Foundation Phase**: UTC storage with IST display prevents timezone bugs
- **Foundation Phase**: Self-hosted deployment on Ubuntu homelab via Cloudflare tunnel
- **01-01**: Complete configuration schema defined upfront covering all 5 phases to prevent future schema changes
- **01-01**: Environment-based config files (config.test.json, config.prod.json) with .gitignore protection for secrets
- **01-01**: Request ID correlation via ContextVar for tracing related log entries
- **01-02**: TDD approach ensures state machine, timezone, and idempotency correctness before features depend on them
- **01-02**: Database-level slot locking via PRIMARY KEY constraint prevents race conditions
- **01-02**: Idempotency event_id is globally unique (not per-source) for complete deduplication
- **01-02**: tzdata dependency required for Windows timezone support (ZoneInfo)
- **01-03**: Session never expires (max_age=None) per AUTH-02 requirement
- **01-03**: Any Google account accepted (no allowlist) per AUTH-03 requirement
- **01-03**: Protected routes check session directly rather than using dependency injection for cleaner redirect handling
- **01-04**: Multi-stage Docker build separates dependency installation from runtime for smaller images
- **01-04**: docker-compose profiles enforce test/prod separation via DOCBOT_ENV variable
- **01-04**: Admin CLI requires --confirm flag for all write operations as safety mechanism
- **01-04**: Backup verification validates integrity (not just creation) with PRAGMA checks and row counts
- **01-04**: Alert stub uses structured JSON logging with categories for future notification integration
- **01-05**: Database initialization runs in lifespan startup with try/except for fail-fast behavior
- **01-05**: init_db() is safe to run on every startup (CREATE TABLE IF NOT EXISTS)
- **01-05**: Standardized on datetime.now(timezone.utc) throughout codebase to avoid deprecation warnings
- **02-01**: WhatsApp Cloud API v21.0 for messaging integration
- **02-01**: Exponential backoff retry (1s, 2s, 4s) for 5xx and network errors
- **02-01**: Failed sends return None and log alerts without raising exceptions
- **02-01**: Webhook always returns 200 to Meta to prevent retry storms
- **02-01**: Message deduplication via idempotency framework using message_id
- **02-03**: TDD approach for business logic ensures slot generation and booking correctness before bot integration
- **02-03**: Break period is half-open interval (break_start excluded, break_end included)
- **02-03**: Same-day filtering uses IST time comparison for user-facing correctness
- **02-03**: Expired locks automatically cleaned up before acquiring new locks (no separate cleanup job needed)
- **02-03**: Appointment creation releases soft-lock (transition from reservation to booking)
- **02-03**: Double-booking prevented at both application (ValueError) and database level (UNIQUE constraint)

### Pending Todos

None yet.

### Blockers/Concerns

**User Setup Required**: Plan 02-01 introduced WhatsApp Cloud API integration requiring manual Meta Business Suite configuration (see 02-USER-SETUP.md). Must be completed before WhatsApp integration will function in production.

## Session Continuity

Last session: 2026-02-06
Stopped at: Completed 02-03-PLAN.md (Slot Availability and Booking Service)
Resume file: None

**Phase 2 (WhatsApp Bot & Booking Flow) In Progress** - Slot and booking services complete, ready for bot flow (2/4 plans)
