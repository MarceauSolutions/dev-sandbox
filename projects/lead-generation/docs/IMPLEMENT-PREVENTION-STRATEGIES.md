# Implementation Guide: Follow-Up Automation Prevention Strategies

**Quick Start**: Implement these 3 strategies in 1 hour to prevent future failures

---

## Strategy 1: Dead Man's Switch (15 minutes) ⭐⭐⭐⭐⭐

### Step 1: Add heartbeat recording to follow_up_sequence.py

```python
# Add this function after get_sequence_stats()

def record_heartbeat(self, stats: Dict[str, Any]) -> None:
    """Record successful run for health monitoring."""
    heartbeat_file = self.output_dir / "followup_heartbeat.json"
    data = {
        "last_run": datetime.now().isoformat(),
        "leads_processed": stats["processed"],
        "messages_sent": stats["sent"],
        "total_due": stats["total_due"],
        "errors": len(stats.get("errors", []))
    }
    with open(heartbeat_file, 'w') as f:
        json.dump(data, f, indent=2)
    logger.info(f"Heartbeat recorded: {stats['sent']} sent, {stats['total_due']} due")
```

### Step 2: Call it in main() after processing

Find this section in main():
```python
if args.command == "process":
    # ... existing code ...
    stats = manager.process_due_touchpoints(
        leads_collection=collection,
        dry_run=dry_run,
        limit=args.limit
    )

    # ADD THIS LINE
    manager.record_heartbeat(stats)

    print("\n=== Processing Results ===")
    # ... rest of output ...
```

### Step 3: Create health check script

Create `src/check_followup_health.py`:

```python
#!/usr/bin/env python3
"""
Health check for follow-up automation.
Alerts if system hasn't run in 25+ hours.
"""
import json
import logging
from pathlib import Path
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def send_alert(message: str) -> None:
    """Send alert via logging and/or SMS."""
    logger.error(message)

    # TODO: Add SMS alert via Twilio
    # from twilio.rest import Client
    # client = Client(account_sid, auth_token)
    # client.messages.create(
    #     to="+1XXXXXXXXXX",  # William's phone
    #     from_="+18552399364",
    #     body=message
    # )


def check_health() -> None:
    """Check follow-up system health."""
    heartbeat_file = Path(__file__).parent.parent / "output" / "followup_heartbeat.json"

    if not heartbeat_file.exists():
        send_alert("❌ ALERT: Follow-up system has never run! (no heartbeat file)")
        return

    with open(heartbeat_file, 'r') as f:
        data = json.load(f)

    last_run = datetime.fromisoformat(data["last_run"])
    hours_since = (datetime.now() - last_run).total_seconds() / 3600

    if hours_since > 25:  # Should run daily at 9 AM
        send_alert(
            f"⚠️ ALERT: Follow-up system hasn't run in {hours_since:.1f} hours!\n"
            f"Last run: {last_run.strftime('%Y-%m-%d %H:%M')}\n"
            f"Expected: Daily at 9 AM"
        )
    else:
        logger.info(f"✅ Follow-up system healthy (last run {hours_since:.1f}h ago)")


if __name__ == "__main__":
    check_health()
```

### Step 4: Add health check to crontab

```bash
# Edit crontab
crontab -e

# Add this line (runs at 10 AM, 1 hour after expected 9 AM run)
0 10 * * * cd /Users/williammarceaujr./dev-sandbox/projects/shared/lead-scraper && /opt/anaconda3/bin/python -m src.check_followup_health >> /Users/williammarceaujr./dev-sandbox/projects/shared/lead-scraper/output/health_check.log 2>&1
```

### Test It

```bash
# 1. Run follow-up processor manually
cd /Users/williammarceaujr./dev-sandbox/projects/shared/lead-scraper
python -m src.follow_up_sequence process --for-real

# 2. Check heartbeat was created
cat output/followup_heartbeat.json
# Should show current timestamp

# 3. Test health check
python -m src.check_followup_health
# Should show: ✅ Follow-up system healthy

# 4. Test alert (simulate old heartbeat)
# Edit followup_heartbeat.json, change last_run to 2 days ago
python -m src.check_followup_health
# Should show: ⚠️ ALERT: Follow-up system hasn't run in 48 hours
```

---

## Strategy 2: Multiple Daily Runs (5 minutes) ⭐⭐⭐⭐

### Update crontab to run 3x daily

```bash
crontab -e

# REPLACE the single 9 AM job:
# 0 9 * * * cd /Users/williammarceaujr./dev-sandbox/projects/lead-scraper && ...

# WITH 3 jobs (9 AM, 1 PM, 5 PM):
0 9 * * * cd /Users/williammarceaujr./dev-sandbox/projects/shared/lead-scraper && /opt/anaconda3/bin/python -m src.follow_up_sequence process --for-real >> /Users/williammarceaujr./dev-sandbox/projects/shared/lead-scraper/output/followup.log 2>&1

0 13 * * * cd /Users/williammarceaujr./dev-sandbox/projects/shared/lead-scraper && /opt/anaconda3/bin/python -m src.follow_up_sequence process --for-real >> /Users/williammarceaujr./dev-sandbox/projects/shared/lead-scraper/output/followup.log 2>&1

0 17 * * * cd /Users/williammarceaujr./dev-sandbox/projects/shared/lead-scraper && /opt/anaconda3/bin/python -m src.follow_up_sequence process --for-real >> /Users/williammarceaujr./dev-sandbox/projects/shared/lead-scraper/output/followup.log 2>&1
```

### Why This Works

The code already prevents duplicate sends:
- `get_due_touchpoints()` only returns touchpoints with `status == "pending"`
- Once sent, status changes to `"sent"`
- Safe to run multiple times per day

### Benefits

- **3x redundancy**: If 9 AM fails, 1 PM catches it
- **Faster recovery**: Max 4-hour delay vs 24-hour
- **Same code**: No changes needed to Python code

---

## Strategy 3: Logging Improvements (10 minutes) ⭐⭐⭐

### Update process_due_touchpoints() logging

Find this function in `src/follow_up_sequence.py`:

```python
def process_due_touchpoints(
    self,
    leads_collection: LeadCollection,
    dry_run: bool = True,
    limit: int = 100,
    delay_seconds: float = 2.0
) -> Dict[str, Any]:
    """Process all due touchpoints across all sequences."""
    import time

    stats = {
        "total_due": 0,
        "processed": 0,
        "sent": 0,
        "errors": [],
        "by_touch_number": {}
    }

    due_touchpoints = self.get_due_touchpoints()
    stats["total_due"] = len(due_touchpoints)

    # ADD THIS BLOCK
    if len(due_touchpoints) == 0:
        logger.info("✅ No touchpoints due - all sequences on schedule")
        logger.info(f"   Total sequences: {len(self.sequences)}")
        logger.info(f"   In sequence: {sum(1 for s in self.sequences.values() if s.status == 'in_sequence')}")
        return stats

    # ADD THIS LINE
    logger.info(f"📤 Processing {len(due_touchpoints)} due touchpoints...")

    # Rest of function continues as normal...
```

### Benefits

- Distinguishes "no messages due" from "cron didn't run"
- Log entry every time cron runs (even if 0 sent)
- Easier to debug in retrospect

### Test It

```bash
# Run when no messages are due
python -m src.follow_up_sequence process --for-real

# Check log shows the new message
tail -20 output/followup.log
# Should show: ✅ No touchpoints due - all sequences on schedule
```

---

## Quick Verification Checklist

After implementing all 3 strategies:

### ✅ Strategy 1: Dead Man's Switch
- [ ] `record_heartbeat()` added to follow_up_sequence.py
- [ ] Called in main() after processing
- [ ] `src/check_followup_health.py` created
- [ ] Health check added to crontab (runs at 10 AM)
- [ ] Tested manually (shows ✅ healthy)

### ✅ Strategy 2: Multiple Runs
- [ ] Crontab has 3 entries (9 AM, 1 PM, 5 PM)
- [ ] All 3 point to same script
- [ ] Tested: running twice doesn't duplicate sends

### ✅ Strategy 3: Logging
- [ ] "No touchpoints due" message added
- [ ] "Processing N touchpoints" message added
- [ ] Log shows entries even when 0 sent

---

## Testing the Complete System

### Day 1: Verify All Runs Execute

```bash
# Check log shows 3 daily runs
$ grep "^2026-01-22" output/followup.log | grep -E "Processing|No touchpoints"
2026-01-22 09:00:00 - 📤 Processing 15 due touchpoints...
2026-01-22 13:00:00 - ✅ No touchpoints due - all sequences on schedule
2026-01-22 17:00:00 - ✅ No touchpoints due - all sequences on schedule
```

### Day 2: Verify Health Check Works

```bash
# Check health check ran at 10 AM
$ tail -5 output/health_check.log
2026-01-22 10:00:00 - INFO - ✅ Follow-up system healthy (last run 1.0h ago)
```

### Day 3: Simulate Failure (Test Alert)

```bash
# 1. Comment out all 3 cron jobs temporarily
crontab -e

# 2. Wait 25 hours

# 3. Check health check log
$ tail -5 output/health_check.log
2026-01-23 10:00:00 - ERROR - ⚠️ ALERT: Follow-up system hasn't run in 25.1 hours!

# 4. Re-enable cron jobs
crontab -e
```

---

## Time Investment

- **Strategy 1** (Dead Man's Switch): 15 minutes
- **Strategy 2** (Multiple Runs): 5 minutes
- **Strategy 3** (Logging): 10 minutes
- **Testing**: 10 minutes

**Total**: ~40 minutes

**ROI**: Prevents 5-day silent failures worth $500-2000 in lost responses

---

## Optional: Add SMS Alerts to Health Check

If you want SMS alerts when the system fails:

```python
# In src/check_followup_health.py, update send_alert():

def send_alert(message: str) -> None:
    """Send alert via logging and SMS."""
    logger.error(message)

    # Add Twilio SMS
    import os
    from twilio.rest import Client

    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")

    if account_sid and auth_token:
        client = Client(account_sid, auth_token)
        client.messages.create(
            to="+1XXXXXXXXXX",  # William's phone
            from_="+18552399364",  # Your Twilio number
            body=message[:160]  # Truncate to SMS limit
        )
        logger.info("SMS alert sent")
```

**When to Add**: If you're not checking logs daily, add SMS alerts

---

## Next Steps (Optional - Week 2+)

### Strategy 4: Status Dashboard
- Create `output/followup_dashboard.json` with summary stats
- Update after each run
- Check anytime with `cat output/followup_dashboard.json`

### Strategy 5: Morning Digest Integration
- Add follow-up status to `projects/personal-assistant/src/morning_digest.py`
- Shows in daily email: "✅ 87 follow-ups scheduled today"

---

**Ready to Implement**: Follow Steps 1-3 above, should take ~40 minutes total
