# HANDOFF.md — Agent Task Queue

**Purpose**: Single source of truth for work handoffs between EC2 (Clawdbot/Ralph) and MacBook (Claude Code).

**Last Updated**: 2026-03-17

---

## For Ralph (EC2, PRD-driven)

### Task: Content Batch Processing Pipeline Test
**Priority**: Medium | **Complexity**: 7/10 | **Status**: Ready

1. Check if FitAI backend video modules run standalone on EC2
2. Process a test video through: silence removal → output
3. If FitAI modules need FastAPI context, use `execution/video_jumpcut.py`
4. Report results below under Completed Tasks

---

## For Clawdbot (EC2, Telegram)

### Standing Orders:
- Morning accountability: 6:45am ET (n8n)
- EOD check-in: 7pm ET (n8n)
- Weekly report: Sunday 7pm ET (n8n)
- Treatment day detector: daily 5am ET (n8n)
- Parse replies per Knowledge Base accountability rules
- Monitor 5 upgrade triggers per Knowledge Base

---

## For Claude Code (Mac)

### Session 2026-03-17 Status:
- Phases 0-4, 7-8: COMPLETE
- Phase 5 (content pipeline): Agent building
- Phase 6 (performance tracking): Agent building
- 49 n8n workflows active
- Command Center dashboard at localhost:8780
- All upgrade trigger plans written + deployed

---

## Completed Tasks
(Ralph has not yet executed first task)
