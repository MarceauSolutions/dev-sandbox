# n8n on EC2 Setup Guide

*Created: 2026-02-01*
*Last Updated: 2026-02-01*

## Current Status: TROUBLESHOOTING

**Issue:** Port 5678 not accessible from internet despite:
- n8n running and listening on `*:5678`
- Security group open to `0.0.0.0/0`
- No iptables firewall blocking

**Next step to debug:** Run from Mac:
```bash
curl -v http://34.193.98.97:5678/healthz
```

---

## Server Status

| Component | Status |
|-----------|--------|
| n8n Service | Running (v2.4.8) |
| Systemd | Enabled (auto-restart) |
| Workflows | 6 imported (inactive) |
| Credentials | **NEEDS SETUP** |
| External Access | **NOT WORKING - debugging** |

## Access n8n UI

### Step 1: Open SSH Tunnel

Run this on your Mac:
```bash
ssh -i ~/.ssh/marceau-ec2-key.pem -L 5679:localhost:5678 ec2-user@34.193.98.97
```

Keep this terminal open.

### Step 2: Open n8n in Browser

Go to: **http://localhost:5679**

### Step 3: First-Time Setup

1. Create your admin account (use wmarceau@marceausolutions.com)
2. Skip the onboarding prompts

## Credential Setup

### 1. SMTP (Gmail) - For Email Alerts

Go to: **Settings → Credentials → Add Credential**

| Field | Value |
|-------|-------|
| Type | SMTP |
| Name | Gmail SMTP |
| Host | smtp.gmail.com |
| Port | 587 |
| User | wmarceau@marceausolutions.com |
| Password | oaei kdah jrfo pgpm |
| SSL/TLS | STARTTLS |

**Test**: Send a test email.

### 2. Google Sheets - For Logging

Go to: **Settings → Credentials → Add Credential**

| Field | Value |
|-------|-------|
| Type | Google Sheets OAuth2 |
| Name | Google Sheets |
| Client ID | 915754256960-ujpassm3aaf9s8hkn3dbusm5euq5qhb2.apps.googleusercontent.com |
| Client Secret | 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 |

**OAuth Redirect URI** (add to Google Cloud Console):
```
http://localhost:5679/rest/oauth2-credential/callback
```

Click "Connect" and authorize with your Google account.

### 3. Gmail - For Reading Emails

Go to: **Settings → Credentials → Add Credential**

| Field | Value |
|-------|-------|
| Type | Gmail OAuth2 |
| Name | Gmail |
| Client ID | 915754256960-ujpassm3aaf9s8hkn3dbusm5euq5qhb2.apps.googleusercontent.com |
| Client Secret | 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 |

Click "Connect" and authorize.

## Activate Workflows

After credentials are set up:

1. Go to **Workflows**
2. Open each workflow
3. Click the **Active** toggle (top right)
4. Verify no credential errors

### Workflows to Activate

| Workflow | Trigger | Webhook Path |
|----------|---------|--------------|
| SMS-Response-Handler-v2 | Webhook | /n8n-webhook/sms-response |
| Form-Submission-Pipeline | Webhook | /n8n-webhook/form-submit |
| Daily-Operations-Digest | Schedule | 8 AM daily |
| Follow-Up-Sequence-Engine | Webhook | /n8n-webhook/enroll-followup |
| Hot-Lead-to-ClickUp | Webhook | /n8n-webhook/hot-lead-clickup |
| X-Social-Post-Scheduler | Schedule | Custom schedule |

## Update Twilio Webhook

After activating SMS-Response-Handler-v2, update Twilio:

1. Go to: https://console.twilio.com
2. Navigate to: Phone Numbers → Manage → Active Numbers
3. Click on: +1 855 239 9364
4. Under "Messaging", set webhook to:
   ```
   http://34.193.98.97/n8n-webhook/sms-response
   ```
5. Set method to: POST

## Test Webhooks

### SMS Webhook Test
```bash
curl -X POST http://34.193.98.97/n8n-webhook/sms-response \
  -d "From=+1234567890&Body=Test message"
```

### Form Webhook Test
```bash
curl -X POST http://34.193.98.97/n8n-webhook/form-submit \
  -H "Content-Type: application/json" \
  -d '{"name":"Test User","email":"test@example.com","message":"Test submission"}'
```

## Troubleshooting

### n8n Not Starting
```bash
ssh -i ~/.ssh/marceau-ec2-key.pem ec2-user@34.193.98.97
sudo systemctl status n8n
sudo journalctl -u n8n -n 50
```

### Restart n8n
```bash
sudo systemctl restart n8n
```

### View Logs
```bash
sudo journalctl -u n8n -f
```

## Server Details

| Property | Value |
|----------|-------|
| EC2 IP | 34.193.98.97 |
| n8n Port | 5678 (internal) |
| Webhook URL | http://34.193.98.97/n8n-webhook/{path} |
| Data Directory | /var/lib/n8n |
| Service | systemd (n8n.service) |
| Timezone | America/New_York |
