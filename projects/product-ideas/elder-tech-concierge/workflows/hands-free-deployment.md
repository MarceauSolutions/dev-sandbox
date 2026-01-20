# Hands-Free Elder Tech Deployment Strategy

*Created: 2026-01-16*
*Goal: Minimize setup friction - senior only needs to learn the UI, not configuration*

---

## The Vision

**Before:** You visit client, set up server, configure contacts, teach them everything
**After:** You ship pre-configured iPad, they open it, it just works

---

## Deployment Architecture Options

### Option A: QR Code Onboarding (Recommended - Simplest)

**How it works:**
1. You create a unique onboarding URL per client
2. Client receives iPad with Safari bookmarked to their URL
3. URL contains encrypted config (contacts, preferences)
4. App auto-configures on first load

**Implementation:**
```
https://eldertech.marceausolutions.com/setup/{client_id}

GET /setup/{client_id}:
  1. Look up client config in database
  2. Set session/localStorage with their contacts
  3. Redirect to main app (/)
  4. App reads config from localStorage
```

**Pros:**
- No Contact Picker API needed (iOS doesn't support it by default)
- You pre-configure contacts during sales call
- Zero configuration for senior
- Works as PWA or regular web app

**Cons:**
- Requires server-side client database
- You do the data entry (but that's part of the service!)

---

### Option B: PWA with Add to Home Screen

**How it works:**
1. Senior visits website
2. Prompted to "Add to Home Screen"
3. App installs as PWA icon
4. Guided Access locks iPad to just this app

**PWA Manifest (already partially implemented):**
```json
{
  "name": "Elder Tech Assistant",
  "short_name": "Elder Tech",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#ffffff",
  "theme_color": "#2563eb",
  "icons": [
    {
      "src": "/static/icon-192.png",
      "sizes": "192x192",
      "type": "image/png"
    },
    {
      "src": "/static/icon-512.png",
      "sizes": "512x512",
      "type": "image/png"
    }
  ]
}
```

**Guided Access Setup (for kiosk mode):**
1. Settings > Accessibility > Guided Access > ON
2. Set passcode (you keep this, not the senior)
3. Launch Elder Tech app
4. Triple-click Home button > Start Guided Access
5. iPad is now locked to Elder Tech only

---

### Option C: Native iOS App (Future)

**When to consider:**
- 10+ paying customers
- Need deeper iOS integration (Contacts, Siri, etc.)
- Want App Store distribution

**Not recommended now because:**
- $99/year Apple Developer fee
- App Store review process
- More development time
- PWA is sufficient for MVP

---

## Recommended Deployment Flow

### Phase 1: Sales Call (15 min)

```
1. Collect client info:
   - Senior's name
   - Emergency contacts (name, phone, relationship)
   - Family contacts (name, phone, relationship)
   - Email (optional - for email feature)
   - Preferred wake word (optional)

2. Enter into admin dashboard
   - Creates unique client_id
   - Generates onboarding URL
   - Stores encrypted config
```

### Phase 2: iPad Preparation (30 min one-time setup)

**Hardware:**
- iPad (any model with iOS 15+)
- Case with stand (so they can see screen hands-free)
- Charger positioned in common area

**Software Setup:**
```bash
# On iPad:
1. Sign in with YOUR Apple ID (for remote management)
   OR create dedicated eldertech@marceausolutions.com Apple ID

2. Safari > Go to: https://eldertech.marceausolutions.com/setup/{client_id}

3. Follow prompts to "Add to Home Screen"

4. Settings > Display & Brightness > Auto-Lock > Never

5. Settings > Accessibility > Guided Access > ON
   - Set passcode (you keep this)
   - Enable "Accessibility Shortcut"

6. Launch Elder Tech from Home Screen

7. Triple-click Home > Start Guided Access

8. iPad is now locked to Elder Tech only
```

### Phase 3: Delivery & Training (30-60 min)

**What you teach:**
1. "Tap the big blue button to call family"
2. "Tap the microphone to talk to Claude"
3. "The red button is for emergencies only"
4. "You never need to close this or open anything else"

**What you DON'T teach:**
- How to configure contacts (you did this)
- How to exit the app (they can't - Guided Access)
- How to update settings (you do this remotely)

---

## Technical Implementation Plan

### 1. Add PWA Manifest

Create `/static/manifest.json`:
```json
{
  "name": "Elder Tech Assistant",
  "short_name": "Elder Tech",
  "description": "Voice assistant for seniors",
  "start_url": "/",
  "display": "standalone",
  "orientation": "portrait",
  "background_color": "#ffffff",
  "theme_color": "#2563eb",
  "icons": [
    {"src": "/static/icon-192.png", "sizes": "192x192", "type": "image/png"},
    {"src": "/static/icon-512.png", "sizes": "512x512", "type": "image/png"}
  ]
}
```

### 2. Add to index.html

```html
<link rel="manifest" href="/static/manifest.json">
<link rel="apple-touch-icon" href="/static/icon-192.png">
```

### 3. Create Client Config Endpoint

```python
# New endpoint: /setup/{client_id}
@app.route('/setup/<client_id>')
def setup_client(client_id):
    # Load client config from database
    client = get_client_config(client_id)

    if not client:
        return "Invalid setup link", 404

    # Store config in session/response
    response = make_response(redirect('/'))
    response.set_cookie('client_config',
                        encrypt(json.dumps(client)),
                        max_age=365*24*60*60,  # 1 year
                        httponly=True)
    return response
```

### 4. Client Database Schema

```sql
CREATE TABLE clients (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    emergency_contacts JSON,  -- [{name, phone, email, relationship}]
    family_contacts JSON,
    preferences JSON,  -- {speech_rate, font_size, high_contrast}
    subscription_status TEXT DEFAULT 'trial',
    subscription_end DATE
);
```

### 5. Admin Dashboard (Simple)

Basic Flask admin to:
- Add new clients
- Generate setup URLs
- View client list
- Update contacts remotely

---

## iOS Contact Picker Reality Check

Per [MDN](https://developer.mozilla.org/en-US/docs/Web/API/Contact_Picker_API) and [iOS compatibility](https://github.com/mdn/browser-compat-data/issues/14648):

- Contact Picker API exists but is **behind a feature flag** on iOS Safari
- Users must manually enable: Settings > Safari > Advanced > Feature Flags > Contact Picker API
- **Not practical for seniors**

**Our solution:** Pre-configure contacts server-side. The senior never touches settings.

---

## Pricing Model Alignment

From GO-NO-GO decision:

| Tier | Setup Fee | Monthly | What You Do |
|------|-----------|---------|-------------|
| Basic | $299 | $49 | Ship pre-configured iPad, 1hr training |
| Standard | $299 | $79 | + SMS, Email features enabled |
| Premium | $299 | $99 | + Family dashboard, priority support |

**The $299 setup fee covers:**
- iPad configuration time (30 min)
- Data entry of contacts (15 min)
- Delivery and training (1 hr)
- Guided Access setup

---

## Future Enhancements

### Voice Activation (Phase 2)
- "Hey Elder Tech" wake word
- Uses Web Speech API (already supported)
- Requires browser tab to stay active

### Remote Updates (Phase 2)
- Push config changes without visiting client
- Add/remove contacts via admin dashboard
- Update preferences remotely

### Family Dashboard (Phase 3)
- Family members can see activity
- Get alerts if senior hasn't interacted in 24hrs
- Update contacts themselves

---

## Files to Create

| File | Purpose |
|------|---------|
| `static/manifest.json` | PWA manifest |
| `static/icon-192.png` | App icon (192x192) |
| `static/icon-512.png` | App icon (512x512) |
| `src/admin.py` | Admin dashboard routes |
| `src/client_db.py` | Client database operations |
| `templates/admin/` | Admin dashboard templates |

---

## Next Steps

1. [ ] Create PWA manifest + icons
2. [ ] Add /setup/{client_id} endpoint
3. [ ] Create simple client database (SQLite for now)
4. [ ] Build basic admin dashboard
5. [ ] Test full deployment flow on iPad
6. [ ] Document iPad setup checklist for yourself

---

## References

- [PWA on iOS Limitations](https://brainhub.eu/library/pwa-on-ios)
- [Contact Picker API - MDN](https://developer.mozilla.org/en-US/docs/Web/API/Contact_Picker_API)
- [iPad Kiosk Setup](https://www.onboardingtutorials.com/article/kiosk-setup-instructions-for-ipad)
- [Guided Access - Apple](https://support.apple.com/guide/ipad/guided-access-ipada16d1f50/ipados)
