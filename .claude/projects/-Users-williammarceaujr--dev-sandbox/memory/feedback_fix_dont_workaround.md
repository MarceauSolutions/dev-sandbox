---
name: Fix broken tools, don't work around them
description: When a standard tool (e.g. Apollo) is broken, fix it — don't substitute a different API/service as a workaround. Workarounds break standardization across systems.
type: feedback
---

When a tool in the stack is broken (expired API key, stale credential, etc.), **fix the tool** rather than substituting a different service to accomplish the same task.

**Why:** Using workarounds (e.g., Google Places instead of Apollo for prospecting) breaks standardization across businesses and systems. Apollo is the standard prospecting tool — it provides emails, decision-maker names, enrichment data that Places doesn't. Routing around it with a lesser tool means the output is worse AND future runs won't be consistent.

**How to apply:**
- If a tool is broken due to an expired key/credential, tell William and help fix it (generate new key, re-auth, etc.)
- Only use a fallback if the primary tool is fundamentally broken (discontinued, not just expired)
- If a fallback IS used temporarily, flag it clearly and create a task to migrate back to the standard tool
- This applies to all tools in the stack: Apollo, Twilio, Google APIs, n8n workflows, etc.
