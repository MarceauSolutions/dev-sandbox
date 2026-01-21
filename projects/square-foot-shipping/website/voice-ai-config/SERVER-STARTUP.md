# Voice AI Server - Startup Guide

**Last Updated:** 2026-01-19

This guide covers starting the Voice AI webhook server that handles calls for both:
- **SW Florida Comfort HVAC** (+1 239-766-6129)
- **Square Foot Shipping & Storage** (+1 239-880-3365)

---

## Quick Start

```bash
# From any directory
cd /Users/williammarceaujr./dev-sandbox/projects/ai-customer-service
python scripts/start_server.py
```

The script will:
1. ✅ Check if server is already running (port 8000)
2. ✅ Start uvicorn server if needed
3. ✅ Start ngrok tunnel if needed
4. ✅ Verify system health (Twilio + Claude configured)
5. ✅ Display public URL for Twilio webhooks

---

## What You'll See

```
🚀 Voice AI Server Startup

1️⃣ Checking existing processes...
   Starting uvicorn on port 8000...
   ✅ Uvicorn started successfully

2️⃣ Checking ngrok tunnel...
   ✅ ngrok URL: https://abc123.ngrok-free.app

3️⃣ Verifying system...
   ✅ System healthy and ready!

==================================================
✅ VOICE AI SERVER READY
==================================================
   Local:  http://localhost:8000
   Public: https://abc123.ngrok-free.app
   Twilio: ✅
   Claude: ✅

   To make outreach calls:
   python scripts/outreach_call.py <phone> --person Name --business Company

   Logs: tail -f /tmp/server.log
```

---

## Server Already Running?

If server is already running and healthy, you'll see:

```
1️⃣ Checking existing processes...
   ✅ Server already running and healthy
```

**To restart** (kill existing server and start fresh):

```bash
python scripts/start_server.py --restart
```

---

## How the Multi-Business Routing Works

The server automatically routes calls based on **which phone number is called**:

| Phone Number | Business | Configuration File |
|--------------|----------|-------------------|
| **+1 239-766-6129** | SW Florida Comfort HVAC | `businesses/swflorida_hvac.py` |
| **+1 239-880-3365** | Square Foot Shipping & Storage | `businesses/squarefoot_shipping.py` |

**No manual switching needed** - Twilio sends the "To" phone number, and the server loads the right business config automatically.

---

## Configuring Twilio Webhooks

**After starting the server**, you need to configure Twilio to send calls to your ngrok URL.

### Option 1: Automatic Configuration (Recommended)

```bash
python scripts/configure_twilio.py --ngrok-url https://abc123.ngrok-free.app
```

This will:
- Update both phone numbers (+1 239-766-6129, +1 239-880-3365)
- Set webhook URLs to: `https://abc123.ngrok-free.app/twilio/voice`
- Set method to POST

### Option 2: Manual Configuration (Twilio Console)

1. Go to: https://console.twilio.com/us1/develop/phone-numbers/manage/incoming
2. Click on **+1 239-766-6129** (HVAC)
3. Under "Voice Configuration":
   - **A Call Comes In**: Webhook
   - **URL**: `https://abc123.ngrok-free.app/twilio/voice`
   - **HTTP**: POST
4. Click **Save**
5. Repeat for **+1 239-880-3365** (Shipping)

---

## Testing the System

### Test 1: Health Check

```bash
# Check local server
curl http://localhost:8000/health

# Check via ngrok (public)
curl https://abc123.ngrok-free.app/health
```

**Expected Output:**

```json
{
  "status": "healthy",
  "services": {
    "voice_ai": {
      "twilio_configured": true,
      "anthropic_configured": true,
      "deepgram_configured": true
    },
    "forms": {
      "enabled": true,
      "endpoint": "/api/form/submit"
    }
  }
}
```

### Test 2: Make a Test Call

Call one of the numbers from your phone:
- **HVAC**: +1 239-766-6129
- **Shipping**: +1 239-880-3365

You should hear:
- **HVAC**: "Thank you for calling SW Florida Comfort HVAC! This is our AI assistant..."
- **Shipping**: "Thank you for calling Square Foot Shipping and Storage! This is our AI assistant..."

### Test 3: Outreach Call (Sales/Lead Follow-Up)

```bash
python scripts/outreach_call.py "+1XXXXXXXXXX" \
    --person "John Smith" \
    --business "Naples Air Conditioning" \
    --pain-point "no_website"
```

This initiates an outbound sales call using the Voice AI.

---

## Monitoring & Logs

### View Server Logs

```bash
# Live tail
tail -f /tmp/server.log

# Last 50 lines
tail -50 /tmp/server.log
```

### View ngrok Logs

```bash
tail -f /tmp/ngrok.log
```

### Twilio Call Logs

https://console.twilio.com/us1/monitor/logs/calls

---

## Troubleshooting

### Issue: Server Won't Start (Port Already in Use)

**Solution:**

```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9

# Or use restart flag
python scripts/start_server.py --restart
```

### Issue: ngrok URL Changes Every Time

**Why:** Free ngrok URLs change on restart.

**Solution:**

1. Get new URL: `python scripts/start_server.py`
2. Reconfigure Twilio: `python scripts/configure_twilio.py --ngrok-url <NEW_URL>`

**Better Solution:** Upgrade to ngrok paid ($8/mo) for static domain.

### Issue: "Health Check Failed via ngrok"

**Possible Causes:**
- ngrok tunnel not established (wait 5 seconds)
- Server not running on port 8000
- Firewall blocking ngrok

**Debug:**

```bash
# Check if ngrok is running
curl http://localhost:4040/api/tunnels

# Check if server is running
curl http://localhost:8000/health
```

### Issue: Calls Go to Voicemail Instead of AI

**Possible Causes:**
- Twilio webhook not configured
- Wrong webhook URL
- Server not running

**Fix:**

```bash
# 1. Verify server is running
curl http://localhost:8000/health

# 2. Get current ngrok URL
curl http://localhost:4040/api/tunnels | grep public_url

# 3. Reconfigure Twilio
python scripts/configure_twilio.py --ngrok-url <NGROK_URL>

# 4. Test with a call
```

### Issue: "Twilio: ❌" in Status

**Cause:** Missing Twilio credentials in `.env`

**Fix:**

```bash
# Check .env file
cd /Users/williammarceaujr./dev-sandbox
grep TWILIO .env

# Should show:
# TWILIO_ACCOUNT_SID=ACxxxx...
# TWILIO_AUTH_TOKEN=xxxx...
# TWILIO_PHONE_NUMBER=+18552399364
```

If missing, add credentials from: https://console.twilio.com/us1/account/keys-credentials/api-keys

---

## Environment Variables Required

All stored in: `/Users/williammarceaujr./dev-sandbox/.env`

```bash
# Twilio (Voice API)
TWILIO_ACCOUNT_SID=ACxxxx...
TWILIO_AUTH_TOKEN=xxxx...
TWILIO_PHONE_NUMBER=+18552399364  # Outbound caller ID

# Anthropic (Claude API for AI responses)
ANTHROPIC_API_KEY=sk-ant-...

# Deepgram (Speech-to-Text)
DEEPGRAM_API_KEY=xxxx...

# ElevenLabs (Text-to-Speech)
ELEVENLABS_API_KEY=xxxx...
ELEVENLABS_VOICE_ID=21m00Tcm4TlvDq8ikWAM  # Rachel (default)
```

---

## Server Architecture

```
┌─────────────────────────────────────────────┐
│  Twilio Call Comes In                       │
│  (to +1 239-766-6129 or +1 239-880-3365)    │
└────────────────┬────────────────────────────┘
                 │
                 v
┌─────────────────────────────────────────────┐
│  ngrok Tunnel (https://abc123.ngrok...)     │
└────────────────┬────────────────────────────┘
                 │
                 v
┌─────────────────────────────────────────────┐
│  FastAPI Server (localhost:8000)            │
│  /twilio/voice endpoint                     │
└────────────────┬────────────────────────────┘
                 │
                 v
┌─────────────────────────────────────────────┐
│  Business Router                            │
│  Detects "To" number → Loads business config│
└────────────────┬────────────────────────────┘
                 │
        ┌────────┴────────┐
        v                 v
┌──────────────┐  ┌──────────────┐
│ HVAC Config  │  │Shipping Config│
│ swflorida_   │  │ squarefoot_  │
│ hvac.py      │  │ shipping.py  │
└──────┬───────┘  └──────┬───────┘
       │                 │
       └────────┬────────┘
                v
┌─────────────────────────────────────────────┐
│  Business Voice Engine                      │
│  - Deepgram (transcribe)                    │
│  - Claude (understand + respond)            │
│  - ElevenLabs (speak response)              │
└─────────────────────────────────────────────┘
```

---

## Directory Structure

```
/Users/williammarceaujr./dev-sandbox/projects/ai-customer-service/
├── src/
│   ├── main.py                      # FastAPI app (entry point)
│   ├── twilio_handler.py            # Twilio webhook routes
│   ├── business_voice_engine.py     # Multi-business voice logic
│   ├── config.py                    # Environment variables
│   └── form_router.py               # Form submission handler
├── businesses/
│   ├── swflorida_hvac.py            # HVAC business config
│   └── squarefoot_shipping.py       # Shipping business config
├── scripts/
│   ├── start_server.py              # ⭐ Main startup script
│   ├── configure_twilio.py          # Update Twilio webhooks
│   ├── outreach_call.py             # Make outbound calls
│   └── check_call_logs.py           # View call history
└── workflows/
    └── voice-ai-server-sop.md       # This guide (backup location)
```

---

## Production Deployment (Future)

Currently running on **ngrok tunnel** (dev mode).

For production, deploy to:
- **DigitalOcean** ($4/mo droplet + $12/mo domain)
- **Heroku** (free tier available)
- **Railway** (pay-per-use)

Then point `api.marceausolutions.com` to the server.

**When ready:** See `workflows/production-deployment-sop.md` (to be created).

---

## Next Steps

1. ✅ **Start server**: `python scripts/start_server.py`
2. ✅ **Configure Twilio**: `python scripts/configure_twilio.py --ngrok-url <URL>`
3. ✅ **Test with a call**: Dial +1 239-766-6129 or +1 239-880-3365
4. ✅ **Monitor logs**: `tail -f /tmp/server.log`
5. ✅ **Make outreach calls**: `python scripts/outreach_call.py ...`

---

## Contact

Questions? Check:
- **Main AI Customer Service Docs**: `/Users/williammarceaujr./dev-sandbox/projects/ai-customer-service/README.md`
- **Twilio Console**: https://console.twilio.com
- **ngrok Dashboard**: http://localhost:4040 (when tunnel running)

---

**Status:** ✅ Ready for production testing (dev mode with ngrok)
