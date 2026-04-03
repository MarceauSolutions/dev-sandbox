# Twilio-First Architecture — Deployment Guide

## What Changed

The AI phone agent now implements a **Twilio-first** architecture where ALL inbound calls hit the AI receptionist before William's phone ever rings. This mitigates Verizon's unreliable call delivery.

### Call Flow

```
Caller dials (855) 239-9364  ──┐
                                ├──► AI Receptionist (ElevenLabs voice clone)
Caller dials (239) 398-5676  ──┘    │
  (forwarded to 855 via *72)        ├── Qualifies caller
                                    ├── If transfer needed → Try William's cell (20s)
                                    │   ├── Answered → Connected
                                    │   └── No answer → Voicemail + Telegram alert
                                    └── If AI-only mode → Take message, alert William
```

### New Endpoints

| Route | Method | Purpose |
|---|---|---|
| `/incoming-call` | POST | **Modified** — detects forwarded calls, known contacts |
| `/elevenlabs-tool/transfer` | POST | **New** — ElevenLabs tool callback for transfer |
| `/initiate-transfer` | POST | **New** — Dials William's cell |
| `/transfer-result` | POST | **New** — Handles answered/missed |
| `/william-cell-status` | POST | **New** — Cell reliability tracking |
| `/admin/routing` | GET/POST | **New** — View/toggle AI-only mode |
| `/admin/test-cell` | POST | **New** — Test call to William's cell |

---

## Deployment Steps

### Step 1: Deploy Updated Code to EC2

```bash
# On EC2 (via SSH or git pull)
cd /home/clawdbot/dev-sandbox
git pull origin main

# Copy updated files to the phone agent service directory
cp projects/marceau-solutions/labs/ai-phone-agent/src/app.py /path/to/ai-phone-agent/app.py
cp projects/marceau-solutions/labs/ai-phone-agent/config/agent_config.json /path/to/ai-phone-agent/config/agent_config.json

# Restart the service
sudo systemctl restart ai-phone-agent
# OR if using pm2:
pm2 restart ai-phone-agent
```

### Step 2: Add Environment Variables

Add to `/home/clawdbot/dev-sandbox/.env` on EC2:

```
APP_BASE_URL=https://ai-phone.marceausolutions.com
```

(WILLIAM_CELL, TRANSFER_ENABLED, etc. are now read from agent_config.json instead of env vars)

### Step 3: Configure ElevenLabs Agent Tool

This MUST be done in the ElevenLabs dashboard (not in code):

1. Go to https://elevenlabs.io/app/conversational-ai
2. Select agent: `Marceau Solutions AI Services Assistant` (ID: `agent_9801kmgjg670fb7bdv5z9r96y66d`)
3. Go to **Tools** tab
4. Add a new **Server Tool**:

   - **Name**: `transfer_to_william`
   - **Description for LLM**: "Transfers the current call to William Marceau's phone. Use when: (1) the caller explicitly asks to speak to William, (2) the caller says they are returning William's call, (3) the caller is urgent or a hot lead ready to buy. Always complete a greeting first. Tell the caller 'Let me connect you with William now' BEFORE calling this tool."
   - **Server URL**: `https://ai-phone.marceausolutions.com/elevenlabs-tool/transfer`
   - **Method**: POST
   - **Parameters**:
     - `call_sid` (string) — "The call session ID, available from the stream parameters"
     - `caller_name` (string) — "The caller's name if they provided it"
     - `reason` (string) — "Why the transfer is being requested"
     - `urgency` (string, enum: low/medium/high) — "How urgent the transfer is"

5. Update the agent's **System Prompt** to include:

```
TRANSFER RULES:
- If the caller asks to speak to William directly, use the transfer_to_william tool.
- If the caller says they are "returning William's call" or "he called me", use the transfer_to_william tool immediately after confirming their name.
- If the caller indicates urgency or readiness to buy, use the transfer_to_william tool.
- Always tell the caller "Let me connect you with William now, one moment" BEFORE calling the tool.
- If the tool returns status "rejected" with reason "ai_only_mode", DO NOT try again. Instead tell the caller William is unavailable and take a detailed message.
- For all other callers, complete the qualifying questions before considering a transfer.
```

### Step 4: Set Up Call Forwarding (Verizon)

On William's phone:
1. Dial `*72 8552399364` and press call
2. Wait for confirmation tone
3. All calls to (239) now route to (855) → AI receptionist

**To undo**: Dial `*73`

**If star codes don't work** (known Verizon issue):
- Call Verizon at *611
- Request unconditional call forwarding to 855-239-9364
- Or use My Verizon app → Account → Call Forwarding

### Step 5: Verify Twilio Webhook Config

In Twilio Console (https://console.twilio.com):
1. Navigate to Phone Numbers → (855) 239-9364
2. Confirm Voice webhook: `https://ai-phone.marceausolutions.com/incoming-call` (POST)
3. Add Status Callback: `https://ai-phone.marceausolutions.com/call-status` (POST)
4. Add Fallback URL: `https://ai-phone.marceausolutions.com/voicemail` (POST)

### Step 6: Test End-to-End

1. **Test AI receptionist**: Call (855) 239-9364 from a different phone
2. **Test transfer**: During AI call, say "Can I speak to William?"
3. **Test fallback**: Set AI-only mode, then try transfer — should take message instead
4. **Test forwarding**: Call (239) 398-5676, verify it hits AI at (855)
5. **Test cell dead**: POST to `/admin/routing` with `{"ai_only_mode": true}`, verify all calls go AI-only

---

## Admin Commands

### Check Status
```
GET https://ai-phone.marceausolutions.com/health
GET https://ai-phone.marceausolutions.com/admin/routing
```

### Toggle AI-Only Mode
```bash
# Enable (when phone is dead)
curl -X POST https://ai-phone.marceausolutions.com/admin/routing \
  -H "Content-Type: application/json" \
  -d '{"ai_only_mode": true}'

# Disable (when phone is working again)
curl -X POST https://ai-phone.marceausolutions.com/admin/routing \
  -H "Content-Type: application/json" \
  -d '{"ai_only_mode": false}'
```

### Test Cell Phone
```bash
curl -X POST https://ai-phone.marceausolutions.com/admin/test-cell
```

---

## Auto-Detection: Dead Phone Mode

The system automatically tracks whether William's cell answers transfer attempts. If fewer than 50% of the last 10 attempts are answered, it automatically:

1. Switches to AI-only mode
2. Sends a Telegram alert explaining what happened
3. All future calls are handled entirely by AI (no transfer attempts)

William can re-enable transfers via the admin endpoint when his phone is working again.

---

## Files Changed

| File | What Changed |
|---|---|
| `src/app.py` | Full rewrite — Twilio-first with transfer, fallback, reliability tracking |
| `config/agent_config.json` | Added `routing`, `fallback_chain`, updated `twilio_config` |
| `data/cell_reliability.json` | New — auto-created, tracks transfer attempts |
