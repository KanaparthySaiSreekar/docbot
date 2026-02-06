# Phase 03: User Setup Required

**Generated:** 2026-02-06
**Phase:** 03-payments-calendar-integration
**Status:** Incomplete

This phase introduces Razorpay payment integration requiring manual account configuration.

## Service: Razorpay

**Purpose:** Payment processing for online consultations

### Environment Variables

Add these to your `config.prod.json` file:

| Status | Variable | Source | Value Type |
|--------|----------|--------|------------|
| [ ] | `razorpay.key_id` | Razorpay Dashboard → Settings → API Keys → Key ID | Test: `rzp_test_*`, Live: `rzp_live_*` |
| [ ] | `razorpay.key_secret` | Razorpay Dashboard → Settings → API Keys → Key Secret | Secret string |
| [ ] | `razorpay.webhook_secret` | Razorpay Dashboard → Settings → Webhooks → Secret | Auto-generated after webhook creation |

### Account Setup

- [ ] **Create Razorpay account**
  - Visit: https://razorpay.com/
  - Sign up for business account
  - Complete KYC verification for live mode

- [ ] **Generate API keys**
  - Location: Razorpay Dashboard → Settings → API Keys
  - Generate Test Mode keys first
  - Generate Live Mode keys after KYC approval

### Dashboard Configuration

- [ ] **Create webhook endpoint**
  - Location: Razorpay Dashboard → Settings → Webhooks → Add endpoint
  - URL: `{base_url}/webhook/razorpay` (replace {base_url} with your actual domain)
  - Events to subscribe:
    - `payment.captured` (required)
    - `refund.processed` (for future refund support)
  - Copy the webhook secret after creation

### Testing

**Test Mode:** Use Razorpay test cards to verify integration
- Test card: 4111 1111 1111 1111
- Any future expiry date
- Any CVV

**Verification commands:**

```bash
# 1. Check config loaded correctly
uv run python -c "from docbot.config import get_settings; s = get_settings(); print(f'Key ID: {s.razorpay.key_id[:12]}...')"

# 2. Test payment link creation (requires test database)
uv run pytest tests/test_razorpay_client.py tests/test_payment_service.py -v

# 3. Verify webhook signature validation works
uv run pytest tests/test_payment_service.py::test_process_payment_webhook_success -v
```

## Post-Setup Verification

Once all items are complete:

1. Mark status above as "Complete"
2. Test end-to-end payment flow:
   - Create online appointment via WhatsApp bot
   - Payment link generated and sent
   - Complete payment with test card
   - Webhook received and appointment status updated to CONFIRMED
3. Check logs for any Razorpay API errors

---
**Next:** Complete plan 03-02 (Google Calendar integration) which also requires user setup.
