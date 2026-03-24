---
rule: E04
name: Verify Before Spending
hook: api-cost-guard.sh (warning for active providers, BLOCKING for blocked providers)
trigger: Before any call to a paid external API — Apollo, Hunter, OpenAI, ElevenLabs, fal.ai, Replicate, Ideogram, etc.
---

## Rule

Check existing capabilities and credit balances before calling any paid API. If `.env` already has the key and a free/cheaper alternative exists in `execution/`, use it. If the API has a credit balance, check it before burning credits on a test call.

## Why it exists

Paid API credits were burned on redundant calls and test runs when equivalent functionality already existed in `execution/`. Apollo credits are limited. Hunter.io found 0 Naples leads and isn't worth the credits.

## How to apply

Before any paid API call:
1. `python scripts/inventory.py search <capability>` — does `execution/` already have this?
2. `./scripts/api-key-manager.sh` → http://127.0.0.1:8793 — what's the current balance?
3. Is this a test call? Use the health/auth endpoint, not a full query
4. Is this provider in `provider-status.json`? If status is "blocked" — the hook will stop you
5. If credits are low, tell William before proceeding

## Provider-specific notes

| Provider | Notes |
|----------|-------|
| Apollo | Limited credits — use `auth/health` to test, avoid bulk searches unless needed |
| Hunter.io | Found 0 Naples leads in past run — low value for local B2B, warn William |
| OpenAI | Check balance at api-key-manager before large jobs; TTS is expensive |
| ElevenLabs | Julia's voice clone is ID `Dfq9xw2lqy9dGc5FIpi5` — confirm before generating |
| fal.ai | Image gen is costly — always confirm scope before bulk runs |

## Examples

- Need to find leads → search `execution/` for lead scraper → `python scripts/inventory.py search lead` before calling Apollo
- Need to generate audio → check ElevenLabs balance first → `./scripts/api-key-manager.sh`
- Need to test Apollo auth → `GET /auth/health` not a contact search
