# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-04)

**Core value:** Fully automated appointment booking and management that eliminates manual coordination - patients can book, pay, cancel, and receive prescriptions entirely through WhatsApp while the doctor focuses solely on consultations through a clean web interface.
**Current focus:** Phase 3 - Payments & Calendar Integration

## Current Position

Phase: 3 of 5 (Payments & Calendar Integration)
Plan: 3 of 3 in current phase
Status: Phase complete
Last activity: 2026-02-06 — Completed 03-03-PLAN.md (Payment & Calendar Integration wiring)

Progress: [████████████] 100% of Phase 3 (Payments & Calendar Integration) ✓

## Performance Metrics

**Velocity:**
- Total plans completed: 12
- Average duration: 8 min
- Total execution time: 1.8 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01-foundation | 5/5 | 55 min | 11 min |
| 02-whatsapp-bot-booking-flow | 4/4 | 27 min | 7 min |
| 03-payments-calendar-integration | 3/3 | 31 min | 10 min |

**Recent Trend:**
- Last 5 plans: 02-03 (5min), 02-04 (7min), 03-01 (10min), 03-02 (13min), 03-03 (8min)
- Trend: Consistent velocity, integration plans average 10 min

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
- **02-02**: Auto-discovery of schema files - database.py loads all .sql files in sorted order for automatic migration management
- **02-02**: Conversation data stored as JSON blob for flexibility in tracking booking flow progress
- **02-02**: 30-minute rolling expiry for conversations to prevent stale bookings
- **02-02**: One active conversation per phone enforced at database level (PRIMARY KEY on phone)
- **02-02**: Message catalog structure supports template substitution via .format()
- **02-03**: TDD approach for business logic ensures slot generation and booking correctness before bot integration
- **02-03**: Break period is half-open interval (break_start excluded, break_end included)
- **02-03**: Same-day filtering uses IST time comparison for user-facing correctness
- **02-03**: Expired locks automatically cleaned up before acquiring new locks (no separate cleanup job needed)
- **02-03**: Appointment creation releases soft-lock (transition from reservation to booking)
- **02-03**: Double-booking prevented at both application (ValueError) and database level (UNIQUE constraint)
- **02-04**: Bot handler uses state-based routing with dedicated handler functions per conversation state
- **02-04**: Integration tests mock WhatsApp client but use real test database for state assertions
- **02-04**: Gender values stored in English, converted to lowercase for i18n lookup (gender_male, gender_female, gender_other)
- **02-04**: Contact clinic and cancel appointment menu items are placeholders for Phase 3+ (show "Coming soon")
- **03-01**: TDD approach for payment integration ensures correctness before production
- **03-01**: Payment link expiry handled via slot soft-lock (not Razorpay expire_by) for consistent UX
- **03-01**: Phone numbers cleaned (+91 prefix removed) before sending to Razorpay for compatibility
- **03-01**: Webhook idempotency uses razorpay:{payment_id}:{event_type} as globally unique event_id
- **03-01**: Payment confirmation transitions appointment PENDING_PAYMENT → CONFIRMED atomically
- **03-02**: OAuth2 credentials stored in token.json in project root with automatic refresh
- **03-02**: Meet link generation only for online consultations via conferenceData
- **03-02**: Event deletion returns success if event already deleted (404 = success)
- **03-02**: Calendar service is idempotent - skips creation if event already exists
- **03-03**: Webhook always returns 200 to prevent Razorpay retry storms
- **03-03**: Calendar creation is non-blocking - logs alert on failure without blocking payment confirmation
- **03-03**: Online bookings send payment link immediately, calendar created after payment
- **03-03**: Offline bookings create calendar event immediately with clinic address

### Pending Todos

None yet.

### Blockers/Concerns

**User Setup Required (WhatsApp)**: Plan 02-01 introduced WhatsApp Cloud API integration requiring manual Meta Business Suite configuration (see 02-USER-SETUP.md). Must be completed before WhatsApp integration will function in production.

**User Setup Required (Razorpay)**: Plan 03-01 introduced Razorpay payment integration requiring account creation, KYC verification, API key generation, and webhook configuration (see 03-USER-SETUP.md). Must be completed before online consultation payments will function.

**User Setup Required (Google Calendar)**: Plan 03-02 introduced Google Calendar integration requiring OAuth 2.0 credentials, calendar ID configuration, and initial browser authentication flow (see 03-USER-SETUP.md). Must be completed before calendar events and Meet links will function.

**Human Verification Recommended**: Phase 2 verification identified 6 scenarios requiring testing with actual WhatsApp account (see 02-VERIFICATION.md). All code verified to exist and be properly wired; manual testing recommended before production launch.

**Ready for Phase 4**: Phase 3 complete with full end-to-end booking flows. Online flow: patient books → payment link → webhook → calendar event → Meet link. Offline flow: patient books → calendar event → clinic address. Admin dashboard next for doctor-side management.

## Session Continuity

Last session: 2026-02-06
Stopped at: Completed 03-03-PLAN.md (Payment & Calendar Integration wiring)
Resume file: None

**Phase 3 (Payments & Calendar Integration) Complete ✓** - All 3 plans executed: Razorpay payment service (03-01), Google Calendar integration (03-02), and end-to-end booking flows (03-03)
