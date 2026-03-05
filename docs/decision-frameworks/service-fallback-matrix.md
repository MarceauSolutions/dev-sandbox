# Service Fallback Decision Matrix

When a primary service is unavailable, use this matrix to select the fallback WITHOUT asking William.

## Decision Flow

```
Primary service down?
  |
  v
Is there a client/user waiting RIGHT NOW?
  NO  --> Wait for recovery. Monitor and notify when back.
  YES --> Use the highest-ranked available fallback below.
```

## Fallback Priority (Approved Stack Only)

| Service Down | Fallback 1 (Preferred) | Fallback 2 | DO NOT USE |
|-------------|----------------------|------------|------------|
| **GitHub Pages** (static hosting) | EC2 — serve static files via existing infra | Wait for recovery | ngrok, tunnels, Netlify, Vercel, random hosts |
| **Twilio SMS** (local number blocked) | Twilio toll-free number | Email via Gmail API | Personal phone, other SMS services |
| **Gmail** | Twilio SMS as notification | n8n email node | Random SMTP services |
| **EC2** (server down) | GitHub Pages for static content | Wait + alert William | Spin up new instances without approval |
| **n8n** (workflows down) | Direct API calls via execution/ scripts | Manual process via CLI | New automation platforms |
| **Google Workspace** (for client) | Direct API if available | Wait for recovery | Create accounts on other services |

## Rules

1. ONLY use tools already in the approved stack (see MEMORY.md "Active Infrastructure")
2. Fallback must be DECIDED and EXECUTED — never present options to William unless genuinely ambiguous
3. If no fallback exists, say so clearly and explain the constraint
4. Log the fallback decision in session history for review
5. When primary recovers, migrate back — fallbacks are temporary by nature

## How to Decide (Self-Check)

Before choosing a fallback, verify:
- [ ] Is this tool already in our stack? (Check MEMORY.md, .env, execution/)
- [ ] Does this solve the IMMEDIATE need without creating tech debt?
- [ ] Will this need to be undone/redone later? If yes, is there a better option?
- [ ] Am I reaching for this because it's easy, or because it's right?
