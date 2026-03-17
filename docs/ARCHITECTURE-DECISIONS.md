# Architecture Decisions Log

> Key decisions that ALL three agents (Claude Code, Clawdbot, Ralph) must know about.
> Updated after every significant architectural or business decision.
> This file gets committed and pushed so EC2 agents can access it.

## Active Decisions

### Domain Tiers (March 2026)
- **Tier 1**: GitHub Pages — static sites, free (client websites, marceausolutions.com)
- **Tier 2**: Subdomain — e.g., n8n.marceausolutions.com, fitai.marceausolutions.com (EC2-hosted services)
- **Tier 3**: Localhost — dev/special cases only (never client-facing)

### Business Model (March 16, 2026)
- **PRIMARY**: AI Automation Services for Naples SMBs (Nick Saraev productized model)
- **SECONDARY**: Fitness coaching + content (Ryan Humiston content model + Alex Hormozi offer engineering)
- **PARKED**: All SaaS/product ideas (DumbPhone, ClaimBack) until primary + secondary generate revenue
- **Revenue target**: $10K/mo within 12 months

### Pricing (March 16, 2026)
- **AI Services**: $2,500-7,500 setup + $500-1,500/mo retainer (5-tier productized menu)
- **Fitness**: Kill $197/mo dead zone. New tiers: $19.99 digital / $97/mo group / $1,500 premium 1:1
- **First 3 clients FREE** (both businesses) for testimonials/case studies

### Accountability System (March 16, 2026)
- **Platform**: Clawdbot via Telegram (NOT terminal scripts, NOT manual spreadsheets)
- **Scorecard Sheet**: `1Y5PwloUBbHM8AeiL032_zWy9jjo9vwhyRZkl7qaKw5o`
- **Interaction**: Morning check-in (6:45am), EOD report (7pm), Sunday weekly summary
- **Reply parsing**: Energy (1-10), EOD numbers (outreach, meetings, videos, content), status commands
- **Spec location**: `docs/clawdbot-accountability-spec.md`, `docs/clawdbot-reply-handler-spec.md`

### Outreach Tools (March 16, 2026)
- **Apollo.io ONLY** — handles both prospecting AND email sequencing. No Instantly.ai.
- **Prospect list script**: `scripts/build-naples-prospect-list.py`
- **Sequence script**: `scripts/setup-apollo-sequences.py`
- **Note**: Apollo API key needs refresh (was expired as of March 16)

### E10 Best-Path Evaluation (March 16, 2026)
- Before building ANYTHING, answer 5 questions: who uses it, what infrastructure fits, how it scales, what are constraints, can it consolidate with existing tools
- Litmus test: "Would William use this on a low-energy day from his phone?"
- Terminal scripts and manual spreadsheets are almost never the right answer for William

### E11 Spec ≠ Deployed (March 17, 2026)
- Writing a spec document does NOT mean the system is built
- Pipeline: Research → Design → Build → Deploy → Test on target → Verify user interaction → Mark complete
- Origin: Accountability system was "built" as specs but never deployed to EC2/n8n

### Three-Agent Sync Protocol (March 17, 2026)
- **Every significant Claude Code session MUST end with commit + push**
- **HANDOFF.md** must be updated with decisions AND tasks for other agents
- **This file** (ARCHITECTURE-DECISIONS.md) captures decisions that affect all agents
- **Clawdbot/Ralph** should check this file on session start (same as SYSTEM-STATE.md)

## Decision History

| Date | Decision | Impact | Made By |
|------|----------|--------|---------|
| 2026-03-17 | E11 Spec ≠ Deployed rule | All agents | Claude Code |
| 2026-03-16 | E10 Best-Path Evaluation | All agents | Claude Code |
| 2026-03-16 | Apollo.io only (no Instantly) | AI Services outreach | Claude Code |
| 2026-03-16 | Kill $197/mo coaching | Fitness pricing | Claude Code |
| 2026-03-16 | AI Services as primary business | Business strategy | Claude Code |
| 2026-03-16 | Clawdbot for accountability | Accountability system | Claude Code |
