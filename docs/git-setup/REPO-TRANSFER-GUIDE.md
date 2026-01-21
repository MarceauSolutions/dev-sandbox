# Repository Transfer Guide: SW Florida Comfort to MarceauSolutions Org

**Date:** January 20, 2026
**Purpose:** Move swflorida-comfort-hvac repo from personal account to organization

---

## Current State

**Repository:** `github.com/wmarceau/swflorida-comfort-hvac`
**Local Path:** `/Users/williammarceaujr./swflorida-comfort-hvac`
**Remote:** https://github.com/wmarceau/swflorida-comfort-hvac.git

---

## Target State

**Repository:** `github.com/MarceauSolutions/swflorida-comfort-hvac`
**Local Path:** Same (`/Users/williammarceaujr./swflorida-comfort-hvac`)
**Remote:** https://github.com/MarceauSolutions/swflorida-comfort-hvac.git

---

## Prerequisites

### Step 1: Verify MarceauSolutions Organization Exists

**Check if organization exists:**
1. Go to: https://github.com/orgs/MarceauSolutions
2. OR: https://github.com/settings/organizations

**If organization DOES NOT exist:**
1. Create organization: https://github.com/account/organizations/new
   - Organization name: `MarceauSolutions`
   - Billing email: `wmarceau@marceausolutions.com`
   - Plan: Free (or Pro if needed)
2. Add organization profile:
   - Name: Marceau Solutions
   - Website: https://marceausolutions.com
   - Description: "AI Automation for Local Businesses"
   - Location: Naples, FL

**If organization DOES exist:**
- Verify you have owner/admin access
- Proceed to transfer

---

## Transfer Process

### Option A: GitHub Web Interface (Recommended - Easiest)

**Steps:**

1. **Navigate to Repository**
   - Go to: https://github.com/wmarceau/swflorida-comfort-hvac

2. **Open Settings**
   - Click "Settings" tab (top right)
   - Scroll down to "Danger Zone" (bottom of page)

3. **Transfer Repository**
   - Click "Transfer" button
   - Enter new owner: `MarceauSolutions`
   - Confirm repository name: `swflorida-comfort-hvac`
   - Type repository name to confirm
   - Click "I understand, transfer this repository"

4. **Accept Transfer (if prompted)**
   - Go to MarceauSolutions organization
   - Accept the transfer request

5. **Verify Transfer**
   - Check: https://github.com/MarceauSolutions/swflorida-comfort-hvac
   - Should now show under organization

### Option B: GitHub CLI (Alternative)

```bash
# Install GitHub CLI if not installed
brew install gh

# Login
gh auth login

# Transfer repository
gh repo transfer wmarceau/swflorida-comfort-hvac MarceauSolutions
```

---

## Post-Transfer: Update Local Repository

**After transfer completes, update local git remote:**

```bash
# Navigate to local repo
cd /Users/williammarceaujr./swflorida-comfort-hvac

# Check current remote
git remote -v
# Should show: https://github.com/wmarceau/swflorida-comfort-hvac.git

# Update remote to new organization URL
git remote set-url origin https://github.com/MarceauSolutions/swflorida-comfort-hvac.git

# Verify update
git remote -v
# Should now show: https://github.com/MarceauSolutions/swflorida-comfort-hvac.git

# Test connection
git fetch origin

# If successful, you're done!
```

---

## Post-Transfer: Update Deployment Configuration

### Update ngrok Configuration

**If using ngrok custom domain:**

```bash
# Check current ngrok config
cat ~/.ngrok2/ngrok.yml

# No changes needed - ngrok config uses domain, not repo URL
# But verify website still accessible at: https://www.swfloridacomfort.com
```

### Update Deployment Scripts (if any)

**Check for hardcoded repo URLs:**

```bash
# Search for old repo URL in project
cd /Users/williammarceaujr./swflorida-comfort-hvac
grep -r "wmarceau/swflorida-comfort-hvac" . 2>/dev/null | grep -v ".git"

# If found, update to:
# MarceauSolutions/swflorida-comfort-hvac
```

### Update README/Documentation

**Update repository links in documentation:**

```bash
# Update README.md badges/links (if any)
# Change from:
https://github.com/wmarceau/swflorida-comfort-hvac

# To:
https://github.com/MarceauSolutions/swflorida-comfort-hvac
```

---

## Verification Checklist

After transfer, verify ALL of these:

- [ ] Repository visible at `github.com/MarceauSolutions/swflorida-comfort-hvac`
- [ ] Local git remote updated (`git remote -v`)
- [ ] Can push commits: `git push origin main`
- [ ] Can pull updates: `git pull origin main`
- [ ] Website still accessible: https://www.swfloridacomfort.com
- [ ] ngrok tunnel still working (if used)
- [ ] All links in README.md updated
- [ ] No broken references to old repo URL

---

## Troubleshooting

### Issue: "Repository not found" after transfer

**Solution:**
```bash
cd /Users/williammarceaujr./swflorida-comfort-hvac
git remote set-url origin https://github.com/MarceauSolutions/swflorida-comfort-hvac.git
git fetch origin
```

### Issue: Permission denied when pushing

**Solution:**
- Verify you're a member of MarceauSolutions organization
- Check: https://github.com/orgs/MarceauSolutions/people
- Add yourself as owner if needed

### Issue: Old URL cached in git

**Solution:**
```bash
# Clear git remote cache
git remote remove origin
git remote add origin https://github.com/MarceauSolutions/swflorida-comfort-hvac.git
git fetch origin
git branch --set-upstream-to=origin/main main
```

---

## Additional Benefits of Organization Structure

**After transfer:**

1. **Professional Branding**
   - Repos under MarceauSolutions umbrella
   - Consistent organization namespace

2. **Team Collaboration**
   - Can add team members to organization
   - Granular permission management

3. **Repository Management**
   - All business repos in one place
   - Organization-wide settings

4. **Separation of Concerns**
   - Personal projects: `github.com/wmarceau/*`
   - Business projects: `github.com/MarceauSolutions/*`

---

## Current MarceauSolutions Repositories (After Transfer)

**Existing:**
- `github.com/MarceauSolutions/marceausolutions.com` (already in org)

**New:**
- `github.com/MarceauSolutions/swflorida-comfort-hvac` (after transfer)

**Future:**
- `github.com/MarceauSolutions/dev-sandbox` (optional - consider if team grows)
- `github.com/MarceauSolutions/squarefoot-shipping` (if created)

---

## Commands Summary

```bash
# 1. Transfer via GitHub web (see Option A above)
# OR use CLI:
gh repo transfer wmarceau/swflorida-comfort-hvac MarceauSolutions

# 2. Update local remote
cd /Users/williammarceaujr./swflorida-comfort-hvac
git remote set-url origin https://github.com/MarceauSolutions/swflorida-comfort-hvac.git

# 3. Verify
git remote -v
git fetch origin
git push origin main

# 4. Check for hardcoded URLs
grep -r "wmarceau/swflorida-comfort-hvac" . 2>/dev/null | grep -v ".git"

# 5. Test website
curl -I https://www.swfloridacomfort.com
```

---

## Timeline

**Total Time:** 10-15 minutes

1. Transfer repository (5 min)
2. Update local remote (2 min)
3. Update documentation (3 min)
4. Verification (5 min)

---

## Next Steps After Transfer

1. ✅ Verify all links work
2. ✅ Update platform strategy docs (reference new org)
3. ✅ Commit PLATFORM-ANALYSIS-2026.md to dev-sandbox
4. ✅ Begin TikTok account creation for HVAC
5. ✅ Cancel X automation plans for HVAC

---

**Ready to transfer?** Follow Option A (Web Interface) for easiest process.
