# Social Media API Setup Checklist
**Date:** January 21, 2026
**Goal:** Get Facebook + LinkedIn APIs working today

---

## ✅ Progress Tracker

### Facebook API Setup (Phone Method)

- [ ] **Step 1:** Open developers.facebook.com on phone browser
- [ ] **Step 2:** Create "SW Florida Comfort Automation" app
- [ ] **Step 3:** Get App ID: `___________________`
- [ ] **Step 4:** Get App Secret: `___________________`
- [ ] **Step 5:** Add to .env file
- [ ] **Step 6:** Get Page Access Token (permanent)
- [ ] **Step 7:** Test posting with `python -m src.facebook_api test`

**Estimated Time:** 20 minutes
**Current Status:** In Progress

---

### LinkedIn API Setup

- [x] **Step 1:** Go to https://www.linkedin.com/developers/ (on computer, no security issues)
- [x] **Step 2:** Create "Marceau Solutions Automation" app
- [ ] **Step 3:** Add redirect URL: `http://localhost:8000/callback`
- [x] **Step 4:** Get Client ID: `7850ny5aexdxs1`
- [x] **Step 5:** Get Client Secret: `WPL_AP1.B4SxEeO0FDdLxqn2.fUk6HQ==`
- [x] **Step 6:** Community Management API access (auto-provisioned ✅)
- [x] **Step 7:** Add to .env file
- [ ] **Step 8:** Configure OAuth and test posting

**Estimated Time:** 15 minutes
**Current Status:** ✅ COMPLETE - Ready to configure OAuth flow

---

### Apollo.io Optimization Review

- [ ] **Read:** methods/r-and-d-department/apollo-io-cost-optimization.md
- [ ] **Identify:** Top 3 credit-saving strategies to implement
- [ ] **Create:** First saved search in Apollo.io dashboard
- [ ] **Document:** Any additional insights from team session

**Estimated Time:** 30 minutes
**Current Status:** Not Started

---

## Environment Variables Needed

After all setups, your `.env` should have:

```bash
# Facebook (ADD TODAY)
FACEBOOK_PAGE_ACCESS_TOKEN="EAA..."
FACEBOOK_PAGE_ID="..."

# LinkedIn (ADD TODAY - Client ID/Secret, Access Token after approval)
LINKEDIN_CLIENT_ID="..."
LINKEDIN_CLIENT_SECRET="..."
# LINKEDIN_ACCESS_TOKEN="..." (add after approval in 2-4 weeks)

# X (ALREADY EXISTS)
X_API_KEY="..."
X_API_SECRET="..."
X_ACCESS_TOKEN="..."
X_ACCESS_TOKEN_SECRET="..."

# TikTok (ADD WHEN APPROVED)
# TIKTOK_ACCESS_TOKEN="..." (waiting for audit)

# Apollo.io (ALREADY EXISTS)
APOLLO_API_KEY="..."
```

---

## Commands Reference

### Test Facebook API:
```bash
cd /Users/williammarceaujr./dev-sandbox/projects/social-media-automation
python -m src.facebook_api test
```

### Test LinkedIn API (after approval):
```bash
python -m src.linkedin_auth  # Run OAuth flow once
python -m src.linkedin_api test  # Test posting
```

### Test Multi-Platform:
```bash
python -m src.multi_platform_scheduler test
```

---

## Next: After Setup Complete

1. **Film TikTok content** (20-30 videos)
2. **Draft LinkedIn posts** (30 posts for Month 1)
3. **Create Facebook content calendar** (30 posts)
4. **Set up posting schedule** (cron jobs)

---

**Current Task:** Creating Facebook Developer App on phone
**Next Task:** LinkedIn API setup
**Then:** Apollo.io optimization review
