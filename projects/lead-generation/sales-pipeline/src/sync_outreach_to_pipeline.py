#!/usr/bin/env python3
"""
Sync cold outreach records from lead-scraper into pipeline.db.

Bridges the gap between:
  - lead-scraper/output/outreach_campaigns.json (emails sent)
  - lead-scraper/output/sms_campaigns.json (SMS sent)
  - sales-pipeline/data/pipeline.db (CRM deals)

For each outreach record:
  1. Find or create a deal in pipeline.db
  2. Log the outreach to outreach_log
  3. Set appropriate stage and follow-up date

Usage:
    python -m src.sync_outreach_to_pipeline          # Dry run
    python -m src.sync_outreach_to_pipeline --sync    # Actually sync
    python -m src.sync_outreach_to_pipeline --stats   # Show sync stats
"""

import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

DB_PATH = str(Path(__file__).parent.parent / "data" / "pipeline.db")
LEAD_SCRAPER_OUTPUT = Path(__file__).resolve().parents[2] / "lead-scraper" / "output"


def load_outreach_records() -> list:
    """Load all outreach records from lead-scraper output."""
    records = []

    # Email campaigns
    email_path = LEAD_SCRAPER_OUTPUT / "outreach_campaigns.json"
    if email_path.exists():
        with open(email_path) as f:
            data = json.load(f)
        for r in data.get("records", []):
            r["channel"] = "Email"
            records.append(r)

    # SMS campaigns
    sms_path = LEAD_SCRAPER_OUTPUT / "sms_campaigns.json"
    if sms_path.exists():
        with open(sms_path) as f:
            data = json.load(f)
        for r in data.get("records", data if isinstance(data, list) else []):
            r["channel"] = "SMS"
            records.append(r)

    return records


def find_deal_by_company(conn, company: str) -> dict:
    """Find existing deal by company name (exact or fuzzy)."""
    # Try exact match first
    row = conn.execute(
        "SELECT id, company, stage FROM deals WHERE company = ?", (company,)
    ).fetchone()
    if row:
        return dict(row)

    # Try fuzzy match (company name contained)
    row = conn.execute(
        "SELECT id, company, stage FROM deals WHERE company LIKE ? ORDER BY lead_score DESC LIMIT 1",
        (f"%{company}%",)
    ).fetchone()
    if row:
        return dict(row)

    return None


def create_deal(conn, record: dict) -> int:
    """Create a new deal from an outreach record."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute(
        """INSERT INTO deals (company, contact_name, contact_email, stage, lead_source,
           outreach_method, created_at, updated_at)
           VALUES (?, ?, ?, 'Intake', 'cold_outreach', ?, ?, ?)""",
        (
            record.get("business_name", "Unknown"),
            record.get("owner_name", ""),
            record.get("email", ""),
            record.get("channel", "email").lower(),
            now, now,
        )
    )
    deal_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    return deal_id


def outreach_already_logged(conn, deal_id: int, channel: str, sent_at: str) -> bool:
    """Check if this outreach was already logged (prevent duplicates)."""
    if not sent_at:
        # Check by deal_id + channel + same day
        count = conn.execute(
            "SELECT COUNT(*) FROM outreach_log WHERE deal_id = ? AND channel = ?",
            (deal_id, channel)
        ).fetchone()[0]
        return count > 0

    count = conn.execute(
        "SELECT COUNT(*) FROM outreach_log WHERE deal_id = ? AND channel = ? AND created_at LIKE ?",
        (deal_id, channel, f"{sent_at[:10]}%")
    ).fetchone()[0]
    return count > 0


def sync_outreach(dry_run=True):
    """Sync all outreach records into pipeline.db."""
    records = load_outreach_records()
    if not records:
        print("No outreach records found.")
        return {"synced": 0, "skipped": 0, "created": 0}

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    stats = {"synced": 0, "skipped": 0, "created_deals": 0, "already_logged": 0}

    for record in records:
        company = record.get("business_name", "Unknown")
        channel = record.get("channel", "Email")
        status = record.get("status", "pending")
        sent_at = record.get("sent_at", "")
        template = record.get("template_used", "")
        subject = record.get("subject", "")
        email = record.get("email", "")

        # Skip pending (not actually sent)
        if status == "pending":
            stats["skipped"] += 1
            continue

        # Find or create deal
        deal = find_deal_by_company(conn, company)
        if deal:
            deal_id = deal["id"]
        else:
            if dry_run:
                stats["created_deals"] += 1
                deal_id = -1  # placeholder
            else:
                deal_id = create_deal(conn, record)
                stats["created_deals"] += 1

        # Check if already logged
        if deal_id > 0 and outreach_already_logged(conn, deal_id, channel, sent_at):
            stats["already_logged"] += 1
            continue

        # Log the outreach
        if not dry_run and deal_id > 0:
            now = sent_at or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            summary = f"Subject: {subject}" if subject else f"Template: {template}"
            conn.execute(
                """INSERT INTO outreach_log
                   (deal_id, company, contact, channel, message_summary, created_at, tower, template_used)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (deal_id, company, record.get("owner_name", ""), channel,
                 summary[:200], now, "digital-ai-services", template)
            )

            # Set follow-up date if not already set
            existing = conn.execute(
                "SELECT next_action_date FROM deals WHERE id = ?", (deal_id,)
            ).fetchone()
            if not existing["next_action_date"]:
                followup = (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d")
                conn.execute(
                    "UPDATE deals SET next_action_date = ?, next_action = 'Re-email with value-add' WHERE id = ?",
                    (followup, deal_id)
                )

        stats["synced"] += 1
        if dry_run:
            print(f"  [DRY] {channel:5s} → {company[:40]:40s} | template={template}")

    if not dry_run:
        conn.commit()

    conn.close()

    print(f"\n{'DRY RUN' if dry_run else 'SYNC'} Results:")
    print(f"  Synced: {stats['synced']}")
    print(f"  Skipped (pending): {stats['skipped']}")
    print(f"  New deals created: {stats['created_deals']}")
    print(f"  Already logged: {stats['already_logged']}")

    return stats


def show_stats():
    """Show current sync status."""
    records = load_outreach_records()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    total = len(records)
    sent = sum(1 for r in records if r.get("status") == "sent")
    pending = total - sent

    # Check how many are already in pipeline
    matched = 0
    for r in records:
        deal = find_deal_by_company(conn, r.get("business_name", ""))
        if deal:
            matched += 1

    conn.close()

    print(f"Outreach Records: {total} total ({sent} sent, {pending} pending)")
    print(f"Already in Pipeline: {matched}/{total}")
    print(f"Missing from Pipeline: {total - matched}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2 or sys.argv[1] == "--dry-run":
        sync_outreach(dry_run=True)
    elif sys.argv[1] == "--sync":
        sync_outreach(dry_run=False)
    elif sys.argv[1] == "--stats":
        show_stats()
    else:
        print("Usage:")
        print("  python -m src.sync_outreach_to_pipeline           # Dry run")
        print("  python -m src.sync_outreach_to_pipeline --sync     # Actually sync")
        print("  python -m src.sync_outreach_to_pipeline --stats    # Show stats")
