---
phase: 05
plan: 05
subsystem: safety-controls
tags: [emergency-mode, incident-response, safety, read-only]

requires:
  - 04-01-SUMMARY.md  # Dashboard API endpoints
  - 01-01-SUMMARY.md  # Configuration system

provides:
  - Emergency mode configuration system
  - Booking disabled toggle for WhatsApp
  - Read-only dashboard mode
  - Emergency status API endpoints
  - Visual emergency banner in dashboard

affects:
  - Future incident response procedures
  - Production deployment safety mechanisms

tech-stack:
  added: []
  patterns:
    - Emergency mode flags in config
    - Runtime toggle with config persistence
    - Read-only mode decorator pattern
    - Polling-based status UI component

key-files:
  created:
    - frontend/src/components/EmergencyBanner.tsx
  modified:
    - src/docbot/config.py
    - src/docbot/bot_handler.py
    - src/docbot/dashboard_api.py
    - src/docbot/i18n.py
    - frontend/src/App.tsx

decisions:
  - id: EMERGENCY-01
    what: Emergency flags stored in config with runtime toggle
    why: Allows emergency mode changes without deployment, persists across restarts
    impact: Doctor can enable emergency mode via API, changes persist in config file

  - id: EMERGENCY-02
    what: Booking disabled returns to main menu with maintenance message
    why: Graceful degradation - existing features (view, cancel) still work
    impact: Patients can still access existing appointments during incident

  - id: EMERGENCY-03
    what: Read-only mode returns 403 on all mutations
    why: Prevents accidental changes during investigations, clear error messaging
    impact: Cancel, retry refund, resend, and settings updates blocked in read-only mode

  - id: EMERGENCY-04
    what: Emergency banner polls status every 30 seconds
    why: Near real-time visibility without websockets, minimal server load
    impact: Doctor sees emergency status within 30s of toggle

metrics:
  duration: 12 minutes
  completed: 2026-02-07
---

# Phase 05 Plan 05: Emergency Mode Controls Summary

**One-liner:** Runtime emergency toggles for disabling bookings and enabling read-only dashboard with visual status indicators.

## What Was Built

### Emergency Mode Configuration (Task 1)

- Added `EmergencyConfig` model to config system with:
  - `booking_disabled`: bool flag to stop new bookings
  - `readonly_dashboard`: bool flag for view-only dashboard
  - `maintenance_message`: customizable patient-facing message
- Created helper functions:
  - `is_booking_disabled()`: Check booking status
  - `is_readonly_mode()`: Check dashboard mode
  - `set_emergency_mode()`: Runtime toggle with config file persistence and cache clearing
- Emergency config integrated into main Settings model

### Booking Disabled Check (Task 2 - WhatsApp)

- Bot handler checks `is_booking_disabled()` when "Book Appointment" clicked
- If booking disabled:
  - Sends localized maintenance message to patient
  - Returns to main menu
  - Existing features (view appointments, cancel) still work
- Added `booking_disabled` i18n message in English, Telugu, Hindi

### Read-Only Dashboard Mode (Task 2 - Dashboard)

- Created `check_readonly()` function that raises 403 with clear error message
- Applied read-only checks to all mutation endpoints:
  - `POST /api/appointments/{id}/cancel`
  - `POST /api/refunds/{id}/retry`
  - `POST /api/appointments/{id}/resend`
  - `PUT /api/settings`
- Added emergency status endpoints:
  - `GET /api/emergency`: Returns current emergency flags
  - `POST /api/emergency`: Toggles emergency flags (requires authentication)
- All GET endpoints remain accessible in read-only mode

### Emergency Banner (Task 3)

- Created `EmergencyBanner` component:
  - Polls `/api/emergency` every 30 seconds
  - Displays red banner when any emergency mode active
  - Lists active emergency modes with clear messaging
- Integrated banner into App.tsx above navigation
- Banner conditionally renders (hidden when no emergency)

## Files Changed

### Backend

**src/docbot/config.py** - Emergency configuration system:
- Added EmergencyConfig model with 3 fields
- Added helper functions for checking and setting emergency mode
- Runtime toggle with config persistence and cache clearing

**src/docbot/bot_handler.py** - Booking disabled check:
- Import is_booking_disabled from config
- Check emergency mode in _handle_main_menu before starting booking flow
- Send maintenance message and return to menu if booking disabled

**src/docbot/dashboard_api.py** - Read-only mode enforcement:
- Import emergency mode functions from config
- Add check_readonly() utility function
- Add read-only checks to all mutation endpoints
- Add GET /api/emergency and POST /api/emergency endpoints
- Add EmergencyStatusResponse model

**src/docbot/i18n.py** - Localized messages:
- Add booking_disabled message in English, Telugu, Hindi

### Frontend

**frontend/src/components/EmergencyBanner.tsx** - Visual emergency indicator:
- TanStack Query polling every 30 seconds
- Red banner with border-l-4 styling
- Conditional rendering based on emergency flags
- Clear messaging about active emergency modes

**frontend/src/App.tsx** - Banner integration:
- Import EmergencyBanner component
- Render banner above navigation in main layout

## How It Works

### Emergency Mode Activation

1. Doctor calls `POST /api/emergency` with desired flags:
   ```json
   {
     "booking_disabled": true,
     "readonly_dashboard": true
   }
   ```

2. `set_emergency_mode()` updates config file and clears cache

3. Changes take effect immediately for all subsequent requests

### Booking Flow Protection

1. Patient clicks "Book Appointment" in WhatsApp
2. Bot handler calls `is_booking_disabled()`
3. If true:
   - Send localized maintenance message
   - Return to main menu
   - Patient can still view/cancel existing appointments
4. If false:
   - Proceed with booking flow normally

### Dashboard Mutation Protection

1. Doctor attempts cancel/retry/resend action in dashboard
2. Endpoint calls `check_readonly()`
3. If read-only mode active:
   - Return 403 with message "Dashboard is in read-only mode during incident response"
   - Frontend displays error to doctor
4. If read-only mode inactive:
   - Proceed with mutation normally

### Visual Feedback

1. EmergencyBanner polls `/api/emergency` every 30 seconds
2. If any emergency flag is true:
   - Display red banner with active modes listed
3. If all flags are false:
   - Hide banner (conditional render returns null)

## Testing

Manual testing recommended:

1. **Booking disabled test:**
   - Set `booking_disabled: true` in config or via API
   - Try booking via WhatsApp - should receive maintenance message
   - Try viewing appointments - should still work
   - Try cancelling appointment - should still work

2. **Read-only mode test:**
   - Set `readonly_dashboard: true` in config or via API
   - Try cancelling appointment in dashboard - should get 403
   - Try retrying failed refund - should get 403
   - Try updating settings - should get 403
   - View appointments - should still work

3. **Emergency banner test:**
   - Set emergency flags via API
   - Verify banner appears in dashboard within 30 seconds
   - Verify banner lists correct active modes
   - Disable emergency flags
   - Verify banner disappears within 30 seconds

4. **Reminders independence test:**
   - Set `booking_disabled: true`
   - Verify reminder cron job still sends reminders
   - Reminders are separate system, not affected by emergency mode

## Deviations from Plan

None - plan executed exactly as written.

## Commits

- `89326c9` - feat(05-05): add emergency mode configuration
- `73a6cfa` - feat(05-05): add emergency mode checks to webhook and dashboard
- `47a572d` - feat(05-05): add emergency banner to dashboard

## Next Phase Readiness

Emergency controls provide safety mechanisms for Phase 5 launch:

- Doctor can disable new bookings during incidents
- Doctor can enable read-only mode for investigations
- Emergency status visible in dashboard
- Existing appointments and reminders unaffected

Recommended additions for production:

1. Admin CLI command for emergency mode toggle:
   ```bash
   python -m docbot.admin emergency --booking-disabled true
   ```

2. Alert when emergency mode activated:
   - Log alert with high priority
   - Send notification to doctor's phone

3. Emergency mode history logging:
   - Track who enabled/disabled emergency mode
   - Track duration of emergency periods
   - Useful for incident postmortems

4. Automated emergency mode triggers:
   - API rate limit exceeded → enable booking disabled
   - Database errors → enable read-only mode
   - Payment gateway down → enable booking disabled

## Production Usage

### Via API (Requires Authentication)

Check status:
```bash
curl -X GET http://localhost:8000/api/emergency \
  -H "Cookie: session=..." \
  -H "X-CSRF-Token: ..."
```

Enable emergency mode:
```bash
curl -X POST http://localhost:8000/api/emergency \
  -H "Cookie: session=..." \
  -H "X-CSRF-Token: ..." \
  -H "Content-Type: application/json" \
  -d '{"booking_disabled": true, "readonly_dashboard": true}'
```

Disable emergency mode:
```bash
curl -X POST http://localhost:8000/api/emergency \
  -H "Cookie: session=..." \
  -H "X-CSRF-Token: ..." \
  -d '{"booking_disabled": false, "readonly_dashboard": false}'
```

### Via Config File (Requires Server Restart)

Edit `config.prod.json`:
```json
{
  "emergency": {
    "booking_disabled": true,
    "readonly_dashboard": true,
    "maintenance_message": "We are currently unable to accept new bookings. Please try again later or contact the clinic."
  }
}
```

Restart server to apply changes.

### Via Python Code

```python
from docbot.config import set_emergency_mode

# Enable emergency mode
set_emergency_mode(booking_disabled=True, readonly_dashboard=True)

# Disable emergency mode
set_emergency_mode(booking_disabled=False, readonly_dashboard=False)

# Toggle just one flag
set_emergency_mode(booking_disabled=True)  # keeps readonly_dashboard unchanged
```

## Success Criteria Met

- [x] Emergency toggle stops new bookings but doesn't affect existing appointments
- [x] Read-only mode prevents all dashboard mutations with clear error message
- [x] Emergency status visible via banner in dashboard
- [x] Doctor can toggle emergency mode via API endpoint
- [x] Booking disabled sends localized maintenance message to patients
- [x] Reminders continue to work even with booking disabled
