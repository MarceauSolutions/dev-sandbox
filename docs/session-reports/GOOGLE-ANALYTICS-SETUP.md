# Google Analytics Setup Guide

**Date**: 2026-01-20
**Purpose**: Add GA4 tracking to marceausolutions.com and swfloridacomfort.com

---

## Executive Summary

**Websites Assessed**:
1. ✅ **marceausolutions.com** - Needs Google Analytics
2. ⚠️ **swfloridacomfort.com** - Website not found in standard location

**Recommendation**: Add GA4 to marceausolutions.com immediately

---

## Website Analysis

### 1. marceausolutions.com
**Location**: `/projects/marceau-solutions/marceausolutions.com/`

**Files**:
- `index.html` - Main landing page
- `contact.html` - Contact form
- `pricing.html` - Pricing page (assumed to exist)

**Current Tracking**: None detected

**Forms to Track**:
- Inquiry form on `index.html` (data-form-handler="inquiry")
- Contact form on `contact.html` (data-form-handler="contact")

**Needs GA4**: ✅ YES

---

### 2. swfloridacomfort.com
**Status**: ⚠️ Website files not found in expected location

**Search Results**:
```
Found references to:
- /projects/swflorida-hvac/ (business config, not website)
- /projects/shared/ai-customer-service/businesses/swflorida_hvac.py
- /output/form_submissions/swfloridacomfort/ (form data)
- /docs/companies/swflorida-hvac/
```

**Likely Scenarios**:
1. Website is hosted elsewhere (not in dev-sandbox)
2. Website is part of website-builder output
3. Website is embedded in ai-customer-service project

**Action Required**: Locate actual website files before adding GA4

---

## Google Analytics 4 (GA4) Setup

### Prerequisites

**Step 0: Create GA4 Property**

1. Go to: https://analytics.google.com
2. Create account (if needed): "Marceau Solutions"
3. Create property: "Marceau Solutions Website"
4. Select industry: "Business and Industrial Markets"
5. Set timezone: EST
6. Get Measurement ID: `G-XXXXXXXXXX`

---

## Implementation for marceausolutions.com

### Step 1: Add GA4 Tracking Code

**Where to insert**: In `<head>` section of ALL HTML files

**Files to update**:
- `/projects/marceau-solutions/marceausolutions.com/index.html`
- `/projects/marceau-solutions/marceausolutions.com/contact.html`
- `/projects/marceau-solutions/marceausolutions.com/pricing.html`

**Code to insert** (immediately after `<meta>` tags):

```html
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());

  gtag('config', 'G-XXXXXXXXXX');
</script>
```

**Example placement in index.html**:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Marceau Solutions | AI Automation - Coming Soon</title>

    <!-- Google tag (gtag.js) -->
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX"></script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){dataLayer.push(arguments);}
      gtag('js', new Date());
      gtag('config', 'G-XXXXXXXXXX');
    </script>

    <style>
        /* Existing styles... */
    </style>
</head>
```

---

### Step 2: Track Form Submissions

**Current form handler**: `/assets/js/form-handler.js`

**Add GA4 event tracking** to form submission success:

**Location**: After successful form submission in `form-handler.js`

**Code to add**:

```javascript
// After form submission succeeds
function trackFormSubmission(formType, formData) {
    // Send event to GA4
    if (typeof gtag !== 'undefined') {
        gtag('event', 'form_submission', {
            'form_type': formType,  // 'inquiry' or 'contact'
            'form_name': formData.get('name'),
            'interest': formData.get('interest'),
            'email_optin': formData.get('emailOptIn') === 'on',
            'sms_optin': formData.get('smsOptIn') === 'on',
            'source': formData.get('source')
        });
    }
}

// Call this function in success handler
// Example location:
document.getElementById('inquiryForm').addEventListener('submit', function(e) {
    e.preventDefault();

    const formData = new FormData(this);
    const formType = this.getAttribute('data-form-handler');

    // Send to backend
    sendFormData(formData).then(() => {
        // Show success message
        showSuccessMessage();

        // Track in GA4
        trackFormSubmission(formType, formData);
    });
});
```

---

### Step 3: Track Custom Events

**Events to track**:

1. **Pricing Page View**
```javascript
// In pricing.html, add to <head> after GA4 code:
<script>
  gtag('event', 'page_view', {
    'page_title': 'Pricing Page',
    'page_location': window.location.href
  });
</script>
```

2. **External Link Clicks** (email, phone)
```javascript
// Add to bottom of each HTML file before </body>:
<script>
  document.querySelectorAll('a[href^="mailto:"]').forEach(link => {
    link.addEventListener('click', () => {
      gtag('event', 'contact_click', {
        'contact_method': 'email',
        'contact_value': link.href
      });
    });
  });

  document.querySelectorAll('a[href^="tel:"]').forEach(link => {
    link.addEventListener('click', () => {
      gtag('event', 'contact_click', {
        'contact_method': 'phone',
        'contact_value': link.href
      });
    });
  });
</script>
```

3. **Checkbox Opt-In/Out Tracking**
```javascript
// Track when users toggle email/SMS opt-in
document.getElementById('emailOptIn')?.addEventListener('change', function() {
  gtag('event', 'optin_change', {
    'optin_type': 'email',
    'optin_status': this.checked
  });
});

document.getElementById('smsOptIn')?.addEventListener('change', function() {
  gtag('event', 'optin_change', {
    'optin_type': 'sms',
    'optin_status': this.checked
  });
});
```

---

### Step 4: Configure GA4 Goals/Conversions

**In GA4 Dashboard**:

1. Go to: Admin → Events → Create Event
2. Create conversion events:

| Event Name | Condition | Purpose |
|------------|-----------|---------|
| `form_submission` | Mark as conversion | Track lead submissions |
| `contact_click` | Mark as conversion | Track contact attempts |

---

## Events Summary

**Standard Events** (automatic with GA4):
- `page_view` - Page loads
- `scroll` - User scrolls 90%
- `click` - Outbound link clicks
- `session_start` - New sessions

**Custom Events** (manual tracking):

| Event Name | Parameters | Trigger |
|------------|-----------|---------|
| `form_submission` | `form_type`, `interest`, `email_optin`, `sms_optin` | Form submit success |
| `contact_click` | `contact_method`, `contact_value` | Email/phone link click |
| `optin_change` | `optin_type`, `optin_status` | Checkbox toggle |

---

## Verification Checklist

After implementation:

### Immediate Testing (1 hour)
- [ ] Install Google Tag Assistant Chrome extension
- [ ] Visit index.html in browser
- [ ] Verify GA4 tag fires (green checkmark)
- [ ] Submit test form
- [ ] Verify `form_submission` event appears in GA4 DebugView

### GA4 Dashboard Setup (30 minutes)
- [ ] Create custom report: "Form Submissions by Interest"
- [ ] Create custom report: "Contact Method Usage"
- [ ] Set up conversion goals
- [ ] Enable enhanced measurement (scroll tracking, file downloads)

### 24-Hour Check
- [ ] Verify real-time data appearing in GA4
- [ ] Check user flow: Landing → Pricing → Contact
- [ ] Verify form submission conversions tracked

---

## File Modification Summary

**Files to modify**:

1. **index.html** - Add GA4 code + event tracking
2. **contact.html** - Add GA4 code + event tracking
3. **pricing.html** - Add GA4 code + page view event
4. **form-handler.js** - Add form submission tracking

**Total changes**: ~50 lines of code across 4 files

---

## Implementation Script

**Quick implementation** (copy-paste ready):

```bash
# Replace G-XXXXXXXXXX with your actual Measurement ID

cd /Users/williammarceaujr./dev-sandbox/projects/marceau-solutions/marceausolutions.com

# Backup files first
cp index.html index.html.backup
cp contact.html contact.html.backup
cp pricing.html pricing.html.backup

# Then manually edit files to add GA4 code
# (No automated script provided to avoid breaking HTML)
```

**Manual steps**:
1. Get Measurement ID from GA4
2. Add GA4 tracking code to `<head>` of all 3 HTML files
3. Add event tracking scripts before `</body>` of all 3 HTML files
4. Update `form-handler.js` with form submission tracking
5. Test in browser with Tag Assistant

---

## swfloridacomfort.com - Next Steps

**Action required**: Locate website files

**Possible locations to check**:
1. `/projects/marceau-solutions/website-builder/output/` (generated sites)
2. Hosted externally (Netlify, Vercel, etc.)
3. Part of AI customer service landing pages

**Once found**:
- Follow same GA4 setup process as marceausolutions.com
- Track HVAC-specific form submissions
- Track quote requests

---

## Privacy & Compliance

**GDPR/CCPA Considerations**:

1. **Cookie Consent** (if targeting EU/CA):
   - Add cookie consent banner
   - Only load GA4 after user consent
   - Use Google Consent Mode

2. **Privacy Policy Update**:
   - Add section about analytics cookies
   - Explain data collection (anonymous usage stats)
   - Link to Google Analytics privacy policy

3. **IP Anonymization**:
   - GA4 anonymizes IPs by default (good!)

**Current marceausolutions.com**:
- Has links to `terms.html` and `privacy.html`
- Ensure privacy policy mentions analytics

---

## Cost

**Google Analytics 4**: FREE (up to 10M events/month)

No additional cost for:
- Unlimited websites
- Unlimited users
- Standard reports
- Custom dashboards

---

## Conclusion

**Recommendation**: Add GA4 to marceausolutions.com immediately

**Priority**:
1. **HIGH**: Add basic GA4 tracking code (10 minutes)
2. **MEDIUM**: Add form submission events (20 minutes)
3. **LOW**: Add advanced event tracking (30 minutes)

**Total implementation time**: 1 hour

**Expected insights**:
- Traffic sources (where visitors come from)
- Most popular pricing tier selections
- Form submission conversion rate
- User journey (Landing → Pricing → Contact flow)

---

**Next Steps**:
1. Create GA4 property and get Measurement ID
2. Update HTML files with GA4 code
3. Test with Google Tag Assistant
4. Monitor data for 24-48 hours
5. Set up custom reports

---

**Report Prepared By**: Claude Sonnet 4.5
**Date**: 2026-01-20
**Status**: Ready for Implementation
