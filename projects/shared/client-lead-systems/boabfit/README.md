# BoabFit Lead Nurturing System

Automated lead capture and email drip sequence for the BoabFit 6-Week Barbie Body program.

## Architecture

```
Landing Page (6week.html)
         │
         ▼
    n8n Webhook (/webhook/boabfit-signup)
         │
    ┌────┴────────────────────────┐
    │                              │
    ▼                              ▼
Immediate Actions            Lead Nurturing Service
• Welcome email              (localhost:5025)
• Notify Julia + William          │
• Respond to webhook              ▼
                             SQLite Database
                                  │
                             ┌────┴────┐
                             │         │
                             ▼         ▼
                          Leads    Email Queue
                                       │
                     Hourly Processor ◄┘
                     (n8n scheduled)
                             │
                             ▼
                      Drip Emails Sent
```

## Components

### 1. Landing Page Form
- URL: https://marceausolutions.github.io/boabfit-website/6week.html
- Collects: email, name, phone, commitment level
- Posts to: `https://n8n.marceausolutions.com/webhook/boabfit-signup`

### 2. n8n Workflows (Active)
- **BOABFIT - Signup Complete** (LZWsipBAXKTMMVjV)
  - Receives webhook
  - Sends welcome email immediately
  - Notifies Julia + William
  - Forwards to lead nurturing service
  
- **BOABFIT - Abandonment Tracker** (ibb87FTli1Z5AGPW)
  - Tracks partial form completions
  - Notifies William

- **BoabFit - Drip Sequence Processor** (5dhcbMi7wIwUrL3O)
  - Runs hourly
  - Sends scheduled drip emails

### 3. Lead Nurturing Service
- Port: 5025
- Location: `src/webhook_handler.py`
- Database: `leads.db`

#### Endpoints
- `POST /webhook/boabfit-signup` - Receive new signups
- `POST /process-queue` - Process due emails
- `GET /stats` - Lead statistics
- `GET /health` - Health check

### 4. Email Drip Sequence

| Timing | Template | Subject |
|--------|----------|---------|
| Immediate | welcome | 🎉 You're In! Welcome to BOABFIT |
| +24 hours | day1_getting_started | 💪 Day 1: Let's Get Started! |
| +72 hours | day3_checkin | 📊 Day 3 Check-In: How Are You Feeling? |
| +7 days | day7_motivation | 🏆 Week 1 DONE! You're Officially Crushing It |
| +14 days | day14_halfway | 🔥 HALFWAY! 3 Weeks Down, 3 To Go |

## Management

### Check Stats
```bash
curl http://localhost:5025/stats
```

### View Pending Emails
```bash
sqlite3 leads.db "SELECT * FROM email_queue WHERE status='pending'"
```

### Manual Email Queue Process
```bash
curl -X POST http://localhost:5025/process-queue
```

### Start Service
```bash
/home/clawdbot/scripts/start-boabfit-leads.sh
```

## Files
```
boabfit/
├── README.md              # This file
├── config.json            # Client configuration
├── leads.db               # SQLite database
├── src/
│   ├── lead_db.py         # Database operations
│   ├── email_sender.py    # SMTP email delivery
│   └── webhook_handler.py # Flask webhook server
└── email-templates/
    └── welcome.html       # HTML welcome email
```

## Replicating for New Clients

This system is designed to be templatable:

1. Copy `boabfit/` to `[client-name]/`
2. Update `config.json` with client details
3. Create client-specific email templates
4. Create n8n workflows pointing to new service
5. Update landing page webhook URLs

See `ARCHITECTURE.md` for the full client lead system design.
