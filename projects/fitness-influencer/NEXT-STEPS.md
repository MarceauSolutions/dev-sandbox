# Fitness Influencer MCP - Next Steps

**Updated**: 2026-01-14
**Current Version**: 1.2.0 (Published)

---

## Phase 1: Validation (COMPLETE)

- [x] MCP v1.2.0 published to PyPI
- [x] MCP v1.2.0 published to Claude Registry
- [x] GitHub repo updated (MarceauSolutions/fitness-influencer-mcp)
- [x] MONETIZATION.md created
- [x] Landing page created (`landing-page/index.html`)
- [x] gmail-mcp verified (NOT ours - third-party package)

### Landing Page Deployment Options

The landing page is ready at `landing-page/index.html`. To deploy:

**Option 1: Carrd (Recommended - $9 one-time)**
1. Sign up at carrd.co
2. Copy content from index.html
3. Add email capture form
4. Publish

**Option 2: GitHub Pages (FREE)**
1. Create repo `fitness-influencer-landing`
2. Push index.html
3. Enable GitHub Pages in settings
4. URL: `marceausolutions.github.io/fitness-influencer-landing`

**Option 3: Netlify (FREE)**
1. Drag and drop landing-page folder
2. Instant deployment
3. Custom domain support

**Email Capture Setup**:
The landing page form submits directly to our form webhook at `form_webhook.py`, which:
- Saves to Google Sheets
- Creates ClickUp task
- Sends SMS notification
- Sends email notification

---

## Phase 2: Usage Tracking (Week 2)

**Goal**: Implement free tier limits to enable monetization

### Files to Create

**1. `src/fitness_influencer_mcp/usage_tracker.py`**

```python
"""
Track usage per user to enforce free tier limits.

Free tier limits:
- 5 video edits/month
- 10 comment batches/day
- 3 workout plans/month
- 1 content calendar/week
- 2 AI images/month

Storage: Local JSON file (simple MVP)
"""

import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

class UsageTracker:
    FREE_LIMITS = {
        "video_edit": {"limit": 5, "period": "month"},
        "comment_categorize": {"limit": 10, "period": "day"},
        "workout_plan": {"limit": 3, "period": "month"},
        "content_calendar": {"limit": 1, "period": "week"},
        "ai_image": {"limit": 2, "period": "month"},
    }

    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or Path.home() / ".fitness_mcp_usage.json"
        self._load_data()

    def _load_data(self):
        if self.storage_path.exists():
            with open(self.storage_path) as f:
                self.data = json.load(f)
        else:
            self.data = {}

    def _save_data(self):
        with open(self.storage_path, "w") as f:
            json.dump(self.data, f, indent=2)

    def check_limit(self, user_id: str, action: str) -> tuple[bool, str]:
        """
        Returns (can_proceed, message).
        True if user can perform action, False if limit reached.
        """
        if action not in self.FREE_LIMITS:
            return True, "Action not limited"

        limit_info = self.FREE_LIMITS[action]
        usage = self._get_usage(user_id, action, limit_info["period"])

        if usage >= limit_info["limit"]:
            return False, f"Free limit reached ({usage}/{limit_info['limit']} {action}s this {limit_info['period']}). Upgrade to Pro for unlimited access."

        return True, f"Usage: {usage}/{limit_info['limit']} this {limit_info['period']}"

    def increment_usage(self, user_id: str, action: str):
        """Record that user performed action."""
        if user_id not in self.data:
            self.data[user_id] = {}

        timestamp = datetime.now().isoformat()
        if action not in self.data[user_id]:
            self.data[user_id][action] = []

        self.data[user_id][action].append(timestamp)
        self._save_data()

    def _get_usage(self, user_id: str, action: str, period: str) -> int:
        """Count usage within period."""
        if user_id not in self.data or action not in self.data[user_id]:
            return 0

        now = datetime.now()
        if period == "day":
            cutoff = now - timedelta(days=1)
        elif period == "week":
            cutoff = now - timedelta(weeks=1)
        elif period == "month":
            cutoff = now - timedelta(days=30)
        else:
            cutoff = now - timedelta(days=365)

        count = 0
        for ts in self.data[user_id][action]:
            if datetime.fromisoformat(ts) > cutoff:
                count += 1

        return count

    def get_usage_summary(self, user_id: str) -> dict:
        """Return current usage vs limits for all actions."""
        summary = {}
        for action, limit_info in self.FREE_LIMITS.items():
            usage = self._get_usage(user_id, action, limit_info["period"])
            summary[action] = {
                "used": usage,
                "limit": limit_info["limit"],
                "period": limit_info["period"],
                "remaining": max(0, limit_info["limit"] - usage),
            }
        return summary
```

**2. `src/fitness_influencer_mcp/pro_manager.py`**

```python
"""
Manage Pro subscriptions.

MVP: JSON file with pro user emails
Future: Stripe webhook integration
"""

import json
from pathlib import Path
from typing import Optional

class ProManager:
    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or Path.home() / ".fitness_mcp_pro_users.json"
        self._load_data()

    def _load_data(self):
        if self.storage_path.exists():
            with open(self.storage_path) as f:
                self.data = json.load(f)
        else:
            self.data = {"pro_users": []}

    def _save_data(self):
        with open(self.storage_path, "w") as f:
            json.dump(self.data, f, indent=2)

    def is_pro_user(self, user_email: str) -> bool:
        """Check if user has active Pro subscription."""
        return user_email.lower() in [u["email"].lower() for u in self.data["pro_users"]]

    def add_pro_user(self, user_email: str, stripe_customer_id: str = ""):
        """Add user to Pro list after payment."""
        if not self.is_pro_user(user_email):
            self.data["pro_users"].append({
                "email": user_email.lower(),
                "stripe_customer_id": stripe_customer_id,
                "added_at": datetime.now().isoformat(),
            })
            self._save_data()

    def remove_pro_user(self, user_email: str):
        """Remove user from Pro list (subscription cancelled)."""
        self.data["pro_users"] = [
            u for u in self.data["pro_users"]
            if u["email"].lower() != user_email.lower()
        ]
        self._save_data()

    def list_pro_users(self) -> list:
        """List all Pro users."""
        return self.data["pro_users"]
```

### Integration with server.py

Add usage tracking to each tool:

```python
from .usage_tracker import UsageTracker
from .pro_manager import ProManager

tracker = UsageTracker()
pro_manager = ProManager()

@mcp.tool()
async def create_jump_cut_video(...):
    user_email = os.getenv("MCP_USER_EMAIL", "anonymous")

    # Skip limits for Pro users
    if not pro_manager.is_pro_user(user_email):
        can_proceed, message = tracker.check_limit(user_email, "video_edit")
        if not can_proceed:
            return {"error": message, "upgrade_url": "https://your-landing-page.com"}

    # ... rest of function ...

    tracker.increment_usage(user_email, "video_edit")
    return result
```

---

## Phase 3: Payment Integration (Week 3-4)

**Goal**: Accept payments via Stripe

### Steps

1. **Create Stripe Account**
   - Sign up at stripe.com
   - Complete business verification

2. **Create Product**
   - Name: "Fitness Influencer Pro"
   - Price: $9/month (or $79/year)

3. **Generate Payment Link**
   - Stripe Dashboard → Payment Links
   - Add to landing page

4. **Manual Activation (MVP)**
   - Check Stripe dashboard daily
   - Add paying customers to `~/.fitness_mcp_pro_users.json`

5. **Future: Webhook Automation**
   - Set up Stripe webhook endpoint
   - Auto-add/remove users on payment events

---

## Phase 4: Customer Acquisition (Ongoing)

### Week 1 Targets

| Channel | Action | Goal |
|---------|--------|------|
| Reddit | Post in r/fitness, r/bodybuilding | 50 signups |
| Twitter | Share 3 fitness content tips | 20 signups |
| YouTube | Comment on 10 fitness creator videos | 30 signups |

### Post Templates

**Reddit Post (r/fitness)**:
```
Title: I built an AI tool to auto-edit fitness videos - looking for beta testers

Hey everyone! I'm a developer who trains and got frustrated with how long it takes to edit workout videos.

Built an AI tool that:
- Auto-removes silence and dead air from videos
- Categorizes your comments/DMs (finds brand deals!)
- Generates content calendars to prevent burnout

Free to try. Looking for fitness creators to test it out.

Link: [landing page]
```

**Twitter Thread**:
```
If you're a fitness creator, you probably spend:

- 4+ hours editing each video
- 2 hours managing DMs daily
- Sunday nights stressed about content

I built an AI assistant to fix this 🧵

1/ Auto jump-cuts remove silence. Turn 20 min raw footage → 8 min edit.

2/ Comment categorizer finds brand inquiries you're missing.

3/ Content calendar with burnout prevention.

Free to try: [link]
```

---

## Summary

| Phase | Status | Timeline |
|-------|--------|----------|
| 1. Validation | ✅ Complete | Done |
| 2. Usage Tracking | 🔜 Next | Week 2 |
| 3. Payment | 📅 Planned | Week 3-4 |
| 4. Acquisition | 📅 Ongoing | Week 1+ |

**Immediate Next Action**: Deploy landing page and post in 1 fitness community today.
