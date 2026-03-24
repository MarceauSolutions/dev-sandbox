---
rule: E08
name: Stay In the Stack
hook: stack-guard.sh (BLOCKING)
trigger: Before using any external service, hosting provider, or third-party tool not in the approved stack
---

## Rule

No ngrok, Netlify, FormSubmit, Vercel, Heroku, or random third-party services. The stack is EC2 + nginx + n8n + Twilio + approved APIs. Build on the stack, not beside it. The hook blocks known unapproved services.

## Why it exists

One-off services create maintenance overhead, hidden costs, and fragmentation. Every time a random service was used for "just a quick test," it either became permanent or had to be redone on the correct stack.

## How to apply

Approved stack:
| Need | Use |
|------|-----|
| Hosting / web apps | EC2 + nginx |
| Automation / scheduling | n8n at https://n8n.marceausolutions.com |
| SMS | Twilio (registered A2P number) |
| Email | SMTP via wmarceau@marceausolutions.com |
| Temporary public URL | nginx subdomain on EC2 (not ngrok) |
| Image/video hosting | EC2 static files or existing CDN |
| Forms | n8n webhook handler (not FormSubmit) |
| Database | SQLite (simple) or PostgreSQL (if scaling) on EC2 |

Before using any service not in this table:
1. Check `docs/service-standards.md` — is it approved?
2. If not approved, escalate to William with justification
3. Do NOT proceed without approval

## Examples

- Need a webhook endpoint → n8n webhook node (not a random ngrok tunnel)
- Need to deploy a web app → EC2 systemd + nginx (not Vercel)
- Need a contact form → n8n webhook + email notification (not FormSubmit)
