# Elder Tech Concierge - Deployment Architecture

*Created: 2026-01-16*
*Status: Production Ready (MVP)*

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     Elder Tech Deployment Flow                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. SALES CALL                                                              │
│     ┌─────────────────────────────────────────────────────────────────┐    │
│     │  Collect: Name, Emergency Contacts, Family Contacts             │    │
│     │  Enter into Admin Dashboard → Generate Setup URL                │    │
│     └─────────────────────────────────────────────────────────────────┘    │
│                               │                                             │
│                               ▼                                             │
│  2. ADMIN DASHBOARD (marceausolutions.com/eldertech/admin)                 │
│     ┌─────────────────────────────────────────────────────────────────┐    │
│     │  POST /admin/clients                                             │    │
│     │  → Creates client_id: "abc12345"                                │    │
│     │  → Generates: /setup/abc12345                                    │    │
│     │  → Stores contacts, preferences, tier                           │    │
│     └─────────────────────────────────────────────────────────────────┘    │
│                               │                                             │
│                               ▼                                             │
│  3. iPAD SETUP (You do this before shipping)                               │
│     ┌─────────────────────────────────────────────────────────────────┐    │
│     │  Safari → eldertech.marceausolutions.com/setup/abc12345         │    │
│     │  → Cookie set with client config                                 │    │
│     │  → Redirects to main app (/)                                     │    │
│     │  → App loads with pre-configured contacts                        │    │
│     │  → "Add to Home Screen" → PWA installed                         │    │
│     │  → Guided Access enabled → Kiosk mode                           │    │
│     └─────────────────────────────────────────────────────────────────┘    │
│                               │                                             │
│                               ▼                                             │
│  4. SHIP TO CLIENT                                                         │
│     ┌─────────────────────────────────────────────────────────────────┐    │
│     │  iPad arrives pre-configured                                     │    │
│     │  Client sees: "Hello Dorothy! Tap to talk to me."               │    │
│     │  Training visit: 30 min teaching the UI                          │    │
│     └─────────────────────────────────────────────────────────────────┘    │
│                               │                                             │
│                               ▼                                             │
│  5. ONGOING (Tesla-Style OTA Updates)                                      │
│     ┌─────────────────────────────────────────────────────────────────┐    │
│     │  App polls /api/features every 15 minutes                       │    │
│     │  Admin toggles features → Client sees changes on next poll      │    │
│     │  No app update required!                                         │    │
│     └─────────────────────────────────────────────────────────────────┘    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Key Components

### 1. Client Database (`client_db.py`)

**Purpose:** Store client profiles and configurations

**Tables:**
- `clients` - Profile, subscription status, tier
- `contacts` - Emergency and family contacts
- `preferences` - Speech rate, font size, feature flags
- `activity_log` - Track interactions for monitoring

**CLI Commands:**
```bash
python client_db.py create-test    # Create test client
python client_db.py list           # List all clients
python client_db.py get <id>       # Get client details
python client_db.py stats          # Database statistics
```

---

### 2. Admin Dashboard (`admin.py`)

**Routes:**

| Route | Method | Purpose |
|-------|--------|---------|
| `/admin/login` | GET/POST | Admin authentication |
| `/admin` | GET | Dashboard home |
| `/admin/clients` | GET | List all clients |
| `/admin/clients` | POST | Create new client |
| `/admin/clients/<id>` | GET | Client details |
| `/admin/clients/<id>` | PUT | Update client |
| `/admin/clients/<id>` | DELETE | Delete client |
| `/admin/stats` | GET | System statistics |

**Authentication:**
- Simple password: `ELDER_TECH_ADMIN_PASSWORD` env var
- Default: `eldertech2026` (change in production!)
- Cookie-based session (24 hour expiry)

---

### 3. Setup Endpoint

**Route:** `GET /setup/<client_id>`

**Flow:**
1. Look up client in database
2. Set `client_config` cookie with contacts/preferences
3. Set `client_id` cookie for tracking
4. Mark `setup_completed = True`
5. Redirect to main app (`/`)

**Client-side:**
- JavaScript reads cookie on page load
- Populates contacts in UI
- Stores locally for offline access

---

### 4. Feature Flags (`feature_flags.py`)

**Tesla-Style OTA Updates:**

Features can be enabled/disabled per client without app updates.

**Tiers:**
| Tier | Monthly | Features |
|------|---------|----------|
| Basic | $49 | Voice, Emergency, Calls |
| Standard | $79 | + SMS, Email, Music |
| Premium | $99 | + Calendar, Family Dashboard, Reports |

**Feature Categories:**
- **Core:** Always enabled (Voice, Emergency, Calls)
- **Standard:** Enabled for Standard+ tiers
- **Premium:** Premium tier only
- **Beta:** Opt-in, gradual rollout
- **Accessibility:** Any tier, disabled by default

**API Endpoint:**
```bash
GET /api/features
# Returns current feature flags for client

GET /api/features/catalog
# Returns all available features
```

**How Apps Get Updates:**
```javascript
// Client-side (every 15 minutes)
async function checkFeatures() {
    const response = await fetch('/api/features');
    const data = await response.json();

    // Update UI based on flags
    if (data.flags.music_player) {
        showMusicButton();
    } else {
        hideMusicButton();
    }
}

// Poll periodically
setInterval(checkFeatures, 15 * 60 * 1000);
```

---

## Cross-Platform Compatibility

The architecture is platform-agnostic:

| Feature | iOS (iPad) | Android Tablet | Browser |
|---------|------------|---------------|---------|
| SMS | Twilio (server) | Twilio (server) | Twilio (server) |
| Calls | tel: links | tel: links | Twilio voice |
| Email | Gmail API | Gmail API | Gmail API |
| Voice Input | Web Speech API | Web Speech API | Web Speech API |
| TTS | Web Speech API | Web Speech API | Web Speech API |
| PWA | Safari Add to Home | Chrome Add to Home | N/A |
| Kiosk | Guided Access | Screen Pinning | N/A |

**Recommendation:** Start with iPad (iOS) market, expand to Android when demand warrants.

---

## Database Hosting Options

**MVP (Current):** SQLite (free, embedded)
- Location: `data/clients.db`
- Perfect for < 50 clients
- Zero monthly cost

**Scale (When needed):** Supabase
- Free tier: 500MB, unlimited API calls
- Postgres database
- Built-in auth
- Easy migration from SQLite

---

## File Structure

```
projects/elder-tech-concierge/
├── src/
│   ├── app.py                 # Main Flask app
│   ├── admin.py               # Admin dashboard routes
│   ├── client_db.py           # Client database operations
│   ├── feature_flags.py       # Tesla-style feature system
│   ├── config.py              # Configuration
│   ├── integrations/          # Claude, Twilio, Gmail clients
│   ├── templates/
│   │   ├── index.html         # Main app UI
│   │   └── admin/             # Admin dashboard templates
│   │       ├── login.html
│   │       ├── dashboard.html
│   │       ├── clients.html
│   │       └── client_detail.html
│   └── static/
│       ├── manifest.json      # PWA manifest
│       ├── icon-192.png       # App icon
│       └── icon-512.png       # App icon (large)
├── data/
│   └── clients.db             # SQLite database
├── workflows/
│   ├── hands-free-deployment.md
│   ├── music-integration-spec.md
│   ├── speaker-hardware-spec.md
│   └── deployment-architecture.md  # This file
├── .env                       # Environment variables
└── requirements.txt           # Python dependencies
```

---

## Quick Start

### 1. Start the server
```bash
cd projects/elder-tech-concierge/src
python app.py
# Server at http://0.0.0.0:8080
```

### 2. Access admin dashboard
```
http://localhost:8080/admin?password=eldertech2026
```

### 3. Create a client
- Fill out the form on dashboard
- Get setup URL: `/setup/abc12345`

### 4. Test the setup flow
```
http://localhost:8080/setup/abc12345
# Should redirect to / with contacts configured
```

### 5. Check feature flags
```bash
python feature_flags.py check abc12345
```

---

## Environment Variables

```bash
# Required
ANTHROPIC_API_KEY=sk-ant-...     # Claude API
TWILIO_ACCOUNT_SID=AC...          # Twilio SMS
TWILIO_AUTH_TOKEN=...             # Twilio auth
TWILIO_PHONE_NUMBER=+1...         # Twilio phone

# Optional
ELDER_TECH_ADMIN_PASSWORD=...     # Admin password (default: eldertech2026)
GOOGLE_CLIENT_ID=...              # Gmail integration
GOOGLE_CLIENT_SECRET=...          # Gmail integration
```

---

## Pricing Alignment

| Tier | Setup | Monthly | Features |
|------|-------|---------|----------|
| Basic | $299 | $49 | Voice, Calls, Emergency |
| Standard | $299 | $79 | + SMS, Email, Music |
| Premium | $299 | $99 | + Calendar, Family Dashboard |

**$299 setup covers:**
- iPad pre-configuration (30 min)
- Contact data entry (15 min)
- Delivery + training (1 hr)
- Guided Access setup

---

## Next Steps

1. [x] Client database created
2. [x] Admin dashboard built
3. [x] Setup endpoint working
4. [x] Feature flags system implemented
5. [ ] Deploy to production server
6. [ ] Configure production domain
7. [ ] Set up SSL certificate
8. [ ] Create first real client
9. [ ] Test full iPad deployment flow
10. [ ] Document iPad setup checklist
