#!/usr/bin/env python3
"""
Propane Fitness — Gmail Email Exporter for Dispute Evidence

Automatically retrieves ALL emails to/from Propane Fitness contacts,
saves each as a PDF with metadata, and organizes them into the dispute folder.

Usage:
    python export_propane_emails.py

Output structure:
    PropaneFitnessDispute/
    ├── emails/
    │   ├── 01_2026-02-22_from-jonny_video-download.pdf
    │   ├── 02_2026-02-23_from-propane_call-booked.pdf
    │   └── ...
    ├── evidence/          (your manually saved screenshots go here)
    ├── circle-messages/   (Circle.so screenshots)
    ├── statements/        (Amex statements)
    └── EVIDENCE-INDEX.md  (auto-generated master index)
"""

import os
import sys
import json
import base64
import re
from pathlib import Path
from datetime import datetime
from email.utils import parsedate_to_datetime

# Add project root for imports
ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
sys.path.insert(0, str(ROOT))

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
except ImportError:
    print("ERROR: Google API libraries not installed.")
    print("Run: pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client")
    sys.exit(1)

try:
    from reportlab.lib import colors
    from reportlab.lib.colors import HexColor
    from reportlab.lib.enums import TA_LEFT, TA_JUSTIFY
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    )
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    print("WARNING: reportlab not installed — will save as .txt instead of .pdf")

# --- Config ---
DISPUTE_DIR = Path(__file__).resolve().parent
EMAILS_DIR = DISPUTE_DIR / "emails"
EVIDENCE_DIR = DISPUTE_DIR / "evidence"
CIRCLE_DIR = DISPUTE_DIR / "circle-messages"
STATEMENTS_DIR = DISPUTE_DIR / "statements"
TOKEN_PATH = ROOT / "token.json"
CREDENTIALS_PATH = ROOT / "credentials.json"

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

# All Propane-related email addresses and domains
PROPANE_QUERIES = [
    'from:propanefitness.com',
    'to:propanefitness.com',
    'from:samcart.com propane',
    'from:jotform.com propane',
    'from:stripe.com propanefitness',
    'subject:propane',
    'subject:"secure your spot"',
    'subject:"SECOND CARD"',
    'subject:"Payment Link" from:jim',
    'subject:"Full Terms" from:jim',
]

# PDF Styles
NAVY = HexColor("#1a2744")
CHARCOAL = HexColor("#333333")
LIGHT_GRAY = HexColor("#f2f2f2")
MID_GRAY = HexColor("#e0e0e0")


def get_gmail_service():
    """Authenticate and return Gmail API service."""
    creds = None

    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            # Save refreshed token
            with open(TOKEN_PATH, 'w') as f:
                f.write(creds.to_json())
        else:
            print("ERROR: No valid Gmail token. Run google_auth_setup.py first.")
            sys.exit(1)

    return build('gmail', 'v1', credentials=creds)


def search_emails(service, query):
    """Search Gmail and return list of message IDs."""
    results = []
    page_token = None

    while True:
        response = service.users().messages().list(
            userId='me', q=query, pageToken=page_token, maxResults=100
        ).execute()

        messages = response.get('messages', [])
        results.extend(messages)

        page_token = response.get('nextPageToken')
        if not page_token:
            break

    return results


def get_email_details(service, msg_id):
    """Get full email details including body."""
    msg = service.users().messages().get(
        userId='me', id=msg_id, format='full'
    ).execute()

    headers = msg.get('payload', {}).get('headers', [])
    header_dict = {}
    for h in headers:
        name = h['name'].lower()
        if name in ('from', 'to', 'cc', 'subject', 'date'):
            header_dict[name] = h['value']

    # Parse date
    date_str = header_dict.get('date', '')
    try:
        date_obj = parsedate_to_datetime(date_str)
    except Exception:
        date_obj = datetime.now()

    # Extract body text
    body = extract_body(msg.get('payload', {}))

    # Get attachments info
    attachments = []
    extract_attachment_info(msg.get('payload', {}), attachments)

    return {
        'id': msg_id,
        'from': header_dict.get('from', 'Unknown'),
        'to': header_dict.get('to', 'Unknown'),
        'cc': header_dict.get('cc', ''),
        'subject': header_dict.get('subject', '(No Subject)'),
        'date': date_obj,
        'date_str': date_str,
        'body': body,
        'attachments': attachments,
        'labels': msg.get('labelIds', []),
    }


def extract_body(payload, prefer_html=False):
    """Recursively extract email body text."""
    body_text = ""

    mime_type = payload.get('mimeType', '')

    # Direct body
    if 'body' in payload and payload['body'].get('data'):
        data = payload['body']['data']
        decoded = base64.urlsafe_b64decode(data).decode('utf-8', errors='replace')
        if mime_type == 'text/plain':
            return decoded
        elif mime_type == 'text/html' and prefer_html:
            return decoded

    # Multipart — recurse
    parts = payload.get('parts', [])
    plain_text = ""
    html_text = ""
    for part in parts:
        part_mime = part.get('mimeType', '')
        if part_mime == 'text/plain':
            if 'body' in part and part['body'].get('data'):
                plain_text += base64.urlsafe_b64decode(
                    part['body']['data']
                ).decode('utf-8', errors='replace')
        elif part_mime == 'text/html':
            if 'body' in part and part['body'].get('data'):
                html_text += base64.urlsafe_b64decode(
                    part['body']['data']
                ).decode('utf-8', errors='replace')
        elif 'parts' in part:
            # Nested multipart
            nested = extract_body(part)
            if nested:
                plain_text += nested

    # Prefer plain text, fall back to stripped HTML
    if plain_text:
        return plain_text
    elif html_text:
        # Basic HTML stripping
        import re
        clean = re.sub(r'<br\s*/?>', '\n', html_text)
        clean = re.sub(r'<[^>]+>', '', clean)
        clean = re.sub(r'&nbsp;', ' ', clean)
        clean = re.sub(r'&amp;', '&', clean)
        clean = re.sub(r'&lt;', '<', clean)
        clean = re.sub(r'&gt;', '>', clean)
        return clean.strip()

    return body_text


def extract_attachment_info(payload, attachments):
    """Extract attachment filenames and sizes."""
    if payload.get('filename'):
        attachments.append({
            'filename': payload['filename'],
            'size': payload.get('body', {}).get('size', 0),
            'mimeType': payload.get('mimeType', ''),
        })
    for part in payload.get('parts', []):
        extract_attachment_info(part, attachments)


def sanitize_filename(s, max_len=50):
    """Make a string safe for filenames."""
    s = re.sub(r'[^\w\s-]', '', s)
    s = re.sub(r'\s+', '-', s.strip())
    return s[:max_len].rstrip('-')


def email_to_pdf(email_data, output_path):
    """Convert email data to a professional PDF."""
    if not REPORTLAB_AVAILABLE:
        # Fallback to text
        txt_path = output_path.with_suffix('.txt')
        with open(txt_path, 'w') as f:
            f.write(f"From: {email_data['from']}\n")
            f.write(f"To: {email_data['to']}\n")
            if email_data['cc']:
                f.write(f"CC: {email_data['cc']}\n")
            f.write(f"Subject: {email_data['subject']}\n")
            f.write(f"Date: {email_data['date_str']}\n")
            f.write(f"\n{'='*60}\n\n")
            f.write(email_data['body'])
        return txt_path

    styles = {
        'header_label': ParagraphStyle(
            'HeaderLabel', fontName='Helvetica-Bold', fontSize=9,
            leading=13, textColor=HexColor("#555555"),
        ),
        'header_value': ParagraphStyle(
            'HeaderValue', fontName='Helvetica', fontSize=9,
            leading=13, textColor=CHARCOAL,
        ),
        'subject': ParagraphStyle(
            'Subject', fontName='Helvetica-Bold', fontSize=13,
            leading=18, textColor=NAVY, spaceAfter=8,
        ),
        'body': ParagraphStyle(
            'Body', fontName='Helvetica', fontSize=10,
            leading=14, textColor=CHARCOAL, alignment=TA_JUSTIFY,
        ),
        'meta': ParagraphStyle(
            'Meta', fontName='Helvetica', fontSize=8,
            leading=11, textColor=HexColor("#999999"),
        ),
        'attachment': ParagraphStyle(
            'Attachment', fontName='Helvetica-Oblique', fontSize=9,
            leading=13, textColor=HexColor("#666666"), leftIndent=10,
        ),
    }

    doc = SimpleDocTemplate(
        str(output_path), pagesize=letter,
        leftMargin=0.7*inch, rightMargin=0.7*inch,
        topMargin=0.7*inch, bottomMargin=0.6*inch,
    )

    story = []

    # Email header block
    story.append(Paragraph(
        f"DISPUTE EVIDENCE — EMAIL RECORD",
        ParagraphStyle('Tag', fontName='Helvetica-Bold', fontSize=8,
                       textColor=HexColor("#c0392b"), spaceAfter=10)
    ))

    # Subject
    safe_subject = email_data['subject'].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    story.append(Paragraph(safe_subject, styles['subject']))

    # Header table
    header_rows = [
        ['From:', email_data['from']],
        ['To:', email_data['to']],
    ]
    if email_data['cc']:
        header_rows.append(['CC:', email_data['cc']])
    header_rows.append(['Date:', email_data['date'].strftime('%B %d, %Y at %I:%M %p %Z') if email_data['date'] else email_data['date_str']])

    # Convert to Paragraphs for wrapping
    header_table_data = []
    for label, value in header_rows:
        safe_value = str(value).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        header_table_data.append([
            Paragraph(label, styles['header_label']),
            Paragraph(safe_value, styles['header_value']),
        ])

    ht = Table(header_table_data, colWidths=[0.6*inch, 6.2*inch])
    ht.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('BACKGROUND', (0, 0), (-1, -1), LIGHT_GRAY),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(ht)
    story.append(Spacer(1, 12))

    # Horizontal rule
    story.append(HRFlowable(width="100%", thickness=1, color=MID_GRAY))
    story.append(Spacer(1, 12))

    # Body text
    body = email_data['body']
    if body:
        # Escape HTML entities and convert newlines to <br/>
        body = body.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        # Split into paragraphs on double newlines
        paragraphs = re.split(r'\n\s*\n', body)
        for para in paragraphs:
            para = para.strip()
            if para:
                # Convert single newlines to <br/>
                para = para.replace('\n', '<br/>')
                try:
                    story.append(Paragraph(para, styles['body']))
                    story.append(Spacer(1, 6))
                except Exception:
                    # If paragraph fails to render, add as plain text
                    story.append(Paragraph(
                        para[:500] + ('...' if len(para) > 500 else ''),
                        styles['body']
                    ))
    else:
        story.append(Paragraph("<i>(No text body — email may be HTML-only or contain only attachments)</i>", styles['meta']))

    # Attachments
    if email_data['attachments']:
        story.append(Spacer(1, 12))
        story.append(HRFlowable(width="100%", thickness=0.5, color=MID_GRAY))
        story.append(Spacer(1, 6))
        story.append(Paragraph("Attachments:", styles['header_label']))
        for att in email_data['attachments']:
            size_kb = att['size'] / 1024
            story.append(Paragraph(
                f"&bull; {att['filename']} ({size_kb:.0f} KB, {att['mimeType']})",
                styles['attachment']
            ))

    # Footer
    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", thickness=0.5, color=MID_GRAY))
    story.append(Paragraph(
        f"Gmail Message ID: {email_data['id']} | "
        f"Labels: {', '.join(email_data.get('labels', []))} | "
        f"Exported: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        styles['meta']
    ))

    doc.build(story)
    return output_path


def generate_evidence_index(emails_exported, dispute_dir):
    """Generate a master evidence index markdown file."""
    index_path = dispute_dir / "EVIDENCE-INDEX.md"

    lines = [
        "# Propane Fitness Dispute — Master Evidence Index",
        f"\n**Generated:** {datetime.now().strftime('%B %d, %Y at %I:%M %p')}",
        f"**Total emails exported:** {len(emails_exported)}",
        "",
        "---",
        "",
        "## Email Evidence (Auto-Exported from Gmail)",
        "",
        "| # | Date | From | Subject | File |",
        "|---|------|------|---------|------|",
    ]

    for i, email in enumerate(emails_exported, 1):
        date_str = email['date'].strftime('%Y-%m-%d %H:%M') if email['date'] else 'Unknown'
        from_short = email['from'].split('<')[0].strip()[:30]
        subj_short = email['subject'][:50]
        filename = email.get('saved_filename', 'N/A')
        lines.append(f"| {i} | {date_str} | {from_short} | {subj_short} | `emails/{filename}` |")

    lines.extend([
        "",
        "---",
        "",
        "## Manually Saved Evidence",
        "",
        "| File | Description | Exhibit |",
        "|------|-------------|---------|",
    ])

    # List existing manually saved files
    for f in sorted(dispute_dir.iterdir()):
        if f.is_file() and f.suffix == '.pdf' and f.name != 'EVIDENCE-INDEX.md':
            if f.parent == dispute_dir:  # Top-level files (manually saved)
                lines.append(f"| `{f.name}` | Manually saved | — |")

    # List circle messages
    if CIRCLE_DIR.exists():
        lines.extend(["", "## Circle.so Messages (Screenshots)", ""])
        for f in sorted(CIRCLE_DIR.iterdir()):
            if f.is_file():
                lines.append(f"- `circle-messages/{f.name}`")

    # List statements
    if STATEMENTS_DIR.exists():
        lines.extend(["", "## Amex Statements", ""])
        for f in sorted(STATEMENTS_DIR.iterdir()):
            if f.is_file():
                lines.append(f"- `statements/{f.name}`")

    lines.extend([
        "",
        "---",
        "",
        "## Folder Structure",
        "```",
        "PropaneFitnessDispute/",
        "├── emails/              ← Auto-exported Gmail emails (PDF)",
        "├── evidence/            ← Screenshots, manual evidence",
        "├── circle-messages/     ← Circle.so message screenshots",
        "├── statements/          ← Amex statements",
        "├── *.pdf                ← Your manually saved email PDFs",
        "├── EVIDENCE-INDEX.md    ← This file (master index)",
        "└── export_propane_emails.py  ← Re-run anytime to refresh",
        "```",
        "",
        "## Critical Notes",
        "",
        "- **DO NOT respond to Phil in Circle** — redirect all communication to email",
        "- **Screenshot propane-business.com/terms TODAY** before they modify it",
        "- **File both Amex chargebacks** using docs/propane-chargeback-letters.md narratives",
        "- Phil's Circle outreach (March 12) is a tactic to get you to re-engage and weaken the dispute",
        "",
    ])

    with open(index_path, 'w') as f:
        f.write('\n'.join(lines))

    return index_path


def main():
    print("=" * 60)
    print("PROPANE FITNESS — EMAIL EVIDENCE EXPORTER")
    print("=" * 60)

    # Create folder structure
    for d in [EMAILS_DIR, EVIDENCE_DIR, CIRCLE_DIR, STATEMENTS_DIR]:
        d.mkdir(parents=True, exist_ok=True)
        print(f"  Directory ready: {d.name}/")

    # Connect to Gmail
    print("\nConnecting to Gmail API...")
    service = get_gmail_service()
    print("  Connected.")

    # Search for all Propane-related emails
    print("\nSearching for Propane-related emails...")
    all_msg_ids = set()
    for query in PROPANE_QUERIES:
        results = search_emails(service, query)
        for msg in results:
            all_msg_ids.add(msg['id'])
        print(f"  Query '{query}' → {len(results)} results")

    print(f"\nTotal unique emails found: {len(all_msg_ids)}")

    # Fetch and export each email
    emails_exported = []
    print("\nExporting emails...")

    for msg_id in sorted(all_msg_ids):
        try:
            email_data = get_email_details(service, msg_id)
            emails_exported.append(email_data)
        except Exception as e:
            print(f"  WARNING: Could not fetch message {msg_id}: {e}")

    # Sort by date
    emails_exported.sort(key=lambda e: e['date'] or datetime.min)

    # Export each to PDF
    for i, email_data in enumerate(emails_exported, 1):
        date_prefix = email_data['date'].strftime('%Y-%m-%d_%H%M') if email_data['date'] else 'unknown-date'

        # Determine sender shortname
        from_addr = email_data['from'].lower()
        if 'jim@' in from_addr:
            sender = 'from-jim'
        elif 'joe@' in from_addr or 'halford' in from_addr:
            sender = 'from-joe'
        elif 'jonny@' in from_addr:
            sender = 'from-jonny'
        elif 'propane' in from_addr:
            sender = 'from-propane'
        elif 'samcart' in from_addr:
            sender = 'from-samcart'
        elif 'jotform' in from_addr:
            sender = 'from-jotform'
        elif 'stripe' in from_addr:
            sender = 'from-stripe'
        elif 'wmarceau' in from_addr or 'marceau' in from_addr:
            sender = 'from-william'
        else:
            sender = 'from-other'

        subj_clean = sanitize_filename(email_data['subject'], 40)
        filename = f"{i:02d}_{date_prefix}_{sender}_{subj_clean}.pdf"
        email_data['saved_filename'] = filename

        output_path = EMAILS_DIR / filename
        try:
            email_to_pdf(email_data, output_path)
            print(f"  [{i:02d}/{len(emails_exported)}] {filename}")
        except Exception as e:
            print(f"  [{i:02d}] ERROR exporting {filename}: {e}")
            # Try text fallback
            try:
                txt_path = output_path.with_suffix('.txt')
                with open(txt_path, 'w') as f:
                    f.write(f"From: {email_data['from']}\n")
                    f.write(f"To: {email_data['to']}\n")
                    f.write(f"Subject: {email_data['subject']}\n")
                    f.write(f"Date: {email_data['date_str']}\n\n")
                    f.write(email_data['body'][:5000])
                email_data['saved_filename'] = txt_path.name
                print(f"         → Saved as text: {txt_path.name}")
            except Exception:
                pass

    # Generate evidence index
    print("\nGenerating evidence index...")
    index_path = generate_evidence_index(emails_exported, DISPUTE_DIR)
    print(f"  Index: {index_path}")

    print(f"\n{'=' * 60}")
    print(f"DONE — {len(emails_exported)} emails exported to: {EMAILS_DIR}")
    print(f"Evidence index: {index_path}")
    print(f"{'=' * 60}")

    return emails_exported


if __name__ == "__main__":
    main()
