# SW Florida Comfort HVAC - ngrok Tunnel Setup

## Quick Start

```bash
cd /Users/williammarceaujr./swflorida-comfort-hvac
./start-tunnel.sh
```

This will:
1. Start a web server on `http://localhost:3002`
2. Start ngrok tunnel to `www.swfloridacomfort.com`

## DNS Configuration

**Domain:** `www.swfloridacomfort.com`

### Namecheap DNS Records Required

| Type | Host | Value | TTL |
|------|------|-------|-----|
| CNAME | www | `tunnel.us.ngrok.com` | Automatic |

**Or if using A record:**

| Type | Host | Value | TTL |
|------|------|-------|-----|
| A | www | [ngrok IP from dashboard] | Automatic |

### How to Add DNS Records in Namecheap

1. Go to https://namecheap.com
2. Sign in to your account
3. Click "Domain List" in left sidebar
4. Find `swfloridacomfort.com` and click "Manage"
5. Go to "Advanced DNS" tab
6. Click "Add New Record"
7. Select "CNAME Record"
8. Set:
   - Host: `www`
   - Value: `tunnel.us.ngrok.com`
   - TTL: Automatic
9. Click the green checkmark to save

### Verify DNS Propagation

```bash
# Check if DNS is set up correctly
dig www.swfloridacomfort.com

# Should show CNAME pointing to tunnel.us.ngrok.com
```

**Note:** DNS changes can take 5-30 minutes to propagate.

## ngrok Configuration

The ngrok config is located at:
```
/Users/williammarceaujr./Library/Application Support/ngrok/ngrok.yml
```

HVAC tunnel configuration:
```yaml
tunnels:
  hvac:
    proto: http
    addr: 3002
    domain: www.swfloridacomfort.com
```

## Verify Tunnel Status

Once running, check:

1. **Local server:** http://localhost:3002
2. **ngrok web interface:** http://localhost:4040
3. **Public URL:** https://www.swfloridacomfort.com

## Troubleshooting

### "Domain not verified" in ngrok

**Cause:** DNS records not set up or not propagated yet

**Fix:**
1. Add CNAME record in Namecheap (see above)
2. Wait 5-30 minutes for DNS propagation
3. Verify with `dig www.swfloridacomfort.com`
4. Restart ngrok tunnel

### Port 3002 already in use

**Cause:** Server already running from previous session

**Fix:**
```bash
# Find and kill the process
lsof -ti:3002 | xargs kill -9

# Or the startup script will prompt you
```

### Website shows 502 Bad Gateway

**Cause:** Web server not running

**Fix:**
```bash
# Check if server is running
lsof -i:3002

# If not, start it
cd /Users/williammarceaujr./swflorida-comfort-hvac
python3 serve.py
```

## Manual Commands

### Start web server only
```bash
cd /Users/williammarceaujr./swflorida-comfort-hvac
python3 serve.py
```

### Start ngrok tunnel only
```bash
ngrok start hvac
```

### View ngrok logs
```bash
ngrok logs
```

### Check running tunnels
```bash
curl http://localhost:4040/api/tunnels | jq
```

## Files

- `serve.py` - Python HTTP server (port 3002)
- `start-tunnel.sh` - Combined startup script
- `NGROK-SETUP.md` - This file

## Next Steps

1. ✅ ngrok config file created (`ngrok.yml`)
2. ✅ Web server script created (`serve.py`)
3. ✅ Startup script created (`start-tunnel.sh`)
4. ⏳ **Add DNS records in Namecheap** (you mentioned you already did this)
5. ⏳ **Run `./start-tunnel.sh`** to start the tunnel
6. ⏳ **Verify** website loads at https://www.swfloridacomfort.com

---

*Last Updated: 2026-01-20*
