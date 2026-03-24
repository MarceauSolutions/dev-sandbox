# SOP 00 — Project Kickoff

> Complete this questionnaire before writing any code for a new project.

## Pre-Kickoff Check
- [ ] Searched inventory for existing similar tools: `python scripts/inventory.py search <keyword>`
- [ ] Confirmed this doesn't duplicate an existing capability

## Kickoff Questionnaire

### 1. What problem does this solve?
> One sentence. If you can't say it in one sentence, the scope is too big.

### 2. Who is the user?
> Be specific. "Me" is fine. "Developers" is too vague.

### 3. How will the user interact with it?
> Pick ONE primary interface:
> - Web app (dashboard, tool)
> - CLI (developer tool only — never for end users)
> - API (consumed by other services)
> - Automation (runs on schedule, no UI)
> - Bot (Telegram, Slack, Discord)
> - Document (PDF, report)

### 4. What's the minimum viable version?
> What's the smallest thing you can build that proves the concept?

### 5. What existing tools/infrastructure does this build on?
> Check: execution/ scripts, existing projects, API keys in .env

### 6. Where does it deploy?
> Local only, VPS, GitHub Pages, serverless, etc.

### 7. Success criteria?
> How do you know it's working? Be specific and testable.

## Output
After answering, proceed to SOP 01 (Project Initialization).
