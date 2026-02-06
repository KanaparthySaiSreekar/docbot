# Roadmap: DocBot

## Overview

DocBot transforms a single-doctor practice into a fully automated WhatsApp-based appointment system. We build from infrastructure through bot interactions, payment processing, doctor dashboard, and finally automation features for a complete launch-ready system. Every phase delivers a coherent, testable capability toward the goal of eliminating manual appointment coordination.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Foundation** - Infrastructure, authentication, and deployment setup
- [x] **Phase 2: WhatsApp Bot & Booking Flow** - Patient-facing bot with booking capability
- [ ] **Phase 3: Payments & Calendar Integration** - Complete online/offline booking with Google Calendar
- [ ] **Phase 4: Dashboard & Management** - Doctor web interface and appointment operations
- [ ] **Phase 5: Automation & Launch** - Notifications, prescriptions, testing, and production readiness

## Phase Details

### Phase 1: Foundation
**Goal**: Production-ready infrastructure with doctor authentication, system configuration, and core data integrity framework
**Depends on**: Nothing (first phase)
**Requirements**: AUTH-01, AUTH-02, AUTH-03, CONF-01, CONF-02, CONF-03, CONF-04, DEPLOY-01, DEPLOY-02, DEPLOY-03, OPS-01, OPS-02, OPS-03, OPS-04, OPS-05, DATA-01, DATA-02, DATA-03, DATA-04, DATA-05, TIME-01, TIME-02, TIME-03, TIME-04, TIME-05
**Success Criteria** (what must be TRUE):
  1. Doctor can log in to web dashboard via Google OAuth and session persists
  2. System runs on Ubuntu server accessible via Cloudflare tunnel
  3. Structured logs capture all application events with health checks operational
  4. Configuration files contain clinic details, doctor credentials, and signature image
  5. Separate test and production configurations prevent environment mixing
  6. Appointment state machine defined and enforced in DB schema (PENDING_PAYMENT → CONFIRMED → CANCELLED → REFUNDED)
  7. Timezone strategy implemented globally (all timestamps stored in UTC, displayed in IST)
  8. Idempotency framework supports duplicate webhook prevention with event ID tracking
**Plans**: 5 plans

Plans:
- [x] 01-01-PLAN.md -- Project scaffolding, config system, structured logging, health endpoints
- [x] 01-02-PLAN.md -- Database schema, state machine, timezone utilities, idempotency (TDD)
- [x] 01-03-PLAN.md -- Google OAuth authentication, sessions, landing page
- [x] 01-04-PLAN.md -- Docker deployment, admin override script, backup verification
- [x] 01-05-PLAN.md -- Gap closure: Add init_db() to lifespan, fix deprecated datetime

### Phase 2: WhatsApp Bot & Booking Flow
**Goal**: Patients can interact with bot, select appointments, and complete booking flow (without payment)
**Depends on**: Phase 1
**Requirements**: BOT-01, BOT-02, BOT-03, BOT-04, BOT-05, BOT-06, BOT-07, BOT-08, BOT-09, BOOK-01, BOOK-02, BOOK-03, BOOK-04, BOOK-05, BOOK-06, BOOK-07, BOOK-08, BOOK-09, FAIL-01, FAIL-02
**Success Criteria** (what must be TRUE):
  1. Patient receives language selection on first interaction and preferences persist
  2. Patient navigates main menu using buttons only (no free text required)
  3. Patient selects consultation type, date, and available time slots
  4. Patient enters details (name, age, gender) and selected slot soft-locks for 10-15 minutes
  5. System prevents overbooking and respects doctor's configured working hours
**Plans**: 4 plans

Plans:
- [x] 02-01-PLAN.md -- WhatsApp Cloud API client, webhook endpoint, message retry
- [x] 02-02-PLAN.md -- Patient storage, conversation state, language/i18n system
- [x] 02-03-PLAN.md -- Slot availability engine and booking service (TDD)
- [x] 02-04-PLAN.md -- Bot conversation handler wiring all subsystems together

### Phase 3: Payments & Calendar Integration
**Goal**: Complete booking system with Razorpay payments, refunds, and Google Calendar synchronization with reconciliation
**Depends on**: Phase 2
**Requirements**: PAY-01, PAY-02, PAY-03, PAY-04, PAY-05, PAY-06, PAY-07, OFFL-01, OFFL-02, OFFL-03, CAL-01, CAL-02, CAL-03, CAL-04, CAL-05, CAL-06, CAL-07, CAL-08, CNCL-01, CNCL-02, CNCL-04, CNCL-05, CNCL-06, CNCL-07, FAIL-03, FAIL-04, FAIL-05, FAIL-06, SEC-01
**Success Criteria** (what must be TRUE):
  1. Patient completes online booking with ₹500 Razorpay payment and receives Meet link
  2. Patient completes offline booking without payment and receives clinic address
  3. Every appointment creates Google Calendar event with Meet link for online consultations
  4. Patient can cancel appointment >1 hour before slot and receives automatic refund with retry on failure
  5. Database is authoritative; Google Calendar synced as projection with nightly reconciliation
  6. All booking operations are transactional and leverage idempotency framework from Phase 1
**Plans**: TBD

Plans:
- [ ] 03-01: TBD during phase planning

### Phase 4: Dashboard & Management
**Goal**: Doctor has full web interface to view, manage, and configure appointments with operational visibility
**Depends on**: Phase 3
**Requirements**: DASH-01, DASH-02, DASH-03, DASH-04, DASH-05, DASH-06, DASH-07, DASH-08, DASH-09, DASH-10, CNCL-03, SEC-02, SEC-03, SEC-04, FAIL-07
**Success Criteria** (what must be TRUE):
  1. Doctor views appointments in day and week calendar views with full patient details
  2. Doctor joins online consultations directly from dashboard via "Join Meet" button
  3. Doctor cancels appointments manually triggering appropriate refunds and notifications
  4. Doctor configures working hours (days, times, breaks) which updates slot availability
  5. Dashboard is responsive and protected with CSRF and session security
  6. Failed refunds visible on dashboard with status indicators and manual retry capability
**Plans**: TBD

Plans:
- [ ] 04-01: TBD during phase planning

### Phase 5: Automation & Launch
**Goal**: Complete system with automated reminders, prescription delivery, production readiness, and safety controls
**Depends on**: Phase 4
**Requirements**: NOTIF-01, NOTIF-02, NOTIF-03, NOTIF-04, PRSC-01, PRSC-02, PRSC-03, PRSC-04, PRSC-05, PRSC-06, PRSC-07, PRSC-08, PRSC-09, PRSC-10, PRSC-11, SEC-05, TEST-01, TEST-02, TEST-03, TEST-04, LAUNCH-01, LAUNCH-02
**Success Criteria** (what must be TRUE):
  1. Patients receive automated reminders 24 hours and 1 hour before appointments
  2. Doctor generates prescriptions from dashboard and patients receive PDFs via WhatsApp
  3. Prescription PDFs include signature, credentials, and are immutable after generation
  4. Prescriptions served via time-limited secure URLs with no plain-text PII in logs
  5. Complete test scenarios verified with WhatsApp test numbers and Razorpay sandbox
  6. Soft launch completed with family members before production rollout
  7. Emergency toggle can disable new bookings without affecting reminders or existing appointments
  8. Read-only dashboard mode available for incident response (view only, no mutations)
**Plans**: TBD

Plans:
- [ ] 05-01: TBD during phase planning

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation | 5/5 | Complete | 2026-02-05 |
| 2. WhatsApp Bot & Booking Flow | 4/4 | Complete | 2026-02-06 |
| 3. Payments & Calendar Integration | 0/TBD | Not started | - |
| 4. Dashboard & Management | 0/TBD | Not started | - |
| 5. Automation & Launch | 0/TBD | Not started | - |
