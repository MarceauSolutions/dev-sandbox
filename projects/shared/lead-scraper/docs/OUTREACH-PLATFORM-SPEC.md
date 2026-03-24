# Outreach Engine — Product Specification

**Version:** 1.0
**Author:** William Marceau
**Date:** March 23, 2026
**Status:** Specification — Pending Build
**Target Port:** 8796
**Launch Script (future):** `scripts/outreach-engine.sh`

---

## Overview

The Outreach Engine is a web-based platform that replaces the current fragmented outreach workflow — Claude Code research in chat, JSON files, manual copy-paste approvals, and terminal-based SMTP sends — with a single unified interface operable from any device, including a phone on a low-energy day.

**The core promise:** William reviews leads, approves emails, and fires campaigns without opening a terminal or touching a file.

**Rule of 100 integration:** The dashboard prominently tracks daily outreach progress toward the 100-contact goal.

---

## Problem Statement

The current workflow has five critical friction points:

1. **Research lives in chat** — Deep-validate steps happen in conversation, are ephemeral, and cannot be reviewed later
2. **Approval is manual** — Approved leads require copy-pasting into JSON files or another script
3. **Sending requires terminal access** — SMTP send scripts must be run from the command line
4. **No persistent log** — Once emails are sent, tracking depends on maintaining CSV files manually
5. **No performance feedback** — There is no way to know which pain-point angles or industries are generating replies

The Outreach Engine eliminates all five friction points.

---

## Architecture

### Tech Stack

- **Backend:** Flask (Python) — same pattern as existing dashboards (FitAI, LaunchPad, etc.)
- **Database:** SQLite — `outreach_engine.db` (separate from other project DBs)
- **Frontend:** Dark theme — `#0d1117` background, `#C9963C` gold accents, matching brand
- **AI Research:** Calls Agent Bridge API at `localhost:5010` (existing EC2 infrastructure)
- **Email Send:** SMTP via credentials in `.env` (`SMTP_USERNAME` / `SMTP_PASSWORD`)
- **Lead Source:** Reads from routed CSV output of the existing lead-scraper pipeline

### Data Flow

```
Lead CSV (routed)
      |
      v
[1] Research Queue  -->  Agent Bridge (localhost:5010)
      |                        |
      |                  AI deep-validation
      |                        |
      v                        v
[2] Email Draft Review  <-- Confirmed pain point + angle
      |
      v
[3] Send Queue  -->  SMTP (rate-limited)
      |                   |
      v                   v
[4] Outreach Log  <--  Send confirmation + tracking
      |
      v
[5] Template Performance  <--  Reply tracking + feedback tags
      |
      v
[6] Research Quality Feedback Loop
```

---

## Feature Specifications

### Module 1: Lead Research Queue

**Purpose:** Surface unresearched Tier 1 candidates and trigger AI deep-validation per lead.

**Display fields per lead card:**
- Name, Company, Title, Email
- Score (from Apollo enrichment)
- Industry tag
- Validation status badge: PENDING / RESEARCHING / YES / MAYBE / NO

**Actions:**
- **Research** button — triggers background AI agent call to `localhost:5010`; card updates in-place when complete (no page reload)
- **Approve** — moves lead to Email Draft Review queue
- **Reject** — archives lead with reason tag

**Research result fields (shown inline after completion):**
- B2C vs B2B verdict
- Phone dependency score (high/medium/low)
- Online booking status (yes/no/partial)
- Specific pain point angle identified (e.g., "missed calls during procedures")
- Overall verdict: YES / MAYBE / NO with one-sentence rationale

**Design notes:**
- Leads displayed as scrollable cards, not a table — better on mobile
- Research status updates via polling (every 3s while RESEARCHING)
- Keyboard shortcut: `A` = approve, `R` = reject, `→` = next lead

---

### Module 2: Email Draft Review

**Purpose:** Review and edit AI-drafted emails before queuing for send.

**Display per email draft:**
- To (name + address)
- Subject line
- Body (full, editable inline — no modal required)
- Pain point angle used (shown as metadata tag)
- Industry category

**Actions:**
- **Edit inline** — click any field to edit; changes saved on blur
- **Approve** — moves to Send Queue
- **Reject with comment** — sends comment back to AI for redraft; lead returns to Research Queue with agent note attached
- **Regenerate** — re-drafts with same pain point angle but different phrasing

**Draft generation trigger:**
- Fires automatically when a lead moves from Research Queue to approved status
- Uses confirmed pain point angle + free 2-week onboarding offer template
- Pulls from existing `email_templates/` in lead-scraper directory

---

### Module 3: Send Queue + Batch Send

**Purpose:** Review all approved emails and fire them as a batch.

**Display:**
- List of all queued emails with: To, Subject, Industry, Pain Point Tag, Draft Approved timestamp
- Total count + estimated send time (based on 2s rate limit)
- Rule of 100 progress ring showing daily total

**Actions:**
- **Send All** — fires all queued emails via SMTP with 2-second delay between sends
- **Remove** — pull a specific email from the batch before send
- **Preview** — expand to see full email body before firing

**Send behavior:**
- Rate limit: 2 seconds between sends (configurable in settings)
- Real-time progress bar with per-email status indicators
- On completion: auto-updates `outreach_engine.db` + writes to tracking CSV
- On failure: marks email as FAILED with SMTP error message; retry available

---

### Module 4: Outreach Log

**Purpose:** Complete auditable history of all sent outreach.

**Table columns:**
- Date Sent
- Company
- Contact Name
- Industry
- Pain Point Angle Used
- Subject Line
- Status: Sent / Replied / Bounced / No Response
- Reply Date
- Pipeline Stage: Cold / Engaged / Discovery Booked / Proposal / Closed

**Interactions:**
- Click any row → expand panel showing full email body + any reply text
- Filter by: Industry, Date Range, Status, Pipeline Stage
- Export to CSV

**Auto-update triggers:**
- Gmail monitor writes replies back to the DB (via existing `gmail_api_monitor.py`)
- Bounce detection via SMTP error codes on send

---

### Module 5: Template Performance

**Purpose:** Surface which outreach angles and industries are generating replies.

**Metrics displayed:**
- Per-industry reply rate (bar chart)
- Per pain-point angle reply rate (sorted descending)
- A/B comparison when 2+ angles have been tested in the same industry

**Example insight cards:**
- "Best angle for dental practices: missed calls during procedures — 12% reply rate (n=8)"
- "Worst performing: generic AI efficiency pitch — 1.4% reply rate (n=22)"
- "Untested angles in HVAC: after-hours callback automation"

**Data source:** `outreach_engine.db` — populated automatically on send and reply receipt

**Minimum data requirement:** Module activates when ≥ 10 emails sent (shows placeholder below threshold)

---

### Module 6: Research Quality Feedback Loop

**Purpose:** Over time, identify which deep-validation criteria actually predict reply quality.

**Workflow:**
1. When a prospect replies, William tags the reply: Interested / Not Interested / Wrong Person / Already Has Solution / Unsubscribe
2. System records the tag alongside the validation data that was generated at research time
3. After 50+ tagged replies: correlation analysis runs — shows which research signals predicted quality

**Insight output examples:**
- "Leads with online_booking=NO reply at 2.3x the rate of leads with online_booking=YES — adjust the qualifying rubric"
- "Phone dependency HIGH correlates with 18% reply rate vs 4% for LOW"

**Rubric auto-update:** Shows recommended changes to the qualifying criteria with one-click acceptance; updates the research prompt template sent to `localhost:5010`

---

## Database Schema

### `outreach_engine.db`

**Table: `leads`**
- `id`, `name`, `company`, `title`, `email`, `score`, `industry`
- `source_csv`, `imported_at`
- `research_status` (pending/researching/done/skipped)
- `b2c_b2b`, `phone_dependency`, `online_booking`, `pain_point_angle`, `verdict`
- `researched_at`, `approved`, `rejected`, `rejection_reason`

**Table: `email_drafts`**
- `id`, `lead_id` (FK), `to_name`, `to_email`
- `subject`, `body`, `pain_point_angle`, `industry`
- `draft_status` (pending/approved/rejected/sent)
- `rejection_comment`, `created_at`, `approved_at`

**Table: `sent_emails`**
- `id`, `draft_id` (FK), `sent_at`, `smtp_status`
- `reply_received`, `reply_date`, `reply_body`
- `reply_tag` (interested/not_interested/wrong_person/has_solution/unsubscribe)
- `pipeline_stage`

**Table: `template_performance`**
- `id`, `industry`, `pain_point_angle`
- `emails_sent`, `replies_received`, `reply_rate`
- `last_updated`

---

## UI Design Principles

1. **One click per action** — Research, Approve, Send — never more than one interaction
2. **No terminal required** — ever, for any action
3. **Mobile-first layout** — card-based, large tap targets (min 44px), readable at arm's length
4. **Rule of 100 always visible** — persistent progress ring in the top navigation bar
5. **Dark brand theme** — `#0d1117` background, `#C9963C` gold, `#f8fafc` text
6. **Status is always obvious** — color-coded badges (gold=pending, green=approved, red=rejected/failed)
7. **Failure surfaces immediately** — SMTP errors, AI research failures, and bounce notifications shown inline, not in logs

---

## Implementation Plan

### Phase 1 — Foundation (Days 1–2)

- Flask app skeleton at port 8796
- SQLite schema creation and migration script
- Lead import from routed CSV (reads existing output format)
- Basic research queue UI with static data
- `scripts/outreach-engine.sh` launch script

**Deliverable:** App runs locally; William can see leads in a browser.

### Phase 2 — AI Research Integration (Days 3–4)

- Wire "Research" button to `localhost:5010` agent bridge
- Research result parser — extracts structured fields from agent response
- Polling endpoint for research status updates
- Approve / Reject flow writing to DB

**Deliverable:** William can trigger research and approve/reject leads without leaving the browser.

### Phase 3 — Email Draft + Send (Days 5–6)

- AI draft generation on lead approval (calls agent bridge with pain point context)
- Inline edit UI for subject + body
- Send Queue view
- SMTP batch send with rate limiting and progress indicator
- Post-send DB update

**Deliverable:** Full end-to-end flow: research → draft → send, all from the browser.

### Phase 4 — Log + Tracking (Day 7)

- Outreach Log with filters and row expansion
- Gmail monitor integration — auto-writes replies to DB
- Pipeline stage tagging

**Deliverable:** William can see full history and incoming replies without checking email manually.

### Phase 5 — Performance Analytics (Days 8–9)

- Template Performance module with charts
- Research Quality Feedback Loop with reply tagging
- Rubric auto-update suggestions

**Deliverable:** Data-driven angle selection replaces intuition.

### Phase 6 — Production Deployment (Day 10)

- EC2 systemd service (`outreach-engine.service`)
- nginx reverse proxy at subdomain `outreach.marceausolutions.com`
- SSL via existing Certbot setup
- HANDOFF.md + SYSTEM-STATE.md updates

**Deliverable:** Accessible from phone, anywhere, on any day.

---

## Integration Points

| System | Integration | Direction |
|--------|-------------|-----------|
| Lead Scraper CSV | Read routed output CSV | Inbound |
| Agent Bridge (`localhost:5010`) | Deep-validation + draft generation | Outbound |
| SMTP (`.env` credentials) | Send emails | Outbound |
| Gmail API Monitor | Receive reply data | Inbound |
| n8n | Optional: trigger research on new CSV drop | Inbound |
| Clawdbot | `/outreach status` command to check queue | Outbound |

---

## Out of Scope (v1)

- CRM sync (ClickUp) — Phase 2 enhancement
- Multi-user access — single-user only
- LinkedIn outreach — email only
- Automated follow-up sequences — manual follow-up only in v1
- AI-generated subject line A/B testing — flagged for Phase 5+ enhancement

---

## Success Criteria

- William can go from "new CSV uploaded" to "batch of emails sent" without opening a terminal
- Full research-to-send flow takes under 5 minutes per batch of 10 leads
- All sent email history persists across sessions
- Template performance module shows statistically useful insights within 30 days of use
- App loads and is fully functional on mobile (iPhone, portrait mode)

---

*Marceau Solutions — Embrace the Pain & Defy the Odds*
*marceausolutions.com*
