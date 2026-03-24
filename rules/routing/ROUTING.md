# Master Routing Decision Tree

> Load this file for ANY routing, interface, agent, output format, or code placement decision.
> Use IF/THEN — do not freestyle. Every answer is in one of the 7 trees below.

---

## 1. INTERFACE SELECTION (E10/E12 — decide BEFORE writing code)

```
What is this feature/tool?
│
├── William needs to interact with it conversationally, look something up, or use it from his phone
│   └── → Clawdbot (Telegram command to @w_marceaubot)
│       Examples: lead lookup, quick status check, accountability prompt, data query
│
├── It runs on a schedule, responds to a trigger, or connects systems together
│   └── → n8n workflow at https://n8n.marceausolutions.com
│       Examples: daily digest, SMS drip, form handler, API connector, cron job
│
├── It displays data, has multiple views, or requires a browser UI
│   └── → Web app at subdomain (FastAPI + nginx + EC2 systemd service)
│       Examples: dashboard, tracker, client portal, interactive tool
│       REQUIRED: scripts/[name].sh launch script + nginx subdomain + SSL
│
├── It produces a document, guide, report, proposal, or readable content
│   └── → Branded PDF via execution/branded_pdf_engine.py
│       Examples: workout program, proposal, SOP, sales leave-behind, progress report
│       See tree #5 for template selection
│
├── It is a notification, alert, or time-sensitive update
│   └── → SMS via execution/twilio_sms.py  OR  email via SMTP pattern
│       SMS: time-sensitive, mobile-first, short content
│       Email: longer content, attachments, formal comms
│
└── It is a CLI script
    └── → NEVER the final interface for William-facing tools
        CLI is allowed ONLY for: internal utilities, data processing pipelines, dev tools
        If William would ever need to "run this command" → WRONG interface → go back up
```

**The 5 E10 questions to answer before building anything:**
1. Who is the end user and how will they interact? (William on mobile? A client? An n8n node?)
2. What existing infrastructure is the natural fit? (Clawdbot, n8n, FitAI, branded PDF, SMS)
3. How does this need to scale? (1 user → 10 → 100? One-time → daily → real-time?)
4. What are the real constraints? (Energy levels, dystonia, treatment days, Naples FL)
5. Is there a consolidation opportunity? (Feature in existing tool > new tool)

---

## 2. OUTPUT FORMAT

```
What am I producing?
│
├── Guide / SOP / report / proposal / document / readable content
│   └── → execution/branded_pdf_engine.py --template [see tree #5]
│       Key: content_markdown (NOT 'content', NOT 'sections')
│       Always open with: open [output_path]
│
├── Data / leads / contacts / records
│   └── → CSV or JSON to projects/[name]/output/  OR  logged to pipeline.db
│       Never a markdown table as final output for data
│
├── Real-time or interactive data display
│   └── → Web app (FastAPI), not a static file
│
├── Quick answer / status / lookup for William right now
│   └── → Plain text response in conversation
│
└── Markdown file (.md)
    └── → NEVER as final output for William-facing content
        Markdown is: internal notes, SOPs for Claude to read, code comments
        If William would read it → convert to branded PDF
        If William would view it in a browser → convert to web app
```

---

## 3. AGENT ROUTING (three-agent model)

```
What type of task is this?
│
├── Interactive / requires Mac / publishing to PyPI / debugging this session's code
│   └── → Claude Code (this session, Mac terminal)
│
├── Quick lookup / research / Telegram command / status check / complexity 0-6
│   └── → Clawdbot (Telegram @w_marceaubot, chat ID 5692454753, EC2 24/7)
│       └── Can be done in <30min without a full dev environment
│
├── Complex build / PRD-driven / multi-hour autonomous work / complexity 7-10
│   └── → Ralph (EC2, PRD-driven, fully autonomous)
│       └── Requires: PRD written first, clear acceptance criteria, no interaction needed
│
└── 4+ independent components / parallel workstreams
    └── → Multiple subagents via Agent tool (Claude Code orchestrates)
        └── Each subagent gets: clear scope, file paths, acceptance criteria
```

**How to hand off between agents:**
- Claude Code → Clawdbot/Ralph: Write task to `HANDOFF.md`, then `git push origin main` (EC2 auto-syncs)
- Clawdbot → Claude Code: Send Telegram message or update `HANDOFF.md`
- All agents read: `docs/ARCHITECTURE-DECISIONS.md` (conventions) on session start

**Deployment targets by agent:**
| What | Deploy To | SOP |
|------|-----------|-----|
| Skills (dev-sandbox Claude) | `~/production/[name]-prod/` | `docs/sops/sop-03-deployment.md` |
| AI Assistants (standalone) | `~/ai-assistants/[name]/` | `docs/sops/sop-31-ai-assistant.md` |
| MCP Packages | PyPI + MCP Registry | `docs/sops/sop-11-mcp-structure.md` through `sop-14` |
| Client Websites | GitHub Pages | `./scripts/deploy_website.sh <client>` |

---

## 4. CODE PLACEMENT

```
Where does this script/file go?
│
├── Logic used by 2+ projects
│   └── → execution/ (shared utilities, DOE strict)
│       Rules: must have Directive → Orchestration → Execution structure
│       Promote from projects/ when second project adopts it
│
├── Logic used by exactly 1 project
│   └── → projects/[tower]/[project]/src/
│       Examples: projects/marceau-solutions/fitness/tools/fitness-influencer/src/
│
├── One-time output / generated artifact / pipeline result
│   └── → projects/[name]/output/  OR  /tmp for truly temporary files
│       Never commit large output files (CSV, PDF, JSON data) to git
│
└── Scheduled / triggered automation
    └── → n8n workflow (NOT a .py cron script)
        Python .py files are NOT deployment targets for scheduled work
        n8n is the scheduler — Python is the logic called BY n8n if needed
```

---

## 5. PDF TEMPLATE SELECTION

```
What type of document?
│
├── General markdown content / guide / SOP / how-to / any freeform document
│   └── → generic_document  (key: content_markdown)
│
├── Client proposal / service pitch / scope of work
│   └── → proposal
│
├── Workout plan / training program / exercise protocol
│   └── → workout_program
│
├── Nutrition plan / meal guide / diet protocol
│   └── → nutrition_guide
│
├── Client progress update / metrics review
│   └── → progress_report
│
├── Service agreement / contract / terms
│   └── → agreement
│
├── Client onboarding packet / welcome materials
│   └── → onboarding_packet
│
├── Sales leave-behind / one-pager / marketing doc
│   └── → leave_behind
│
├── Peptide protocol / supplement guide (fitness-specific)
│   └── → peptide_guide
│
└── Challenge workout / event-specific training
    └── → challenge_workout
```

**Always run first:** `python execution/branded_pdf_engine.py --list-templates`
**See full usage:** `rules/tools/branded-pdf-engine.md`

---

## 6. AUTONOMOUS AGENT TRIGGERS (launch without being asked)

```
Trigger → Action
│
├── William says "Should we build X?" OR mentions a new product idea
│   └── → Auto-launch SOP 17 (4 market viability agents, no permission needed)
│
├── William says "How should we implement X?" OR multiple approaches exist
│   └── → Auto-launch SOP 9 (3-4 architecture exploration agents)
│
├── Complex feature is done + manual test passed
│   └── → Auto-launch SOP 2 (multi-agent testing suite)
│
├── 4+ independent components need to be built
│   └── → Auto-launch SOP 10 (parallel development agents)
│
└── Task took >30min AND affected 2+ systems
    └── → Write session notes to docs/session-history.md before ending session
```

---

## 7. COMMUNICATION PATTERNS (William says X → Claude does Y)

| William Says | Claude Does |
|-------------|------------|
| "Deploy" / "Ship it" | `/deploy` SOP |
| "New project" | `/new-project` SOP |
| "Should we build X?" | Auto-launch SOP 17 (market viability, 4 agents) |
| "How should we implement X?" | Auto-launch SOP 9 (architecture exploration, 3-4 agents) |
| "Run morning digest" | `python -m projects.shared.personal-assistant.src.morning_digest --preview` |
| "Check leads" | `python -m projects.shared.lead-scraper.src.campaign_analytics report` |
| "Continue from last session" | Check `docs/session-history.md` |
| "Roll back" | `docs/sops/sop-07-rollback.md` |
| "Publish to registry" | `/publish-mcp` |
| "Run SMS campaign" | `docs/sops/sop-18-sms-campaign.md` |
| "Download photos" / "Export photos" | `/photos` interactive flow |
| "Working on [project]" | Run `/context [project]` then load suggested files |
| "What tool for X?" / "Should we use Y?" | Tool Selection Framework in `docs/service-standards.md` |
| "New web dev client" | `projects/marceau-solutions/digital/tools/web-dev/workflows/client-onboarding.md` |
| "Deploy {client} website" | `./scripts/deploy_website.sh {client}` |
| "PT client needs a website" | POST to `/webhook/cross-referral` (cross-business handoff) |
| "End of session" / "Wrapping up" | Run `/session-summary` |
