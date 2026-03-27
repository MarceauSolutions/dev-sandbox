# Three-Agent Architecture — Updated for Autonomous Operations

**Date**: March 26, 2026
**Status**: Active, reevaluated after autonomy sprint

## Agent Roles (Post-Autonomy)

### Agent 1: Claude Code (Mac — Local Development)

**Platform**: MacBook, VS Code / terminal
**Identity**: Claude Opus, running as Claude Code CLI

**Core responsibilities**:
- Code development, refactoring, debugging
- Tower creation and structural work (tower_factory.py)
- Monolith decomposition and architecture enforcement
- Running standardization_enforcer.py during development
- Producing the morning_digest, daily_loop, and health_check code

**New with autonomy**:
- daily_loop.py runs as launchd job (authored by Claude Code, executed by macOS scheduler)
- unified_morning_digest.py runs as launchd job
- standardization_enforcer.py runs in both launchd contexts
- autonomous_tower_manager.py detects signals and proposes via SMS

**Does NOT**:
- Run 24/7 (launchd jobs handle scheduling)
- Directly interact with clients
- Make pricing or commitment decisions

### Agent 2: Clawdbot / Panacea (EC2 — Telegram Bot)

**Platform**: EC2 instance, Telegram interface
**Identity**: @w_marceaubot

**Core responsibilities**:
- Telegram bot interface for William
- Pipeline queries from EC2 (reads same pipeline.db schema)
- Daily accountability check-ins (5am ET Mon-Sat, 7pm ET Mon-Fri)
- Sending notifications and alerts
- n8n workflow orchestration

**New with autonomy**:
- Receives pipeline digest at 5:30pm (from daily_loop on Mac)
- Could receive morning digest if Mac is asleep (future redundancy)
- Handles Telegram-based commands for pipeline queries

**Handoff protocol with Claude Code**:
- pipeline.db is the shared state (Mac dev copy ↔ EC2 production copy)
- `pipeline_db.py --sync` pushes Mac → EC2
- `pipeline_db.py --pull` pulls EC2 → Mac
- tower_protocol.py tower_requests table for inter-tower coordination

### Agent 3: Ralph (EC2 — Autonomous PRD-Driven)

**Platform**: EC2 instance, PRD-driven execution
**Identity**: Autonomous development agent

**Core responsibilities**:
- Execute Product Requirements Documents (PRDs) autonomously
- Build features defined by Grok's strategic direction
- Social media automation (X posting, content calendar)
- Long-running batch operations

**New with autonomy**:
- social-media-automation code (now in fitness-influencer/social-media/) was built by Ralph
- Auto-iterator optimization loops (now in lead-generation/src/) authored by Ralph
- Could be assigned new PRDs for tower development

**Does NOT**:
- Make architectural decisions (Grok's role)
- Deploy without human review
- Handle client-facing communication

### Strategic Layer: Grok (External Advisor)

**Platform**: X.ai / conversation interface
**Identity**: Strategic architect

**Role**:
- Architecture decisions and tower design
- Priority setting and resource allocation
- Evaluating Claude Code's work for compliance
- Recommending course corrections
- Approving major structural changes

**Does NOT**:
- Execute code directly
- Access the codebase (relies on reports from Claude Code)
- Run scheduled jobs

## Coordination Protocol

```
Grok → Strategic direction → Claude Code → Implementation
                                          → Launchd jobs (autonomous execution)
                                          → pipeline.db (shared state)
                                          → tower_protocol.py (cross-tower messaging)

Claude Code → pipeline.db → Clawdbot (EC2 reads shared state)
Claude Code → tower_requests table → Other towers poll for work

William → SMS reply → Twilio webhook → hot_lead_handler / tower_manager
William → Telegram → Clawdbot → pipeline queries
William → Morning digest (reads) → Action items → Phone actions
```

## What Changed With Autonomy

| Before | After |
|--------|-------|
| Claude Code runs only during sessions | Launchd runs daily_loop and morning_digest 24/7 |
| Manual lead outreach | Autonomous 9-stage acquisition loop |
| No cross-tower coordination | tower_protocol.py + pipeline.db coordination |
| No compliance checking | standardization_enforcer.py on every run |
| Manual tower creation | autonomous_tower_manager.py proposes, William approves via SMS |
| No self-monitoring | Health check + failure alerting after 2 consecutive failures |
| Grok advises reactively | Grok sets strategic direction, system executes autonomously |

## Handoff Points (When Each Agent Takes Over)

| Trigger | From | To | How |
|---------|------|----|-----|
| New feature request | Grok | Claude Code | Conversation directive |
| Code written, needs scheduling | Claude Code | Launchd | Plist creation + install |
| HOT lead detected | daily_loop (launchd) | William via SMS | Twilio API |
| William replies "1" | Twilio webhook | hot_lead_handler | Pipeline DB update |
| Coaching deal won | daily_loop | fitness-influencer | tower_protocol request |
| New vertical detected | daily_loop | William via SMS | autonomous_tower_manager |
| William approves | Twilio webhook | tower_factory | CLAUDE.md-compliant creation |
| Pipeline query | William (Telegram) | Clawdbot (EC2) | Pipeline DB read |
| PRD assigned | Grok | Ralph (EC2) | PRD JSON → autonomous execution |
