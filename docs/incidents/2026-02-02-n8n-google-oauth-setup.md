# Incident Report: n8n Google OAuth Setup

**Date:** 2026-02-02
**Duration:** ~45 minutes
**Outcome:** Successfully configured Google Sheets OAuth2 for n8n on EC2

---

## Summary

Setting up Google Sheets OAuth2 credentials in n8n required resolving four distinct errors, each with a different root cause. This document explains each error, why it happened, and how it was fixed.

---

## Error 1: "This app is blocked"

### What We Saw
```
Access blocked: This app is blocked

This app tried to access sensitive info in your Google Account.
To keep your account safe, Google blocked this access.
```

### Root Cause
The OAuth consent screen was configured as **"Internal"** user type. Internal apps are restricted to users within the same Google Workspace organization. Since we were trying to authenticate from an external server (EC2), the app blocked access.

### The Fix
1. Go to Google Cloud Console → **Google Auth Platform** → **Audience**
2. Change from **"Internal"** to **"External"**
3. Save changes

### Why This Works
External apps can be used by any Google account (with proper consent), not just accounts in your Workspace organization.

---

## Error 2: "This app is blocked" (Second occurrence - Testing mode)

### What We Saw
Same error as above, but after changing to External.

### Root Cause
When an OAuth app is set to **"External"** but has **"Testing"** publishing status, only explicitly added **test users** can authenticate. Our email wasn't in the test users list.

### The Fix
1. Go to Google Cloud Console → **Google Auth Platform** → **Audience**
2. Scroll to **"Test users"** section
3. Click **"+ ADD USERS"**
4. Add: `wmarceau@marceausolutions.com`
5. Save

### Alternative Fix
Instead of adding test users, you can **"Publish"** the app to move it to production. However, publishing requires HTTPS redirect URIs (which we didn't have yet).

### Why This Works
Test users are explicitly authorized to use apps in Testing mode. Adding yourself as a test user grants permission to authenticate.

---

## Error 3: "redirect_uri_mismatch" (Error 400)

### What We Saw
```
Access blocked: This app's request is invalid

Error 400: redirect_uri_mismatch
```

### Root Cause
OAuth requires the `redirect_uri` sent by the application to **exactly match** one of the authorized redirect URIs in the Google Cloud Console credentials.

**What n8n was sending:**
```
http://n8n.marceausolutions.com:5678/rest/oauth2-credential/callback
```

**What was authorized in Google Cloud Console:**
```
https://web-production-44ade.up.railway.app/api/oauth/callback
```

These didn't match, causing the error.

### The Fix
1. Go to Google Cloud Console → **APIs & Services** → **Credentials**
2. Click on **"Fitness AI Assistant Web"** (OAuth 2.0 Client ID)
3. Under **"Authorized redirect URIs"**, click **"+ ADD URI"**
4. Add: `http://n8n.marceausolutions.com:5678/rest/oauth2-credential/callback`
5. Save

### Important Notes
- The URI must match **exactly** (protocol, domain, port, path)
- No trailing slash differences
- Case sensitive
- `http` vs `https` matters

---

## Error 4: redirect_uri_mismatch (Still occurring after adding URI)

### What We Saw
Same `redirect_uri_mismatch` error even after adding the correct URI to Google Cloud Console.

### Root Cause
n8n determines its redirect URI based on:
1. The `WEBHOOK_URL` environment variable (if set), OR
2. The URL you're currently accessing n8n from

**The problem:** n8n had no `WEBHOOK_URL` configured, so it used whatever URL you accessed it from. If you accessed n8n via the IP address (`http://34.193.98.97:5678`), n8n would send that as the redirect_uri instead of the domain.

**Checking the n8n config showed:**
```bash
$ cat /etc/n8n.env
N8N_SECURE_COOKIE=false
```

No `WEBHOOK_URL` was set.

### The Fix
Add `WEBHOOK_URL` to force n8n to always use the domain:

```bash
ssh ec2 "echo 'WEBHOOK_URL=http://n8n.marceausolutions.com:5678/' | sudo tee -a /etc/n8n.env"
ssh ec2 "sudo systemctl restart n8n"
```

**Updated /etc/n8n.env:**
```
N8N_SECURE_COOKIE=false
WEBHOOK_URL=http://n8n.marceausolutions.com:5678/
```

### Why This Works
With `WEBHOOK_URL` set, n8n always uses `http://n8n.marceausolutions.com:5678/rest/oauth2-credential/callback` regardless of how you access the UI. This matches the authorized redirect URI in Google Cloud Console.

---

## Final Configuration

### Google Cloud Console Settings

**Project:** `fitness-influencer-assistant`

**OAuth Consent Screen:**
- User Type: External
- Publishing Status: Testing
- Test Users: `wmarceau@marceausolutions.com`

**OAuth 2.0 Client ID:** "Fitness AI Assistant Web"
- Client ID: `915754256960-608fnf2lcof0sc5amu17b5q13rhpqkrk.apps.googleusercontent.com`
- Authorized redirect URIs:
  - `http://n8n.marceausolutions.com:5678/rest/oauth2-credential/callback`
  - `https://web-production-44ade.up.railway.app/api/oauth/callback` (legacy)

### n8n EC2 Configuration

**/etc/n8n.env:**
```
N8N_SECURE_COOKIE=false
WEBHOOK_URL=http://n8n.marceausolutions.com:5678/
```

### n8n Credential
- Type: Google Sheets OAuth2 API
- Client ID: (from Google Cloud Console)
- Client Secret: (from Google Cloud Console)
- Connected Account: `wmarceau@marceausolutions.com`

---

## Troubleshooting Checklist

If you encounter Google OAuth issues with n8n in the future:

### 1. "This app is blocked"
- [ ] Is OAuth consent screen set to "External"? (Google Auth Platform → Audience)
- [ ] Is your email added as a test user? (if app is in Testing mode)
- [ ] Or is the app published to Production?

### 2. "redirect_uri_mismatch"
- [ ] Is the redirect URI added to the OAuth client credentials?
- [ ] Does the URI match **exactly**? (protocol, domain, port, path)
- [ ] Is `WEBHOOK_URL` set in n8n config? (check `/etc/n8n.env`)
- [ ] Did you restart n8n after changing config? (`sudo systemctl restart n8n`)

### 3. How to find what redirect_uri n8n is using
- Open browser developer tools (F12)
- Go to Network tab
- Click "Sign in with Google" in n8n
- Look at the request to `accounts.google.com`
- Find the `redirect_uri` parameter in the URL

---

## Key Learnings

1. **OAuth has multiple layers of authorization:**
   - Consent screen (Internal/External)
   - Publishing status (Testing/Production)
   - Test users (only for Testing mode)
   - Authorized redirect URIs

2. **n8n's redirect_uri is dynamic** unless you set `WEBHOOK_URL`
   - Without it, n8n uses the URL you're accessing it from
   - This can cause mismatches if you access via IP vs domain

3. **Google requires HTTPS for Production apps**
   - Testing mode allows HTTP redirect URIs
   - Production mode requires HTTPS
   - This is why we stayed in Testing mode with test users

4. **Order of troubleshooting matters:**
   - First fix consent screen access (Internal → External)
   - Then fix user authorization (add test user)
   - Then fix redirect URI configuration
   - Finally fix n8n's WEBHOOK_URL if needed

---

---

## The Complete Fix (Summary)

### What We Changed

**1. Google Cloud Console - OAuth Consent Screen**
```
Location: Google Auth Platform → Audience
Change: Internal → External
```
**Why:** Internal apps only work for users in your Google Workspace organization. External allows any Google account (with proper authorization).

**2. Google Cloud Console - Test Users**
```
Location: Google Auth Platform → Audience → Test users
Added: wmarceau@marceausolutions.com
```
**Why:** Apps in "Testing" mode only allow explicitly listed test users to authenticate. Without being in this list, Google blocks the OAuth flow.

**3. Google Cloud Console - Redirect URI**
```
Location: APIs & Services → Credentials → "Fitness AI Assistant Web"
Added: http://n8n.marceausolutions.com:5678/rest/oauth2-credential/callback
```
**Why:** OAuth requires the application's redirect URI to exactly match an authorized URI. This is where Google sends the user back after authentication.

**4. n8n EC2 Server - WEBHOOK_URL**
```bash
# Added to /etc/n8n.env:
WEBHOOK_URL=http://n8n.marceausolutions.com:5678/

# Then restarted n8n:
sudo systemctl restart n8n
```
**Why:** Without this setting, n8n dynamically constructs its redirect URI based on how you access it (IP vs domain). If you accessed n8n via IP but authorized the domain URL in Google, they wouldn't match. Setting `WEBHOOK_URL` forces n8n to always use the same URL.

### Why The Fix Works

The OAuth flow works like this:

```
1. User clicks "Sign in with Google" in n8n
   ↓
2. n8n redirects to Google with:
   - client_id (identifies the app)
   - redirect_uri (where to send user back)
   - scope (what permissions to request)
   ↓
3. Google checks:
   ✓ Is this client_id valid?
   ✓ Is the user authorized? (External + test user)
   ✓ Does redirect_uri match an authorized URI?
   ↓
4. User grants permission
   ↓
5. Google redirects back to redirect_uri with auth code
   ↓
6. n8n exchanges auth code for access token
   ↓
7. n8n can now access Google Sheets
```

Our errors occurred at step 3:
- **Error 1-2:** User authorization failed (Internal mode, no test user)
- **Error 3-4:** Redirect URI didn't match

By fixing all four items, every check at step 3 passes:
- ✅ Client ID is valid (unchanged)
- ✅ User is authorized (External mode + test user added)
- ✅ Redirect URI matches (URI added + WEBHOOK_URL set)

### The Key Insight

The final fix (`WEBHOOK_URL`) was the non-obvious one. Even with the correct redirect URI in Google Cloud Console, the OAuth still failed because **n8n wasn't sending that URI**.

n8n was sending: `http://34.193.98.97:5678/rest/oauth2-credential/callback`
Google expected: `http://n8n.marceausolutions.com:5678/rest/oauth2-credential/callback`

Same server, different URLs = mismatch = error.

Setting `WEBHOOK_URL` tells n8n: "Always use this base URL, regardless of how the user accessed you."

---

## Related Documentation

- [Google OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [n8n Google OAuth Setup](https://docs.n8n.io/integrations/builtin/credentials/google/)
- [n8n Environment Variables](https://docs.n8n.io/hosting/configuration/environment-variables/)
