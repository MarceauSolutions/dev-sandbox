# HANDOFF.md — Agent Task Queue

**Purpose**: Single source of truth for work handoffs between EC2 (Clawdbot/Ralph) and MacBook (Claude Code).

**Last Updated**: 2026-03-22

## CRITICAL: Read These Files At Session Start

| File | Why |
|------|-----|
| `docs/ARCHITECTURE-DECISIONS.md` | Cross-agent conventions, E10 quality rules, interface-first standards |
| `docs/SYSTEM-STATE.md` | What's built, what's broken, DO NOT REDO list |
| `docs/session-history.md` | What was done in recent sessions |

---

## Current Sprint: AI Client Acquisition (March 23 – April 5)

**Goal**: Land 1 AI systems client before William starts new job on April 6.
**New job**: Electrical technician, Collier County Wastewater, 7am-3pm weekdays.
**After April 6**: Training at 3pm, side hustle work evenings/weekends. All current goals continue.

---

## For Clawdbot (EC2, Telegram)

### Standing Orders:
- Morning accountability: 6:45am ET (n8n)
- EOD check-in: 7pm ET (n8n)
- Weekly report: Sunday 7pm ET (n8n)
- Treatment day detector: daily 5am ET (n8n)
- Parse replies per accountability_handler.py rules
- Monitor upgrade triggers per Knowledge Base

### Quality Enforcement:
- **SOUL.md v2.1.0** now includes E10, interface-first, and quality benchmark sections
- Every recommendation must pass: "Is this the right interface for William's life, not just the easiest to code?"
- When building anything: n8n > CLI script, branded PDF > markdown, SMS > "check this command"

### Gmail Capability (NEW):
- `token.json` now has full Gmail scopes: read, send, compose, modify, drafts
- Can create email drafts via Google API (see SOUL.md for code example)
- Can send via SMTP (credentials in .env)

---

## For Ralph (EC2, PRD-driven)

### Task: Content Batch Processing Pipeline Test
**Priority**: Medium | **Complexity**: 7/10 | **Status**: Ready

1. Check if FitAI backend video modules run standalone on EC2
2. Process a test video through: silence removal → output
3. If FitAI modules need FastAPI context, use `execution/video_jumpcut.py`
4. Report results below under Completed Tasks

---

## For Claude Code (Mac)

### Current Priorities:
1. AI client acquisition sprint support (outreach assets, case study, website updates)
2. YouTube video: "I Built a Better Claude Dispatch" (script ready at `projects/marceau-solutions/media/tools/youtube-creator/scripts/`)
3. Calendar management on **Time Blocks** calendar (not primary)
4. System maintenance and cross-agent consistency

### Session 2026-03-22 Completed:
- Claude Dispatch evaluation (not adopting — our system is superior)
- YouTube video script written + branded PDF generated
- Gmail token re-authed with full scopes (6 scopes), pushed to EC2
- Added `/gmail/draft` endpoint to agent_bridge_api.py
- Updated Clawdbot SOUL.md to v2.1.0 (E10, interface-first, quality benchmark, cross-agent sync)
- Updated ARCHITECTURE-DECISIONS.md with quality standards, calendar rules, sync architecture
- Calendar reorganized: training moved to 3pm, added hand therapy/dog walks/Spanish
- New job orientation event added: April 6, Collier County Wastewater

---

## Completed Tasks
(Ralph has not yet executed first task)
