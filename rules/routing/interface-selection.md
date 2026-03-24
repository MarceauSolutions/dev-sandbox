# Interface Selection — Detailed Guide

> Summary version lives in `rules/routing/ROUTING.md` tree #1.
> This file has the full E10 reasoning, examples, and anti-patterns.

## The Non-Negotiable Rule

Every tool must be usable by William WITHOUT opening VS Code. If it isn't, it isn't finished.

## Interface Decision Map

| Use Case | Interface | Why |
|----------|-----------|-----|
| William asks a question on his phone | Clawdbot (Telegram) | Available 24/7, no terminal needed |
| Something runs every day at 7am | n8n workflow | William operates it independently |
| Multiple views, interactive data | Web app at subdomain | Browser, works on mobile |
| Document William reads or shares | Branded PDF | Professional, auto-opens |
| Time-sensitive update | SMS via Twilio | Comes TO William, not the other way |
| Script William runs in terminal | NEVER for William | Wrong interface — go back to this table |

## The 5 E10 Questions (answer before writing a single line of code)

**Q1: Who is the end user and how will they interact?**
- William on mobile during a low-energy day → Telegram command or SMS
- A client receiving a document → Branded PDF or email
- An n8n node fetching data → Python script called via HTTP
- CLI answer → almost never right for William

**Q2: What existing infrastructure is the natural fit?**
- Conversational / quick lookup → Clawdbot already running on EC2
- Automation / scheduling → n8n already has 41+ active workflows
- Fitness features → FitAI platform already built
- Documents → branded_pdf_engine.py already has 10 templates
- Alerts → Twilio already configured with A2P registered number
- Build ON these, not beside them

**Q3: How does this need to scale?**
- 1 user, one-time → Google Sheet or JSON file is fine
- 1 user, daily → n8n workflow with SQLite archive
- 10 users → Web app with database
- 100 users → Same web app, but design the DB schema now
- Choose architecture for the 6-month version, not just today

**Q4: What are the real constraints?**
- Energy levels vary — dystonia affects left side, treatment days are harder
- Must work on worst-case day from phone
- Naples FL location, some features local-market-specific
- Currently zero AI services clients — build to impress, not just to work

**Q5: Is there a consolidation opportunity?**
- New Telegram command > new bot
- New PDF template > new PDF generator script
- New FitAI feature > separate fitness app
- New n8n node in existing workflow > new workflow
- Always ask: "Can this be a capability of something that already exists?"

## Required Deliverables by Interface Type

### Clawdbot command
- [ ] Command handler in Clawdbot codebase on EC2
- [ ] Command documented in Clawdbot help
- [ ] Deployed and tested via Telegram

### n8n workflow
- [ ] Workflow built and active in n8n
- [ ] Backed up to `projects/shared/n8n-workflows/backups/`
- [ ] Tested with real data (not just "workflow saved")

### Web app
- [ ] FastAPI app running as EC2 systemd service
- [ ] nginx proxy configured with subdomain + SSL
- [ ] `scripts/[name].sh` launch script (opens browser)
- [ ] URL documented in `docs/SYSTEM-STATE.md`

### Branded PDF
- [ ] Template selected from existing 10 (or new template added to engine)
- [ ] JSON data keys match template requirements exactly
- [ ] PDF auto-opened after generation: `open [output_path]`

### SMS / Email
- [ ] Uses `execution/twilio_sms.py` (SMS) or `execution/send_onboarding_email.py` pattern (email)
- [ ] Inbox monitor run after send (E07 complete-the-loop)
- [ ] TCPA compliance confirmed for SMS campaigns

## Anti-Patterns (What NOT to Do)

| Anti-Pattern | Correct Pattern |
|-------------|----------------|
| "Run `python tool.py` to use this" | Wire to Clawdbot command or n8n |
| Markdown file as deliverable | Convert to branded PDF |
| launchd .plist on Mac for scheduling | n8n workflow on EC2 |
| ngrok for temporary URL | nginx subdomain on EC2 |
| New standalone bot | New command in Clawdbot |
| Google Sheet for daily metrics | n8n → SQLite → web dashboard |
