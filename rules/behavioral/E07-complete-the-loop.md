---
rule: E07
name: Complete the Loop
hook: complete-the-loop-guard.sh
trigger: After sending any SMS or email
---

## Rule

After sending an SMS or email, ALWAYS run the inbox monitor to check for replies. Sending without monitoring is an incomplete action — the loop is not closed until you've verified the response channel is being watched.

## Why it exists

Outreach was sent and replies sat unread because the inbox monitor wasn't triggered. Prospects responded and got no follow-up, burning the lead.

## How to apply

**After SMS send:**
```bash
python execution/twilio_sms.py --send ...   # send
python execution/twilio_sms.py --monitor    # then immediately monitor
```

**After email send:**
```bash
python execution/send_onboarding_email.py ...  # send
# then check Gmail via MCP or inbox monitor
```

**For campaigns:**
After any batch send (10+ messages), set up n8n reply monitoring workflow before considering the campaign "sent."

The hook will warn if a send command is detected without a subsequent monitor command in the same session.

## Examples

- Send cold outreach SMS to 5 leads → immediately check for auto-replies and responses
- Send proposal email to HVAC client → monitor inbox for 24h via n8n, not just "it was sent"
- Run SMS drip campaign → ensure n8n reply handler is active before triggering the drip
