# Phase 02: User Setup Required

**Generated:** 2026-02-06
**Phase:** 02-whatsapp-bot-booking-flow
**Status:** Incomplete

---

## Overview

This phase introduces WhatsApp Cloud API integration for patient communication. You need to configure Meta WhatsApp Business API credentials and webhook settings.

---

## Environment Variables

| Status | Variable | Source | Add to |
|--------|----------|--------|--------|
| [ ] | `whatsapp.phone_number_id` | Meta Business Suite → WhatsApp → API Setup → Phone number ID | `config.prod.json` |
| [ ] | `whatsapp.access_token` | Meta Business Suite → WhatsApp → API Setup → Temporary/Permanent access token | `config.prod.json` |
| [ ] | `whatsapp.verify_token` | Self-generated string used for webhook verification handshake | `config.prod.json` |

**Example config.prod.json section:**

```json
{
  "whatsapp": {
    "phone_number_id": "your_phone_number_id_here",
    "access_token": "your_access_token_here",
    "verify_token": "your_self_generated_verify_token_here",
    "api_version": "v21.0"
  }
}
```

**Note on verify_token:** This is a string you create yourself (e.g., a random UUID or passphrase). It's used during the webhook verification handshake with Meta. Store it securely and use the same value when configuring the webhook in Meta Business Suite.

---

## Dashboard Configuration

### 1. Create Meta Business App with WhatsApp product

- **Location:** developers.facebook.com → My Apps → Create App → Business → WhatsApp
- **Steps:**
  1. Go to https://developers.facebook.com/apps
  2. Click "Create App"
  3. Select "Business" as app type
  4. Add "WhatsApp" as a product
  5. Complete app setup wizard
  6. Note your App ID and App Secret

### 2. Configure webhook URL pointing to /webhook/whatsapp

- **Location:** Meta Business Suite → WhatsApp → Configuration → Webhook
- **Steps:**
  1. In your WhatsApp Business API settings, find "Webhooks"
  2. Click "Edit" or "Configure"
  3. Enter callback URL: `https://your-domain.com/webhook/whatsapp`
     - Replace `your-domain.com` with your actual production domain
     - Must use HTTPS (required by Meta)
  4. Enter verify token: The same value you set in `config.prod.json` as `whatsapp.verify_token`
  5. Click "Verify and Save"
  6. Meta will send a GET request to verify the webhook

**Important:** Your webhook endpoint must be accessible over the internet and use HTTPS. For local development, you can use tools like ngrok or Cloudflare Tunnel.

### 3. Subscribe to 'messages' webhook field

- **Location:** Meta Business Suite → WhatsApp → Configuration → Webhook fields
- **Steps:**
  1. After webhook is verified, find "Webhook fields" section
  2. Subscribe to the following field:
     - [x] messages (required for receiving patient messages)
  3. Save configuration

---

## Verification

Once all configuration is complete, verify the integration works:

### 1. Check webhook verification

```bash
# Meta should have verified your webhook during configuration
# Check your application logs for:
# "WhatsApp webhook verified successfully"
```

### 2. Test message sending (requires valid credentials)

```bash
# From your application server, test sending a message
uv run python -c "
from docbot.whatsapp_client import send_text
import asyncio

async def test():
    result = await send_text('+919876543210', 'Test message from DocBot')
    print(f'Result: {result}')

asyncio.run(test())
"
```

### 3. Test message receiving

1. Send a WhatsApp message to your configured business phone number
2. Check application logs for:
   - "WhatsApp message received"
   - Message should be logged with sender phone and content

---

## Local Development

For local testing without exposing your development server to the internet:

1. **Use ngrok or Cloudflare Tunnel:**

```bash
# Using ngrok
ngrok http 8000

# Or using Cloudflare Tunnel (cloudflared)
cloudflared tunnel --url http://localhost:8000
```

2. **Update webhook URL in Meta Business Suite** with the temporary public URL (e.g., `https://abc123.ngrok.io/webhook/whatsapp`)

3. **Remember to update back to production URL** when done testing

**Note:** Meta requires HTTPS for webhooks, so you cannot use `http://localhost:8000` directly.

---

## Troubleshooting

### Webhook verification fails

- Verify that `whatsapp.verify_token` in your config matches the token you entered in Meta Business Suite
- Check that your webhook endpoint is accessible over HTTPS
- Review application logs for any errors during the GET request

### Messages not being received

- Confirm "messages" webhook field is subscribed in Meta Business Suite
- Check that your webhook endpoint returns 200 status (even on errors)
- Verify idempotency table is working (duplicate messages should be ignored)

### Message sending fails

- Confirm `whatsapp.phone_number_id` and `whatsapp.access_token` are correct
- Check that the access token has not expired (use permanent token for production)
- Review application logs for error details and retry attempts

---

**Once all items complete:** Mark status at top as "Complete"
