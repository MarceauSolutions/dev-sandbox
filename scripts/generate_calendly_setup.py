#!/usr/bin/env python3
"""Generate branded PDF: AI Services Discovery Call — Calendly Setup Guide."""

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "execution"))
sys.path.insert(0, str(ROOT / "execution" / "pdf_templates"))

from branded_pdf_engine import BrandedPDFEngine

output_path = str(ROOT / "docs" / "calendly-ai-services-setup.pdf")

data = {
    "title": "AI Services Discovery Call",
    "subtitle": "Calendly Setup Guide — 2 Minutes, 5 Clicks",
    "author": "Marceau Solutions",
    "date": "March 2026",
    "content_markdown": """
## Step 1: Create New Event Type

- Go to **calendly.com/event_types** (or click "+ Create" on your dashboard)
- Select **One-on-One**

## Step 2: Configure Event Details

Copy-paste these exact values:

| Field | Value |
|-------|-------|
| Event name | AI Services Discovery Call |
| Duration | 15 min |
| Location | Google Meet (select from dropdown) |
| Event link | ai-services-discovery (custom URL slug) |

**Description / Additional Notes (copy-paste this):**

Quick 15-minute call to discuss how AI automation can help your business capture more leads, follow up automatically, and save you 10+ hours per week.

We will cover:
- Your current workflow bottlenecks
- Which tasks AI can handle today
- A rough ROI estimate for your business

No pressure, no pitch — just an honest assessment of what is possible.

## Step 3: Set Availability

- Use your existing availability schedule (or create a new one with your preferred hours)
- Recommended: Mon-Fri, 9am-5pm ET with 15-min buffer between events

## Step 4: Add Questions (Optional but Recommended)

Under **Booking Form**, add one custom question:

- **Question:** "What is your biggest business challenge right now?" (Short text, required)

## Step 5: Save and Share

- Click **Save and Close**
- Your link will be: **calendly.com/wmarceau/ai-services-discovery**
- This link is already added to your .env as `CALENDLY_AI_SERVICES_URL`

---

## Optional: Add Calendly API Token (for automation)

If you want automated booking notifications and lead matching, generate a Personal Access Token:

1. Go to **calendly.com/integrations/api_webhooks**
2. Click **Generate New Token**, name it "dev-sandbox"
3. Copy the token and add to .env as: `CALENDLY_API_TOKEN=cal_live_...`
4. This will enable calendly_monitor.py to use the Calendly API directly

---

## Where This Link Gets Used

Once created, this Calendly link powers:

- **Lead follow-up emails** — AI services prospects get a direct booking link
- **Website CTA** — marceausolutions.com digital services page
- **Cold outreach** — email signatures and proposals
- **n8n automations** — auto-send booking link after form submission
"""
}

engine = BrandedPDFEngine()
engine.generate_to_file("generic_document", data, output_path)
print(f"PDF generated: {output_path}")

# Open it
subprocess.run(["open", output_path])
