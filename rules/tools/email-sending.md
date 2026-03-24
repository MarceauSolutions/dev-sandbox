# Tool: Email Sending (SMTP)

**Pattern file:** `execution/send_onboarding_email.py`
**When to use:** Any time an email needs to be sent — client onboarding, follow-ups, proposals, notifications.

## Never do this

- Do NOT write a new email sender script (check-existing-tools.sh will block it)
- Do NOT use a third-party email service (FormSubmit, Mailchimp API) without checking the stack first
- Do NOT tell William to "manually send an email" without trying the SMTP pattern first

## Environment Variables Required

```bash
SMTP_USERNAME=wmarceau@marceausolutions.com
SMTP_PASSWORD=[app password in .env]
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
```

**Primary email:** `wmarceau@marceausolutions.com` (Google Workspace) — ALWAYS use this.
**Never use:** `wmarceau26@gmail.com` for business email — that's the test account for FitAI only.

## Adapting the SMTP Pattern

The `send_onboarding_email.py` file is a reference implementation. For new email types:

```python
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
from dotenv import load_dotenv

load_dotenv()

def send_email(to_address: str, subject: str, body_html: str, body_text: str = None):
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = os.getenv('SMTP_USERNAME')
    msg['To'] = to_address

    if body_text:
        msg.attach(MIMEText(body_text, 'plain'))
    msg.attach(MIMEText(body_html, 'html'))

    with smtplib.SMTP(os.getenv('SMTP_HOST', 'smtp.gmail.com'),
                       int(os.getenv('SMTP_PORT', 587))) as server:
        server.starttls()
        server.login(os.getenv('SMTP_USERNAME'), os.getenv('SMTP_PASSWORD'))
        server.sendmail(msg['From'], to_address, msg.outstr())
```

## Complete the Loop (E07)

After sending any email:
1. Check Gmail for immediate delivery issues (MCP: `gmail_search_messages`)
2. Monitor for replies — set n8n workflow or check Gmail within 24h
3. Never consider outreach "done" without a reply-monitoring plan

## Attachments (PDF proposals, etc.)

```python
from email.mime.base import MIMEBase
from email import encoders

# Attach a PDF
with open(pdf_path, 'rb') as f:
    part = MIMEBase('application', 'octet-stream')
    part.set_payload(f.read())
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', f'attachment; filename="{filename}"')
    msg.attach(part)
```
