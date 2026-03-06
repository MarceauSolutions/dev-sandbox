# EC2 Server Information

*Created: 2026-01-26*

## Server Details

| Property | Value |
|----------|-------|
| **Instance ID** | `i-01752306f94897d7d` |
| **Instance Type** | `t4g.small` (2 vCPU, 2GB RAM, ARM) |
| **Elastic IP** | `34.193.98.97` |
| **Region** | us-east-1 |
| **OS** | Amazon Linux 2023 (ARM64) |
| **Storage** | 30GB gp3 EBS |

## Access

### SSH Connection
```bash
ssh -i ~/.ssh/marceau-ec2-key.pem ec2-user@34.193.98.97
```

### SSH Key Location
```
~/.ssh/marceau-ec2-key.pem
```

## Services Running

### SW Florida Comfort Website
- **URL**: https://swfloridacomfort.com (SSL enabled)
- **Alt URL**: http://34.193.98.97:3002
- **Files**: `/var/www/swflorida-comfort/`
- **Config**: `/etc/nginx/conf.d/swflorida-comfort.conf`
- **SSL**: Let's Encrypt (auto-renews via certbot-renew.timer)

### Voice AI API (Twilio Webhooks)
- **URL**: https://api.marceausolutions.com (pending DNS update)
- **Direct**: http://34.193.98.97:8000
- **Files**: `/var/www/ai-customer-service/`
- **Config**: `/etc/nginx/conf.d/voice-api.conf`
- **Service**: `voice-api.service` (systemd)
- **Env**: `/var/www/ai-customer-service/.env`

## Security Group

**Name**: `marceau-web-server`
**ID**: `sg-0df0d2c4080a9348d`

| Port | Protocol | Source | Purpose |
|------|----------|--------|---------|
| 22 | TCP | Your IP (69.242.254.222) | SSH |
| 80 | TCP | 0.0.0.0/0 | HTTP |
| 443 | TCP | 0.0.0.0/0 | HTTPS |
| 3002 | TCP | 0.0.0.0/0 | HVAC website |
| 8000 | TCP | 0.0.0.0/0 | Voice AI API |

## AWS Credentials

Stored in `/Users/williammarceaujr./dev-sandbox/.env`:
```
AWS_EC2_ACCESS_KEY=AKIAQCK3KHMRF44TLIPM
AWS_EC2_SECRET_KEY=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
AWS_DEFAULT_REGION=us-east-1
```

## Monthly Cost Estimate

| Item | Cost |
|------|------|
| EC2 t4g.small | $15.18 |
| Elastic IP | $3.60 |
| EBS 30GB | $2.40 |
| Data Transfer | ~$5.00 |
| **Total** | **~$26/month** |

## DNS Configuration

### Completed
- ✅ `swfloridacomfort.com` → A record → 34.193.98.97
- ✅ `www.swfloridacomfort.com` → A record → 34.193.98.97
- ✅ SSL certificates installed (Let's Encrypt)

### Pending (Namecheap - marceausolutions.com)
- ⬜ `api.marceausolutions.com` → A record → 34.193.98.97
  - Currently: CNAME to ngrok (needs update)
  - After update: Run `sudo certbot --nginx -d api.marceausolutions.com`

## Useful Commands

```bash
# SSH into server
ssh -i ~/.ssh/marceau-ec2-key.pem ec2-user@34.193.98.97

# Check nginx status
sudo systemctl status nginx

# View nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# Restart nginx
sudo systemctl restart nginx

# Update website files (from local Mac)
scp -i ~/.ssh/marceau-ec2-key.pem -r /Users/williammarceaujr./dev-sandbox/projects/swflorida-hvac/website/* ec2-user@34.193.98.97:/var/www/swflorida-comfort/

# Check Voice API status
sudo systemctl status voice-api

# View Voice API logs
sudo journalctl -u voice-api -f

# Restart Voice API
sudo systemctl restart voice-api
```

## AWS CLI Commands

```bash
# Set credentials
export AWS_ACCESS_KEY_ID="AKIAQCK3KHMRF44TLIPM"
export AWS_SECRET_ACCESS_KEY="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"
export AWS_DEFAULT_REGION="us-east-1"

# Check instance status
aws ec2 describe-instances --instance-ids i-01752306f94897d7d

# Stop instance (to save money when not needed)
aws ec2 stop-instances --instance-ids i-01752306f94897d7d

# Start instance
aws ec2 start-instances --instance-ids i-01752306f94897d7d

# Reboot instance
aws ec2 reboot-instances --instance-ids i-01752306f94897d7d
```
