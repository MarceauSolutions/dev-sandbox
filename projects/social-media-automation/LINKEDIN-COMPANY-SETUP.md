# LinkedIn Company Page Setup Guide

**App**: Marceau Solutions Company Posting
**Client ID**: 78gy4q6d5k2e3d
**Purpose**: Post to Marceau Solutions LLC company page via Community Management API
**Status**: ⏳ Awaiting API approval from LinkedIn

---

## When API Approval Email Arrives

### Step 1: Add Redirect URL to App

1. Go to https://www.linkedin.com/developers/apps/
2. Open "Marceau Solutions Company Posting" app
3. Click "Auth" tab
4. Under "Redirect URLs", click "Add redirect URL"
5. Enter: `http://localhost:8000/callback`
6. Click "Update"

### Step 2: Get Client Secret

1. Still in "Auth" tab
2. Under "Application credentials", find "Client Secret"
3. Click "Show" or copy the secret
4. Add to `.env` file:
   ```
   LINKEDIN_COMPANY_CLIENT_SECRET=YOUR_SECRET_HERE
   ```

### Step 3: Run OAuth Flow

```bash
cd /Users/williammarceaujr./dev-sandbox/projects/social-media-automation

python -m src.linkedin_company_auth
```

**What happens:**
1. Browser opens to LinkedIn authorization page
2. Click "Allow" to grant permissions
3. Script exchanges code for access token
4. Token saved to `.env` as `LINKEDIN_COMPANY_ACCESS_TOKEN`

**Expected output:**
```
🔐 LinkedIn Company Page OAuth 2.0 Authentication Flow

📄 App: Marceau Solutions Company Posting
🏢 Company Page: https://www.linkedin.com/company/marceau-solutions-llc/
🔑 Scopes: w_organization_social r_organization_social

🌐 Opening browser for LinkedIn authorization...
⏳ Waiting for authorization...
✅ Authorization code received
✅ Access token received (expires in 60 days)
✅ Saved LINKEDIN_COMPANY_ACCESS_TOKEN to .env

✅ LinkedIn company page authentication complete!
```

### Step 4: Get Organization ID

```bash
python -m src.linkedin_company_api get-org-id
```

**Expected output:**
```
✅ Organization ID: 123456
   Organization URN: urn:li:organization:123456
```

**Save this ID** - you'll need it for posting.

### Step 5: Test Company Page Posting

```bash
python -m src.linkedin_company_api test
```

**Expected output:**
```
📋 Step 1: Getting organization ID...
✅ Organization ID: 123456

📝 Step 2: Creating test post...
✅ Posted to company page!
   Post URN: urn:li:share:7890123456
   View at: https://www.linkedin.com/company/marceau-solutions-llc/

✅ Test successful!
```

**Verify**: Visit https://www.linkedin.com/company/marceau-solutions-llc/ and confirm test post appears.

---

## Integration with Social Media Automation

Once setup is complete, update the automation system:

### Add to business_content_generator.py

```python
from src.linkedin_company_api import LinkedInCompanyAPI

def post_to_linkedin_company(post_content: str, org_id: str):
    """Post to Marceau Solutions company page."""
    api = LinkedInCompanyAPI()
    return api.create_text_post(
        text=post_content,
        organization_id=org_id,
        visibility="PUBLIC"
    )
```

### Add to business_scheduler.py

```python
# When scheduling posts
if platform == "linkedin_company":
    post_to_linkedin_company(
        post_content=post.content,
        org_id=os.getenv("LINKEDIN_ORG_ID")  # Add to .env
    )
```

---

## Troubleshooting

### Error: "Community Management API access required"
**Solution**: Wait for LinkedIn approval email (usually 24-48 hours for Development Tier)

### Error: "Redirect URI mismatch"
**Solution**: Make sure `http://localhost:8000/callback` is added to app's redirect URLs

### Error: "Not authorized for organization"
**Solution**: Make sure you're an admin of Marceau Solutions LLC company page

### Error: "Invalid client credentials"
**Solution**: Verify `LINKEDIN_COMPANY_CLIENT_ID` and `LINKEDIN_COMPANY_CLIENT_SECRET` match the app

### Token expired (after 60 days)
**Solution**: Re-run OAuth flow: `python -m src.linkedin_company_auth`

---

## Next Steps After Setup

1. ✅ Update `.env` with organization ID
2. ✅ Integrate with `business_content_generator.py`
3. ✅ Test posting schedule (dry run first)
4. ✅ Enable automated company page posting

---

## Credentials Summary

**App 1** (Personal posting - already working):
- App: Marceau Solutions Automation
- Client ID: 7850ny5aexdxs1
- Scopes: `w_member_social`
- Use case: Personal profile posting (fallback)

**App 2** (Company posting - this guide):
- App: Marceau Solutions Company Posting
- Client ID: 78gy4q6d5k2e3d
- Scopes: `w_organization_social r_organization_social`
- Use case: Company page posting (primary)

---

## Status Checklist

- [x] Created second LinkedIn app
- [x] Requested Community Management API access
- [ ] Received approval email from LinkedIn
- [ ] Added redirect URL to app
- [ ] Got Client Secret from app
- [ ] Ran OAuth flow (`linkedin_company_auth.py`)
- [ ] Got organization ID
- [ ] Tested posting
- [ ] Integrated with automation system

**Current Status**: ⏳ Waiting for Community Management API approval
