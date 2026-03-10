# GA4 Events Tracking Reference

**Website:** Marceau Solutions (marceausolutions.com)
**Last Updated:** 2026-01-20

---

## Overview

This document lists all events being tracked on the Marceau Solutions website, including automatic GA4 events and custom events implemented via `form-handler.js`.

---

## Event Categories

### 1. Automatic Events (GA4 Default)

These events are tracked automatically by GA4 without any custom code.

#### `page_view`
**Description:** User views a page
**When:** Every page load
**Parameters:**
- `page_title` - Title of the page (e.g., "Marceau Solutions | AI Automation - Coming Soon")
- `page_location` - Full URL (e.g., "https://marceausolutions.com/contact.html")
- `page_referrer` - Previous page URL

**Example Use Cases:**
- Most popular pages
- User navigation flow
- Landing page performance

---

#### `session_start`
**Description:** New session begins
**When:** First page view in a session (after 30 min of inactivity)
**Parameters:**
- `session_id` - Unique session identifier
- `engagement_time_msec` - Time spent engaged

**Example Use Cases:**
- Total sessions per day
- Average session duration
- Peak traffic hours

---

#### `first_visit`
**Description:** First time user visits
**When:** User's very first visit to the site (cookie-based)
**Parameters:**
- `session_id` - First session ID

**Example Use Cases:**
- New visitor count
- First visit conversion rate
- Acquisition effectiveness

---

#### `user_engagement`
**Description:** User actively engaged with page
**When:** After user is on page for 10+ seconds
**Parameters:**
- `engagement_time_msec` - Time engaged (milliseconds)

**Example Use Cases:**
- Content engagement
- Page quality score
- User interest level

---

#### `scroll`
**Description:** User scrolls page
**When:** User scrolls 90% down the page
**Parameters:**
- `percent_scrolled` - 90 (default GA4 threshold)

**Example Use Cases:**
- Content read-through rate
- Page length optimization
- User attention span

---

### 2. Custom Events (Implemented)

These events are tracked via custom code in `form-handler.js`.

#### `form_submission`
**Description:** User submits a form (inquiry or contact)
**When:** Form successfully submitted (before API call)
**Parameters:**
- `form_type`: `"inquiry"` | `"contact"`
- `business_id`: `"marceausolutions"`
- `source`: `"coming-soon-page"` | `"contact-page"`

**Implementation:**
```javascript
gtag('event', 'form_submission', {
    'form_type': formType,
    'business_id': formData.business_id || 'marceausolutions',
    'source': formData.source || 'unknown'
});
```

**Example Use Cases:**
- Total lead submissions
- Form conversion rate by page
- Source attribution (which page drives leads)

**How to track as Conversion:**
1. Go to: Admin → Events
2. Find `form_submission`
3. Toggle "Mark as conversion" ON

---

#### `opt_in_email`
**Description:** User email opt-in preference
**When:** Form submission with email opt-in checkbox state
**Parameters:**
- `opted_in`: `true` | `false`

**Implementation:**
```javascript
// Track email opt-in
gtag('event', 'opt_in_email', {
    'opted_in': formData.emailOptIn === 'on'
});
```

**Example Use Cases:**
- Email opt-in rate
- Consent tracking
- Communication preferences

---

#### `opt_in_sms`
**Description:** User SMS opt-in preference
**When:** Form submission with SMS opt-in checkbox state
**Parameters:**
- `opted_in`: `true` | `false`

**Implementation:**
```javascript
// Track SMS opt-in
gtag('event', 'opt_in_sms', {
    'opted_in': formData.smsOptIn === 'on'
});
```

**Example Use Cases:**
- SMS opt-in rate
- Multi-channel consent tracking
- TCPA compliance documentation

---

### 3. Recommended Events (Not Yet Implemented)

These events can be added for enhanced tracking. See [GA4-ACTIVATION-GUIDE.md Section 8](#advanced-configuration) for implementation code.

#### `scroll_depth` (Enhanced)
**Description:** User scrolls to specific depth thresholds
**When:** User scrolls past 25%, 50%, 75%, or 100%
**Parameters:**
- `percent`: `25` | `50` | `75` | `100`
- `page`: `/` | `/contact.html` | etc.

**Why Add This:**
- More granular than default 90% scroll
- Identify content drop-off points
- Optimize page length

**Implementation:** See [GA4-ACTIVATION-GUIDE.md Section 8.A](#a-enhanced-scroll-tracking)

---

#### `outbound_link_click`
**Description:** User clicks external link
**When:** Click on link with different domain
**Parameters:**
- `link_url`: Full URL of external link
- `link_text`: Link anchor text
- `page`: Current page path

**Why Add This:**
- Track referral traffic you're sending
- Measure partner link clicks
- Identify external resources users value

**Implementation:** See [GA4-ACTIVATION-GUIDE.md Section 8.B](#b-outbound-link-tracking)

---

#### `email_click`
**Description:** User clicks email link (mailto:)
**When:** Click on `mailto:` link
**Parameters:**
- `email`: Email address from href
- `page`: Current page path

**Why Add This:**
- Track intent to contact via email
- Measure email vs form preference
- Contact funnel analysis

**Implementation:** See [GA4-ACTIVATION-GUIDE.md Section 8.B](#b-outbound-link-tracking)

---

#### `phone_click`
**Description:** User clicks phone link (tel:)
**When:** Click on `tel:` link
**Parameters:**
- `phone`: Phone number from href
- `page`: Current page path

**Why Add This:**
- Track call intent (especially mobile)
- Measure phone vs form preference
- Mobile user behavior

**Implementation:** See [GA4-ACTIVATION-GUIDE.md Section 8.B](#b-outbound-link-tracking)

---

#### `cta_click`
**Description:** User clicks call-to-action button
**When:** Click on button with `data-ga-event="cta_click"`
**Parameters:**
- `button_label`: Button text or custom label
- `page`: Current page path

**Why Add This:**
- Measure CTA effectiveness
- A/B test button copy
- Identify high-performing CTAs

**Implementation:** See [GA4-ACTIVATION-GUIDE.md Section 8.C](#c-cta-button-tracking)

---

## Event Naming Conventions

GA4 recommends using **snake_case** for event names (lowercase with underscores).

### Good Examples:
- ✅ `form_submission`
- ✅ `opt_in_email`
- ✅ `scroll_depth`
- ✅ `outbound_link_click`

### Avoid:
- ❌ `FormSubmission` (PascalCase)
- ❌ `form-submission` (kebab-case)
- ❌ `FORM_SUBMISSION` (uppercase)
- ❌ `formSubmission` (camelCase)

---

## Custom Dimensions & Metrics

### User-Scoped Properties

**What:** Attributes that apply to the user across all sessions

**Potential Additions:**
- `interest_tier`: Tier selected in form (starter, growth, enterprise)
- `has_website`: Whether user indicated they have a website
- `first_contact_method`: Form, email, or phone

**How to Set:**
```javascript
gtag('set', 'user_properties', {
    'interest_tier': 'automation-starter',
    'has_website': 'yes'
});
```

### Event-Scoped Parameters

**What:** Attributes specific to a single event occurrence

**Already Implemented:**
- `form_type` (form_submission)
- `business_id` (form_submission)
- `source` (form_submission)
- `opted_in` (opt_in_email, opt_in_sms)

**Potential Additions:**
- `tier_selected`: Specific tier from dropdown
- `message_length`: Character count of message
- `response_time`: Time to submit form (seconds)

---

## Event Limits & Quotas

### GA4 Limits

| Limit Type | Value | Notes |
|------------|-------|-------|
| **Events per month** | 10 million | Free tier (standard property) |
| **Distinct event names** | 500 | Per property |
| **Event parameters** | 25 | Per event |
| **Parameter name length** | 40 characters | Max length |
| **Parameter value length** | 100 characters | Max length |

**Our Current Usage:**
- Automatic events: ~5
- Custom events: 3 (form_submission, opt_in_email, opt_in_sms)
- **Total:** 8 events (well under 500 limit)

**Recommended events would add:** +5 (total: 13 events)

---

## Event Conversion Tracking

### How to Mark Events as Conversions

**Goal:** Count certain events as business goals (leads, signups, etc.)

**Steps:**
1. Go to: **Admin** → **Events**
2. Find your event (e.g., `form_submission`)
3. Toggle **"Mark as conversion"** ON
4. Event now appears in: **Reports** → **Conversions**

**Recommended Conversions for Marceau Solutions:**

| Event | Why Mark as Conversion |
|-------|----------------------|
| `form_submission` | ✅ Primary conversion (lead generation) |
| `opt_in_email` | ✅ Secondary goal (list growth) |
| `phone_click` | ✅ Call intent (if implemented) |
| `cta_click` | ⚠️ Optional (depends on CTA importance) |
| `scroll_depth` (100%) | ❌ Don't convert (engagement metric, not goal) |

---

## Event Debugging

### Real-time Event Monitoring

**DebugView** (recommended for testing):

1. Go to: **Admin** → **DebugView**
2. Enable debug mode in browser:
   ```javascript
   // Add to browser console
   gtag('config', 'G-XXXXXXXXXX', {'debug_mode': true});
   ```
3. Or add to GA4 config:
   ```javascript
   gtag('config', 'G-XXXXXXXXXX', {
       'debug_mode': true
   });
   ```
4. Visit your site - events appear in DebugView within seconds

**Real-time Reports:**

- Go to: **Reports** → **Real-time**
- View: **Event count by Event name**
- See events as they fire (30-60 second delay)

### Browser Console Testing

**Manually trigger events:**

```javascript
// Test form submission event
gtag('event', 'form_submission', {
    'form_type': 'test',
    'business_id': 'marceausolutions',
    'source': 'console-test'
});

// Verify gtag is loaded
console.log(typeof gtag);  // Should output: "function"

// View dataLayer
console.log(window.dataLayer);
```

### Chrome Extension: Tag Assistant

**Install:** https://chrome.google.com/webstore (search "Tag Assistant")

**Use:**
1. Click extension icon
2. Click "Connect"
3. Navigate your site
4. View all tags firing + parameters

---

## Event Data Retention

### GA4 Data Retention Settings

**Default:** 2 months (user-level data)
**Max:** 14 months (free tier)

**How to Change:**
1. Go to: **Admin** → **Data Settings** → **Data Retention**
2. Select: **14 months**
3. Enable: **Reset user data on new activity** (recommended)

**What This Affects:**
- User-scoped data in Explorations
- Does NOT affect aggregated reports (kept indefinitely)
- Does NOT affect real-time reports

---

## Privacy & Compliance

### GDPR Compliance

**GA4 automatically:**
- ✅ Anonymizes IPs in EU
- ✅ Supports Do Not Track (DNT)
- ✅ Provides Data Deletion API

**You must:**
- ✅ Update privacy policy (mention GA4 usage)
- ✅ Allow users to opt-out
- ✅ Disclose what data is collected

### Cookie Consent

**GA4 cookies:**
- `_ga` - Main GA4 cookie (2 years)
- `_ga_<container-id>` - Stores campaign info (2 years)

**If targeting EU users:**
- Consider cookie consent banner
- Only load GA4 after consent
- Or use cookieless tracking (server-side GTM)

### Data Controller Agreement

**Already accepted during setup** (Step 1.6 in activation guide)

If you need to review or modify:
- Go to: **Admin** → **Account Settings** → **Data Processing Amendment**

---

## Reporting & Analysis Ideas

### Pre-built Reports

**Coming Soon (24-48 hours after activation):**

1. **Traffic Sources:** Where visitors come from
   - Path: Reports → Acquisition → Traffic acquisition
   - Question: "Which channel brings most leads?"

2. **Page Performance:** Most popular pages
   - Path: Reports → Engagement → Pages and screens
   - Question: "Which page converts best?"

3. **Form Conversion Funnel:**
   - Path: Explore → Funnel exploration
   - Steps: Page view → Form view → Form submission
   - Question: "Where do users drop off?"

### Custom Explorations

**Ideas for Marceau Solutions:**

1. **Lead Source Attribution:**
   - Dimension: `source` (from form_submission event)
   - Metric: Event count
   - Question: "Does contact page or home page drive more leads?"

2. **Tier Interest Analysis:**
   - Dimension: `interest` (from form data - if tracked as parameter)
   - Metric: Users
   - Question: "Which tier is most popular?"

3. **Opt-in Preferences:**
   - Events: `opt_in_email`, `opt_in_sms`
   - Dimension: `opted_in`
   - Question: "What % of users opt into each channel?"

4. **User Journey (Path Exploration):**
   - Path: Explore → Path exploration
   - Start: Landing page
   - End: Form submission
   - Question: "What path leads to conversion?"

---

## Integration with Other Tools

### Google Ads (Future)

**When running Google Ads:**
1. Link GA4 to Google Ads account
2. Import conversions from GA4
3. Use `form_submission` as conversion goal
4. Optimize campaigns based on GA4 data

### Google Search Console (Recommended)

**Connect GA4 to Search Console:**
1. Admin → Property → Product Links → Search Console
2. Link properties
3. View search queries driving traffic to your site

### CRM Integration (ClickUp)

**Potential:** Send GA4 events to ClickUp via webhook

**Use case:** Automatically create ClickUp task when `form_submission` event fires

**Implementation:** Use Google Tag Manager or Zapier

---

## Quick Reference

### Event Testing Checklist

Before deploying new events:

- [ ] Event name follows `snake_case` convention
- [ ] All parameters defined and documented
- [ ] Tested in browser console
- [ ] Verified in DebugView
- [ ] Appears in Real-time reports
- [ ] Added to this tracking reference doc

### Monthly Review Checklist

Once GA4 is active:

- [ ] Review top 10 pages (which get most traffic?)
- [ ] Check conversion rate (form submissions / visitors)
- [ ] Identify top traffic sources
- [ ] Review user behavior flow
- [ ] Check for errors in events (malformed parameters)
- [ ] Optimize underperforming pages

---

## Contact

**Questions about event tracking?**
- Developer: William Marceau (wmarceau@marceausolutions.com)
- GA4 Support: https://support.google.com/analytics

---

**Last Updated:** 2026-01-20
**Next Review:** After GA4 activation + 1 week
