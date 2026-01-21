# Google Analytics GA4 Activation Guide

**For:** Marceau Solutions Website
**Status:** GA4 code present but commented out (ready to activate)
**Last Updated:** 2026-01-20

---

## Quick Start (3 Steps)

1. **Get Measurement ID** from Google Analytics (see Section 1)
2. **Run activation script**: `./activate-ga4.sh G-XXXXXXXXXX`
3. **Verify tracking** in GA4 Real-time report (see Section 4)

---

## Table of Contents

1. [Create Google Analytics Account & Property](#1-create-google-analytics-account--property)
2. [Get Your Measurement ID](#2-get-your-measurement-id)
3. [Activate GA4 on Website](#3-activate-ga4-on-website)
4. [Verify Tracking is Working](#4-verify-tracking-is-working)
5. [Events Being Tracked](#5-events-being-tracked)
6. [View Reports & Data](#6-view-reports--data)
7. [Troubleshooting](#7-troubleshooting)
8. [Advanced Configuration (Optional)](#8-advanced-configuration-optional)

---

## 1. Create Google Analytics Account & Property

### Step 1.1: Go to Google Analytics

Visit: **https://analytics.google.com**

Sign in with: **wmarceau@marceausolutions.com**

### Step 1.2: Create Account

1. Click **"Start measuring"** (if first time) or **Admin** → **Create Account**
2. **Account Name:** `Marceau Solutions`
3. **Account Data Sharing Settings:** (Recommended defaults - all checked)
   - ✅ Google products & services
   - ✅ Benchmarking
   - ✅ Technical support
   - ✅ Account specialists
4. Click **Next**

### Step 1.3: Create Property

1. **Property Name:** `Marceau Solutions Website`
2. **Reporting Time Zone:** `(GMT-05:00) Eastern Time`
3. **Currency:** `US Dollar ($)`
4. Click **Next**

### Step 1.4: Business Details

1. **Industry Category:** `Technology / Internet & Telecom`
   - Or: `Professional Services`
2. **Business Size:** `Small - 1 to 10 employees`
3. Click **Next**

### Step 1.5: Business Objectives

Select all relevant goals:
- ✅ **Generate leads**
- ✅ **Examine user behavior**
- ☐ Drive online sales (optional)
- ☐ Raise brand awareness (optional)

Click **Create**

### Step 1.6: Accept Terms of Service

- ✅ I accept the Google Analytics Terms of Service Agreement
- ✅ I accept the Measurement Controller-Controller Data Protection Terms
- Click **I Accept**

### Step 1.7: Set Up Data Stream (Web)

1. Choose platform: **Web**
2. **Website URL:** `https://marceausolutions.com`
   - (If not live yet, use: `http://localhost` for testing)
3. **Stream Name:** `Marceau Solutions Main Site`
4. Click **Create stream**

**✅ Success!** You should now see your **Measurement ID** (format: `G-XXXXXXXXXX`)

---

## 2. Get Your Measurement ID

### Where to Find It

1. In Google Analytics, go to: **Admin** (gear icon, bottom left)
2. Under **Property** column, click: **Data Streams**
3. Click on your stream: `Marceau Solutions Main Site`
4. Copy the **Measurement ID** (top right)

**Format:** `G-` followed by 10 alphanumeric characters
**Example:** `G-ABC1234567`

**IMPORTANT:** Keep this ID secure. You'll need it for the activation script.

---

## 3. Activate GA4 on Website

### Method 1: Automated (Recommended)

**Use the activation script:**

```bash
# Navigate to website directory
cd /Users/williammarceaujr./marceausolutions.com

# Run activation script with your Measurement ID
./activate-ga4.sh G-ABC1234567
```

**What the script does:**
1. ✅ Validates Measurement ID format
2. ✅ Creates backup of all HTML files
3. ✅ Removes comment markers around GA4 code
4. ✅ Replaces placeholder `G-XXXXXXXXXX` with your real ID
5. ✅ Updates all 5 HTML files (index, contact, pricing, terms, privacy)

**Output:**
```
🚀 Activating GA4 with Measurement ID: G-ABC1234567

📦 Creating backup in .ga4-backup-20260120-143025...
  ✓ Backed up index.html
  ✓ Backed up contact.html
  ✓ Backed up pricing.html
  ✓ Backed up terms.html
  ✓ Backed up privacy.html

Processing index.html...
  ✅ GA4 activated in index.html
Processing contact.html...
  ✅ GA4 activated in contact.html
Processing pricing.html...
  ✅ GA4 activated in pricing.html
Processing terms.html...
  ✅ GA4 activated in terms.html
Processing privacy.html...
  ✅ GA4 activated in privacy.html

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Google Analytics GA4 activated successfully!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Method 2: Manual (Alternative)

If you prefer to manually edit files:

1. Open each HTML file (index.html, contact.html, pricing.html, terms.html, privacy.html)
2. Find the GA4 comment block (lines 11-22)
3. Remove the comment markers: `<!--` and `-->`
4. Replace `G-XXXXXXXXXX` with your real Measurement ID
5. Save all files

**Before (commented out):**
```html
<!-- Google Analytics GA4 -->
<!-- TODO: Replace G-XXXXXXXXXX with real Measurement ID from analytics.google.com -->
<!-- To activate: Uncomment the lines below after obtaining your GA4 Measurement ID -->
<!--
<script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-XXXXXXXXXX');
</script>
-->
```

**After (activated):**
```html
<!-- Google Analytics GA4 -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-ABC1234567"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-ABC1234567');
</script>
```

### Deploy to Production

```bash
# Review changes
git diff

# Stage changes
git add -A

# Commit
git commit -m "feat: Activate GA4 tracking (G-ABC1234567)"

# Push to production
git push
```

---

## 4. Verify Tracking is Working

### 4.1 Local Testing (Before Deployment)

**Test locally first:**

```bash
# Open website in browser
open index.html
```

**Check browser console:**

1. Open Developer Tools (F12 or Cmd+Opt+I)
2. Go to **Console** tab
3. Look for GA4 messages (no errors)
4. Go to **Network** tab
5. Filter by `google-analytics.com` or `gtag`
6. You should see requests to GA4

**Expected Console Output:**
```
[GA4] Analytics initialized
[GA4] Page view sent
```

### 4.2 Real-time Verification (After Deployment)

**Wait 30-60 seconds after deployment**, then:

1. **Open GA4 Real-time Report:**
   - Go to: https://analytics.google.com
   - Select property: `Marceau Solutions Website`
   - Left sidebar: **Reports** → **Real-time**

2. **Visit your website:**
   - Open: https://marceausolutions.com
   - Navigate to a few pages (contact, pricing)

3. **Watch Real-time Report:**
   - **Users in last 30 minutes:** Should show 1+ users
   - **Event count by Event name:** Should show `page_view` events
   - **View by Page title and screen name:** Should show page names

**✅ Success Indicators:**
- Real-time users count increases
- Page views appear within 5-10 seconds
- Geographic location shows (if enabled)

### 4.3 Test Form Submission Event

**Built-in event tracking** (already in form-handler.js):

1. Visit: https://marceausolutions.com/contact.html
2. Fill out and submit the contact form
3. Check GA4 Real-time → Events
4. Look for: `form_submission` event

**Event parameters tracked:**
- `form_type`: contact | inquiry
- `business_id`: marceausolutions
- `source`: contact-page | coming-soon-page

---

## 5. Events Being Tracked

### Automatic Events (GA4 Default)

These are tracked automatically without custom code:

| Event | Description | When Triggered |
|-------|-------------|----------------|
| `page_view` | User views a page | Every page load |
| `session_start` | New session begins | First page in session |
| `first_visit` | First time user | User's first visit ever |
| `user_engagement` | User actively engaged | After 10+ seconds on page |
| `scroll` | User scrolls page | After scrolling 90% |

### Custom Events (Already Implemented)

These are tracked via our form-handler.js:

| Event | Description | Parameters |
|-------|-------------|------------|
| `form_submission` | User submits a form | `form_type`, `business_id`, `source` |
| `opt_in_email` | Email opt-in selected | `opted_in` (true/false) |
| `opt_in_sms` | SMS opt-in selected | `opted_in` (true/false) |

**Implementation in form-handler.js:**
```javascript
// Track form submission
if (typeof gtag !== 'undefined') {
    gtag('event', 'form_submission', {
        'form_type': formType,
        'business_id': formData.business_id || 'marceausolutions',
        'source': formData.source || 'unknown'
    });
}
```

### Recommended Additional Events (Optional)

See [Section 8: Advanced Configuration](#8-advanced-configuration-optional) for how to add:

- **Scroll Depth Tracking** (25%, 50%, 75%, 100%)
- **Outbound Link Clicks** (external links)
- **CTA Button Clicks** ("View Pricing", "Get Early Access")
- **Phone/Email Clicks** (mailto: and tel: links)

---

## 6. View Reports & Data

### Real-time Reports

**Purpose:** See current activity (last 30 minutes)

**Access:** Reports → Real-time

**What you see:**
- Users right now
- Pages being viewed
- Traffic sources
- Geographic locations
- Events happening live

**Use cases:**
- Verify tracking works
- Test new features
- Monitor campaigns in real-time

### Standard Reports (Available after 24-48 hours)

#### Traffic Acquisition
**Path:** Reports → Acquisition → Traffic acquisition

**Shows:**
- Where visitors come from (Google, Direct, Referral)
- New vs returning users
- Engagement rate by source

#### Pages & Screens
**Path:** Reports → Engagement → Pages and screens

**Shows:**
- Most popular pages
- Average time on page
- Bounce rate per page

#### Events
**Path:** Reports → Engagement → Events

**Shows:**
- All events tracked
- Event count
- Total users triggering events

#### Conversions (Coming Soon)
**Path:** Reports → Conversions

**How to set up:**
1. Go to: Admin → Events
2. Find `form_submission` event
3. Toggle **"Mark as conversion"** ON
4. Now form submissions count as conversions

### Custom Reports & Explorations

**Path:** Explore → Create new exploration

**Useful explorations:**
- Form submission funnel (landing → form view → submission)
- User journey (path exploration)
- Cohort analysis (user retention)

---

## 7. Troubleshooting

### Issue: No data in GA4

**Checklist:**
1. ✅ GA4 code is uncommented (not wrapped in `<!--` `-->`)
2. ✅ Measurement ID is correct (format: `G-XXXXXXXXXX`)
3. ✅ Website is deployed to production (not just local)
4. ✅ Ad blockers disabled (test in incognito mode)
5. ✅ Wait 30-60 seconds for data to appear in Real-time

**How to check:**
```bash
# View GA4 code in deployed HTML
curl https://marceausolutions.com | grep "gtag"

# Expected output:
# <script async src="https://www.googletagmanager.com/gtag/js?id=G-ABC1234567"></script>
# (If you see <!-- before it, code is still commented out)
```

### Issue: "G-XXXXXXXXXX" still showing

**Problem:** Measurement ID not replaced

**Solution:**
```bash
# Re-run activation script with correct ID
./activate-ga4.sh G-ABC1234567

# Or manually replace in all 5 HTML files
```

### Issue: Events not showing

**Problem:** Custom events not firing

**Check browser console:**
```javascript
// Manually test event
gtag('event', 'test_event', {
    'test_param': 'test_value'
});
```

**Verify gtag is loaded:**
```javascript
console.log(typeof gtag);  // Should output: "function"
```

### Issue: Real-time shows data, but standard reports empty

**This is normal!** Standard reports have a 24-48 hour delay.

**Wait 24 hours**, then check:
- Reports → Engagement → Pages and screens
- Reports → Acquisition → Traffic acquisition

### Issue: Ad blocker blocking GA4

**Problem:** Browser extensions blocking analytics

**Solutions:**
1. Test in **Incognito/Private mode**
2. Disable ad blockers temporarily
3. Use different browser (Safari, Firefox, Chrome)

**Note:** GA4 respects Do Not Track (DNT) signals. If user has DNT enabled, tracking is blocked.

### Issue: Multiple data streams sending data

**Problem:** Duplicate Measurement IDs in code

**Check:**
```bash
# Search for all GA4 IDs in code
grep -r "G-" *.html

# Should only show YOUR Measurement ID (not G-XXXXXXXXXX)
```

---

## 8. Advanced Configuration (Optional)

### A. Enhanced Scroll Tracking

**Add to end of `<head>` in all HTML files:**

```html
<script>
// Enhanced scroll tracking (25%, 50%, 75%, 100%)
let scrollDepths = [25, 50, 75, 100];
let scrollTriggered = [];

window.addEventListener('scroll', function() {
    let scrollPercent = (window.scrollY / (document.documentElement.scrollHeight - window.innerHeight)) * 100;

    scrollDepths.forEach(depth => {
        if (scrollPercent >= depth && !scrollTriggered.includes(depth)) {
            scrollTriggered.push(depth);
            if (typeof gtag !== 'undefined') {
                gtag('event', 'scroll_depth', {
                    'percent': depth,
                    'page': window.location.pathname
                });
            }
        }
    });
});
</script>
```

### B. Outbound Link Tracking

**Add to end of `<body>` in all HTML files:**

```html
<script>
// Track outbound links
document.addEventListener('click', function(e) {
    let link = e.target.closest('a');
    if (!link) return;

    let href = link.getAttribute('href');
    if (!href) return;

    // External link
    if (href.startsWith('http') && !href.includes(window.location.hostname)) {
        if (typeof gtag !== 'undefined') {
            gtag('event', 'outbound_link_click', {
                'link_url': href,
                'link_text': link.innerText,
                'page': window.location.pathname
            });
        }
    }

    // Email link
    if (href.startsWith('mailto:')) {
        if (typeof gtag !== 'undefined') {
            gtag('event', 'email_click', {
                'email': href.replace('mailto:', ''),
                'page': window.location.pathname
            });
        }
    }

    // Phone link
    if (href.startsWith('tel:')) {
        if (typeof gtag !== 'undefined') {
            gtag('event', 'phone_click', {
                'phone': href.replace('tel:', ''),
                'page': window.location.pathname
            });
        }
    }
});
</script>
```

### C. CTA Button Tracking

**Add data attributes to CTA buttons:**

```html
<button
    class="btn-submit"
    data-ga-event="cta_click"
    data-ga-label="Get Early Access">
    Request Early Access
</button>
```

**Add tracking script:**

```html
<script>
// Track CTA button clicks
document.addEventListener('click', function(e) {
    let button = e.target.closest('[data-ga-event]');
    if (!button) return;

    if (typeof gtag !== 'undefined') {
        gtag('event', button.dataset.gaEvent, {
            'button_label': button.dataset.gaLabel || button.innerText,
            'page': window.location.pathname
        });
    }
});
</script>
```

### D. User Properties (Demographics)

**Track user business size or tier interest:**

```javascript
// Set user property based on form selection
gtag('set', 'user_properties', {
    'interest_tier': 'automation-starter',
    'has_website': 'yes'
});
```

### E. Google Tag Manager (Alternative Method)

**Instead of direct GA4 code, use GTM for more flexibility:**

1. Create GTM account: https://tagmanager.google.com
2. Add GTM container snippet to `<head>` and `<body>`
3. Configure GA4 tag inside GTM
4. Add triggers and variables via GTM interface

**Benefits:**
- No code changes for new tracking
- Version control for tags
- Testing environment
- Multiple analytics tools (GA4, Facebook Pixel, etc.)

**Tradeoff:** More complexity, another platform to manage

---

## Summary

### Files Modified by Activation Script

- ✅ `index.html` (coming soon page)
- ✅ `contact.html` (contact form)
- ✅ `pricing.html` (pricing page)
- ✅ `terms.html` (terms of service)
- ✅ `privacy.html` (privacy policy)

### What Gets Tracked Automatically

- Page views (all pages)
- Sessions & users
- Traffic sources
- Geographic data
- Device type (mobile, desktop, tablet)
- Form submissions (custom event)
- Opt-in preferences (custom events)

### What Requires Manual Setup

- Conversion goals (mark events as conversions in GA4)
- Custom reports (create in Explorations)
- Alerts (set up in Admin → Custom alerts)
- User segments (create in Audience builder)

### Compliance & Privacy

**GDPR/CCPA Considerations:**

Your privacy policy (privacy.html) should mention:
- ✅ Use of Google Analytics
- ✅ What data is collected (IP, pages, device)
- ✅ Purpose (improve user experience)
- ✅ User's right to opt-out (browser DNT)
- ✅ Google's privacy policy: https://policies.google.com/privacy

**IP Anonymization:**

GA4 automatically anonymizes IPs in the EU. No additional config needed.

**Cookie Consent (Optional):**

If targeting EU users, consider adding cookie consent banner:
- Only load GA4 after user consent
- Use tools like: OneTrust, Cookiebot, or custom implementation

---

## Quick Reference

### Important Links

| Resource | URL |
|----------|-----|
| **Google Analytics** | https://analytics.google.com |
| **GA4 Help Center** | https://support.google.com/analytics |
| **DebugView** (check events) | Analytics → Admin → DebugView |
| **Tag Assistant** (Chrome extension) | https://chrome.google.com/webstore (search "Tag Assistant") |

### Common Commands

```bash
# Activate GA4
./activate-ga4.sh G-ABC1234567

# Check if GA4 is active
grep "gtag" index.html

# View recent git changes
git diff HEAD~1 index.html

# Rollback (if needed)
git checkout HEAD~1 -- index.html contact.html pricing.html terms.html privacy.html
```

### Support Contacts

- **Google Analytics Support:** https://support.google.com/analytics/gethelp
- **Developer:** William Marceau (wmarceau@marceausolutions.com)

---

## Changelog

| Date | Change |
|------|--------|
| 2026-01-20 | Initial guide created with activation script |
| TBD | GA4 activated with Measurement ID: G-XXXXXXXXXX |

---

**Ready to activate?** Run: `./activate-ga4.sh G-XXXXXXXXXX` 🚀
