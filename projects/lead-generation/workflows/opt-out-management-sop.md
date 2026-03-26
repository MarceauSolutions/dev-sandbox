# Workflow: Opt-Out Management SOP

## Overview

This workflow covers how to manage opt-outs for SMS and email campaigns in the lead-scraper project. The opt-out system ensures compliance with TCPA (SMS) and CAN-SPAM (email) regulations.

## Key Files

- **Source code**: `src/opt_out_manager.py`
- **Opt-out list**: `output/opt_out_list.json`
- **SMS replies**: `output/sms_replies.json`
- **Campaign records**: `output/sms_campaigns.json`

## Use Cases

### 1. Check If a Contact Is Opted Out (Before Sending)

```bash
# Check by phone
python -m src.opt_out_manager check --phone "+12395551234"

# Check by email
python -m src.opt_out_manager check --email "test@example.com"
```

**Programmatic check:**
```python
from src.opt_out_manager import OptOutManager, check_before_send

# Quick helper function
if check_before_send(phone="+12395551234"):
    # OK to send
    pass
else:
    # Do not send - opted out
    pass

# Or use the manager directly
manager = OptOutManager(output_dir="output")
if not manager.is_opted_out(phone="+12395551234"):
    # OK to send
    pass
```

### 2. Manually Add an Opt-Out

```bash
# Add phone
python -m src.opt_out_manager add --phone "+12395551234" --reason sms_stop --business "Gym Name"

# Add email
python -m src.opt_out_manager add --email "test@example.com" --reason email_unsubscribe
```

**Available reasons:**
- `sms_stop` - SMS STOP keyword
- `sms_unsubscribe` - SMS unsubscribe request
- `email_bounce` - Hard email bounce
- `email_unsubscribe` - Email unsubscribe link clicked
- `email_complaint` - Marked as spam
- `manual` - Manually added
- `dnc_list` - Do Not Call list
- `legal_request` - Legal/compliance request
- `invalid_number` - Invalid phone number
- `invalid_email` - Invalid email address

### 3. Import Opt-Outs from SMS Replies

After running the Twilio webhook or fetching replies, import all opt-outs:

```bash
# Import all opt-out categorized replies into the opt-out list
python -m src.opt_out_manager import-replies
```

### 4. Sync Opt-Outs to Campaign Records

Update `sms_campaigns.json` to mark all opted-out contacts:

```bash
python -m src.opt_out_manager sync-campaigns
```

### 5. View Statistics

```bash
python -m src.opt_out_manager stats
```

Output:
```
=== Opt-Out Statistics ===
  Total opt-outs: 13
  Active opt-outs: 13

  By Type:
    phone: 13
    email: 0

  By Reason:
    sms_stop: 13
```

### 6. List All Opted-Out Contacts

```bash
# All contacts
python -m src.opt_out_manager list

# Phones only
python -m src.opt_out_manager list --type phone

# Emails only
python -m src.opt_out_manager list --type email
```

### 7. Export Opt-Out List

```bash
# Export to CSV
python -m src.opt_out_manager export --format csv

# Export to JSON (stdout)
python -m src.opt_out_manager export --format json
```

### 8. Remove Opt-Out (Re-subscribe)

Only do this if the contact explicitly requests to re-subscribe:

```bash
python -m src.opt_out_manager remove --phone "+12395551234"
```

## Detected Opt-Out Phrases

The system automatically detects these phrases (case-insensitive):

**Stop keywords:**
- STOP, stop, Stop
- END, QUIT

**Unsubscribe phrases:**
- unsubscribe
- remove me, remove
- opt out, opt-out
- cancel
- no thanks
- not interested
- don't contact, do not contact
- stop texting, stop messaging, stop sending
- leave me alone
- take me off
- delete my number

**Invalid number:**
- wrong number

## Integration with SMS Outreach

The `sms_outreach.py` module automatically checks the opt-out list before sending:

```python
from src.sms_outreach import SMSOutreachManager
from src.models import LeadCollection

# Load leads
collection = LeadCollection(output_dir="output")
collection.load_json()

# Initialize manager (automatically loads opt-out list)
manager = SMSOutreachManager(output_dir="output")

# Run campaign - opted-out contacts are automatically skipped
stats = manager.run_campaign(
    leads=list(collection.leads.values()),
    dry_run=True
)

print(f"Skipped (opted out): {stats['skipped_opted_out']}")
```

## Integration with Twilio Webhook

The `twilio_webhook.py` automatically adds opt-outs when processing replies:

```python
from src.twilio_webhook import TwilioWebhookHandler

handler = TwilioWebhookHandler(output_dir="output")

# Process incoming SMS (automatically handles opt-outs)
result = handler.process_reply(
    from_phone="+12395551234",
    to_phone="+18555551234",
    body="STOP"
)

print(result["category"])  # "opt_out"
print(result["actions_taken"])  # ["added_to_optout_list", "logged_to_tracking"]
```

## Daily Maintenance Routine

1. **Morning**: Import any new opt-outs from overnight replies
   ```bash
   python -m src.opt_out_manager import-replies
   ```

2. **Before campaigns**: Sync opt-outs to campaign records
   ```bash
   python -m src.opt_out_manager sync-campaigns
   ```

3. **Weekly**: Export opt-out list for compliance records
   ```bash
   python -m src.opt_out_manager export --format csv
   ```

## Compliance Notes

- **TCPA Compliance**: All SMS opt-outs must be honored immediately
- **CAN-SPAM Compliance**: Email unsubscribes must be processed within 10 days (we do it immediately)
- **Record Keeping**: The opt-out list includes timestamps and reasons for audit purposes
- **Normalization**: Phone numbers are normalized for consistent matching (e.g., `+1 (239) 555-1234` matches `12395551234`)

## Troubleshooting

### Opt-out not being detected

Check if the message contains a detected phrase:

```python
from src.opt_out_manager import detect_opt_out

result = detect_opt_out("Please stop texting me")
print(result)  # (True, OptOutReason.SMS_STOP, 'stop')
```

### Phone format mismatch

All phone numbers are normalized to digits only (no +, spaces, or formatting). Both of these will match:
- `+1 (239) 555-1234`
- `12395551234`

### Campaign not skipping opted-out contacts

1. Ensure the opt-out manager is initialized:
   ```python
   manager = SMSOutreachManager(output_dir="output")
   print(manager.opt_out_manager.get_statistics())
   ```

2. Check if the specific number is in the list:
   ```bash
   python -m src.opt_out_manager check --phone "+12395551234"
   ```

## Success Criteria

- All SMS opt-outs are honored immediately
- Campaign statistics show `skipped_opted_out` count
- Opt-out list persists across sessions
- Normalized phone matching works across formats
