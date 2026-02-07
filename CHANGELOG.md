# DocBot Changelog

## [2026-02-07] - Landing Page & OAuth Updates

### Changed
- **Public Landing Page**: Created a new public showcase landing page that doesn't require authentication
  - Displays all key features (WhatsApp integration, payments, scheduling, reminders, prescriptions, multi-language)
  - Shows "How It Works" section with step-by-step guide
  - Professional design with gradient header and feature cards
  - Provides clear call-to-action to access the dashboard

- **OAuth Requirement**: OAuth authentication is now only required for the doctor dashboard
  - Root URL (`/`) now serves public landing page (no auth required)
  - Dashboard URL (`/dashboard`) shows login page if not authenticated
  - Login page updated to clarify it's for the "Doctor Dashboard"
  - Added "Back to home" link on login page

### Files Modified
- `src/docbot/main.py`:
  - Updated `/` route to serve public landing page
  - Updated `/dashboard` route to show login page instead of redirecting

- `src/docbot/templates/landing.html`: **NEW**
  - Full-featured public landing page
  - Responsive design
  - Feature showcase
  - How It Works section

- `src/docbot/templates/login.html`:
  - Updated title to "Doctor Dashboard"
  - Added descriptive text
  - Added back to home link

### Deployment
- Container rebuilt and deployed to production
- Database reset (fresh schema applied)
- All services running healthy

### Testing
- ✅ Root page (`/`) shows public landing page
- ✅ Dashboard page (`/dashboard`) shows login page when not authenticated
- ✅ Container health check passing
- ✅ Accessible through Traefik at `docbot.kanapa.space`

### Impact
- **Before**: Landing page immediately required Google OAuth authentication
- **After**: Public can view the service showcase without authentication; OAuth only required for doctor dashboard access

---

## Deployment History

### Initial Deployment - 2026-02-07
- Set up Docker containerization with multi-stage build
- Fixed build issues:
  - Added source code to builder stage
  - Resolved README.md .dockerignore conflict
  - Added build dependencies for pycairo (PDF generation)
- Configured Traefik routing
- Set up Cloudflare Tunnel integration
- Deployed to `docbot.kanapa.space`
