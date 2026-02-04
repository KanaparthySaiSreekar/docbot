# Requirements: DocBot

**Defined:** 2026-02-04
**Core Value:** Fully automated appointment booking and management that eliminates manual coordination - patients can book, pay, cancel, and receive prescriptions entirely through WhatsApp while the doctor focuses solely on consultations.

## v1 Requirements

### Authentication
- [ ] **AUTH-01**: Doctor can log in to web dashboard via Google OAuth
- [ ] **AUTH-02**: Doctor session persists across browser sessions
- [ ] **AUTH-03**: System supports single doctor account only

### WhatsApp Bot (Patient Interface)
- [ ] **BOT-01**: Bot responds to patient messages 24/7
- [ ] **BOT-02**: Patient selects language on first interaction (English/Telugu/Hindi)
- [ ] **BOT-03**: Language preference stored per phone number
- [ ] **BOT-04**: All bot interactions use buttons only (no free text parsing)
- [ ] **BOT-05**: Main menu displays: Book Appointment, View Appointment, Cancel Appointment, Contact Clinic
- [ ] **BOT-06**: Bot messages display in patient's selected language
- [ ] **BOT-07**: Bot handles invalid/expired button clicks gracefully
- [ ] **BOT-08**: Bot provides "Session expired, restart booking" message
- [ ] **BOT-09**: Bot prevents multiple parallel bookings from same phone number

### Appointment Booking
- [ ] **BOOK-01**: Patient selects consultation type (Online or Offline)
- [ ] **BOOK-02**: Patient selects appointment date from available dates
- [ ] **BOOK-03**: Patient sees only available 15-minute slots for selected date
- [ ] **BOOK-04**: Patient enters name, age, and gender
- [ ] **BOOK-05**: Selected slot is soft-locked for 10-15 minutes during booking
- [ ] **BOOK-06**: System prevents overbooking (max 50 appointments/day)
- [ ] **BOOK-07**: Slots only available during doctor's configured working hours
- [ ] **BOOK-08**: Same-day booking is allowed if slots available
- [ ] **BOOK-09**: Patient receives confirmation message after successful booking

### Payment & Online Consultations
- [ ] **PAY-01**: Online consultation requires ₹500 payment via Razorpay
- [ ] **PAY-02**: Payment page supports UPI QR code
- [ ] **PAY-03**: Payment page supports UPI intent (direct app)
- [ ] **PAY-04**: Payment verification via Razorpay webhook
- [ ] **PAY-05**: Booking confirmed only after successful payment verification
- [ ] **PAY-06**: Failed payment releases the soft-locked slot
- [ ] **PAY-07**: Patient receives Meet link via WhatsApp after payment success

### Offline Consultations
- [ ] **OFFL-01**: Offline consultation booking requires no payment
- [ ] **OFFL-02**: Patient receives clinic address via WhatsApp after booking
- [ ] **OFFL-03**: Offline appointment created in Google Calendar with offline tag

### Google Calendar Integration
- [ ] **CAL-01**: Every appointment creates a Google Calendar event
- [ ] **CAL-02**: Calendar event includes patient name, phone, consultation type
- [ ] **CAL-03**: Calendar event hard-blocks the slot (prevents conflicts)
- [ ] **CAL-04**: Online appointments auto-generate unique Google Meet link
- [ ] **CAL-05**: Meet link attached to calendar event
- [ ] **CAL-06**: Cancelled appointments remove calendar event
- [ ] **CAL-07**: Database is source of truth; Google Calendar is synchronized projection
- [ ] **CAL-08**: Nightly reconciliation job flags calendar drift and alerts on mismatches

### Automated Notifications
- [ ] **NOTIF-01**: Patient receives reminder 24 hours before appointment
- [ ] **NOTIF-02**: Patient receives reminder 1 hour before appointment
- [ ] **NOTIF-03**: Online consultation reminders include Meet link
- [ ] **NOTIF-04**: Offline consultation reminders include clinic address

### Cancellation & Refunds
- [ ] **CNCL-01**: Patient can cancel appointment via WhatsApp if >1 hour before slot
- [ ] **CNCL-02**: Patient cannot cancel if ≤1 hour before slot
- [ ] **CNCL-03**: Doctor can cancel any appointment anytime via dashboard
- [ ] **CNCL-04**: Cancelled offline appointment sends cancellation confirmation
- [ ] **CNCL-05**: Cancelled online appointment triggers automatic Razorpay refund
- [ ] **CNCL-06**: Refund processes to original payment source
- [ ] **CNCL-07**: Patient receives cancellation + refund confirmation via WhatsApp

### Doctor Dashboard
- [ ] **DASH-01**: Doctor sees calendar view (day and week views)
- [ ] **DASH-02**: Appointment cards show patient name, age, gender, phone, type
- [ ] **DASH-03**: Online appointment cards show "Join Meet" button
- [ ] **DASH-04**: Doctor can click "Join Meet" to open Google Meet link
- [ ] **DASH-05**: Doctor can cancel appointments manually from dashboard
- [ ] **DASH-06**: Doctor can configure working hours (days, start/end times, breaks)
- [ ] **DASH-07**: Dashboard is responsive (works on desktop and tablet)
- [ ] **DASH-08**: Doctor can view appointment history (past appointments)
- [ ] **DASH-09**: Appointment status indicators (online/offline/cancelled/refunded)
- [ ] **DASH-10**: Doctor can resend Meet link or confirmation manually

### Prescription System
- [ ] **PRSC-01**: Doctor accesses separate Prescriptions section in dashboard
- [ ] **PRSC-02**: Doctor can select patient from appointment history
- [ ] **PRSC-03**: Doctor fills prescription form (medicines, dosage, instructions)
- [ ] **PRSC-04**: System generates PDF with prescription template
- [ ] **PRSC-05**: PDF includes doctor's signature image
- [ ] **PRSC-06**: PDF includes doctor's credentials (name, degree, registration number)
- [ ] **PRSC-07**: Prescription PDF automatically sent to patient via WhatsApp
- [ ] **PRSC-08**: Prescription stored in database with appointment reference
- [ ] **PRSC-09**: Prescription includes date and appointment reference ID
- [ ] **PRSC-10**: Prescription marked "Generated electronically"
- [ ] **PRSC-11**: Prescription immutable after generation

### Data Integrity & Concurrency
- [ ] **DATA-01**: All booking, payment, cancellation, and refund operations are transactional
- [ ] **DATA-02**: Slot locking uses database-level constraints, not in-memory locks
- [ ] **DATA-03**: Razorpay webhooks are idempotent (duplicate events do not double-confirm/refund)
- [ ] **DATA-04**: WhatsApp webhook retries do not create duplicate appointments
- [ ] **DATA-05**: Appointment state machine enforced (PENDING_PAYMENT → CONFIRMED → CANCELLED → REFUNDED)

### Time & Slot Handling
- [ ] **TIME-01**: All timestamps stored in UTC, displayed in IST
- [ ] **TIME-02**: Booking cutoff logic explicitly checks IST time
- [ ] **TIME-03**: Slot availability recalculated in real-time before final confirmation
- [ ] **TIME-04**: Soft-locked slots automatically released after TTL expiry
- [ ] **TIME-05**: Appointments cannot span across calendar days

### Failure Handling - WhatsApp
- [ ] **FAIL-01**: If WhatsApp message delivery fails, system retries with backoff
- [ ] **FAIL-02**: Message send failures are logged but do not block booking

### Failure Handling - Payments
- [ ] **FAIL-03**: If payment succeeds but calendar creation fails, system retries calendar sync
- [ ] **FAIL-04**: If refund API fails, system retries with exponential backoff until success or manual intervention
- [ ] **FAIL-07**: Failed refunds surface on doctor dashboard with status indicator and manual retry option

### Failure Handling - Google APIs
- [ ] **FAIL-05**: Google token refresh handled automatically
- [ ] **FAIL-06**: If Meet link creation fails, appointment marked CONFIRMED_NO_MEET and retried

### Security
- [ ] **SEC-01**: All webhook endpoints validate signatures (Razorpay, Meta)
- [ ] **SEC-02**: Doctor dashboard protected by server-side session cookies
- [ ] **SEC-03**: CSRF protection enabled for dashboard actions
- [ ] **SEC-04**: No patient PII logged in plain-text logs
- [ ] **SEC-05**: Prescription PDFs served via time-limited secure URLs

### Observability & Operations
- [ ] **OPS-01**: Structured application logs (JSON)
- [ ] **OPS-02**: Error-level alerts for payment/calendar/refund failures
- [ ] **OPS-03**: Health-check endpoint for Cloudflare
- [ ] **OPS-04**: Manual admin override script for DB corrections
- [ ] **OPS-05**: Daily backup verification (not just backup creation)

### System Configuration
- [ ] **CONF-01**: Clinic address stored in configuration file
- [ ] **CONF-02**: Doctor credentials (name, degree, registration) stored in config
- [ ] **CONF-03**: Doctor signature image uploaded during initial setup
- [ ] **CONF-04**: System timezone set to Indian Standard Time (IST)

### Deployment & Environment
- [ ] **DEPLOY-01**: Separate configs for test and production
- [ ] **DEPLOY-02**: Razorpay test/live keys never mixed
- [ ] **DEPLOY-03**: Google OAuth test users restricted pre-launch

### Testing & Quality
- [ ] **TEST-01**: WhatsApp test number integration for bot testing
- [ ] **TEST-02**: Razorpay test mode support for payment flow testing
- [ ] **TEST-03**: Comprehensive test scenario checklist completed
- [ ] **TEST-04**: Soft launch with limited users (family) completed before full launch

### Launch Safety Controls
- [ ] **LAUNCH-01**: Emergency toggle to disable new bookings without stopping reminders/existing appointments
- [ ] **LAUNCH-02**: Read-only mode for dashboard during incidents (view only, no mutations)

## v2 Requirements

Deferred to future releases.

### Multi-tenancy
- **MULTI-01**: Support for multiple doctors
- **MULTI-02**: Support for multiple clinics
- **MULTI-03**: Separate calendars per doctor

### Enhanced Features
- **ENH-01**: SMS notifications as backup to WhatsApp
- **ENH-02**: Email notifications
- **ENH-03**: Patient medical records system
- **ENH-04**: Insurance integration
- **ENH-05**: Staff/admin accounts for appointment management
- **ENH-06**: Patient web portal
- **ENH-07**: Mobile app (iOS/Android)
- **ENH-08**: NLP for free-text chat in WhatsApp
- **ENH-09**: Configurable consultation fees per appointment type
- **ENH-10**: Variable slot durations (15/30/45 min)
- **ENH-11**: Reason for visit categories
- **ENH-12**: Multiple payment gateways
- **ENH-13**: International payment support

## Out of Scope

Explicitly excluded to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Multi-doctor support | Single doctor practice, unnecessary complexity |
| Multi-clinic support | Single location only |
| Insurance integration | Direct payment only, reduces complexity |
| NLP/free-text chat | Button-based is more reliable, easier multi-language |
| Patient web portal | WhatsApp-only reduces development scope |
| Patient medical records | Focus on scheduling, not EHR |
| SMS/Email notifications | WhatsApp has universal adoption in India |
| Mobile apps | WhatsApp serves as patient mobile interface |
| Multiple payment gateways | Razorpay sufficient for v1 |
| International payments | India-only for initial launch |
| Configurable fees | Fixed ₹500 simplifies implementation |
| Variable slot durations | Fixed 15-min reduces booking complexity |
| Reason for visit | Adds friction, doctor assesses during consult |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| AUTH-01 | Phase 1 | Pending |
| AUTH-02 | Phase 1 | Pending |
| AUTH-03 | Phase 1 | Pending |
| CONF-01 | Phase 1 | Pending |
| CONF-02 | Phase 1 | Pending |
| CONF-03 | Phase 1 | Pending |
| CONF-04 | Phase 1 | Pending |
| DEPLOY-01 | Phase 1 | Pending |
| DEPLOY-02 | Phase 1 | Pending |
| DEPLOY-03 | Phase 1 | Pending |
| OPS-01 | Phase 1 | Pending |
| OPS-02 | Phase 1 | Pending |
| OPS-03 | Phase 1 | Pending |
| OPS-04 | Phase 1 | Pending |
| OPS-05 | Phase 1 | Pending |
| BOT-01 | Phase 2 | Pending |
| BOT-02 | Phase 2 | Pending |
| BOT-03 | Phase 2 | Pending |
| BOT-04 | Phase 2 | Pending |
| BOT-05 | Phase 2 | Pending |
| BOT-06 | Phase 2 | Pending |
| BOT-07 | Phase 2 | Pending |
| BOT-08 | Phase 2 | Pending |
| BOT-09 | Phase 2 | Pending |
| BOOK-01 | Phase 2 | Pending |
| BOOK-02 | Phase 2 | Pending |
| BOOK-03 | Phase 2 | Pending |
| BOOK-04 | Phase 2 | Pending |
| BOOK-05 | Phase 2 | Pending |
| BOOK-06 | Phase 2 | Pending |
| BOOK-07 | Phase 2 | Pending |
| BOOK-08 | Phase 2 | Pending |
| BOOK-09 | Phase 2 | Pending |
| FAIL-01 | Phase 2 | Pending |
| FAIL-02 | Phase 2 | Pending |
| PAY-01 | Phase 3 | Pending |
| PAY-02 | Phase 3 | Pending |
| PAY-03 | Phase 3 | Pending |
| PAY-04 | Phase 3 | Pending |
| PAY-05 | Phase 3 | Pending |
| PAY-06 | Phase 3 | Pending |
| PAY-07 | Phase 3 | Pending |
| OFFL-01 | Phase 3 | Pending |
| OFFL-02 | Phase 3 | Pending |
| OFFL-03 | Phase 3 | Pending |
| CAL-01 | Phase 3 | Pending |
| CAL-02 | Phase 3 | Pending |
| CAL-03 | Phase 3 | Pending |
| CAL-04 | Phase 3 | Pending |
| CAL-05 | Phase 3 | Pending |
| CAL-06 | Phase 3 | Pending |
| CNCL-01 | Phase 3 | Pending |
| CNCL-02 | Phase 3 | Pending |
| CNCL-04 | Phase 3 | Pending |
| CNCL-05 | Phase 3 | Pending |
| CNCL-06 | Phase 3 | Pending |
| CNCL-07 | Phase 3 | Pending |
| TIME-01 | Phase 1 | Pending |
| TIME-02 | Phase 1 | Pending |
| TIME-03 | Phase 1 | Pending |
| TIME-04 | Phase 1 | Pending |
| TIME-05 | Phase 1 | Pending |
| DATA-01 | Phase 1 | Pending |
| DATA-02 | Phase 1 | Pending |
| DATA-03 | Phase 1 | Pending |
| DATA-04 | Phase 1 | Pending |
| DATA-05 | Phase 1 | Pending |
| FAIL-03 | Phase 3 | Pending |
| FAIL-04 | Phase 3 | Pending |
| FAIL-05 | Phase 3 | Pending |
| FAIL-06 | Phase 3 | Pending |
| SEC-01 | Phase 3 | Pending |
| DASH-01 | Phase 4 | Pending |
| DASH-02 | Phase 4 | Pending |
| DASH-03 | Phase 4 | Pending |
| DASH-04 | Phase 4 | Pending |
| DASH-05 | Phase 4 | Pending |
| DASH-06 | Phase 4 | Pending |
| DASH-07 | Phase 4 | Pending |
| DASH-08 | Phase 4 | Pending |
| DASH-09 | Phase 4 | Pending |
| DASH-10 | Phase 4 | Pending |
| CNCL-03 | Phase 4 | Pending |
| SEC-02 | Phase 4 | Pending |
| SEC-03 | Phase 4 | Pending |
| SEC-04 | Phase 4 | Pending |
| NOTIF-01 | Phase 5 | Pending |
| NOTIF-02 | Phase 5 | Pending |
| NOTIF-03 | Phase 5 | Pending |
| NOTIF-04 | Phase 5 | Pending |
| PRSC-01 | Phase 5 | Pending |
| PRSC-02 | Phase 5 | Pending |
| PRSC-03 | Phase 5 | Pending |
| PRSC-04 | Phase 5 | Pending |
| PRSC-05 | Phase 5 | Pending |
| PRSC-06 | Phase 5 | Pending |
| PRSC-07 | Phase 5 | Pending |
| PRSC-08 | Phase 5 | Pending |
| PRSC-09 | Phase 5 | Pending |
| PRSC-10 | Phase 5 | Pending |
| PRSC-11 | Phase 5 | Pending |
| SEC-05 | Phase 5 | Pending |
| TEST-01 | Phase 5 | Pending |
| TEST-02 | Phase 5 | Pending |
| TEST-03 | Phase 5 | Pending |
| TEST-04 | Phase 5 | Pending |

**Coverage:**
- v1 requirements: 99 total (94 original + 5 surgical additions)
- Mapped to phases: 99 (100% coverage after adjustments)
- Unmapped: 0 ✓

---
*Requirements defined: 2026-02-04*
*Last updated: 2026-02-04 with surgical additions (CAL-07/08, FAIL-07, LAUNCH-01/02) and phase boundary fixes*
