# Project Tracker Deployment

Deploy to: **tracker.marceausolutions.com**
Port: **5030**

## Step 1: DNS Record

Add A record in your DNS provider (Cloudflare/Route53):
```
tracker.marceausolutions.com → [EC2 Public IP]
```

## Step 2: Install Systemd Service

```bash
sudo cp deploy/tracker.service /etc/systemd/system/project-tracker.service
sudo systemctl daemon-reload
sudo systemctl enable project-tracker
sudo systemctl start project-tracker
```

## Step 3: Add Nginx Config

```bash
# Append to existing nginx config
sudo bash -c 'cat deploy/tracker.nginx.conf >> /etc/nginx/conf.d/sites.conf'
sudo nginx -t
sudo systemctl reload nginx
```

## Step 4: SSL Certificate

```bash
sudo certbot --nginx -d tracker.marceausolutions.com
```

## Verify

```bash
# Check service is running
systemctl status project-tracker

# Check nginx config
sudo nginx -t

# Test locally
curl http://localhost:5030/health

# Test public
curl https://tracker.marceausolutions.com/health
```

## Quick Deploy (All Steps)

```bash
cd /home/clawdbot/dev-sandbox/execution/project_tracker

# 1. Install service
sudo cp deploy/tracker.service /etc/systemd/system/project-tracker.service
sudo systemctl daemon-reload
sudo systemctl enable project-tracker
sudo systemctl start project-tracker

# 2. Add nginx (assumes DNS is already set)
sudo bash -c 'cat deploy/tracker.nginx.conf >> /etc/nginx/conf.d/sites.conf'
sudo nginx -t && sudo systemctl reload nginx

# 3. SSL
sudo certbot --nginx -d tracker.marceausolutions.com

# 4. Verify
curl https://tracker.marceausolutions.com/health
```
