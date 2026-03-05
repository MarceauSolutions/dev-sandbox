# SOP 32: Pre-Flight Checklist

## Purpose
Prevent recurring inefficiency caused by skipping existing tools, ignoring service status, and reaching for external solutions.

## MANDATORY — Run Before Every Task

This checklist is NON-NEGOTIABLE. Complete it before writing ANY code, creating ANY file, or calling ANY external service.

### 1. Inventory Check (30 seconds)
```
python scripts/inventory.py search <relevant-keywords>
```
- Search for existing tools related to the task
- Read `execution/CLAUDE.md` for the full tool catalog
- Check `projects/<name>/` for project-specific tools and workflows

### 2. Existing Workflow Check (30 seconds)
- Check n8n for existing workflows: `mcp__n8n__list_workflows_minimal` with relevant name filter
- Check `execution/` for existing scripts: `ls execution/*<keyword>*`
- Check `.env` for existing API keys/credentials related to the task

### 3. Service Status Check (10 seconds)
Before deploying or relying on any external service:
- GitHub Pages: `gh api repos/<org>/<repo>/pages --jq '.status'`
- EC2: `ssh -i ~/.ssh/marceau-ec2-key.pem ec2-user@34.193.98.97 "echo ok"`
- n8n: `curl -s https://n8n.marceausolutions.com/healthz`
- If a service is down, use the fallback matrix: `docs/decision-frameworks/service-fallback-matrix.md`

### 4. Standards Check (10 seconds)
- What is the STANDARD way we do this? (Check MEMORY.md, service-standards.md)
- Am I introducing a new tool/service? If yes, STOP — use what we have.
- Will this need to be redone later? If yes, do it right the first time.

### 5. Decision Authority (5 seconds)
- Do I have enough context to decide? (MEMORY.md, .env, execution/, docs/)
- If yes: DECIDE and EXECUTE. Do not present options to William.
- If genuinely ambiguous: Present analysis WITH a recommendation, not an open question.

## After Starting Work

### Communication Loop
- Sent an SMS? → Run `python execution/twilio_inbox_monitor.py check` to monitor replies
- Sent an email? → Check Gmail for responses
- Deployed something? → Verify it's actually live before moving on

### Three-Strike Rule
- Same approach failed 3 times? STOP. Research root cause. (CLAUDE.md Rule #7)
- Service returning errors? Check status FIRST, don't retry blindly.

## Anti-Patterns (NEVER DO THESE)

| Anti-Pattern | Do This Instead |
|-------------|----------------|
| Reach for FormSubmit, Typeform, etc. | Use n8n webhooks (our stack) |
| Use ngrok, localtunnel, cloudflared | Use EC2 or wait for GitHub Pages |
| Say "I can't do X" | Search execution/ and scripts/ first |
| Ask "What do you want to do?" | Make the decision with available context |
| Retry a failed deploy 4 times | Check service status after first failure |
| Create new tools for one-time tasks | Use existing tools |
