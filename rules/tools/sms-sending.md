# Tool: SMS Sending (Twilio)

**File:** `execution/twilio_sms.py`
**When to use:** Alerts, time-sensitive notifications, lead follow-ups, appointment reminders, outreach campaigns.

## Numbers

| Number | Type | Use For |
|--------|------|---------|
| +1 (855) 239-9364 | Toll-free, A2P registered | ALL outbound SMS — use this |
| +1 (239) 880-3365 | Local (inactive) | Do not use |

**Always use the toll-free number.** It is A2P registered, which means it can send to US numbers without carrier filtering. The local number is inactive.

## Environment Variables Required

```bash
TWILIO_ACCOUNT_SID=[in .env]
TWILIO_AUTH_TOKEN=[in .env]
TWILIO_FROM_NUMBER=+18552399364
```

## Exact Commands

```bash
# Send a single SMS
python execution/twilio_sms.py \
  --to "+12395551234" \
  --message "Hi, this is William from Marceau Solutions..."

# Check send status / monitor replies
python execution/twilio_sms.py --monitor

# List recent messages
python execution/twilio_sms.py --list
```

Check the actual script for current flags: `cat execution/twilio_sms.py | head -50`

## Complete the Loop (E07)

MANDATORY after any SMS send:
```bash
python execution/twilio_sms.py --monitor
```
Do not skip this. The hook will warn if a send is detected without monitoring.

## TCPA Compliance

For any marketing or outreach SMS:
- Only text numbers that have opted in or have a prior business relationship
- Include opt-out instruction: "Reply STOP to unsubscribe"
- Do not send between 9pm–8am local time (Naples FL = Eastern Time)
- For bulk campaigns: see `docs/sops/sop-18-sms-campaign.md`

## William's Personal Number

William's phone: +1 (239) 398-5676
Use for: alerts to William, health check failures, accountability reminders
