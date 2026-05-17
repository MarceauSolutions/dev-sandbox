# AI Phone Agent — Pre-Marketing Code Audit

**Date:** 2026-05-16
**Scope:** `projects/marceau-solutions/labs/ai-phone-agent/` (app.py, dashboard.py, agent_config.json, deploy docs)
**Method:** Blind general-purpose agent, read-only review

**Verdict up front: NOT ready for paying customers in 2 weeks.** Demo-ready, yes. Production-multi-tenant-ready, no. 5 blocker-class issues. The product *demos* well; the codebase is single-tenant proof-of-concept wearing a production hat.

---

## Critical bugs / risks

### 1. [BLOCKER] In-memory call state — every restart drops live calls and transcripts
- `app.py:58` `active_calls = {}` is a process-local dict
- `app.py:667` writes `transcript` to webhook only at `/call-complete`
- Any gunicorn worker recycle, EC2 reboot, or systemd restart loses every in-flight call's context, transfer reason, urgency, and fallback alert payload
- `app.py:794` runs `app.run(...)` — no gunicorn, no workers. Concurrent calls will serialize.
- **Fix:** persist `active_calls` to SQLite/Redis keyed on `CallSid`; run under gunicorn with a shared store.

### 2. [BLOCKER] No real transcript capture for AI calls — the dashboard will be empty
- The ElevenLabs media stream (`app.py:331-342`) hands the entire conversation off to ElevenLabs ConvAI
- The Flask app never sees what the AI said or what the caller said
- The only transcript path that populates `active_calls[...]['transcript']` is the *fallback* `/gather-response` branch (`app.py:575-579`), which only runs when ElevenLabs is down
- Webhook lead payloads at `app.py:667` will always send `transcript: []` in normal operation
- Capture happens out-of-band via the n8n `ElevenLabs Call Poller` (polls every 2 min, 10s minimum duration, max 500 dedup history)
- Means transcripts arrive up to **2 minutes after hang-up**, calls under 10s are silently dropped, and the lead in the dashboard and the lead from the poller are in **two separate stores with no join key**
- **Fix:** make ElevenLabs the source of truth — drop the Flask `/call-complete` webhook for AI calls, or have the poller PATCH the existing dashboard lead by `conversation_id`

### 3. [BLOCKER] Hardcoded paths and single-tenant config — cannot onboard client #2 without forking
- `app.py:27` `load_dotenv('/home/clawdbot/dev-sandbox/.env')` — hardcoded EC2 path
- `app.py:41` `TELEGRAM_CHAT_ID = '5692454753'` — hardcoded to William. **Every client's missed-call alert goes to William's phone, not the client's.** Violates `feedback_client_automation_isolation.md`.
- Single `agent_config.json`, single ElevenLabs agent ID, single `WILLIAM_CELL` transfer target
- GTM "client_setup.sh" mentioned in profit analysis does not exist in repo
- "Onboarding 4–6 hours" is optimistic; reality is *fork the file per client* until multi-tenancy is built
- **Fix:** look up tenant by Twilio `To` number → load per-tenant config row (transfer cell, telegram chat id, elevenlabs agent id, persona, qualifying questions). **Required before client #2.**

### 4. [HIGH] Webhook is fire-and-forget with no retry, no dead-letter
- `app.py:677-680` (`/call-complete`) and `app.py:732-735` (`/voicemail-complete`) post lead data with `timeout=10`, catch `Exception`, `print()`, move on
- If n8n is restarting / DNS hiccup / 5xx, the lead is **lost forever**
- Same for `send_telegram_alert` (`app.py:165-167`, 5s timeout, bare except)
- ElevenLabs signed-URL fetch (`app.py:319`) has 5s timeout and on failure falls back to a 4-question Polly TTS gather
- Transfer-phrase detector at `app.py:587-591` is substring match — "I'm not returning his call" would trigger
- **Fix:** queue webhook deliveries (SQLite-backed retry loop or n8n inbound queue), retry on 5xx/timeout, alert on permanent failure.

### 5. [HIGH] No structured logging, no monitoring, no per-call debug record
- Every event is `print(f"...")` to stdout — ~25 print statements in `app.py`
- No per-call log file, no Sentry, no UptimeRobot (profit analysis says "build it this weekend" — not built)
- After a bad demo call, debugging requires `journalctl | grep CallSid`
- `/health` (`app.py:202`) returns `status: ok` even if ElevenLabs API key is invalid or the agent ID is wrong — it doesn't probe dependencies. UptimeRobot pinging this is theatre.
- `data/leads.json` and `data/cell_reliability.json` use file I/O with no locking — concurrent writes during a call surge will corrupt JSON
- `LEADS_FILE` is also a security-thru-obscurity contact DB sitting in plaintext on EC2
- **Fix:** structured JSON logging keyed by CallSid + conversation_id; `/health` probes ElevenLabs + Twilio + webhook target; SQLite for lead + cell_reliability stores; Sentry or at minimum a Telegram error sink.

---

## Additional smaller issues

- `app.py:436-447` and `app.py:451-475` are two near-duplicate dial flows with subtle differences (one plays hold music, one doesn't; one points to absolute URL, one to relative)
- `app.py:606` fallback gather calls `response.gather` after a question but `app.py:614-617` writes the previous answer using `current_q_idx - 1` indexing — off-by-one risk on first question
- `agent_config.json:54` system prompt for "qualified" close asks for callback number AFTER caller already called in — wastes turn
- **Florida is two-party consent for recording (F.S. 934.03)** — the AI's `first_message` does NOT disclose recording. `twilio_config.record_calls: true` is set. **Legal exposure on day one.**

---

## Marketing-readiness verdict

**Do not start paid trials in 2 weeks.** Acceptable to start the GTM motion in 2 weeks ONLY if:
- The demo number stays single-tenant (your own) — fine
- You do NOT onboard client #2 until items 1, 2, 3 are fixed (est. 2 weekends, not 1)
- You add the FL recording disclosure to `first_message` THIS WEEK — legal blocker
- You add UptimeRobot + a webhook-failure Telegram alert before any client hears about it

**Safe to do now:** outreach, demos, signed agreements with a "go-live in 30 days" clause.
**Not safe:** collecting setup fees and promising same-week go-live. The first paid client will expose items 1–3 within a week of real call volume.
