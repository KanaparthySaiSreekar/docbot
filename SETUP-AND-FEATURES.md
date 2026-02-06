# DocBot Setup Guide & Feature List

Complete guide to setting up and using the DocBot automated appointment system.

## Table of Contents

1. [System Overview](#system-overview)
2. [Prerequisites](#prerequisites)
3. [External Services Setup](#external-services-setup)
4. [Installation](#installation)
5. [Configuration](#configuration)
6. [Running the Application](#running-the-application)
7. [Complete Feature List](#complete-feature-list)
8. [Testing](#testing)
9. [Production Deployment](#production-deployment)
10. [Cron Jobs Setup](#cron-jobs-setup)
11. [Troubleshooting](#troubleshooting)

---

## System Overview

**DocBot** is a fully automated WhatsApp-based appointment booking and management system for single-doctor practices. It eliminates manual appointment coordination by allowing patients to book, pay, cancel, and receive prescriptions entirely through WhatsApp while the doctor manages everything through a web dashboard.

**Technology Stack:**
- Backend: Python 3.12, FastAPI, SQLite
- Frontend: React 18, TypeScript, Vite, Tailwind CSS
- Integrations: WhatsApp Cloud API, Razorpay Payments, Google Calendar
- Deployment: Docker, Ubuntu server, Cloudflare tunnel

---

## Prerequisites

### Required Software

1. **Python 3.12+**
   ```bash
   python --version  # Should be 3.12 or higher
   ```

2. **uv** (Python package manager)
   ```bash
   # Install uv
   curl -LsSf https://astral.sh/uv/install.sh | sh  # Linux/Mac
   # or download from https://github.com/astral-sh/uv for Windows
   ```

3. **Node.js 18+** (for frontend)
   ```bash
   node --version  # Should be 18 or higher
   npm --version
   ```

4. **Git**
   ```bash
   git --version
   ```

5. **Docker & Docker Compose** (for production deployment)
   ```bash
   docker --version
   docker-compose --version
   ```

### System Requirements

- **RAM:** 2GB minimum, 4GB recommended
- **Storage:** 5GB free space
- **OS:** Windows 10+, Ubuntu 20.04+, macOS 10.15+

---

## External Services Setup

### 1. WhatsApp Business API Setup

**Required for:** Patient messaging, booking confirmations, reminders

1. **Create Meta Business Account**
   - Go to https://business.facebook.com
   - Create a business account
   - Verify your business

2. **Set Up WhatsApp Business Platform**
   - Visit https://developers.facebook.com/apps
   - Create new app → Business → WhatsApp
   - Note your App ID and App Secret

3. **Configure WhatsApp Business Account**
   - Add WhatsApp product to your app
   - Create a phone number or connect existing business number
   - Get your Phone Number ID

4. **Generate Access Token**
   - System User Access Token (permanent)
   - Grant `whatsapp_business_messaging` permission
   - Save the token securely

5. **Configure Webhook**
   - Set webhook URL: `https://your-domain.com/webhook/whatsapp`
   - Subscribe to `messages` events
   - Set verify token (choose a secret string)

**Configuration needed:**
```json
{
  "whatsapp": {
    "api_url": "https://graph.facebook.com/v21.0",
    "phone_number_id": "YOUR_PHONE_NUMBER_ID",
    "access_token": "YOUR_ACCESS_TOKEN",
    "verify_token": "YOUR_VERIFY_TOKEN"
  }
}
```

📖 **Detailed guide:** See `02-USER-SETUP.md` in project root

---

### 2. Razorpay Payment Gateway Setup

**Required for:** Online consultation payments and refunds

1. **Create Razorpay Account**
   - Sign up at https://razorpay.com
   - Complete KYC verification (required for live mode)
   - Get approval (usually takes 2-3 business days)

2. **Generate API Keys**
   - Dashboard → Settings → API Keys
   - Generate Test Mode keys (for development)
   - Generate Live Mode keys (for production)
   - Format: `rzp_test_XXXXXX` / `rzp_live_XXXXXX`

3. **Configure Webhooks**
   - Settings → Webhooks
   - Add webhook URL: `https://your-domain.com/webhook/razorpay`
   - Select events:
     - `payment.captured`
     - `payment.failed`
     - `refund.processed`
   - Save webhook secret

4. **Configure Payment Links**
   - Enable Payment Links feature
   - Set business details and logo

**Configuration needed:**
```json
{
  "razorpay": {
    "key_id": "rzp_test_XXXXXX",
    "key_secret": "YOUR_KEY_SECRET",
    "webhook_secret": "YOUR_WEBHOOK_SECRET"
  }
}
```

📖 **Detailed guide:** See `03-USER-SETUP.md` in project root

---

### 3. Google Calendar & Meet Setup

**Required for:** Appointment scheduling and Meet link generation

1. **Enable Google Calendar API**
   - Go to https://console.cloud.google.com
   - Create new project (or use existing)
   - Enable Google Calendar API

2. **Create OAuth 2.0 Credentials**
   - APIs & Services → Credentials
   - Create OAuth client ID → Desktop app
   - Download credentials JSON file
   - Rename to `credentials.json` and place in project root

3. **Configure OAuth Consent Screen**
   - Set app name: "DocBot"
   - Add scopes:
     - `https://www.googleapis.com/auth/calendar`
     - `https://www.googleapis.com/auth/calendar.events`
   - Add test users (your doctor's email)

4. **Get Calendar ID**
   - Open Google Calendar
   - Settings → Calendar → Integration
   - Copy Calendar ID (looks like email@group.calendar.google.com)

5. **Initial Authentication**
   ```bash
   # Run this once to authenticate
   python -c "from docbot.calendar_service import authenticate_calendar; authenticate_calendar()"
   # Browser will open → allow access → token.json created
   ```

**Configuration needed:**
```json
{
  "google_calendar": {
    "calendar_id": "YOUR_CALENDAR_ID@group.calendar.google.com"
  }
}
```

📖 **Detailed guide:** See `03-USER-SETUP.md` in project root

---

## Installation

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/docbot.git
cd docbot
```

### 2. Install Backend Dependencies

```bash
# Using uv (recommended)
uv sync

# Or using pip
pip install -e .
```

### 3. Install Frontend Dependencies

```bash
cd frontend
npm install
cd ..
```

### 4. Initialize Database

```bash
# Database will be auto-initialized on first run
# Or manually:
uv run python -c "from docbot.database import init_db; import asyncio; asyncio.run(init_db())"
```

---

## Configuration

### 1. Create Configuration File

Create `config.test.json` for development/testing:

```json
{
  "app": {
    "base_url": "http://localhost:8000",
    "secret_key": "your-secret-key-change-in-production"
  },
  "clinic": {
    "name": "Dr. Sharma's Clinic",
    "doctor_name": "Dr. Rajesh Sharma",
    "doctor_degree": "MBBS, MD",
    "doctor_registration": "MCI12345",
    "address": "123 MG Road, Bangalore 560001",
    "phone": "+919876543210",
    "signature_image_path": "doctor_signature.png"
  },
  "schedule": {
    "working_days": ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday"],
    "start_time": "09:00",
    "end_time": "17:00",
    "slot_duration_minutes": 30,
    "break_start": "13:00",
    "break_end": "14:00"
  },
  "consultation_types": {
    "online": {
      "name": "Online Consultation",
      "price": 500,
      "duration_minutes": 30
    },
    "offline": {
      "name": "Clinic Visit",
      "price": 0,
      "duration_minutes": 30
    }
  },
  "whatsapp": {
    "api_url": "https://graph.facebook.com/v21.0",
    "phone_number_id": "YOUR_PHONE_NUMBER_ID",
    "access_token": "YOUR_ACCESS_TOKEN",
    "verify_token": "YOUR_VERIFY_TOKEN"
  },
  "razorpay": {
    "key_id": "rzp_test_XXXXXX",
    "key_secret": "YOUR_KEY_SECRET",
    "webhook_secret": "YOUR_WEBHOOK_SECRET"
  },
  "google_calendar": {
    "calendar_id": "YOUR_CALENDAR_ID@group.calendar.google.com"
  },
  "emergency": {
    "booking_disabled": false,
    "readonly_dashboard": false,
    "maintenance_message": "We are currently unable to accept new bookings. Please try again later."
  }
}
```

### 2. Set Environment Variable

```bash
# For testing
export DOCBOT_ENV=test  # Linux/Mac
set DOCBOT_ENV=test     # Windows CMD
$env:DOCBOT_ENV="test"  # Windows PowerShell

# For production
export DOCBOT_ENV=prod
```

### 3. Add Doctor Signature Image

Place your signature image as `doctor_signature.png` in project root:
- Format: PNG with transparent background
- Size: 200x60 pixels recommended
- Will appear on prescription PDFs

---

## Running the Application

### Development Mode

**Terminal 1: Backend**
```bash
export DOCBOT_ENV=test
uv run uvicorn src.docbot.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2: Frontend**
```bash
cd frontend
npm run dev
# Opens at http://localhost:5173
# Proxies API calls to backend at localhost:8000
```

Access:
- **Dashboard:** http://localhost:5173/dashboard (login with any Google account)
- **Health Check:** http://localhost:8000/health
- **API Docs:** http://localhost:8000/docs

### Test Mode

```bash
export DOCBOT_ENV=test
uv run uvicorn src.docbot.main:app --host 0.0.0.0 --port 8000

# Frontend - build for production
cd frontend
npm run build
cd ..
```

Access dashboard at: http://localhost:8000/dashboard

### Production Mode

```bash
# Build frontend first
cd frontend
npm run build
cd ..

# Run with production config
export DOCBOT_ENV=prod
uv run uvicorn src.docbot.main:app --host 0.0.0.0 --port 8000 --workers 2
```

Or use Docker (recommended):

```bash
docker-compose --profile prod up -d
```

---

## Complete Feature List

### For Patients (via WhatsApp)

#### 1. Language Selection
- Choose from English, Telugu, or Hindi on first interaction
- Language preference persists across all future interactions
- All messages and confirmations in selected language

#### 2. Book Appointment

**Online Consultation (₹500)**
- Select consultation type: "Online"
- Choose date from available slots
- Select time slot (9 AM - 5 PM, excluding breaks)
- Enter patient details: name, age, gender
- Receive Razorpay payment link
- Complete payment via UPI/Card/NetBanking
- Receive confirmation with Google Meet link
- Automatic calendar event creation

**Offline Consultation (Free)**
- Select consultation type: "Offline"
- Choose date and time slot
- Enter patient details
- Instant confirmation with clinic address
- No payment required

#### 3. View Appointments
- See all upcoming appointments
- Shows: date, time, type (online/offline), status
- For online: Meet link included
- For offline: Clinic address included

#### 4. Cancel Appointment
- Cancel any appointment >1 hour before scheduled time
- Cannot cancel within 1 hour of appointment
- Online consultations: Automatic refund initiated
- Offline consultations: Simple cancellation
- Refund processed to original payment method in 5-7 days

#### 5. Automated Reminders
- **24 hours before:** Appointment reminder with all details
- **1 hour before:** Final reminder with Meet link (online) or address (offline)
- Sent automatically via WhatsApp
- No action required from patient

#### 6. Receive Prescriptions
- Doctor sends prescription after consultation
- Receives WhatsApp message with secure download link
- Link valid for 72 hours
- PDF includes: medicines, dosage, doctor signature, credentials
- Can re-download multiple times within 72 hours

#### 7. Contact Clinic
- Direct access to clinic phone number
- Available 24/7 for urgent queries

---

### For Doctor (via Web Dashboard)

#### 1. Authentication
- Login via Google OAuth
- Session never expires (until manual logout)
- Secure session management
- No password to remember

#### 2. Calendar View

**Day View**
- See all appointments for selected day
- Hourly timeline (9 AM - 5 PM)
- Color-coded by type: Blue (online), Green (offline)
- Shows: patient name, age, gender, time, type

**Week View**
- 7-day calendar (Monday-Sunday)
- See appointments across entire week
- Quick navigation between weeks
- Identifies busy days at a glance

**Appointment Cards**
- Patient details: name, age, gender, masked phone (last 4 digits)
- Appointment: date, time, consultation type, status
- For online: "Join Meet" button (opens Google Meet directly)
- For offline: Clinic address displayed
- Actions: Cancel, Resend confirmation

#### 3. Appointment Management

**Cancel Appointment**
- Doctor can cancel any appointment (no time restriction)
- Automatically triggers refund for online consultations
- Deletes calendar event
- Sends cancellation confirmation to patient
- Updates appointment status to CANCELLED

**Retry Failed Refund**
- View all failed refunds in dedicated panel
- Manual retry with single click
- Resets retry counter and backoff timer
- Real-time status updates

**Resend Confirmation**
- Resend Meet link for online consultations
- Resend booking confirmation for offline
- Useful if patient didn't receive original message

#### 4. Appointment History
- Paginated list (20 per page)
- Shows all past appointments
- Read-only view (no actions)
- Filter by date range
- Search by patient name/phone

#### 5. Settings & Schedule

**Working Hours Configuration**
- Set working days (select from Mon-Sun)
- Configure start time (e.g., 9:00 AM)
- Configure end time (e.g., 5:00 PM)
- Set break times (e.g., 1:00-2:00 PM)
- Changes reflect immediately in slot availability

**Consultation Types**
- Configure online consultation price
- Set slot duration (default: 30 minutes)
- Adjust as needed for practice

#### 6. Prescription Management

**Create Prescription**
- Select patient from completed appointments dropdown
- Add multiple medicines:
  - Medicine name
  - Dosage (e.g., 500mg)
  - Frequency (e.g., 1-0-1 = morning-afternoon-night)
  - Duration (e.g., 5 days)
  - Special notes (optional)
- Add general instructions (optional)
- Click "Create & Send Prescription"

**Prescription Generation**
- Professional PDF auto-generated with:
  - Clinic header (name, address, phone)
  - Doctor details (name, degree, registration number)
  - Patient info (name, age, gender, date)
  - Rx symbol (℞)
  - Medicines list with dosage
  - General instructions
  - Doctor signature (from config image)
  - "Generated electronically" notice
  - Appointment reference ID

**Prescription Delivery**
- Automatic WhatsApp delivery to patient
- Secure download link with 72-hour expiry
- Token regenerated on each send for fresh access
- Track delivery status (Sent/Pending)

**Prescription History**
- View all generated prescriptions
- See patient name, date, delivery status
- Download prescription PDF
- Prescriptions are immutable (one per appointment)

#### 7. Emergency Mode Controls

**Booking Disabled Mode**
- Toggle to stop accepting new bookings
- Existing appointments remain unaffected
- Reminders continue working
- Patient receives maintenance message
- Useful during: holidays, emergencies, system issues

**Read-Only Dashboard**
- Enable during incident investigation
- All dashboard views work normally
- All mutations blocked (cancel, retry, resend, settings, prescriptions)
- Returns 403 error with clear message
- Prevents accidental changes during troubleshooting

**Emergency Banner**
- Red banner displays when emergency mode active
- Shows which modes are enabled
- Refreshes every 30 seconds
- Visible across all dashboard pages

**Toggle Emergency Mode**
- Via API: POST /api/emergency
- Via config file: Edit config.json emergency section
- Immediate effect (no restart required)

---

### System Features (Automated)

#### 1. Slot Management
- Automatic slot generation based on working hours
- Respects break times
- Prevents double booking (database constraint)
- Soft-lock during payment (10-15 minutes)
- Expired locks automatically released
- Same-day slots exclude past times

#### 2. Payment Processing
- Razorpay payment link generation
- UPI QR code for mobile payments
- Multiple payment methods (UPI, cards, wallets, net banking)
- Webhook processing for real-time updates
- Automatic status transition: PENDING_PAYMENT → CONFIRMED
- Idempotent webhook handling (prevents duplicates)

#### 3. Refund Processing
- Automatic refund initiation on cancellation
- Exponential backoff retry (60s, 120s, 240s, 480s, 960s)
- Max 5 retry attempts
- Failed refunds visible on dashboard
- Manual retry capability
- Refund webhook confirms completion

#### 4. Calendar Synchronization
- Automatic Google Calendar event creation
- Meet link generation for online consultations
- Event updates on status changes
- Event deletion on cancellation
- Nightly reconciliation job:
  - Checks for calendar drift
  - Retries failed operations
  - Cleans up orphaned events
  - Limited to 20 retries per run

#### 5. Conversation Management
- 30-minute session expiry
- One active conversation per phone
- State-based routing (language → menu → booking → details)
- Automatic cleanup of expired conversations
- Returns to main menu after timeout

#### 6. Internationalization
- 3 languages: English, Telugu, Hindi
- All messages localized
- Template substitution for dynamic data
- Consistent across bot and dashboard

#### 7. Data Integrity
- UTC storage, IST display for timezone handling
- State machine for appointment status
- Idempotency framework prevents duplicate operations
- Event ID tracking across WhatsApp, Razorpay webhooks
- Transaction safety for critical operations

#### 8. Security
- Google OAuth authentication
- CSRF protection for all mutations
- Session management with secure cookies
- Secure token-based prescription downloads
- PII protection in logs (no patient names/phones)
- Phone number masking in dashboard (last 4 digits only)
- Time-limited prescription URLs (72 hours)

#### 9. Monitoring & Logging
- Structured JSON logging
- Request ID correlation
- Health check endpoints (/health, /ready)
- Alert system for critical failures
- Database integrity checks

---

## Testing

### Run All Tests

```bash
# All tests
uv run pytest tests/ -v

# Specific test files
uv run pytest tests/test_reminder_service.py -v
uv run pytest tests/test_prescription_service.py -v

# E2E tests only
uv run pytest tests/test_e2e_booking.py tests/test_e2e_payment.py tests/test_e2e_prescription.py -v

# With coverage
uv add --dev pytest-cov
uv run pytest tests/ --cov=src/docbot --cov-report=html
# Open htmlcov/index.html
```

### Test Counts
- **Total:** 185+ tests
- **E2E Tests:** 19 (booking, payment, prescription flows)
- **Unit Tests:** 166+ (services, models, utilities)
- **Coverage:** >80% on critical paths

---

## Production Deployment

### Using Docker Compose

1. **Build Images**
   ```bash
   docker-compose build
   ```

2. **Run Production**
   ```bash
   docker-compose --profile prod up -d
   ```

3. **View Logs**
   ```bash
   docker-compose logs -f app
   ```

4. **Stop Services**
   ```bash
   docker-compose down
   ```

### Using Cloudflare Tunnel (Recommended)

1. **Install cloudflared**
   ```bash
   # Ubuntu
   wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
   sudo dpkg -i cloudflared-linux-amd64.deb
   ```

2. **Authenticate**
   ```bash
   cloudflared tunnel login
   ```

3. **Create Tunnel**
   ```bash
   cloudflared tunnel create docbot
   # Note the tunnel ID
   ```

4. **Configure DNS**
   ```bash
   cloudflared tunnel route dns docbot docbot.yourdomain.com
   ```

5. **Create Config File** (`~/.cloudflared/config.yml`)
   ```yaml
   tunnel: YOUR_TUNNEL_ID
   credentials-file: /root/.cloudflared/YOUR_TUNNEL_ID.json

   ingress:
     - hostname: docbot.yourdomain.com
       service: http://localhost:8000
     - service: http_status:404
   ```

6. **Run Tunnel**
   ```bash
   cloudflared tunnel run docbot
   ```

7. **Install as System Service**
   ```bash
   sudo cloudflared service install
   sudo systemctl start cloudflared
   sudo systemctl enable cloudflared
   ```

### Manual Deployment (Ubuntu Server)

1. **Install Dependencies**
   ```bash
   sudo apt update
   sudo apt install python3.12 python3-pip nginx
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Clone and Configure**
   ```bash
   cd /opt
   sudo git clone https://github.com/yourusername/docbot.git
   cd docbot
   uv sync
   cp config.test.json config.prod.json
   # Edit config.prod.json with production values
   ```

3. **Create Systemd Service** (`/etc/systemd/system/docbot.service`)
   ```ini
   [Unit]
   Description=DocBot Appointment System
   After=network.target

   [Service]
   Type=simple
   User=www-data
   WorkingDirectory=/opt/docbot
   Environment="DOCBOT_ENV=prod"
   ExecStart=/root/.local/bin/uv run uvicorn src.docbot.main:app --host 0.0.0.0 --port 8000 --workers 2
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

4. **Start Service**
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl start docbot
   sudo systemctl enable docbot
   ```

5. **Configure Nginx** (`/etc/nginx/sites-available/docbot`)
   ```nginx
   server {
       listen 80;
       server_name docbot.yourdomain.com;

       location / {
           proxy_pass http://localhost:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```

6. **Enable Site**
   ```bash
   sudo ln -s /etc/nginx/sites-available/docbot /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl restart nginx
   ```

---

## Cron Jobs Setup

### 1. Reminder Jobs

Send automated appointment reminders.

```bash
# Edit crontab
crontab -e

# Add these lines:

# 24-hour reminders (run every hour)
0 * * * * cd /opt/docbot && /root/.local/bin/uv run python scripts/run_reminders.py 24h >> /var/log/docbot/reminders-24h.log 2>&1

# 1-hour reminders (run every 15 minutes)
*/15 * * * * cd /opt/docbot && /root/.local/bin/uv run python scripts/run_reminders.py 1h >> /var/log/docbot/reminders-1h.log 2>&1
```

### 2. Reconciliation Job

Nightly calendar drift detection and cleanup.

```bash
# Add to crontab:

# Reconciliation (run at 2 AM daily)
0 2 * * * cd /opt/docbot && /root/.local/bin/uv run python scripts/run_reconciliation.py >> /var/log/docbot/reconciliation.log 2>&1
```

### 3. Create Log Directory

```bash
sudo mkdir -p /var/log/docbot
sudo chown www-data:www-data /var/log/docbot
```

### 4. Verify Cron Jobs

```bash
# Check crontab
crontab -l

# Test reminder script manually
cd /opt/docbot
uv run python scripts/run_reminders.py 24h

# Check logs
tail -f /var/log/docbot/reminders-24h.log
```

---

## Troubleshooting

### Common Issues

#### 1. WhatsApp Messages Not Sending

**Problem:** Bot doesn't respond to messages

**Solutions:**
- Check webhook is configured correctly in Meta dashboard
- Verify `phone_number_id` and `access_token` in config
- Check logs: `grep "whatsapp" /var/log/docbot/app.log`
- Test webhook manually: Send test message from Meta dashboard
- Verify webhook URL is accessible from internet

#### 2. Payment Link Not Generated

**Problem:** Patient doesn't receive payment link

**Solutions:**
- Verify Razorpay `key_id` and `key_secret` are correct
- Check if KYC is approved (required for live mode)
- Use test mode keys for testing
- Check logs: `grep "razorpay" /var/log/docbot/app.log`
- Verify phone number format (should not have +91 prefix for Razorpay)

#### 3. Calendar Events Not Created

**Problem:** Appointments don't show in Google Calendar

**Solutions:**
- Verify `credentials.json` exists in project root
- Run authentication: `python -c "from docbot.calendar_service import authenticate_calendar; authenticate_calendar()"`
- Check `token.json` was created
- Verify `calendar_id` in config
- Check calendar API is enabled in Google Cloud Console
- Check logs: `grep "calendar" /var/log/docbot/app.log`

#### 4. Dashboard Login Fails

**Problem:** Cannot log in to dashboard

**Solutions:**
- Check `secret_key` is set in config
- Clear browser cookies
- Try incognito mode
- Check logs: `grep "auth" /var/log/docbot/app.log`
- Verify `/auth/google/login` endpoint returns redirect

#### 5. Database Locked Errors

**Problem:** `database is locked` errors in logs

**Solutions:**
- SQLite doesn't handle high concurrency well
- Increase timeout: `pragma busy_timeout=30000`
- For high traffic, consider PostgreSQL migration
- Check for long-running queries
- Restart application

#### 6. Reminders Not Sending

**Problem:** Automated reminders not working

**Solutions:**
- Check cron jobs are set up: `crontab -l`
- Verify cron logs: `tail -f /var/log/docbot/reminders-24h.log`
- Test script manually: `uv run python scripts/run_reminders.py 24h`
- Check reminder_sent_24h/1h columns in database
- Verify WhatsApp API is working

#### 7. Prescription PDF Not Generating

**Problem:** Prescription creation fails

**Solutions:**
- Check `xhtml2pdf` is installed: `pip list | grep xhtml2pdf`
- Verify signature image exists at configured path
- Check prescriptions/ directory is writable
- Check logs: `grep "prescription" /var/log/docbot/app.log`
- Test PDF generation manually in Python console

#### 8. Frontend Not Loading

**Problem:** Dashboard shows blank page

**Solutions:**
- Build frontend: `cd frontend && npm run build`
- Check frontend/dist/ directory exists
- Verify FastAPI serves static files
- Check browser console for errors (F12)
- Try accessing API directly: http://localhost:8000/docs

### Debug Mode

Enable detailed logging:

```python
# In src/docbot/logging_config.py
setup_logging("DEBUG")  # Change from "INFO"
```

### Check Logs

```bash
# Application logs
tail -f /var/log/docbot/app.log

# Systemd logs
sudo journalctl -u docbot -f

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Database Inspection

```bash
# Open database
sqlite3 docbot.db

# Check appointments
SELECT * FROM appointments ORDER BY created_at DESC LIMIT 10;

# Check prescriptions
SELECT * FROM prescriptions;

# Check slot locks
SELECT * FROM slot_locks WHERE expires_at > datetime('now');
```

---

## Quick Reference

### Important URLs

- **Dashboard:** https://docbot.yourdomain.com/dashboard
- **Health Check:** https://docbot.yourdomain.com/health
- **API Docs:** https://docbot.yourdomain.com/docs
- **WhatsApp Webhook:** https://docbot.yourdomain.com/webhook/whatsapp
- **Razorpay Webhook:** https://docbot.yourdomain.com/webhook/razorpay

### Important Files

- **Configuration:** `config.prod.json`
- **Database:** `docbot.db`
- **Google Credentials:** `credentials.json`, `token.json`
- **Doctor Signature:** `doctor_signature.png`
- **Logs:** `/var/log/docbot/`
- **Prescriptions:** `prescriptions/` (runtime PDFs)

### Important Commands

```bash
# Start application
uv run uvicorn src.docbot.main:app --host 0.0.0.0 --port 8000

# Run tests
uv run pytest tests/ -v

# Run reminders
uv run python scripts/run_reminders.py 24h
uv run python scripts/run_reminders.py 1h

# Run reconciliation
uv run python scripts/run_reconciliation.py

# Build frontend
cd frontend && npm run build

# Check database
sqlite3 docbot.db

# View logs
tail -f /var/log/docbot/app.log
```

---

## Support & Documentation

- **GitHub Issues:** https://github.com/yourusername/docbot/issues
- **Setup Guides:** See `*-USER-SETUP.md` files in project root
- **Test Scenarios:** `.planning/phases/05-automation-and-launch/05-TEST-SCENARIOS.md`
- **Architecture:** `.planning/PROJECT.md`
- **API Documentation:** http://localhost:8000/docs (when running)

---

**Last Updated:** 2026-02-07
**Version:** Phase 5 Complete (All features implemented)
