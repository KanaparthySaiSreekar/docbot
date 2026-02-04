# Phase 1: Foundation - Context

**Gathered:** 2026-02-04
**Status:** Ready for planning

<domain>
## Phase Boundary

Production-ready infrastructure with doctor authentication, system configuration, and core data integrity framework. This phase establishes the technical foundation that all future phases depend on. WhatsApp bot functionality, booking flows, and payment processing belong in later phases.

</domain>

<decisions>
## Implementation Decisions

### Authentication & Sessions
- Landing page with "Sign in with Google" button (not immediate redirect to OAuth)
- Session never expires - doctor stays logged in indefinitely
- Open access - any Google account can log in (rely on Cloudflare tunnel obscurity)
- Friendly error page with retry button when OAuth fails

### Configuration Management
- Separate config files: `config.test.json` and `config.prod.json` (explicit files prevent environment mixing)
- App starts with warnings and defaults if config invalid (graceful degradation, not fail-fast)
- Secrets in config files, gitignored (simple approach - `config.prod.json` not committed)
- Complete configuration schema up front - include working hours, fees, messages, etc. even if unused in Phase 1

### Database Design Principles
- Manual SQL scripts for migrations (no migration framework)
- Status field approach for cancellations - CANCELLED state, no deletion (state machine via status transitions)
- Application logic enforces state machine (not database constraints)
- Aggressive indexing - index everything that could be queried (maximize read performance)

### Deployment & Operations
- Verbose logging at debug level (all operations, queries, state changes)
- Structured JSON logs (one JSON object per line for machine parsing)
- Separate `/health` (liveness) and `/ready` (readiness) endpoints
- Docker container deployment (containerized, isolated environment)

### Claude's Discretion
- Cloudflare tunnel configuration details
- Specific log fields and structure within JSON format
- Database connection pooling settings
- Docker image optimization and multi-stage build approach

</decisions>

<specifics>
## Specific Ideas

No specific requirements - open to standard approaches for implementation details.

</specifics>

<deferred>
## Deferred Ideas

None - discussion stayed within phase scope

</deferred>

---

*Phase: 01-foundation*
*Context gathered: 2026-02-04*
