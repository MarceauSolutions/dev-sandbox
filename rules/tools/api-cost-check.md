# Tool: API Cost Check (api-key-manager)

**Script:** `./scripts/api-key-manager.sh`
**Web UI:** http://127.0.0.1:8793
**When to use:** Before any paid API call to check credit balance and provider status.

## How to Check Before Spending

```bash
# Open the API key manager dashboard
./scripts/api-key-manager.sh
# Opens http://127.0.0.1:8793 — shows all API keys and credit balances

# Check provider status file directly
cat .claude/hooks/provider-status.json
```

## Provider Status File

Located at: `.claude/hooks/provider-status.json`

Status values:
- `"active"` — provider is available, credits present
- `"blocked"` — do NOT call this provider (api-cost-guard.sh will block automatically)

To unblock a provider: edit `provider-status.json`, change status to `"active"`, add a note with the fix.

## Providers and Credit Status

| Provider | API Key Env Var | Notes |
|----------|----------------|-------|
| Apollo | `APOLLO_API_KEY` | Limited credits — use `auth/health` to test, not full searches |
| Hunter.io | `HUNTER_API_KEY` | Found 0 Naples leads historically — warn William before using |
| OpenAI | `OPENAI_API_KEY` | Check balance; TTS is expensive per character |
| ElevenLabs | `ELEVENLABS_API_KEY` | Julia's voice clone ID: `Dfq9xw2lqy9dGc5FIpi5` |
| fal.ai | `FAL_API_KEY` | Image gen is costly — confirm scope before bulk runs |
| Replicate | `REPLICATE_API_TOKEN` | Check provider-status.json |
| Ideogram | `IDEOGRAM_API_KEY` | Check provider-status.json |

## Apollo Specifically

Apollo is the primary lead enrichment tool. Before bulk searches:
1. Check balance in api-key-manager dashboard
2. Test auth only: hit `/auth/health` endpoint, not a person search
3. Use filters to narrow results — don't pull 500 records to get 20

## Pre-call Checklist

```
[ ] Does .env have the API key?
[ ] Is the provider status "active" in provider-status.json?
[ ] What is the current credit balance?
[ ] Is there a cheaper/free alternative in execution/?
[ ] Is this a test? → use the health/auth endpoint, not a production call
```
