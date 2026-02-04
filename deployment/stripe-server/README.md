# Stripe API Server Deployment

Production-ready Stripe server for webhooks and payment APIs.

## Features

- **Webhook Handling**: Receives Stripe events with signature verification
- **Payment APIs**: Create customers, payment links, invoices
- **Revenue Reports**: Query revenue data via API
- **ClickUp Integration**: Auto-update CRM on payment
- **SMS Notifications**: Alert on payments received

## Quick Start

### 1. Prerequisites

```bash
# On EC2, ensure Python packages are installed
pip install flask stripe python-dotenv
```

### 2. Configure Environment

Add to `/home/clawdbot/dev-sandbox/.env`:
```env
STRIPE_SECRET_KEY=sk_live_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx
STRIPE_API_KEY=your-internal-api-key  # For API authentication
NOTIFICATION_PHONE=+1234567890        # Optional: SMS alerts
```

### 3. Deploy

```bash
# Service only (port 5002)
sudo ./deploy.sh

# With nginx reverse proxy
sudo ./deploy.sh --with-nginx

# With nginx + SSL
sudo ./deploy.sh --with-ssl api.yourdomain.com
```

## API Usage

### Authentication

All `/api/*` endpoints require authentication:
```bash
# Via header
curl -H "X-API-Key: your-api-key" https://api.example.com/api/services

# Via Bearer token
curl -H "Authorization: Bearer your-api-key" https://api.example.com/api/services
```

### Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API documentation |
| `/health` | GET | Health check |
| `/webhooks/stripe` | POST | Stripe webhook receiver |
| `/api/customers` | POST | Create customer |
| `/api/payment-links` | POST | Create payment link |
| `/api/invoices` | POST | Create invoice |
| `/api/revenue` | GET | Revenue report |
| `/api/services` | GET | List services |
| `/api/recent-payments` | GET | Recent payments |

### Examples

**Create Customer:**
```bash
curl -X POST https://api.example.com/api/customers \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"email": "client@example.com", "name": "John Doe"}'
```

**Create Payment Link:**
```bash
curl -X POST https://api.example.com/api/payment-links \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"amount": 500, "description": "Consulting - 5 hours", "clickup_task": "abc123"}'
```

**Create Payment Link from Service:**
```bash
curl -X POST https://api.example.com/api/payment-links \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"service": "website_basic", "clickup_task": "abc123"}'
```

**Get Revenue Report:**
```bash
curl "https://api.example.com/api/revenue?days=30" \
  -H "X-API-Key: your-api-key"
```

## Stripe Webhook Configuration

1. Go to [Stripe Dashboard → Webhooks](https://dashboard.stripe.com/webhooks)
2. Add endpoint: `https://api.yourdomain.com/webhooks/stripe`
3. Select events:
   - `checkout.session.completed`
   - `invoice.paid`
   - `payment_intent.succeeded`
   - `customer.subscription.created`
4. Copy the signing secret to `STRIPE_WEBHOOK_SECRET` in `.env`

## Management

```bash
# View status
sudo systemctl status stripe-server

# View logs
sudo journalctl -u stripe-server -f
tail -f /var/log/stripe-server/server.log

# Restart
sudo systemctl restart stripe-server

# Stop
sudo systemctl stop stripe-server
```

## Security

- API key authentication for all `/api/*` endpoints
- Stripe signature verification for webhooks
- Rate limiting via nginx (10 req/sec)
- Security headers (X-Frame-Options, X-XSS-Protection, etc.)
- systemd hardening (NoNewPrivileges, ProtectSystem)

## Files

```
deployment/stripe-server/
├── deploy.sh              # Deployment script
├── stripe-server.service  # systemd unit file
├── nginx-stripe.conf      # nginx configuration
└── README.md              # This file
```
