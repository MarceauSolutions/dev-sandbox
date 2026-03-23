#!/usr/bin/env python3
"""
Follow-up sequence processor for cold email outreach.

Reads all outreach_tracking_*.json files from the output directory and sends
timed follow-up emails based on where each lead is in the sequence:

  - follow_up_count == 0, initial sent_at >= 3 days ago  → "still_looking"     (Day 3)
  - follow_up_count == 1, last_followup_at >= 4 days ago → "followup_checkin"  (Day 7)
  - follow_up_count == 2, last_followup_at >= 3 days ago → "breakup"           (Day 10)
  - follow_up_count >= 3 OR status in replied/opted_out/bounced → skip

Templates are pulled directly from cold_outreach.TEMPLATES to avoid duplication.

Usage:
    python process_followups.py              # live run
    python process_followups.py --dry-run    # preview without sending
"""

import argparse
import glob
import json
import logging
import os
import smtplib
import sys
import time
from datetime import datetime, timedelta, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from string import Template
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Bootstrap: find repo root and load .env before any other imports
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent          # .../lead-scraper/src/
OUTPUT_DIR = SCRIPT_DIR.parent / "output"             # .../lead-scraper/output/
REPO_ROOT  = SCRIPT_DIR.parent.parent.parent.parent   # dev-sandbox/

# Try dotenv; fall back gracefully if not installed
try:
    from dotenv import load_dotenv
    load_dotenv(REPO_ROOT / ".env")
except ImportError:
    pass  # env vars must be set externally

# Pull in TEMPLATES from cold_outreach (same package, no network/Apollo deps)
sys.path.insert(0, str(SCRIPT_DIR))
try:
    # Import only the TEMPLATES dict — avoids triggering Apollo/model imports
    from cold_outreach import TEMPLATES
except Exception as _e:
    # Fallback: define the three follow-up templates inline so the script
    # remains self-contained even if cold_outreach import fails.
    TEMPLATES = {
        "still_looking": {
            "subject": "Still looking to streamline things at $business_name?",
            "body": "Are you still looking to free up time at $business_name?\n\nWilliam\n",
        },
        "followup_checkin": {
            "subject": "Following up - $business_name",
            "body": (
                "Hi $first_name,\n\n"
                "Just following up on my last message. Totally understand if you're busy running $business_name.\n\n"
                "If there's ever something eating up your time that you think automation could help with, I'm around.\n\n"
                "No pressure either way.\n\n"
                "William\nMarceau Solutions\n"
            ),
        },
        "breakup": {
            "subject": "Closing the loop - $business_name",
            "body": (
                "Hi $first_name,\n\n"
                "I've reached out a few times about automation for $business_name, but haven't heard back.\n\n"
                "No worries at all - I know timing isn't always right.\n\n"
                "I'm going to stop reaching out, but if you ever want to chat about freeing up time at $business_name, "
                "just reply to this email.\n\n"
                "Wishing you the best!\n\n"
                "William\nMarceau Solutions\n"
            ),
        },
    }

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Skip statuses — never follow up on these
# ---------------------------------------------------------------------------
SKIP_STATUSES = {"replied", "opted_out", "bounced"}

# ---------------------------------------------------------------------------
# Sequence definition: (follow_up_count_to_match, days_since, template_name)
# ---------------------------------------------------------------------------
SEQUENCE: List[Tuple[int, int, str]] = [
    (0, 3, "still_looking"),      # Day 3
    (1, 4, "followup_checkin"),   # Day 7  (3 + 4)
    (2, 3, "breakup"),            # Day 10 (3 + 4 + 3)
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_dt(ts: str) -> Optional[datetime]:
    """Parse ISO 8601 timestamp; returns tz-aware datetime or None."""
    if not ts:
        return None
    try:
        dt = datetime.fromisoformat(ts)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        return None


def _render(template_name: str, first_name: str, business_name: str) -> Tuple[str, str]:
    """Render subject + body from TEMPLATES dict."""
    tmpl = TEMPLATES[template_name]
    vars_ = {"first_name": first_name or "there", "business_name": business_name}
    subject = Template(tmpl["subject"]).safe_substitute(vars_)
    body    = Template(tmpl["body"]).safe_substitute(vars_)
    return subject, body


def _send_smtp(
    to_email: str,
    subject: str,
    body: str,
    smtp_host: str,
    smtp_port: int,
    username: str,
    password: str,
    sender_name: str,
    sender_email: str,
) -> bool:
    """Send plain-text email via SMTP/TLS. Returns True on success."""
    try:
        msg = MIMEMultipart()
        msg["From"]    = f"{sender_name} <{sender_email}>"
        msg["To"]      = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(username, password)
            server.send_message(msg)

        logger.info(f"  Sent to {to_email}")
        return True
    except Exception as exc:
        logger.error(f"  SMTP error sending to {to_email}: {exc}")
        return False


# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------

def load_tracking_files(output_dir: Path) -> List[Tuple[Path, Dict[str, Any]]]:
    """Return list of (path, parsed_json) for every outreach_tracking_*.json."""
    pattern = str(output_dir / "outreach_tracking_*.json")
    files = sorted(glob.glob(pattern))
    results = []
    for fp in files:
        try:
            with open(fp, "r") as fh:
                data = json.load(fh)
            results.append((Path(fp), data))
        except Exception as exc:
            logger.warning(f"Could not read {fp}: {exc}")
    return results


def determine_action(email_record: Dict[str, Any], now: datetime) -> Optional[str]:
    """
    Decide which follow-up template to send, or None to skip.

    Email records in outreach_tracking_*.json have:
        recipient, first_name, company, subject, sent_at, status
    We add/read:
        follow_up_count (int, default 0)
        last_followup_at (ISO str, optional)
    """
    status = email_record.get("status", "sent")
    if status in SKIP_STATUSES:
        return None

    follow_up_count = email_record.get("follow_up_count", 0)
    if follow_up_count >= 3:
        return None

    for match_count, days_required, template_name in SEQUENCE:
        if follow_up_count != match_count:
            continue

        # Determine the reference timestamp
        if follow_up_count == 0:
            ref_ts = email_record.get("sent_at", "")
        else:
            ref_ts = email_record.get("last_followup_at", "")

        ref_dt = _parse_dt(ref_ts)
        if ref_dt is None:
            logger.warning(
                f"  No valid timestamp for {email_record.get('recipient')} "
                f"(follow_up_count={follow_up_count}), skipping"
            )
            return None

        age_days = (now - ref_dt).total_seconds() / 86400
        if age_days >= days_required:
            return template_name
        # Not old enough yet
        return None

    return None


def process_followups(dry_run: bool = False) -> Dict[str, Any]:
    """
    Main entry point. Returns a summary dict.
    """
    now = datetime.now(tz=timezone.utc)

    # SMTP config
    smtp_host    = os.getenv("SMTP_HOST",     "smtp.gmail.com")
    smtp_port    = int(os.getenv("SMTP_PORT", "587"))
    username     = os.getenv("SMTP_USERNAME", "")
    password     = os.getenv("SMTP_PASSWORD", "")
    sender_name  = os.getenv("SENDER_NAME",  "William Marceau")
    sender_email = os.getenv("SENDER_EMAIL", username)

    if not dry_run and not username:
        logger.error("SMTP_USERNAME not set. Cannot send emails.")
        sys.exit(1)

    tracking_files = load_tracking_files(OUTPUT_DIR)
    if not tracking_files:
        logger.info("No outreach_tracking_*.json files found in output/")
        return {"files_checked": 0, "sent": 0, "skipped": 0, "errors": 0}

    stats = {
        "files_checked": len(tracking_files),
        "candidates_found": 0,
        "sent": 0,
        "skipped": 0,
        "errors": 0,
        "actions": [],  # list of dicts — one per email actioned
    }

    for file_path, data in tracking_files:
        emails: List[Dict[str, Any]] = data.get("emails", [])
        file_modified = False

        logger.info(f"Checking {file_path.name} ({len(emails)} records)")

        for record in emails:
            recipient     = record.get("recipient", "")
            first_name    = record.get("first_name", "there")
            business_name = record.get("company", "your business")

            template_name = determine_action(record, now)

            if template_name is None:
                stats["skipped"] += 1
                continue

            stats["candidates_found"] += 1
            subject, body = _render(template_name, first_name, business_name)

            action_entry = {
                "recipient":      recipient,
                "business_name":  business_name,
                "template":       template_name,
                "follow_up_count_before": record.get("follow_up_count", 0),
                "subject":        subject,
            }

            if dry_run:
                logger.info(
                    f"  [DRY RUN] Would send '{template_name}' to {recipient} "
                    f"({business_name}) — Subject: {subject}"
                )
                logger.info(f"  Body preview:\n{body[:120].strip()}...")
                action_entry["status"] = "dry_run"
                stats["actions"].append(action_entry)
                stats["sent"] += 1  # counts as "would send" in dry-run
                continue

            # Live send
            success = _send_smtp(
                to_email=recipient,
                subject=subject,
                body=body,
                smtp_host=smtp_host,
                smtp_port=smtp_port,
                username=username,
                password=password,
                sender_name=sender_name,
                sender_email=sender_email,
            )

            if success:
                # Update the record in-place
                record["follow_up_count"] = record.get("follow_up_count", 0) + 1
                record["last_followup_at"] = now.isoformat()
                record["last_followup_template"] = template_name
                file_modified = True

                action_entry["status"] = "sent"
                stats["sent"] += 1
                time.sleep(3)  # brief delay between sends
            else:
                action_entry["status"] = "error"
                stats["errors"] += 1

            stats["actions"].append(action_entry)

        # Persist changes back to the same file
        if file_modified and not dry_run:
            with open(file_path, "w") as fh:
                json.dump(data, fh, indent=2)
            logger.info(f"  Updated {file_path.name}")

    return stats


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Process cold email follow-up sequences (Day 3 / Day 7 / Day 10)."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview what would be sent without actually sending anything.",
    )
    args = parser.parse_args()

    if args.dry_run:
        logger.info("=== DRY RUN MODE — no emails will be sent ===")

    stats = process_followups(dry_run=args.dry_run)

    # Summary
    print("\n" + "=" * 55)
    print("FOLLOW-UP SEQUENCE SUMMARY")
    print("=" * 55)
    print(f"  Tracking files checked : {stats['files_checked']}")
    print(f"  Candidates found       : {stats['candidates_found']}")
    print(f"  {'Would send' if args.dry_run else 'Sent'}               : {stats['sent']}")
    print(f"  Skipped (not due/done) : {stats['skipped']}")
    print(f"  Errors                 : {stats['errors']}")

    if stats["actions"]:
        print("\n  Actions:")
        for a in stats["actions"]:
            tag = f"[{a['status'].upper()}]"
            print(
                f"    {tag:12s} {a['template']:18s} → {a['recipient']} ({a['business_name']})"
            )
    print("=" * 55 + "\n")


if __name__ == "__main__":
    main()
