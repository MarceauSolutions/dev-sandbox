# Agent Routing — Three-Agent Model

> Summary version lives in `rules/routing/ROUTING.md` tree #3.

## Agent Capabilities

| Agent | Location | Best For | Complexity |
|-------|----------|----------|------------|
| **Claude Code** | Mac terminal (this session) | Interactive work, publishing, debugging, Mac-specific tasks | Any |
| **Clawdbot** | EC2 24/7 (Telegram @w_marceaubot) | Quick tasks, research, Telegram commands, check-ins | 0–6 |
| **Ralph** | EC2 (PRD-driven) | Complex builds, fully autonomous multi-hour work | 7–10 |

## Routing Decision

**Use Claude Code when:**
- The work is happening right now in this session
- Requires Mac (Photos.app, local file operations, launchd)
- Publishing to PyPI or MCP registry
- Debugging code in real-time with William
- Interactive decision-making with back-and-forth

**Use Clawdbot when:**
- William wants a quick answer from his phone
- Research task that doesn't need a full dev environment
- Recurring Telegram command to add
- Can complete in <30min without complex build pipeline
- William is away from Mac

**Use Ralph when:**
- Task has a full PRD and clear acceptance criteria
- Multi-hour autonomous build (William doesn't need to be present)
- Complexity 7–10: multiple systems, database design, EC2 deployment
- Full E12 pipeline: build → deploy → test → verify

**Use multiple subagents (Agent tool) when:**
- 4+ independent components that don't depend on each other
- Claude Code orchestrates, subagents do parallel work
- Example: build 4 PDF templates simultaneously

## Cross-Agent Communication

**Handing off to Clawdbot or Ralph:**
1. Write task to `HANDOFF.md` with: context, acceptance criteria, files to read
2. `git commit` + `git push origin main`
3. EC2 auto-syncs via post-push hook
4. Clawdbot/Ralph reads `HANDOFF.md` on next session start

**Receiving from Clawdbot/Ralph:**
- Check `HANDOFF.md` at session start
- Check `docs/session-history.md` for what was completed

**Shared conventions:** `docs/ARCHITECTURE-DECISIONS.md` — ALL agents read this at session start.

## Deployment Targets

| What | Deploy To | SOP |
|------|-----------|-----|
| Skills (dev-sandbox Claude) | `~/production/[name]-prod/` | `docs/sops/sop-03-deployment.md` |
| AI Assistants (standalone) | `~/ai-assistants/[name]/` | `docs/sops/sop-31-ai-assistant.md` |
| MCP Packages | PyPI + MCP Registry | `docs/sops/sop-11-mcp-structure.md` through `sop-14` |
| Client Websites | GitHub Pages | `./scripts/deploy_website.sh <client>` |

## EC2 Access

```bash
ssh -i ~/.ssh/marceau-ec2-key.pem ec2-user@34.193.98.97
```

- n8n: https://n8n.marceausolutions.com (port 5678)
- Clawdbot: Telegram @w_marceaubot, chat ID 5692454753
- Health check: `python scripts/health_check.py`

Full infra state: `docs/SYSTEM-STATE.md`
