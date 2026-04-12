---
name: Cross-Session Changelog Protocol
description: When completing work that affects other sessions, append to HANDOFF.md CHANGELOG section — no manual copy-paste needed between instances
type: feedback
---

When ANY session completes work that affects other Claude Code sessions (rebuild progress, new specs, infrastructure changes, plan updates), append an entry to the CHANGELOG section at the top of `HANDOFF.md` with:
- Date
- What changed (concrete: files, phases, status)
- What the next session needs to know or do differently

**Why:** William runs multiple Claude Code instances. He should never have to copy-paste prompts or manually relay context between them. HANDOFF.md is already read on session start — the CHANGELOG section makes cross-session updates automatic.

**How to apply:**
- At END of every session that changes shared state: append a CHANGELOG entry
- At START of every session: read the CHANGELOG section before doing anything
- Entries older than 2 weeks: archive to `docs/session-history.md`
- The CHANGELOG replaces ad-hoc "Pending Handoff" sections — use the CHANGELOG instead
