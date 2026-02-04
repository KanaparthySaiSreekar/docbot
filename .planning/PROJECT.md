# DocBot - WhatsApp Doctor Appointment System

## What This Is

A WhatsApp-based appointment management system for a single-doctor practice in India. Patients book online (paid) or offline (free) consultations entirely through a button-based WhatsApp bot, with full automation for payments (Razorpay), video consultations (Google Meet), reminders, cancellations with refunds, and prescription delivery. The doctor manages everything through a web dashboard without ever touching WhatsApp manually.

## Core Value

Fully automated appointment booking and management that eliminates manual coordination - patients can book, pay, cancel, and receive prescriptions entirely through WhatsApp while the doctor focuses solely on consultations through a clean web interface.

## Requirements

### Validated

(None yet — ship to validate)

### Active

#### WhatsApp Bot (Patient Interface)
- [ ] Multi-language support (English, Telugu, Hindi) - language selection on first interaction, stored per phone number
- [ ] Button-based flows (no free text input required)
- [ ] Main menu: Book Appointment, View Appointment, Cancel Appointment, Contact Clinic
- [ ] Appointment booking flow with consultation type selection (online/offline)
- [ ] Date and time slot selection showing only available slots
- [ ] Patient details collection (name, age, gender)
- [ ] Slot soft-lock during booking (10-15 minute TTL)
- [ ] Payment integration for online consultations (₹500 via Razorpay)
- [ ] WhatsApp confirmation messages with appointment details
- [ ] Google Meet link delivery for online consultations
- [ ] Clinic address delivery for offline appointments
- [ ] Cancellation flow with >1 hour validation
- [ ] Automated reminders at T-24 hours and T-1 hour
- [ ] Prescription PDF delivery via WhatsApp message

#### Payment System
- [ ] Razorpay integration for ₹500 online consultation fee
- [ ] UPI QR code and UPI intent payment modes
- [ ] Payment verification via webhook
- [ ] Automatic refund processing for cancellations >1 hour before appointment
- [ ] Refund to original payment source

#### Google Integrations
- [ ] Google Calendar event creation for all appointments
- [ ] Calendar event metadata (patient name, phone, consultation type)
- [ ] Hard blocking to prevent double-booking
- [ ] Automatic Google Meet link generation for online consultations
- [ ] Event deletion on cancellation

#### Doctor Web Dashboard
- [ ] Google OAuth authentication (single doctor account)
- [ ] Calendar view (day and week views)
- [ ] Appointment cards showing patient details and consultation type
- [ ] "Join Meet" button for online consultations
- [ ] Manual appointment cancellation capability
- [ ] Working hours configuration interface (set hours, breaks, days off)
- [ ] Separate prescriptions section with patient selection
- [ ] Prescription template form with PDF generation
- [ ] Automatic prescription delivery via WhatsApp
- [ ] Prescription storage and history

#### Appointment Logic
- [ ] Fixed 15-minute appointment slots
- [ ] Maximum 50 appointments per day
- [ ] Zero overbooking enforcement
- [ ] Bot available 24/7, appointments only during configured doctor hours
- [ ] Same-day booking support
- [ ] Automatic slot availability calculation
- [ ] Payment-verified booking confirmation (online consultations only)

#### Prescription System
- [ ] Fixed prescription template
- [ ] Doctor signature image embedding
- [ ] Text credentials footer (Dr. Name, MBBS, Registration Number)
- [ ] PDF generation
- [ ] WhatsApp delivery to patient
- [ ] Database storage with appointment reference

#### Testing & Quality
- [ ] WhatsApp test number integration
- [ ] Razorpay test/sandbox mode support
- [ ] Comprehensive test scenario checklist
- [ ] Soft launch capability with limited rollout

### Out of Scope

- **Multi-doctor support** — System designed for single doctor only
- **Multi-clinic support** — Single location practice
- **Insurance integration** — Direct patient payment only
- **NLP or free-text chat** — Button-based interactions only
- **Patient portal/web access** — Patients use WhatsApp exclusively
- **Patient medical records system** — Focused on appointment management only
- **Admin/staff accounts** — Doctor-only web access
- **Mobile app** — WhatsApp serves as patient mobile interface
- **SMS notifications** — WhatsApp-only communication
- **Email notifications** — WhatsApp-only communication
- **Multiple payment gateways** — Razorpay only for v1
- **International payments** — India-focused (Razorpay, UPI)
- **Configurable consultation fees** — Fixed ₹500 for online consultations
- **Variable slot durations** — Fixed 15-minute slots
- **Reason for visit categories** — Removed to simplify booking flow

## Context

**Practice:** New single-doctor practice starting fresh with no existing patient base or legacy systems.

**User:** Building for family member who is the practicing doctor. Direct access to end user for feedback and iteration.

**Geography:** India-focused with Indian payment methods (Razorpay, UPI), multi-language support (English, Telugu, Hindi), and India data residency.

**Infrastructure:** Self-hosted on existing Ubuntu homelab server with Cloudflare tunnel for secure external access. No cloud hosting costs, full control over patient data.

**Technical background:** Developer has Linux/infrastructure experience and is comfortable managing servers and Cloudflare tunnels.

**Timeline:** ASAP launch target (2-4 weeks) with all features required for initial launch. No phased feature rollout - full PRD required for go-live.

**Testing approach:** Comprehensive testing required before launch including WhatsApp test numbers, Razorpay sandbox mode, soft launch with family members, and full test scenario coverage.

## Constraints

- **Tech Stack**: Python/FastAPI with UV package manager — Required for developer preference
- **Database**: SQLite — Suitable for single-doctor, single-server deployment with simplified backups
- **Hosting**: Self-hosted Ubuntu server via Cloudflare tunnel — Using existing homelab infrastructure
- **WhatsApp API**: Meta WhatsApp Cloud API — Official API for business messaging
- **Payment Gateway**: Razorpay only — India-focused, supports UPI/QR codes
- **Calendar System**: Single Google account — All appointments in one calendar
- **Timeline**: 2-4 weeks to launch — Aggressive but fixed deadline
- **Single Doctor**: System designed for one doctor only — No multi-tenancy required
- **India Only**: Payment methods, language support, and data residency for Indian users
- **Button-based UI**: WhatsApp interactions must use buttons only, no free text parsing
- **No External Services**: Self-contained system, no external SaaS dependencies beyond APIs
- **Consultation Fee**: Fixed ₹500 for online consultations — Not configurable
- **Slot Duration**: Fixed 15 minutes — Not configurable per appointment

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| SQLite vs PostgreSQL/MySQL | Single doctor, single server deployment doesn't need complex database. Simplifies backups (file copy), no separate DB server to manage. | — Pending |
| Fixed 15-min slots | Simplifies scheduling logic and provides consistent patient expectations. Doctor requested fixed duration. | — Pending |
| Button-based bot (no NLP) | Eliminates need for intent parsing, more reliable UX, easier multi-language support. | — Pending |
| WhatsApp-only patient communication | No email/SMS reduces complexity. WhatsApp has near-universal adoption in India. | — Pending |
| Self-hosted vs cloud | Existing homelab server available, reduces ongoing costs, full data control. | — Pending |
| Python/FastAPI | Developer preference, strong library ecosystem for APIs, good async support for webhooks. | — Pending |
| 10-15 min payment soft-lock | Extended from initial 5-min to account for payment gateway delays and user distraction. | — Pending |
| Configurable doctor hours in dashboard | Doctor needs flexibility to adjust availability without code changes. | — Pending |
| Prescription as separate section | Not every consultation needs prescription. Separate workflow allows doctor to handle post-consult. | — Pending |
| Clinic address in config file | Address unlikely to change frequently, simplifies implementation. | — Pending |
| Skip "reason for visit" | Removes friction from booking flow, doctor will assess during consultation. | — Pending |
| Full PRD for v1 | All features critical for launch, no phased rollout. Doctor needs complete system operational. | — Pending |

---
*Last updated: 2026-02-04 after initialization*
