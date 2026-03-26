#!/usr/bin/env python3
"""
Sync Outcomes — Pull William's call results from Google Sheet
and update pipeline.db automatically.

Reads from "Calls YYYY-MM-DD" tabs. Finds rows where CALL OUTCOME
column is filled in. Maps outcomes to pipeline actions — William
should NOT need to specify Next Step or Follow-Up Date.

Outcome mappings:
  Interested       -> Qualified, next=Send proposal, followup=+2 days
  Not Interested   -> Closed Lost
  Voicemail        -> Contacted, next=Re-call, followup=+3 days
  Callback Requested -> Qualified, next=Call back, followup=+1 day
  Meeting Booked   -> Meeting Booked, next=Prepare, followup=today
  No Answer        -> Contacted, next=Try again, followup=+2 days
  Gatekeeper       -> Contacted, next=Try again, followup=+2 days
  Send Info        -> Contacted, next=Send info email, followup=+1 day (auto-send)
"""

import sqlite3
import os
from datetime import datetime, timedelta
from pathlib import Path

from .config import (
    DB_PATH, SPREADSHEET_ID, TOKEN_PATH, OUTCOME_MAP,
    SENDER_EMAIL, SMTP_HOST, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD,
)


def _get_sheets_service():
    """Get authenticated Google Sheets API service."""
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build

    creds = Credentials.from_authorized_user_file(TOKEN_PATH)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
    return build("sheets", "v4", credentials=creds)


def get_call_sheet_tabs() -> list:
    """Get list of all 'Calls YYYY-MM-DD' tabs in the spreadsheet."""
    service = _get_sheets_service()
    metadata = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()

    tabs = []
    for sheet in metadata.get("sheets", []):
        title = sheet["properties"]["title"]
        if title.startswith("Calls "):
            tabs.append(title)
    return sorted(tabs, reverse=True)  # Most recent first


def read_outcomes_from_tab(tab_name: str) -> list:
    """
    Read call outcomes from a specific tab.

    Expected column layout (from daily_report.py):
      A: #
      B: Priority
      C: Company
      D: Contact
      E: Phone
      F: Email
      G: Industry
      H: Score
      I: Stage
      J: Tier
      K-R: Script columns
      S: Prior Outreach
      T: CALL OUTCOME  (column index 19)
      U: SPOKE WITH    (column index 20)
      V: NOTES         (column index 21)

    Returns:
        List of outcome dicts
    """
    service = _get_sheets_service()

    try:
        result = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=f"'{tab_name}'!A2:V200",
        ).execute()
    except Exception as e:
        print(f"  [ERROR] Could not read tab '{tab_name}': {e}")
        return []

    rows = result.get("values", [])
    outcomes = []

    for row in rows:
        if len(row) < 20:
            continue

        outcome = (row[19] if len(row) > 19 else "").strip()
        if not outcome:
            continue

        outcomes.append({
            "row_num": row[0] if row else "",
            "company": (row[2] if len(row) > 2 else "").strip(),
            "contact_name": (row[3] if len(row) > 3 else "").strip(),
            "phone": (row[4] if len(row) > 4 else "").strip(),
            "email": (row[5] if len(row) > 5 else "").strip(),
            "industry": (row[6] if len(row) > 6 else "").strip(),
            "outcome": outcome,
            "spoke_with": (row[20] if len(row) > 20 else "").strip(),
            "notes": (row[21] if len(row) > 21 else "").strip(),
        })

    return outcomes


def _send_info_email(deal: dict, conn: sqlite3.Connection, dry_run: bool = False) -> bool:
    """
    Auto-send info email when outcome is 'Send Info'.

    Returns True if sent successfully.
    """
    email = deal.get("contact_email") or ""
    if not email or "@" not in email:
        return False

    contact_first = (deal.get("contact_name") or "").split()[0] if deal.get("contact_name") else "there"
    company = deal.get("company") or "your business"
    industry = deal.get("industry") or "local"

    subject = f"Info for {company} — Marceau Solutions"
    body = f"""Hi {contact_first},

Thanks for your interest! As promised, here's a quick overview of how we help {industry} businesses like {company}.

We built a system that connects everything you already use — phone, email, website forms, Google — into one unified pipeline. Here's what that means for you:

1. Every lead gets captured instantly, no matter where it comes from
2. Automatic follow-up so nothing falls through the cracks
3. One dashboard to see every inquiry, its status, and next steps
4. After-hours coverage — inquiries at 10 PM get handled the same as 10 AM

Most of our clients see ROI within the first month from leads they were already losing.

Would a quick 15-minute walkthrough be helpful? Here's my calendar:
https://calendly.com/wmarceau/ai-services-discovery

Best,
William Marceau
Marceau Solutions
(239) 398-5676
marceausolutions.com"""

    if dry_run:
        print(f"    [DRY] Would send info email to {email}")
        return True

    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart

        msg = MIMEMultipart()
        msg["From"] = f"William Marceau <{SENDER_EMAIL}>"
        msg["To"] = email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()

        # Log the auto-send
        conn.execute("""
            INSERT INTO outreach_log (deal_id, company, contact, channel,
                message_summary, created_at, tower, template_used)
            VALUES (?, ?, ?, 'Email', ?, datetime('now'), 'digital-ai-services', 'auto_send_info')
        """, (deal["id"], company, deal.get("contact_name", ""),
              f"Auto info email: {subject}"))
        conn.commit()

        print(f"    [SENT] Info email to {email}")
        return True
    except Exception as e:
        print(f"    [ERROR] Info email failed: {e}")
        return False


def sync_outcomes(tab_name: str = None, dry_run: bool = False) -> dict:
    """
    Pull outcomes from Google Sheet and update pipeline.

    Args:
        tab_name: Specific tab to sync (or None for today's)
        dry_run: Preview only

    Returns:
        Dict with updated/logged counts
    """
    print("\n=== SYNC CALL OUTCOMES ===")

    if not tab_name:
        tab_name = f"Calls {datetime.now().strftime('%Y-%m-%d')}"

    outcomes = read_outcomes_from_tab(tab_name)

    if not outcomes:
        print(f"  No outcomes found in '{tab_name}'. Fill in CALL OUTCOME column and re-run.")
        return {"updated": 0, "logged": 0, "errors": 0}

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    now = datetime.now()

    results = {"updated": 0, "logged": 0, "errors": 0, "auto_emails": 0}

    for o in outcomes:
        company = o["company"]
        outcome = o["outcome"]
        mapping = OUTCOME_MAP.get(outcome)

        if not mapping:
            print(f"  [SKIP] {company}: unknown outcome '{outcome}'")
            results["errors"] += 1
            continue

        # Find deal by company name
        deal = conn.execute(
            "SELECT * FROM deals WHERE company = ?", (company,)
        ).fetchone()
        if not deal:
            deal = conn.execute(
                "SELECT * FROM deals WHERE company LIKE ?", (f"%{company}%",)
            ).fetchone()
        if not deal:
            # Try matching by phone
            if o.get("phone"):
                phone_digits = "".join(c for c in o["phone"] if c.isdigit())[-10:]
                if phone_digits:
                    deal = conn.execute(
                        "SELECT * FROM deals WHERE contact_phone LIKE ?",
                        (f"%{phone_digits}%",)
                    ).fetchone()
        if not deal:
            print(f"  [SKIP] {company}: not found in pipeline")
            results["errors"] += 1
            continue

        deal_dict = dict(deal)
        deal_id = deal_dict["id"]
        new_stage = mapping["stage"]
        next_action = mapping.get("next_action")

        # Calculate follow-up date automatically (William doesn't need to set this)
        followup_date = None
        if mapping.get("days_until_followup") is not None:
            followup_date = (now + timedelta(days=mapping["days_until_followup"])).strftime("%Y-%m-%d")

        # Build outreach log summary
        summary = f"Cold call — outcome: {outcome}"
        if o["spoke_with"]:
            summary += f", spoke with {o['spoke_with']}"
        if o["notes"]:
            summary += f". {o['notes'][:150]}"

        print(f"  {'[DRY] ' if dry_run else ''}{company}:")
        print(f"    {outcome} -> {new_stage}, next: {next_action}, followup: {followup_date}")

        if not dry_run:
            # Update deal
            update_fields = {
                "stage": new_stage,
                "updated_at": now.strftime("%Y-%m-%d %H:%M:%S"),
            }
            if next_action:
                update_fields["next_action"] = next_action
            if followup_date:
                update_fields["next_action_date"] = followup_date
            elif mapping.get("days_until_followup") is None:
                update_fields["next_action"] = None
                update_fields["next_action_date"] = None

            # Update contact name if spoke_with is provided
            if o["spoke_with"]:
                update_fields["contact_name"] = o["spoke_with"]

            # Append notes if provided
            if o["notes"]:
                existing_notes = deal_dict.get("notes") or ""
                date_prefix = now.strftime("%m/%d")
                update_fields["notes"] = f"{existing_notes}\n[{date_prefix}] {o['notes']}".strip()

            set_clause = ", ".join(f"{k} = ?" for k in update_fields)
            conn.execute(
                f"UPDATE deals SET {set_clause} WHERE id = ?",
                (*update_fields.values(), deal_id),
            )
            results["updated"] += 1

            # Log to outreach_log
            conn.execute("""
                INSERT INTO outreach_log (deal_id, company, contact, channel,
                    message_summary, response, follow_up_date, created_at, tower)
                VALUES (?, ?, ?, 'Call', ?, ?, ?, datetime('now'), 'digital-ai-services')
            """, (deal_id, company, o["spoke_with"] or o["contact_name"],
                  summary, outcome, followup_date))
            results["logged"] += 1

            conn.commit()

            # Auto-send info email if outcome is "Send Info"
            if mapping.get("auto_send_info"):
                deal_dict["id"] = deal_id  # Ensure id is in dict
                if _send_info_email(deal_dict, conn, dry_run=False):
                    results["auto_emails"] += 1

    conn.close()

    print(f"\n  Done: {results['updated']} updated, {results['logged']} logged, "
          f"{results['auto_emails']} auto-emails, {results['errors']} errors")
    return results


def run_sync(dry_run: bool = False, tab_name: str = None) -> dict:
    """Entry point for orchestrator."""
    return sync_outcomes(tab_name=tab_name, dry_run=dry_run)


if __name__ == "__main__":
    import sys
    dry = "--dry-run" in sys.argv
    tab = None
    for arg in sys.argv[1:]:
        if arg.startswith("--tab="):
            tab = arg.split("=", 1)[1]
    sync_outcomes(tab_name=tab, dry_run=dry)
