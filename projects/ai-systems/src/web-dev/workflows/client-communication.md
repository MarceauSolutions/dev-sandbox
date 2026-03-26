# Web Dev Client Communication Workflow

## Channel Priority

1. **SMS** (Twilio toll-free) — Primary for quick updates, instructions, check-ins
2. **Email** (Gmail) — For invoices, contracts, detailed docs
3. **Phone call** — For discovery calls, complex issues, relationship building

## SMS Templates

All templates use prefix `webdev_` in `execution/twilio_sms.py`.

### Template Reference

| Template Name | When to Send | Content Summary |
|---------------|-------------|-----------------|
| `webdev_welcome` | After invoice paid | Welcome + timeline expectations |
| `webdev_site_live` | After first deploy | Site is live + link |
| `webdev_dns_instructions` | DNS setup needed | Link to visual guide |
| `webdev_dns_reminder` | 48h after instructions sent | Gentle reminder |
| `webdev_update_deployed` | After content update | What changed + link |
| `webdev_monthly_checkin` | Monthly | Check-in, any updates needed? |
| `webdev_subscription_advice` | When cost savings found | Recommendations to cancel unused services |

### Usage

```bash
# Send a template
python execution/twilio_sms.py --template webdev_welcome --to +1XXXXXXXXXX

# Check for replies
python execution/twilio_inbox_monitor.py check --hours 4
```

## Communication Cadence

| When | What | Channel | Automated? |
|------|------|---------|-----------|
| Day 0 | Welcome + timeline | SMS | Template |
| Day 1-3 | Design progress updates | SMS (manual) | No |
| Day 3 | First draft ready | SMS | Template |
| Day 5 | DNS setup instructions | SMS | Template |
| Day 5+48h | DNS reminder (if not done) | SMS | Template |
| Day 7 | Site live notification | SMS | Template |
| Monthly | Check-in | SMS | Template (candidate for n8n) |

## Rules

1. **Always use toll-free number** (+1 855 239 9364) for automated SMS
2. **Always monitor for replies** after sending — use `twilio_inbox_monitor.py`
3. **Never ask what client can't answer** — research first (WHOIS, DNS checks, etc.)
4. **Keep messages short** — clients are busy business owners
5. **Include links when helpful** — hosted on EC2 `/forms/` path
