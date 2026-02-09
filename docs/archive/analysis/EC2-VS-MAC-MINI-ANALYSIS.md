# AWS EC2 vs Mac Mini for Claude Bots & Automation

*Analysis Date: 2026-01-26*

## Executive Summary

| Factor | Mac Mini | EC2 | Winner |
|--------|----------|-----|--------|
| **Upfront Cost** | $700-800 | $0 | EC2 |
| **Monthly Cost** | ~$2.50 | $30-40 | Mac Mini |
| **5-Year TCO** | ~$1,830 | ~$2,500 | Mac Mini |
| **Setup Complexity** | Medium | Low | EC2 |
| **Disaster Recovery** | Manual | Built-in | EC2 |
| **Scalability** | None | Elastic | EC2 |
| **Latency (Local Dev)** | Excellent | Good | Mac Mini |

**Bottom Line**: Mac Mini wins on cost if you already have one. EC2 wins on flexibility, reliability, and zero-maintenance.

---

## Your Current Setup

Based on your dev-sandbox, you're running:
- Twilio SMS webhook handlers
- SW Florida Comfort website (ngrok tunnel)
- Social media automation (cron jobs)
- MCP servers (9 published)
- Personal assistant digest aggregator
- Apollo lead scraper

**Current Infrastructure**:
- Local Mac (always on)
- ngrok tunnels ($0-10/month)
- No cloud instances

---

## Recommended Architecture

### Option A: Keep Mac Mini + Add EC2 for Reliability (Hybrid)

```
┌─────────────────────────────────────────────────────────┐
│ LOCAL MAC (Development)                                 │
├─────────────────────────────────────────────────────────┤
│ ✓ Claude Code sessions                                  │
│ ✓ MCP server development                                │
│ ✓ Testing and iteration                                 │
│ ✓ Temporary ngrok tunnels                               │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ EC2 t4g.small ($15/month) - PRODUCTION                  │
├─────────────────────────────────────────────────────────┤
│ ✓ Twilio webhook handler (always on)                    │
│ ✓ SW Florida Comfort website                            │
│ ✓ Voice AI API endpoint                                 │
│ ✓ Form submission handler                               │
│ ✓ Cron jobs (analytics, digests)                        │
│ ✓ Static IP (no ngrok needed)                           │
└─────────────────────────────────────────────────────────┘

Monthly Cost: ~$18-20
Benefits: 99.95% uptime SLA, no ngrok dependency, proper DNS
```

### Option B: Full EC2 Migration

```
┌─────────────────────────────────────────────────────────┐
│ EC2 t4g.medium ($30/month) - ALL SERVICES               │
├─────────────────────────────────────────────────────────┤
│ ✓ All webhooks and APIs                                 │
│ ✓ All websites                                          │
│ ✓ All cron jobs                                         │
│ ✓ MCP servers (production)                              │
│ ✓ Ralph autonomous agents                               │
└─────────────────────────────────────────────────────────┘
         +
┌─────────────────────────────────────────────────────────┐
│ AWS Lambda ($5-10/month) - SCHEDULED TASKS              │
├─────────────────────────────────────────────────────────┤
│ ✓ Daily digest generation                               │
│ ✓ Weekly analytics reports                              │
│ ✓ Form processing (event-driven)                        │
└─────────────────────────────────────────────────────────┘

Monthly Cost: ~$35-40
Benefits: Zero local dependency, can work from anywhere
```

---

## Cost Comparison (Your Use Case)

### Current Setup
| Item | Monthly | Annual |
|------|---------|--------|
| Mac power | ~$2.50 | $30 |
| ngrok (free tier) | $0 | $0 |
| **Total** | **$2.50** | **$30** |

### Option A: Hybrid
| Item | Monthly | Annual |
|------|---------|--------|
| EC2 t4g.small | $15.18 | $182 |
| Elastic IP | $3.60 | $43 |
| EBS Storage (30GB) | $2.40 | $29 |
| Data Transfer | ~$5 | $60 |
| **Total** | **~$26** | **~$314** |

### Option B: Full Cloud
| Item | Monthly | Annual |
|------|---------|--------|
| EC2 t4g.medium | $30.37 | $364 |
| Elastic IP | $3.60 | $43 |
| EBS Storage (50GB) | $4.00 | $48 |
| Lambda | ~$5 | $60 |
| Data Transfer | ~$10 | $120 |
| **Total** | **~$53** | **~$635** |

---

## EC2 Instance Recommendations

| Instance | vCPU | RAM | Monthly | Best For |
|----------|------|-----|---------|----------|
| **t4g.micro** | 1 | 1GB | $7.59 | Free tier testing |
| **t4g.small** | 2 | 2GB | $15.18 | Lightweight bots |
| **t4g.medium** | 2 | 4GB | $30.37 | **Recommended** |
| **t4g.large** | 2 | 8GB | $60.74 | Heavy workloads |

**Why t4g (Graviton/ARM)?**
- 40% better price-performance than Intel/AMD
- Python runs perfectly on ARM
- Most packages have ARM builds

---

## Eliminating ngrok Dependency

**Current**: ngrok tunnels for webhooks → Limited, can fail
**Better**: EC2 with Elastic IP → Permanent, reliable

### DNS Configuration

```
# Point your domains directly to EC2:
api.marceausolutions.com  → A record → [Elastic IP]
www.swfloridacomfort.com  → A record → [Elastic IP]

# No more ngrok tunnels needed!
```

### Security Groups (Firewall)

```
Inbound Rules:
- Port 22 (SSH): Your IP only
- Port 80 (HTTP): 0.0.0.0/0
- Port 443 (HTTPS): 0.0.0.0/0
- Port 8000 (Voice AI): 0.0.0.0/0
- Port 3002 (HVAC site): 0.0.0.0/0
```

---

## Implementation Steps

### Phase 1: Launch EC2 Instance (30 min)

```bash
# 1. Create EC2 instance via AWS Console or CLI
aws ec2 run-instances \
  --image-id ami-0c55b159cbfafe1f0 \  # Amazon Linux 2023 ARM
  --instance-type t4g.small \
  --key-name your-key-pair \
  --security-groups web-server-sg

# 2. Allocate Elastic IP
aws ec2 allocate-address --domain vpc

# 3. Associate Elastic IP with instance
aws ec2 associate-address --instance-id i-xxx --allocation-id eipalloc-xxx
```

### Phase 2: Setup Server (1 hour)

```bash
# SSH into instance
ssh -i your-key.pem ec2-user@[elastic-ip]

# Install dependencies
sudo yum update -y
sudo yum install python3 python3-pip git nginx -y

# Clone your code
git clone https://github.com/wmarceau/dev-sandbox.git
cd dev-sandbox

# Install Python packages
pip3 install -r requirements.txt

# Setup systemd services (auto-restart on failure)
sudo systemctl enable swflorida-website
sudo systemctl enable twilio-webhook
sudo systemctl enable voice-api
```

### Phase 3: DNS Migration (15 min)

```
# In your DNS provider (Cloudflare, Route53, etc.):

1. Remove ngrok CNAME records
2. Add A records pointing to Elastic IP:
   - api.marceausolutions.com → [Elastic IP]
   - www.swfloridacomfort.com → [Elastic IP]

3. Wait for propagation (5-30 min)
```

### Phase 4: SSL Certificates (15 min)

```bash
# Install certbot
sudo yum install certbot python3-certbot-nginx -y

# Get certificates
sudo certbot --nginx -d api.marceausolutions.com -d www.swfloridacomfort.com

# Auto-renewal (certbot adds cron automatically)
```

---

## Migration Checklist

- [ ] Launch EC2 t4g.small instance
- [ ] Allocate and associate Elastic IP
- [ ] Install Python, pip, nginx
- [ ] Clone dev-sandbox repository
- [ ] Create systemd services for:
  - [ ] SW Florida Comfort website (port 3002)
  - [ ] Twilio webhook handler (port 8000)
  - [ ] Voice AI API
- [ ] Configure nginx as reverse proxy
- [ ] Update DNS records (remove ngrok)
- [ ] Install SSL certificates
- [ ] Test all endpoints
- [ ] Disable local ngrok tunnels
- [ ] Setup CloudWatch monitoring

---

## Monthly Maintenance

1. **Weekly**: Check CloudWatch metrics
2. **Monthly**: Review costs in AWS Cost Explorer
3. **Quarterly**: Update packages, review security groups
4. **Annually**: Consider Reserved Instances (save 30-40%)

---

## Decision: What Should You Do?

**Recommendation: Start with Option A (Hybrid)**

1. Keep your Mac for development
2. Launch one EC2 t4g.small ($15/month)
3. Migrate production webhooks to EC2
4. Eliminate ngrok dependency
5. Get proper SSL + static IP

**Why?**
- Low risk (can always revert)
- Modest cost increase ($15 → $25/month)
- Major reliability improvement
- Professional setup (proper DNS, SSL)

---

## Next Steps

1. **Create AWS account** (if you don't have one)
2. **Launch EC2 instance** following Phase 1 steps
3. **Test migration** with one service (SW Florida website)
4. **Expand** to other services once proven

Would you like me to help you execute Phase 1?
