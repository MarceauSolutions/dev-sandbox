#!/usr/bin/env python3
"""
Morning Call Sheet — one PDF with everything William needs to start dialing.

For each lead:
  - Company, contact, phone (clickable on mobile)
  - Pipeline stage + outreach history timeline
  - Personalized pitch script (opener, hook, discovery question, close)
  - Research context (pain points, website status, industry notes)
  - What NOT to say / what to say instead

Delivered as branded PDF to email at 7am. Open on phone, start calling.

Usage:
    python -m src.morning_call_sheet                  # Generate + email
    python -m src.morning_call_sheet --preview        # Generate only (no email)
    python -m src.morning_call_sheet --limit 15       # Custom lead count
"""

import sqlite3
import json
import os
import sys
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText
from datetime import datetime
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent.parent.parent.parent / ".env")
except ImportError:
    pass

from .pitch_briefer import generate_call_list_with_briefs, generate_pitch_brief, get_deal

DB_PATH = str(Path(__file__).parent.parent / "data" / "pipeline.db")


def validate_pipeline_before_generating():
    """Self-correct pipeline data before generating call sheet.

    Runs every time — ensures stages, follow-ups, and dead leads are accurate
    so the call sheet is correct the first time, every time.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    now = datetime.now()
    fixes = []

    # 1. Close dead leads (explicitly Not Interested, no later positive, no soft language)
    from collections import defaultdict
    responses_by_deal = defaultdict(list)
    all_responses = conn.execute("""
        SELECT d.id, d.company, d.stage, o.response, o.created_at
        FROM deals d JOIN outreach_log o ON o.deal_id = d.id
        WHERE o.response IS NOT NULL AND o.response != ''
        AND d.stage NOT IN ('Closed Won', 'Closed Lost')
        ORDER BY d.id, o.created_at DESC
    """).fetchall()
    for r in all_responses:
        responses_by_deal[r['id']].append(dict(r))

    for did, resps in responses_by_deal.items():
        latest = resps[0]
        resp = (latest.get('response') or '').lower()
        if any(soft in resp for soft in ['open to future', 'relationship', 'not ready now']):
            continue
        if any(neg in resp for neg in ['not interested', 'hung up', 'do not call']):
            has_positive = any(
                'interested' in (r.get('response') or '').lower() and 'not interested' not in (r.get('response') or '').lower()
                for r in resps
            )
            if not has_positive:
                conn.execute("UPDATE deals SET stage = 'Closed Lost' WHERE id = ?", (did,))
                fixes.append(f"Closed: {latest['company']}")

    # 2. Move contacted leads out of Intake/Prospect
    result = conn.execute("""
        UPDATE deals SET stage = 'Contacted'
        WHERE stage IN ('Intake', 'Prospect')
        AND id IN (SELECT DISTINCT deal_id FROM outreach_log WHERE deal_id IS NOT NULL)
    """)
    if result.rowcount > 0:
        fixes.append(f"Stage fix: {result.rowcount} leads -> Contacted")

    # 3. Set follow-up dates for leads missing them
    from datetime import timedelta
    missing_followup = conn.execute("""
        SELECT d.id, d.stage, MAX(o.created_at) as last_touch FROM deals d
        JOIN outreach_log o ON o.deal_id = d.id
        WHERE d.stage NOT IN ('Closed Won', 'Closed Lost')
        AND (d.next_action_date IS NULL OR d.next_action_date = '')
        GROUP BY d.id
    """).fetchall()
    for d in missing_followup:
        try:
            ltd = datetime.strptime(d['last_touch'][:10], '%Y-%m-%d')
            days_since = (now - ltd).days
        except:
            days_since = 99
        followup = (now + timedelta(days=max(1, 5 - days_since))).strftime('%Y-%m-%d')
        action = 'Follow-up call' if d['stage'] == 'Qualified' else 'Follow-up call/email'
        conn.execute("UPDATE deals SET next_action = ?, next_action_date = ? WHERE id = ?",
                     (action, followup, d['id']))
    if missing_followup:
        fixes.append(f"Follow-ups: set for {len(missing_followup)} leads")

    conn.commit()
    conn.close()

    if fixes:
        print(f"Pipeline auto-corrected: {', '.join(fixes)}")
    return fixes
OUTPUT_DIR = Path(__file__).parent.parent / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Brand colors
GOLD = "#C9963C"
DARK = "#1a1a2e"
DARK_BG = "#0f0f1a"
CARD_BG = "#1e1e30"
BORDER = "#2a2a3e"
MUTED = "#8888aa"
WHITE = "#f0f0f5"
GREEN = "#22c55e"
RED = "#ef4444"
BLUE = "#3b82f6"
AMBER = "#f59e0b"


def get_full_call_list(limit: int = 15) -> list:
    """Get prioritized call list with FULL context for each lead."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    leads = []
    seen = set()

    # Priority 1: Follow-ups due today or overdue (WARM — these are money)
    warm = conn.execute("""
        SELECT d.* FROM deals d
        WHERE d.next_action_date <= date('now')
        AND d.next_action_date IS NOT NULL AND d.next_action_date != ''
        AND d.contact_phone IS NOT NULL AND d.contact_phone != ''
        AND d.stage NOT IN ('Closed Won', 'Closed Lost')
        ORDER BY
            CASE WHEN d.stage = 'Qualified' THEN 1
                 WHEN d.stage = 'Meeting Booked' THEN 2
                 WHEN d.stage = 'Proposal Sent' THEN 3
                 WHEN d.stage = 'Active' THEN 4
                 ELSE 5 END,
            d.lead_score DESC
    """).fetchall()

    for d in warm:
        if d["id"] not in seen and len(leads) < limit:
            lead = _enrich_lead(conn, dict(d), "FOLLOW-UP DUE")
            leads.append(lead)
            seen.add(d["id"])

    # Priority 2: Cold leads never called — highest score first
    if len(leads) < limit:
        remaining = limit - len(leads)
        cold = conn.execute("""
            SELECT d.* FROM deals d
            WHERE d.stage IN ('Intake', 'Qualified')
            AND d.contact_phone IS NOT NULL AND d.contact_phone != ''
            AND d.id NOT IN (
                SELECT DISTINCT deal_id FROM outreach_log
                WHERE channel = 'Call' AND deal_id IS NOT NULL
            )
            ORDER BY d.lead_score DESC
            LIMIT ?
        """, (remaining,)).fetchall()
        for d in cold:
            if d["id"] not in seen:
                lead = _enrich_lead(conn, dict(d), "COLD - FIRST CALL")
                leads.append(lead)
                seen.add(d["id"])

    conn.close()
    return leads


def _enrich_lead(conn, deal: dict, priority: str) -> dict:
    """Add outreach history, pitch brief, and research to a deal."""

    # Outreach history
    outreach = conn.execute("""
        SELECT channel, message_summary, response, created_at, template_used
        FROM outreach_log WHERE deal_id = ? ORDER BY created_at DESC
    """, (deal["id"],)).fetchall()
    deal["outreach_history"] = [dict(o) for o in outreach]
    deal["priority"] = priority

    # Pitch brief
    deal["brief"] = generate_pitch_brief(deal)

    # Compute outreach summary
    channels_used = set()
    for o in deal["outreach_history"]:
        channels_used.add(o.get("channel", ""))
    deal["channels_used"] = sorted(channels_used)
    deal["total_touches"] = len(deal["outreach_history"])
    deal["last_touch"] = deal["outreach_history"][0]["created_at"][:10] if deal["outreach_history"] else "Never"

    return deal


def generate_html(leads: list) -> str:
    """Generate branded HTML call sheet."""
    today = datetime.now().strftime("%A, %B %d, %Y")
    now = datetime.now().strftime("%I:%M %p")

    # Stats
    follow_ups = sum(1 for l in leads if l["priority"] == "FOLLOW-UP DUE")
    cold_calls = sum(1 for l in leads if l["priority"] == "COLD - FIRST CALL")

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
  @page {{ size: letter; margin: 0.5in; }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: {DARK_BG}; color: {WHITE}; font-size: 11px; line-height: 1.4;
  }}
  .header {{
    background: linear-gradient(135deg, {DARK} 0%, #16213e 100%);
    border-bottom: 3px solid {GOLD};
    padding: 16px 20px; margin-bottom: 12px;
    display: flex; justify-content: space-between; align-items: center;
  }}
  .header h1 {{ color: {GOLD}; font-size: 20px; letter-spacing: 1px; }}
  .header .date {{ color: {MUTED}; font-size: 11px; text-align: right; }}
  .stats {{
    display: flex; gap: 12px; margin: 0 8px 12px 8px;
  }}
  .stat {{
    flex: 1; background: {CARD_BG}; border: 1px solid {BORDER};
    border-radius: 6px; padding: 8px 12px; text-align: center;
  }}
  .stat .num {{ font-size: 22px; font-weight: 700; color: {GOLD}; }}
  .stat .label {{ font-size: 9px; color: {MUTED}; text-transform: uppercase; letter-spacing: 1px; }}
  .lead-card {{
    background: {CARD_BG}; border: 1px solid {BORDER}; border-radius: 8px;
    margin: 8px; padding: 0; page-break-inside: avoid; overflow: hidden;
  }}
  .lead-header {{
    padding: 10px 14px; display: flex; justify-content: space-between; align-items: center;
    border-bottom: 1px solid {BORDER};
  }}
  .lead-num {{ color: {GOLD}; font-weight: 700; font-size: 14px; margin-right: 8px; }}
  .lead-company {{ font-size: 14px; font-weight: 600; }}
  .lead-priority {{
    font-size: 9px; padding: 2px 8px; border-radius: 10px; font-weight: 600;
    text-transform: uppercase; letter-spacing: 0.5px;
  }}
  .priority-warm {{ background: {AMBER}22; color: {AMBER}; border: 1px solid {AMBER}44; }}
  .priority-cold {{ background: {BLUE}22; color: {BLUE}; border: 1px solid {BLUE}44; }}
  .lead-body {{ padding: 10px 14px; }}
  .lead-meta {{
    display: flex; gap: 16px; margin-bottom: 8px; flex-wrap: wrap;
  }}
  .meta-item {{ font-size: 10px; color: {MUTED}; }}
  .meta-item strong {{ color: {WHITE}; }}
  .meta-item a {{ color: {GOLD}; text-decoration: none; font-weight: 600; font-size: 12px; }}
  .section-label {{
    font-size: 9px; color: {GOLD}; text-transform: uppercase; letter-spacing: 1px;
    font-weight: 600; margin-top: 8px; margin-bottom: 4px;
  }}
  .script-box {{
    background: {DARK_BG}; border-left: 3px solid {GOLD}; padding: 6px 10px;
    margin: 4px 0; font-size: 10.5px; line-height: 1.5;
    border-radius: 0 4px 4px 0;
  }}
  .outreach-timeline {{
    margin: 4px 0; font-size: 10px;
  }}
  .outreach-item {{
    padding: 2px 0; color: {MUTED}; display: flex; gap: 6px;
  }}
  .outreach-item .ch {{ color: {GOLD}; font-weight: 600; min-width: 40px; }}
  .outreach-item .dt {{ color: {MUTED}; min-width: 60px; }}
  .outreach-item .msg {{ color: {WHITE}; }}
  .services {{ display: flex; gap: 6px; flex-wrap: wrap; margin: 4px 0; }}
  .svc-tag {{
    background: {GOLD}18; color: {GOLD}; border: 1px solid {GOLD}44;
    padding: 1px 8px; border-radius: 10px; font-size: 9px;
  }}
  .stage-badge {{
    display: inline-block; padding: 1px 8px; border-radius: 10px; font-size: 9px; font-weight: 600;
  }}
  .stage-intake {{ background: {BLUE}22; color: {BLUE}; }}
  .stage-contacted {{ background: {AMBER}22; color: {AMBER}; }}
  .stage-qualified {{ background: {GREEN}22; color: {GREEN}; }}
  .discovery-q {{
    background: {BLUE}15; border: 1px solid {BLUE}33; border-radius: 4px;
    padding: 4px 10px; margin: 4px 0; font-size: 10.5px; font-style: italic;
  }}
  .next-action {{
    background: {AMBER}15; border: 1px solid {AMBER}33; border-radius: 4px;
    padding: 4px 10px; margin: 4px 0; font-size: 10.5px;
  }}
  .two-col {{ display: flex; gap: 12px; }}
  .two-col > div {{ flex: 1; }}
  .close-script {{
    background: {GREEN}12; border: 1px solid {GREEN}33; border-radius: 4px;
    padding: 4px 10px; margin: 4px 0; font-size: 10px;
  }}
  .footer {{
    text-align: center; padding: 12px; color: {MUTED}; font-size: 9px;
    border-top: 1px solid {BORDER}; margin-top: 12px;
  }}
</style>
</head>
<body>

<div class="header">
  <div>
    <h1>CALL SHEET</h1>
    <div style="color:{MUTED};font-size:10px;margin-top:2px">Marceau Solutions</div>
  </div>
  <div class="date">
    {today}<br>{now}<br>{len(leads)} leads prioritized
  </div>
</div>

<div class="stats">
  <div class="stat"><div class="num">{len(leads)}</div><div class="label">Total Calls</div></div>
  <div class="stat"><div class="num">{follow_ups}</div><div class="label">Follow-ups</div></div>
  <div class="stat"><div class="num">{cold_calls}</div><div class="label">Cold Calls</div></div>
</div>
"""

    for i, lead in enumerate(leads, 1):
        brief = lead.get("brief", {})
        pitch = brief.get("pitch", {})
        priority = lead.get("priority", "")
        stage = lead.get("stage", "Intake")
        priority_class = "priority-warm" if "FOLLOW" in priority else "priority-cold"
        stage_class = f"stage-{stage.lower().replace(' ', '-')}" if stage else "stage-intake"

        # Contact info
        phone = lead.get("contact_phone", "")
        contact = lead.get("contact_name", "Unknown")
        email = lead.get("contact_email", "")
        industry = lead.get("industry", "")
        score = lead.get("lead_score", 0)
        website = lead.get("website", "")
        pain = lead.get("pain_points", "")
        next_action = lead.get("next_action", "")
        next_date = lead.get("next_action_date", "")

        # Format phone as tel: link
        phone_clean = ''.join(c for c in phone if c.isdigit() or c == '+')
        phone_link = f'<a href="tel:{phone_clean}">{phone}</a>' if phone else "No phone"

        html += f"""
<div class="lead-card">
  <div class="lead-header">
    <div>
      <span class="lead-num">#{i}</span>
      <span class="lead-company">{lead.get('company', 'Unknown')}</span>
      <span class="stage-badge {stage_class}">{stage}</span>
    </div>
    <span class="lead-priority {priority_class}">{priority}</span>
  </div>
  <div class="lead-body">
    <div class="lead-meta">
      <div class="meta-item"><strong>Phone:</strong> {phone_link}</div>
      <div class="meta-item"><strong>Contact:</strong> {contact}</div>
      <div class="meta-item"><strong>Industry:</strong> {industry}</div>
      <div class="meta-item"><strong>Score:</strong> {score}</div>
      <div class="meta-item"><strong>Touches:</strong> {lead.get('total_touches', 0)}</div>
      <div class="meta-item"><strong>Last:</strong> {lead.get('last_touch', 'Never')}</div>
    </div>
"""
        # Next action (if follow-up)
        if next_action:
            html += f"""
    <div class="next-action">
      <strong>Next Action:</strong> {next_action} {f'(due {next_date})' if next_date else ''}
    </div>
"""

        # Outreach history
        if lead.get("outreach_history"):
            html += '    <div class="section-label">Outreach History</div>\n'
            html += '    <div class="outreach-timeline">\n'
            for o in lead["outreach_history"][:5]:
                ch = o.get("channel", "?")
                dt = o.get("created_at", "")[:10]
                msg = (o.get("message_summary") or "")[:80]
                resp = o.get("response") or ""
                resp_text = f' → <strong>{resp}</strong>' if resp else ""
                html += f'      <div class="outreach-item"><span class="ch">{ch}</span><span class="dt">{dt}</span><span class="msg">{msg}{resp_text}</span></div>\n'
            html += '    </div>\n'

        # Pitch script
        html += '    <div class="two-col">\n'
        html += '      <div>\n'

        # Opener
        if pitch.get("opener"):
            html += f"""
        <div class="section-label">Opener</div>
        <div class="script-box">"{pitch['opener']}"</div>
"""

        # Hook
        if pitch.get("hook"):
            html += f"""
        <div class="section-label">Hook</div>
        <div class="script-box">"{pitch['hook']}"</div>
"""
        html += '      </div>\n'
        html += '      <div>\n'

        # Discovery question
        if pitch.get("discovery_question"):
            html += f"""
        <div class="section-label">Ask This</div>
        <div class="discovery-q">"{pitch['discovery_question']}"</div>
"""

        # Close
        if pitch.get("close"):
            html += f"""
        <div class="section-label">Close</div>
        <div class="close-script">"{pitch['close']}"</div>
"""
        html += '      </div>\n'
        html += '    </div>\n'

        # Services to mention
        if pitch.get("services_to_mention"):
            html += '    <div class="section-label">Mention</div>\n'
            html += '    <div class="services">\n'
            for svc in pitch["services_to_mention"]:
                html += f'      <span class="svc-tag">{svc}</span>\n'
            html += '    </div>\n'

        # Context (pain points, website)
        context_parts = []
        if pain:
            context_parts.append(f"Pain: {pain}")
        if website:
            context_parts.append(f"Website: {website}")
        elif not website:
            context_parts.append("No website")
        if context_parts:
            html += f'    <div style="font-size:9px;color:{MUTED};margin-top:4px">{" | ".join(context_parts)}</div>\n'

        html += "  </div>\n</div>\n"

    html += f"""
<div class="footer">
  Call Sheet generated {datetime.now().strftime('%Y-%m-%d %I:%M %p')} | Marceau Solutions<br>
  Demo: (855) 239-9364 | marceausolutions.com
</div>
</body></html>"""

    return html


def html_to_pdf(html: str, output_path: Path) -> bool:
    """Convert HTML to PDF using weasyprint, falling back to HTML."""
    try:
        from weasyprint import HTML
        HTML(string=html).write_pdf(str(output_path))
        return True
    except Exception:
        pass

    # Fallback: save as HTML (still viewable on phone, clickable links work)
    html_path = output_path.with_suffix(".html")
    html_path.write_text(html)
    return True


def email_call_sheet(pdf_path: Path):
    """Email the call sheet PDF to William."""
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USERNAME", "")
    smtp_pass = os.getenv("SMTP_PASSWORD", "")
    recipient = os.getenv("DIGEST_RECIPIENT", "wmarceau@marceausolutions.com")

    if not smtp_user or not smtp_pass:
        print("SMTP not configured — skipping email")
        return False

    msg = MIMEMultipart()
    msg["From"] = smtp_user
    msg["To"] = recipient
    msg["Subject"] = f"Call Sheet — {datetime.now().strftime('%B %d, %Y')}"

    body = "Your morning call sheet is attached. Open on phone, start dialing."
    msg.attach(MIMEText(body, "plain"))

    # Attach the file (PDF or HTML)
    if pdf_path.exists():
        with open(pdf_path, "rb") as f:
            attachment = MIMEApplication(f.read(), _subtype=pdf_path.suffix.lstrip("."))
            attachment.add_header("Content-Disposition", "attachment", filename=pdf_path.name)
            msg.attach(attachment)

    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
        print(f"Call sheet emailed to {recipient}")
        return True
    except Exception as e:
        print(f"Email failed: {e}")
        return False


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate morning call sheet")
    parser.add_argument("--preview", action="store_true", help="Generate only, don't email")
    parser.add_argument("--limit", type=int, default=15, help="Number of leads")
    args = parser.parse_args()

    # Self-correct pipeline data before generating
    print("Validating pipeline data...")
    validate_pipeline_before_generating()

    print(f"Generating call sheet with top {args.limit} leads...")
    leads = get_full_call_list(limit=args.limit)

    if not leads:
        print("No leads available for calling.")
        return

    print(f"Found {len(leads)} leads:")
    for i, lead in enumerate(leads, 1):
        print(f"  {i}. [{lead['priority']}] {lead['company']} — {lead.get('contact_phone', 'no phone')}")

    html = generate_html(leads)

    # Save
    today = datetime.now().strftime("%Y-%m-%d")
    pdf_path = OUTPUT_DIR / f"call-sheet-{today}.pdf"
    html_path = OUTPUT_DIR / f"call-sheet-{today}.html"

    # Try PDF first, fall back to HTML
    if html_to_pdf(html, pdf_path):
        output_path = pdf_path if pdf_path.exists() else html_path
        print(f"Saved: {output_path}")
    else:
        html_path.write_text(html)
        output_path = html_path
        print(f"Saved: {output_path}")

    if not args.preview:
        email_call_sheet(output_path)
    else:
        print("Preview mode — not emailing")
        # Open locally
        import subprocess
        subprocess.run(["open", str(output_path)], check=False)


if __name__ == "__main__":
    main()
