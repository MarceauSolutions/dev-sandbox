# KeyVault — API Key Management SaaS

Production SaaS platform for managing API keys, credentials, and service connections across multiple environments. Built by Marceau Solutions.

## Live URLs
- **Local**: http://127.0.0.1:8793
- **Production**: https://keys.marceausolutions.com (pending DNS A record)
- **EC2 Service**: systemd `keyvault.service` on port 8793 behind nginx

## Login
- **Email**: wmarceau@marceausolutions.com
- **Password**: keyvault2026!

## Features
- **Multi-tenant auth** — JWT login/signup, organizations, role-based access (owner/admin/member/viewer)
- **Encrypted storage** — Fernet (AES-256) encryption for key values at rest
- **Health monitoring** — Automated verification that keys actually work (9 service integrations)
- **Environment sync** — Detect credential drift between Mac, EC2, Clawdbot, n8n
- **Expiration alerts** — SMS, email, Telegram, webhook notifications
- **Deprecation tracking** — Log API changes with migration notes
- **API access** — RESTful API with bearer token auth
- **Billing tiers** — Free (25 keys) / Pro $29/mo (100 keys) / Enterprise $99/mo (1000 keys)
- **Audit log** — Every action tracked with user, timestamp, IP
- **Landing page** — Marketing page with pricing for client demos

## Commands
| Command | What It Does |
|---------|-------------|
| `./scripts/api-key-manager.sh` | Launch web dashboard locally |
| `./scripts/api-key-manager.sh --seed-force` | Re-seed database from scratch |
| `./scripts/api-key-manager.sh --sync` | Check sync status between Mac and EC2 |
| `python -m projects.shared.api-key-manager.src.health_checker` | Run health checks on all keys |
| `python -m projects.shared.api-key-manager.src.scheduled_tasks --all` | Run all scheduled tasks (health + expiry + notify) |
| `python -m projects.shared.api-key-manager.src.sync_env` | Push Mac keys to EC2 |

## Architecture
```
projects/shared/api-key-manager/
├── CLAUDE.md
├── data/
│   ├── keyvault.db          # SQLite database (gitignored)
│   └── .encryption_key      # Fernet key (gitignored, auto-generated)
└── src/
    ├── __init__.py
    ├── models.py             # DB schema, auth, encryption, CRUD
    ├── app.py                # FastAPI routes (auth, dashboard, API)
    ├── ui.py                 # Complete SaaS UI templates
    ├── seed.py               # Initial data population
    ├── health_checker.py     # Automated key verification (9 services)
    ├── scheduled_tasks.py    # Cron-triggered health + expiry + notifications
    ├── sync_checker.py       # Mac vs EC2 env comparison
    └── sync_env.py           # Push Mac keys to EC2
```

## API Endpoints (authenticated)
- `GET /api/v1/health` — Public health check
- `GET /api/v1/summary` — Dashboard stats
- `GET /api/v1/keys` — All keys (no values)
- `GET /api/v1/keys/expiring?days=30` — Expiring keys
- `GET /api/v1/deprecations` — Active deprecations

## EC2 Deployment
- **Service**: `/etc/systemd/system/keyvault.service`
- **Nginx**: `/etc/nginx/conf.d/keyvault.conf`
- **Code**: `/home/clawdbot/keyvault/`
- **DB**: `/home/clawdbot/keyvault/data/keyvault.db`
- **DNS**: `keys.marceausolutions.com` → A record → `34.193.98.97` (pending)
- **SSL**: Run `sudo certbot --nginx -d keys.marceausolutions.com` after DNS propagates

## Health Check Integrations
Anthropic, OpenAI, Stripe, Twilio, ElevenLabs, Replicate, xAI, Apollo.io, X/Twitter

## Generated Files
- `data/keyvault.db` — SQLite database
- `data/.encryption_key` — Fernet encryption key (DO NOT DELETE)
