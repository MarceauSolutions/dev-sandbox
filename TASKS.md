# TASKS.md — Unified Task Tracker

**Purpose**: Single source of truth for all tasks, todos, and deferred work.
**Last Updated**: 2026-02-09

> **Agent Handoffs**: See [HANDOFF.md](HANDOFF.md) for EC2 ↔ Mac work exchanges.

---

## 🔥 TODAY — Work On Now

_Active tasks for the current session_

### Personal Training Business Setup
- [x] Test X image generation with new xAI credits ✅ API working
- [x] Gamification GUI complete (fitness-influencer/frontend/gamification.html)
- [x] Alex Hormozi content strategy created

### Infrastructure
- [ ] Verify X scheduler posts at correct EST times (next post: 3 PM EST today)

---

## 📋 THIS WEEK — Near-Term Priorities

### Personal Training Business (P1)
- [x] Build Gamification App GUI (standalone HTML in fitness-influencer/frontend/) ✅
- [x] Create backend API endpoints for gamification (`/api/player/*`, `/api/quests/*`) ✅
- [ ] Connect to EC2 gamification data
- [ ] Record content videos for this week's plan

### Security Hardening (P1)
- [ ] Enable HTTPS for n8n (Let's Encrypt) - credentials currently unencrypted
- [ ] Add IP restriction for n8n admin
- [ ] Enable rate limiting for n8n login

### Clawdbot Enhancements (P2)
- [x] Fix mac-sync.sh permissions (`chmod +x`) ✅
- [ ] Integrate Clawdbot with Voice AI (Twilio)
- [ ] Add Ollama embedding support to memory-lancedb

---

## 🔄 CIRCLE BACK — Deferred with Triggers

_Items waiting for specific conditions before revisiting_

### LinkedIn Company Page Posting
**Trigger**: LinkedIn Community Management API approved (check email)
**Status**: Waiting on LinkedIn approval (submitted 2026-01-21)
**Ready**: OAuth script, API client, setup guide all complete
**Next**: Add redirect URL → Get Client Secret → Run OAuth → Test posting

### Facebook Business Page Integration
**Trigger**: Facebook security verification completes OR 24hr cooldown expires
**Status**: Blocked by Facebook security system
**Alternative**: Try desktop browser after cooldown

### ClickUp Integration Migration
**Trigger**: When working on ClickUp features OR next cleanup sprint
**Request**: Move `execution/clickup_api.py` → `projects/shared/clickup-crm/src/`
**Note**: Works fine in current location, low priority

### Execution Folder Audit
**Trigger**: When 3+ projects need same utility OR during major refactor
**Analysis**: `docs/restructuring/EXECUTION-FOLDER-AUDIT.md`
**Decision**: Migrate incrementally as working on each project

### Website Submodule Health
**Trigger**: Weekly OR before deploying website changes
**Commands**:
```bash
cd /Users/williammarceaujr./dev-sandbox
git submodule status
git submodule update --remote --merge
```

---

## ✅ RECENTLY DONE — Last 7 Days

### 2026-02-09 (Today)
- [x] X Social Media Image Generation Pipeline - batch generator + scheduler v2
- [x] Fixed scheduler timezone (UTC → EST)
- [x] Added xAI billing ($15/mo limit)
- [x] Created personal-training-business folder structure
- [x] Built Gamification App GUI + backend API
- [x] Created Alex Hormozi style content strategy
- [x] Created weekly content plan (Feb 10-16)
- [x] Added task management API to fitness-influencer
- [x] Fixed mac-sync.sh permissions

### 2026-02-08
- [x] Clawdbot handoff system (HANDOFF.md, handoffs.json, sync scripts)

### 2026-02-07
- [x] Agent Orchestrator v5.1-Ultra (21 systems, 73 new endpoints)

### 2026-02-04
- [x] Fitness Influencer Content Pipeline
- [x] EC2 Sync System

### Earlier (Jan 2026)
- [x] Apollo MCP End-to-End Automation (v1.1.0)
- [x] Published Apollo MCP to PyPI + Registry
- [x] LinkedIn Personal Posting Setup
- [x] Apollo.io Cost Optimization Research

---

## 📊 Project Status Overview

| Project | Status | Next Action |
|---------|--------|-------------|
| **X Social Automation** | ✅ Active | Monitor posts at 3/6 PM EST |
| **Personal Training Biz** | 🟡 Setup | Build gamification GUI |
| **Fitness Influencer** | 🟡 Tools ready | Integrate gamification |
| **Lead Scraper** | ✅ Active | Apollo pipeline working |
| **n8n Agent Orchestrator** | ✅ v5.1 | Stable |

---

## 🗂️ Archive

_Moved from active tracking (kept for reference)_

<details>
<summary>Completed Items (Jan 2026)</summary>

- Apollo MCP Server Creation (2026-01-21)
- Apollo Pipeline Integration (2026-01-21)
- Google Cloud $100 Investigation (verification hold, not usage)
- End-Customer Deployment Strategy (Hybrid SaaS recommended)

</details>

---

**Maintenance**:
- Update this file at start/end of each session
- Move completed items to "Recently Done" immediately
- Archive items older than 7 days
- Check "Circle Back" triggers weekly
