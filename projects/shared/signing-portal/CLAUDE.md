# Signing Portal — Client Agreement Signing

> Client-facing branded page for e-signing service agreements.
> Local: `http://localhost:8797/{token}`
> Production: `https://sign.marceausolutions.com/{token}`

## How It Works

1. `close_deal.py` calls `create_signing_agreement(...)` → generates UUID token → inserts into SQLite → returns URL
2. URL goes in the outreach email and is printed in terminal output
3. Client visits URL → sees branded agreement page → types name → clicks sign
4. On submit: marks DB record signed, sends confirmation email to client, sends Telegram notification to William
5. Client sees success page; William gets pinged

## Files

| File | Purpose |
|------|---------|
| `app.py` | Flask app — all routes |
| `models.py` | SQLite schema + CRUD — `signing_portal.db` |
| `run.sh` | Direct launch script |
| `signing_portal.db` | SQLite database (auto-created on first run) |

## Routes

| Route | Method | Description |
|-------|--------|-------------|
| `/{token}` | GET | Show branded signing page |
| `/{token}/sign` | POST | Process signature |
| `/success` | GET | Generic success page |
| `/health` | GET | Health check → JSON `{"status": "ok"}` |

## Database: `agreements` Table

| Column | Type | Notes |
|--------|------|-------|
| `token` | TEXT PK | UUID from `close_deal.py` |
| `business_name` | TEXT | Client's business |
| `client_name` | TEXT | Contact name |
| `client_email` | TEXT | Contact email |
| `tier` | INTEGER | 1–4 |
| `monthly_rate` | TEXT | e.g. `$297/month` |
| `effective_date` | TEXT | ISO date |
| `status` | TEXT | `pending` / `signed` / `expired` |
| `signer_name` | TEXT | Typed at signing |
| `signer_ip` | TEXT | Client IP at signing |
| `signed_at` | TEXT | ISO datetime |
| `created_at` | TEXT | ISO datetime |

## Launch

```bash
# Direct
bash projects/shared/signing-portal/run.sh

# Via launch script
./scripts/signing-portal.sh
```

## Environment Variables

| Key | Required | Default |
|-----|----------|---------|
| `SMTP_USERNAME` | Yes | — |
| `SMTP_PASSWORD` | Yes | — |
| `SMTP_HOST` | No | `smtp.gmail.com` |
| `SMTP_PORT` | No | `587` |
| `TELEGRAM_BOT_TOKEN` | Yes | — |
| `TELEGRAM_CHAT_ID` | No | `5692454753` |
| `SIGNING_PORTAL_URL` | No | `http://localhost:8797` |
| `SIGNING_PORTAL_PORT` | No | `8797` |

## Integration with close_deal.py

`create_signing_agreement()` in `close_deal.py`:
- Generates UUID token
- Inserts pending agreement into `signing_portal.db`
- Returns full signing URL
- URL injected into outreach email and printed to terminal

## Integration with Sales Pipeline

Deal detail page (`/deals/{id}`) has a "Send Proposal & Agreement" card that:
1. Pre-fills tier/contact from deal data
2. Calls `POST /deals/{id}/send-proposal`
3. Runs `close_deal.py` → generates PDFs, sends email with signing URL, logs outreach
4. Shows signing URL + PDF path on success
5. Auto-advances deal stage to "Proposal Sent"
