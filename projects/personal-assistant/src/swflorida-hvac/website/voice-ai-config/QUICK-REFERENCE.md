# Voice AI - Quick Reference Card

**Server handles BOTH businesses automatically:**
- 🏠 **SW Florida Comfort HVAC** - +1 239-766-6129
- 📦 **Square Foot Shipping** - +1 239-880-3365

---

## Start Server (One Command)

```bash
cd /Users/williammarceaujr./dev-sandbox/projects/ai-customer-service
python scripts/start_server.py
```

**Or use the shortcut:**

```bash
./scripts/start_voice_server.sh
```

---

## Restart Server

```bash
python scripts/start_server.py --restart
```

---

## After Server Starts

**You'll see:**
```
✅ VOICE AI SERVER READY
   Local:  http://localhost:8000
   Public: https://abc123.ngrok-free.app  ← Copy this URL
```

**Then configure Twilio:**

```bash
python scripts/configure_twilio.py --ngrok-url https://abc123.ngrok-free.app
```

---

## Test It Works

**Option 1: Call from your phone**
- HVAC: +1 239-766-6129
- Shipping: +1 239-880-3365

**Option 2: Check health endpoint**

```bash
curl http://localhost:8000/health
```

---

## View Logs

```bash
# Server logs
tail -f /tmp/server.log

# ngrok logs
tail -f /tmp/ngrok.log
```

---

## Make Outreach Calls (Sales/Lead Follow-Up)

```bash
python scripts/outreach_call.py "+1XXXXXXXXXX" \
    --person "John Smith" \
    --business "Naples AC Repair" \
    --pain-point "no_website"
```

---

## Troubleshooting

**Server won't start (port in use)?**

```bash
lsof -ti:8000 | xargs kill -9
python scripts/start_server.py
```

**ngrok URL changed?**

```bash
# Get new URL from server startup output, then:
python scripts/configure_twilio.py --ngrok-url <NEW_URL>
```

**Calls not working?**

1. Check server is running: `curl http://localhost:8000/health`
2. Check ngrok is running: `curl http://localhost:4040/api/tunnels`
3. Reconfigure Twilio with new ngrok URL

---

## Environment Variables

All in: `/Users/williammarceaujr./dev-sandbox/.env`

Required:
- `TWILIO_ACCOUNT_SID`
- `TWILIO_AUTH_TOKEN`
- `ANTHROPIC_API_KEY`
- `DEEPGRAM_API_KEY`
- `ELEVENLABS_API_KEY`

---

## Full Documentation

See: `SERVER-STARTUP.md` (in this directory)

---

**Status:** ✅ Ready to use (dev mode with ngrok)
