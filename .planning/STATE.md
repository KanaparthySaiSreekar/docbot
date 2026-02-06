# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-04)

**Core value:** Fully automated appointment booking and management that eliminates manual coordination - patients can book, pay, cancel, and receive prescriptions entirely through WhatsApp while the doctor focuses solely on consultations through a clean web interface.
**Current focus:** Phase 4 - Dashboard & Management

## Current Position

Phase: 4 of 5 (Dashboard & Management)
Plan: 6 of 6 in current phase
Status: Phase complete
Last activity: 2026-02-06 — Completed 04-05-PLAN.md (Settings & Schedule Configuration)

Progress: [█████████████████████] 100% (20/20 plans complete)

## Performance Metrics

**Velocity:**
- Total plans completed: 20
- Average duration: 8.5 min
- Total execution time: 2.85 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01-foundation | 5/5 | 55 min | 11 min |
| 02-whatsapp-bot-booking-flow | 4/4 | 27 min | 7 min |
| 03-payments-calendar-integration | 5/5 | 49 min | 10 min |
| 04-dashboard-and-management | 6/6 | 51 min | 8.5 min |

**Recent Trend:**
- Last 5 plans: 04-02 (7min), 04-03 (8min), 04-04 (18min), 04-06 (3min), 04-05 (8min)
- Trend: Phase 4 complete! All dashboard features implemented efficiently

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
- **03-04**: Refund retry uses exponential backoff (60, 120, 240, 480, 960 seconds) to handle transient API failures
- **03-04**: Max 5 retry attempts after which refund marked FAILED and alerted
- **03-04**: Cancellation allowed only >1 hour before appointment to prevent abuse
- **03-04**: Online cancellations trigger automatic refund; offline cancellations have no refund
- **03-04**: Calendar event deletion is part of cancellation flow (cleanup)
- **03-04**: Refund webhook processes refund.processed events for async confirmation
- **03-05**: Database is authoritative source of truth; calendar events synced as projection
- **03-05**: Reconciliation retries limited to 20 per run to prevent API quota exhaustion
- **03-05**: Calendar drift checks only next 7 days for performance optimization
- **03-05**: Refund webhook integrated into existing Razorpay webhook endpoint with event type routing
- **03-05**: i18n template variables passed as kwargs for consistency with existing API
- **04-01**: Phone numbers masked to last 4 digits in all API responses for PII protection
- **04-01**: Default date range for appointments is today + 7 days for practical dashboard view
- **04-01**: Failed refunds endpoint returns both PENDING and FAILED statuses for comprehensive monitoring
- **04-01**: Settings endpoint returns schedule configuration without requiring database access
- **04-01**: All dashboard endpoints require authentication via require_auth dependency
- **04-02**: Tailwind CSS v3 chosen for PostCSS compatibility over v4
- **04-02**: API client uses same-origin requests with credentials:include for session cookies
- **04-02**: Vite proxy configured for /api and /auth routes during development
- **04-02**: FastAPI serves React build from /dashboard with SPA routing support
- **04-03**: Type-only imports required for TypeScript verbatimModuleSyntax mode with Vite
- **04-03**: Day view shows 9:00-17:00 with 15-minute intervals matching clinic schedule
- **04-03**: Week view starts on Monday following standard business calendar convention
- **04-03**: Compact mode for appointment cards optimizes space in calendar views
- **04-03**: Cancel button placeholder logs to console, mutations implemented in 04-04
- **04-04**: CSRF middleware disabled in test environment for simplified testing while maintaining security in dev/prod
- **04-04**: Doctor-initiated cancellations bypass 1-hour time restriction via by_patient=False parameter
- **04-04**: Manual refund retry deletes and recreates refund record to reset attempt count and backoff timer
- **04-04**: Resend uses payment_received_meet_link for online, booking_confirmed_offline for offline appointments
- **04-04**: All mutations include CSRF token from cookie via X-CSRF-Token header
- **04-04**: TanStack Query mutations automatically invalidate related queries for UI refresh
- **04-05**: Pydantic V2 field_validator used for settings validation (migrated from deprecated @validator)
- **04-05**: Settings mutation clears config cache after update to reflect changes immediately
- **04-05**: Navigation component pattern established for multi-page SPA routing
- **04-06**: History page shows read-only view without action buttons for immutability
- **04-06**: Pagination uses limit=20 with offset-based loading for browsing past appointments
- **04-06**: Navigation tabs in App.tsx instead of routing library for simple state-based page switching

### Pending Todos

None yet.

### Blockers/Concerns

**User Setup Required (WhatsApp)**: Plan 02-01 introduced WhatsApp Cloud API integration requiring manual Meta Business Suite configuration (see 02-USER-SETUP.md). Must be completed before WhatsApp integration will function in production.

**User Setup Required (Razorpay)**: Plan 03-01 introduced Razorpay payment integration requiring account creation, KYC verification, API key generation, and webhook configuration (see 03-USER-SETUP.md). Must be completed before online consultation payments will function.

**User Setup Required (Google Calendar)**: Plan 03-02 introduced Google Calendar integration requiring OAuth 2.0 credentials, calendar ID configuration, and initial browser authentication flow (see 03-USER-SETUP.md). Must be completed before calendar events and Meet links will function.

**Human Verification Recommended**: Phase 2 verification identified 6 scenarios requiring testing with actual WhatsApp account (see 02-VERIFICATION.md). All code verified to exist and be properly wired; manual testing recommended before production launch.

**Phase 4 Complete**: Full-featured dashboard with calendar, history, settings, and mutations. Plan 04-01 created REST API with authenticated endpoints. Plan 04-02 set up React with Vite, TypeScript, Tailwind CSS. Plan 04-03 built day/week calendar views with appointment cards. Plan 04-04 added CSRF-protected mutations (cancel, retry refund, resend) with RefundsList. Plan 04-05 created settings page for schedule configuration with validation and Navigation component for tab-based routing. Plan 04-06 added appointment history with pagination. All dashboard features functional and tested (146 tests passing). Ready for Phase 5 deployment.

**Cron Job Setup Recommended**: Plan 03-05 created scripts/run_reconciliation.py for nightly data integrity checks. Schedule with crontab: `0 2 * * * cd /app && uv run python scripts/run_reconciliation.py` to run at 2 AM daily. Handles calendar drift detection, failed operation retries, and orphaned event cleanup.

## Session Continuity

Last session: 2026-02-06
Stopped at: Completed 04-05-PLAN.md (Settings & Schedule Configuration)
Resume file: None

**Phase 4 (Dashboard & Management) Complete** - All 6 plans executed successfully. Dashboard provides comprehensive appointment management with navigation tabs (Calendar/History/Settings), day/week calendar views with appointment cards, CSRF-protected mutations (cancel, retry refund, resend), failed refunds monitoring panel, paginated appointment history, and settings page for schedule configuration. Doctor can manage working hours, view appointments, review history, and take actions all through the web interface. All 146 tests passing. Ready for Phase 5 deployment.
