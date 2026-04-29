# Marceau Solutions — Dev-Sandbox Architecture

> Read this at the start of every session. Also read MEMORY.md for behavioral rules, project history, and user context.

---

## Build vs. Run Split

| Role | Environment | What it does |
|------|-------------|-------------|
| **Build** | Mac / Claude Code in VS Code | Write code, create features, design systems |
| **Run** | EC2 / Panacea via Telegram | Autonomous tasks: email follow-up, daily loop, monitoring |
| **Strategy** | Grok (xAI API) | Consulted on EVERY AI request. No exceptions. |

**Git workflow:** Both Mac and EC2 push to GitHub. `git pull origin main` to sync. Git is the coordination mechanism.

**EC2 reliability caveat (as of April 2026):** EC2/Telegram has timeout issues and false "third-party app" errors with `claude -p`. Do NOT expand EC2 scope until existing autonomous features are battle-tested. Mac remains the reliable build environment.

**EC2 access:** `ssh -i ~/.ssh/marceau-ec2-key.pem ec2-user@34.193.98.97`

---

## Tower Map

| Tower | Domain | Status | Location |
|-------|--------|--------|----------|
| **personal-assistant** | Email, calendar, Panacea agent, automation | Active | `projects/personal-assistant/` |
| **lead-generation** | Scraping, SMS campaigns, pipeline, competitor research | Active (tool) | `projects/lead-generation/` |
| **ai-systems** | AI infra, customer service, command center | On ice | `projects/ai-systems/` |
| **fitness-influencer** | Video editing, content, social media | On ice | `projects/fitness-influencer/` |
| **amazon-seller** | SP-API, inventory, fee calculator | On ice | `projects/amazon-seller/` |
| **mcp-services** | MCP server dev, PyPI publishing | On ice | `projects/mcp-services/` |
| **marceau-solutions** | Brand hub (digital, fitness, media, labs) | Umbrella | `projects/marceau-solutions/` |
| **boabfit** | Fitness app (React Native) | Halted Apr 14 | `projects/boabfit/` |
| **shared** | Cross-tower tools (md-to-pdf, voice-ai, etc.) | Active | `projects/shared/` |

Each tower has: `src/` (code), `workflows/` (procedures), `VERSION`, and its own `CLAUDE.md`.

---

## Shared Utility Layer: `execution/`

**Rule:** If a script is used by 2+ projects, it goes in `execution/`. If only 1 project uses it, it stays in `projects/[name]/src/`.

Before writing ANY new utility, search `execution/` first — it likely already exists. Key categories:
- **Communication:** `gmail_monitor.py`, `twilio_sms.py`, `send_onboarding_email.py`
- **AI Content:** `grok_image_gen.py`, `multi_provider_image_router.py`, `multi_provider_video_router.py`
- **CRM/Leads:** `add_lead.py`, `lead_manager.py`, `intent_router.py`
- **Documents:** `branded_pdf_engine.py`, `markdown_to_pdf.py`, `pptx_generator.py`
- **Infrastructure:** `agent_bridge_api.py` (n8n bridge), `mem0_api.py` (AI memory), `deploy_to_skills.py`

All scripts read credentials from root `.env` via `python-dotenv`.

---

## Development Workflow

1. **Identify tower:** Which tower owns this work? Code goes there from first commit.
2. **Check existing tools:** Search `execution/` and the tower's `src/` before writing new code.
3. **Work in tower:** `projects/[tower-name]/src/` for code, `workflows/` for procedures.
4. **Use shared utils:** Import from `execution/` when the capability exists.
5. **Test from William's perspective:** Not just syntax — does it actually work end-to-end?
6. **Deploy if needed:** `python deploy_to_skills.py --project [tower] --version X.Y.Z`

## Tower Lifecycle (Creating New Towers)

```
mkdir -p projects/[new-tower]/{src,workflows}
echo "1.0.0-dev" > projects/[new-tower]/VERSION
```

Then: create `directives/[new-tower].md` defining capabilities and integration points. Implement in `src/`, document in `workflows/`, use `execution/` utilities where possible. Expose via Python modules (`from projects.[tower].src import X`) or MCP servers.

## Inter-Tower Communication

Towers import from each other: `from projects.[tower].src import [capability]`
Shared data lives in `data/`. Cross-tower notifications use pub/sub via n8n.
When Tower A needs Tower B's capability: check if it exists first, import directly if yes.

---

## Research-First Execution Policy (MANDATORY)

**Before executing ANY task, Claude MUST:**
1. **Check data first** — Read pipeline.db, outcome tracking, and existing code before recommending an approach
2. **Do NOT execute William's first instinct** — If William says "do X", validate X against data before proceeding. Ask "have you considered Y?" if data suggests a better path
3. **Present alternatives with tradeoffs** — Never present only one option. Show 2-3 approaches with pros/cons
4. **Verify before declaring complete** — Test from the user's perspective. If it touches EC2, SSH and verify. If it touches n8n, check the n8n database
5. **Never give false completion signals** — If something isn't working end-to-end, say so. "Partially done" is honest. "Complete" when it's not is a trust violation

---

## Current Goals (Updated April 28, 2026)

Read `projects/personal-assistant/data/goals.json` for full details.
- **Priority 1:** Excel at Collier County I&E tech job (7am-3pm, 6-month probation)
- **Priority 2:** Low-overhead side income (3D printing/Etsy, crypto trading, Claude-powered projects) — all under Marceau Solutions
- **Priority 3:** Keep autonomous infrastructure running (daily loop, monitoring, lead-gen as research tool)
- **Schedule:** Business work evenings/weekends only. Training 6-8pm non-negotiable.

Update goals: `cd projects/personal-assistant && python3 -m src.goal_manager show`

---

## Agent Architecture

**Three agents** (consolidated from original design):
- **Claude Code (Mac/VS Code)** — Primary build tool. This is where features get created.
- **Panacea (EC2/Telegram)** — Unified agent replacing Clawdbot+Ralph. Runs `claude -p` with Grok direction appended. Telegram bot `@w_marceaubot`.
- **Grok (xAI API)** — Strategic advisor consulted on every request via `grok_strategic_layer.py`. 2-3 sentence direction, never silent on failure.

**Agent rules:**
- "Work on [tower]" → switch context to that tower's directory
- "Deploy [tower]" → run deployment pipeline
- Tower-first thinking: always consider which tower owns the capability
- Minimize coupling between towers
- All operations must be logged, reproducible, and recoverable

---

## Version Control & Deployment

**Single repo:** All towers live in `dev-sandbox/`. No nested git repos (verify weekly).
**Production deploys** create separate repos when needed:
- `~/production/[tower]-prod/` — standalone production
- `~/websites/[domain]/` — web deployments (e.g., `websites/marceausolutions.com/` = GitHub Pages)
- `~/active-projects/[repo]/` — GitHub-published projects

---

## Hooks (Enforced via `.claude/settings.local.json`)

6 pre-tool hooks enforce architectural rules automatically:
- **check-existing-tools** — prevents reinventing utilities that exist in `execution/`
- **project-structure-guard** — ensures code goes in correct tower
- **interface-first-guard** — blocks CLI-only tools (must be web/SMS/PDF/Telegram)
- **api-cost-guard** — prevents expensive API calls without awareness
- **destructive-guard** — blocks dangerous operations (rm -rf, force push, etc.)
- **stack-guard** — enforces technology stack consistency
- **complete-the-loop-guard** — ensures tasks finish end-to-end
- **post-push-ec2-sync** — syncs to EC2 after git push

---

## Key References

| What | Where |
|------|-------|
| Live system state | `docs/SYSTEM-STATE.md` |
| Architecture decisions | `docs/ARCHITECTURE-DECISIONS.md` |
| Agent handoffs | `HANDOFF.md` |
| Session history | `docs/session-history.md` |
| Calendar rules | `rules/tools/calendar-management.md` |
| All SOPs (33) | `docs/sops/INDEX.md` |
| Auto-memory index | `~/.claude/projects/.../memory/MEMORY.md` |
| API Key Manager | `./scripts/api-key-manager.sh` -> http://127.0.0.1:8793 |
| Health check | `python scripts/health_check.py` |
| Daily standup | `./scripts/daily_standup.sh` |

---

## Brand & Contact

- **Email:** wmarceau@marceausolutions.com | **Phone:** (239) 398-5676
- **Brand:** "Embrace the Pain & Defy the Odds" | Gold `#C9963C` / Charcoal `#333333` | NEVER green
- **Website:** marceausolutions.com | **n8n:** n8n.marceausolutions.com
