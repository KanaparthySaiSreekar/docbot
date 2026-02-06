# Test Scenarios Checklist

Document all verified test scenarios for DocBot launch readiness.

**Last updated:** 2026-02-07
**Automated tests:** 19 E2E tests passing
**Status:** Ready for manual verification

---

## Automated Test Coverage

### E2E Tests Status: ✓ 19/19 Passing

**Booking Flow Tests:** 10 tests
- Complete online booking with payment flow
- Complete offline booking (no payment)
- Session expiry handling
- Slot locking and race condition prevention
- Same-day slot filtering
- Cancellation time restrictions
- Reminder timing verification
- Conversation state management
- Expired lock cleanup

**Payment Flow Tests:** 4 tests
- Online consultation payment creation
- Failed payment slot release
- Refund flow for cancellations
- Offline consultation (no payment)

**Prescription Flow Tests:** 5 tests
- Prescription creation and delivery
- One prescription per appointment (immutability)
- Token expiry after 72 hours
- Token regeneration
- Completed appointment filtering

---

## WhatsApp Bot Flows

### Language Selection
- [ ] New user receives language selection on first message
- [ ] English language displays correctly
- [ ] Telugu language displays correctly
- [ ] Hindi language displays correctly
- [ ] Selected language persists across sessions
- [ ] Language can be changed from main menu

### Booking Flow - Online Consultation
- [ ] Main menu shows "Book Appointment" option
- [ ] Select "Online Consultation" works
- [ ] Available dates displayed (next 7 days)
- [ ] Available slots exclude booked/locked slots
- [ ] Same-day slots filter out past times
- [ ] Name input accepted and validated
- [ ] Age input accepted (numeric only)
- [ ] Gender selection buttons work (Male/Female/Other)
- [ ] Confirmation screen shows correct details
- [ ] Payment link generated and sent via WhatsApp
- [ ] Payment link opens Razorpay page correctly
- [ ] Slot soft-locked during payment (10 minutes)

### Booking Flow - Offline Consultation
- [ ] Select "Offline Consultation" from type selection
- [ ] Same slot selection flow as online
- [ ] Patient details captured (name, age, gender)
- [ ] No payment required - direct confirmation
- [ ] Clinic address included in confirmation message
- [ ] Calendar event created immediately
- [ ] Appointment status: CONFIRMED (not PENDING_PAYMENT)

### Payment Processing
- [ ] Razorpay payment page loads correctly
- [ ] UPI QR code displayed for scanning
- [ ] UPI intent works on mobile devices
- [ ] Card payment option available
- [ ] Successful payment triggers confirmation
- [ ] Meet link sent for online consultation
- [ ] Confirmation includes appointment details
- [ ] Failed/abandoned payment releases slot after expiry
- [ ] Multiple payment attempts handled correctly

### Cancellation
- [ ] Patient can cancel >1 hour before appointment
- [ ] Cancellation confirmation message sent
- [ ] Patient cannot cancel <=1 hour before appointment
- [ ] Error message explains time restriction
- [ ] Doctor can cancel anytime (dashboard)
- [ ] Online cancellation initiates refund automatically
- [ ] Offline cancellation (no refund needed)
- [ ] Calendar event deleted on cancellation
- [ ] Cancelled appointment removed from slot locks

### Reminders
- [ ] 24-hour reminder sent correctly
- [ ] 24-hour reminder includes appointment details
- [ ] Online reminder includes Meet link
- [ ] Offline reminder includes clinic address
- [ ] 1-hour reminder sent correctly
- [ ] 1-hour reminder more urgent in tone
- [ ] Reminders not re-sent after first delivery
- [ ] Reminders in correct language (patient's preference)
- [ ] Cancelled appointments don't receive reminders

### Session Management
- [ ] Session expires after 30 minutes inactivity
- [ ] Session expiry message displayed
- [ ] User returned to main menu after expiry
- [ ] New booking restarts conversation cleanly
- [ ] Multiple conversations from same phone handled

### Error Handling
- [ ] Invalid input shows helpful error message
- [ ] Network errors handled gracefully
- [ ] Database errors logged and alerted
- [ ] WhatsApp API errors don't crash bot
- [ ] User can retry after recoverable errors

---

## Dashboard Functions

### Authentication
- [ ] Google OAuth login works
- [ ] Any Google account accepted (no allowlist)
- [ ] Session persists across page refreshes
- [ ] Session never expires (max_age=None)
- [ ] Logout works correctly
- [ ] Protected routes redirect to login

### Calendar Views
- [ ] Day view shows appointments for selected date
- [ ] Day view displays 9:00-17:00 time slots
- [ ] Week view shows all 7 days (Monday start)
- [ ] Appointment cards show patient details
- [ ] Appointment cards show status (online/offline)
- [ ] "Join Meet" button opens correct Google Meet link
- [ ] Meet button only shown for online consultations
- [ ] Navigate between days/weeks works
- [ ] Today button returns to current date
- [ ] View mode toggle (day/week) works

### Appointment Management
- [ ] Cancel appointment button works
- [ ] Cancel confirmation dialog shown
- [ ] Online cancellation triggers refund
- [ ] Offline cancellation (no refund)
- [ ] Cancelled appointments marked in calendar
- [ ] Retry failed refund button works
- [ ] Refund status updated after retry
- [ ] Resend confirmation works
- [ ] Resend uses correct template (online vs offline)
- [ ] Action buttons disabled during processing
- [ ] Success/error messages displayed

### Failed Refunds List
- [ ] Failed refunds page shows PENDING and FAILED refunds
- [ ] Refund details displayed (amount, attempts)
- [ ] Retry button visible for each failed refund
- [ ] Retry increments attempt count
- [ ] Status updated after successful retry
- [ ] Empty state shown when no failed refunds

### Appointment History
- [ ] History page shows past appointments
- [ ] Pagination works (20 per page)
- [ ] All statuses visible (CONFIRMED, CANCELLED, REFUNDED)
- [ ] No action buttons (read-only view)
- [ ] Search/filter by date range (optional)
- [ ] Export to CSV (optional)

### Settings - Schedule Configuration
- [ ] Working hours displayed correctly
- [ ] Working hours can be updated (start/end time)
- [ ] Break times displayed correctly
- [ ] Break times can be updated (start/end time)
- [ ] Slot duration displayed (15 minutes default)
- [ ] Consultation fee displayed
- [ ] Save button works
- [ ] Validation prevents invalid schedules
- [ ] Changes reflect immediately in slot generation
- [ ] Success message shown after save

### Settings - Clinic Details
- [ ] Clinic name editable
- [ ] Clinic address editable
- [ ] Contact phone editable
- [ ] Doctor name and qualifications editable
- [ ] Changes saved correctly
- [ ] Used in prescriptions and messages

### Prescriptions
- [ ] Prescriptions page shows completed appointments only
- [ ] Patient selection dropdown works
- [ ] Selected appointment details displayed
- [ ] Add medicine button adds form row
- [ ] Remove medicine button removes row
- [ ] Medicine name, dosage, duration fields work
- [ ] Instructions textarea works
- [ ] Generate PDF button creates prescription
- [ ] PDF download link works
- [ ] PDF includes doctor signature and credentials
- [ ] PDF includes "Generated electronically" notice
- [ ] WhatsApp delivery automatic after generation
- [ ] Secure download URL sent to patient
- [ ] Token expires after 72 hours
- [ ] Regenerate token button works
- [ ] Cannot create duplicate prescription for same appointment
- [ ] Prescription history shows all past prescriptions
- [ ] Download status visible (sent/delivered)

---

## Safety Controls

### Emergency Mode - Booking Disabled
- [ ] Toggle "Disable New Bookings" in dashboard
- [ ] New booking attempts return maintenance message
- [ ] Existing appointments unaffected
- [ ] Reminders continue working
- [ ] Cancellations still work
- [ ] Dashboard shows emergency banner (red)
- [ ] Banner indicates booking disabled
- [ ] Re-enable restores normal operation

### Emergency Mode - Read-Only Dashboard
- [ ] Toggle "Read-Only Mode" in dashboard
- [ ] All mutation buttons disabled
- [ ] Cancel appointment returns 403 error
- [ ] Retry refund returns 403 error
- [ ] Resend confirmation returns 403 error
- [ ] Settings cannot be saved
- [ ] Prescriptions cannot be created
- [ ] View-only operations work normally
- [ ] Emergency banner shows read-only status (yellow)
- [ ] Disable read-only mode restores mutations

### Emergency Banner
- [ ] Banner visible when any emergency mode active
- [ ] Banner polls status every 30 seconds
- [ ] Banner color matches severity (red/yellow)
- [ ] Banner dismissible but returns on refresh
- [ ] Banner shows which mode(s) active

---

## Integration Tests

### Razorpay Sandbox
- [ ] Test payment succeeds with test card
- [ ] Test refund processes correctly
- [ ] Webhook signature validation works
- [ ] Invalid signature rejected
- [ ] Duplicate webhook events deduplicated
- [ ] Payment notes include appointment_id
- [ ] Amount matches consultation fee

### WhatsApp Test Numbers
- [ ] Messages send successfully to test number
- [ ] Button interactions work correctly
- [ ] List selections work correctly
- [ ] Text input received correctly
- [ ] Media messages (future) work
- [ ] Webhook receives incoming messages
- [ ] Webhook signature validation works
- [ ] Message deduplication works (message_id)

### Google Calendar Integration
- [ ] Events created with correct details
- [ ] Online events include Google Meet link
- [ ] Offline events include clinic location
- [ ] Event title format correct
- [ ] Event description includes patient details
- [ ] Event time in IST displayed correctly
- [ ] Events visible in Google Calendar UI
- [ ] Event updates work (reschedule)
- [ ] Event deletion works (cancellation)
- [ ] OAuth token refresh automatic

---

## Data Integrity

### Database Constraints
- [ ] Slot locks prevent double booking (PRIMARY KEY)
- [ ] One active conversation per phone (PRIMARY KEY)
- [ ] Unique appointment per date+time (UNIQUE constraint)
- [ ] Unique payment per appointment (UNIQUE constraint)
- [ ] Unique prescription per appointment (UNIQUE constraint)
- [ ] Gender values validated (CHECK constraint)
- [ ] Consultation type validated (CHECK constraint)
- [ ] Foreign key constraints enforced

### Timezone Handling
- [ ] All database timestamps in UTC
- [ ] IST conversion for display consistent
- [ ] Same-day booking uses IST time comparison
- [ ] Reminder windows calculated in IST
- [ ] Cancellation time restriction uses IST
- [ ] Calendar events created in IST

### Idempotency
- [ ] WhatsApp webhook events deduplicated
- [ ] Razorpay webhook events deduplicated
- [ ] Duplicate payment capture handled gracefully
- [ ] Retry operations are idempotent
- [ ] Event IDs globally unique

---

## Performance & Reliability

### Response Times
- [ ] WhatsApp messages processed within 5 seconds
- [ ] Dashboard loads within 2 seconds
- [ ] API responses within 1 second
- [ ] PDF generation within 3 seconds

### Concurrent Access
- [ ] Multiple patients booking simultaneously
- [ ] Doctor using dashboard while bookings occur
- [ ] Webhook processing doesn't block API requests
- [ ] Database locks prevent race conditions

### Error Recovery
- [ ] Failed WhatsApp sends logged and alerted
- [ ] Failed refunds retried with exponential backoff
- [ ] Failed calendar operations retried
- [ ] Database errors don't lose data
- [ ] Temporary outages recovered automatically

---

## Soft Launch Checklist

### Pre-Launch Verification
- [ ] All automated tests passing (19/19 E2E tests)
- [ ] WhatsApp Business account verified
- [ ] Razorpay account KYC complete
- [ ] Google Calendar API quota sufficient
- [ ] Cloudflare tunnel configured
- [ ] SSL/TLS certificate valid
- [ ] Environment variables set correctly
- [ ] Database backup configured
- [ ] Log rotation configured
- [ ] Disk space monitoring configured

### Test with 2-3 Family Members
- [ ] Book online consultation successfully
- [ ] Complete payment successfully
- [ ] Receive confirmation with Meet link
- [ ] Cancel appointment successfully
- [ ] Receive refund confirmation
- [ ] Book offline consultation successfully
- [ ] Receive reminder 24h before
- [ ] Receive reminder 1h before
- [ ] Join Google Meet successfully
- [ ] Receive prescription after consultation
- [ ] Download prescription PDF successfully

### Data Isolation Verification
- [ ] User A cannot see User B's appointments
- [ ] User A cannot cancel User B's appointments
- [ ] Phone number masking works in API responses
- [ ] No PII logged in application logs
- [ ] Prescription tokens unique per prescription
- [ ] Expired tokens don't allow downloads

### Graceful Degradation
- [ ] WhatsApp API down: Manual booking via phone
- [ ] Razorpay API down: Manual payment collection
- [ ] Google Calendar API down: Manual calendar entry
- [ ] Database slow: Queue operations
- [ ] All failures logged and alerted

---

## Production Readiness

### Monitoring
- [ ] Application logs written to disk
- [ ] Error logs written to separate file
- [ ] Alert logs written to alerts.log
- [ ] Log rotation configured (daily)
- [ ] Disk space monitored (alert at 80%)
- [ ] Database size monitored
- [ ] API response time monitored

### Backup & Recovery
- [ ] Database backed up daily (via cron)
- [ ] Backup verification runs automatically
- [ ] Backup retention: 30 days
- [ ] Recovery procedure documented
- [ ] Recovery tested (restore from backup)

### Incident Response
- [ ] Emergency mode controls tested
- [ ] Disable bookings procedure documented
- [ ] Read-only mode procedure documented
- [ ] Rollback procedure documented
- [ ] Contact list for escalations

### Documentation
- [ ] User setup guides complete (02, 03, 04)
- [ ] Verification checklist complete (02)
- [ ] Admin CLI usage documented
- [ ] Troubleshooting guide exists
- [ ] Architecture diagrams current

---

## Launch Decision Criteria

### Must Have (Blocking)
- [x] All automated E2E tests passing (19/19)
- [ ] WhatsApp integration verified with real account
- [ ] Payment integration verified with Razorpay sandbox
- [ ] Calendar integration verified with real Google account
- [ ] At least 3 successful end-to-end test bookings by family members
- [ ] No data leaks observed between test users
- [ ] All critical user flows tested manually

### Should Have (Non-Blocking but Important)
- [ ] Reconciliation job running nightly
- [ ] Reminder jobs running on schedule (cron)
- [ ] Backup verification passing
- [ ] All USER-SETUP.md guides completed by doctor
- [ ] Emergency mode controls verified
- [ ] Dashboard fully tested in production environment

### Nice to Have (Post-Launch)
- [ ] Performance optimization
- [ ] Additional test coverage
- [ ] Enhanced monitoring dashboards
- [ ] User feedback mechanism

---

**Verification Status:**
- Automated tests: ✓ Complete (19/19 passing)
- Manual testing: ⏳ Pending user verification
- Production deployment: ⏳ Pending launch approval

**Next Steps:**
1. Complete WhatsApp Business account setup (see 02-USER-SETUP.md)
2. Complete Razorpay account setup (see 03-USER-SETUP.md)
3. Complete Google Calendar setup (see 03-USER-SETUP.md)
4. Perform manual testing with family members
5. Verify all checklist items
6. Launch with 2-3 patients (soft launch)
7. Monitor for 1 week before full launch
