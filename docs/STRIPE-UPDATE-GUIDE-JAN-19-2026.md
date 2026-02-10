# Stripe Product Update Guide - January 19, 2026

**Purpose:** Replace standalone automation tiers with bundled Website + Automation offerings
**Reference:** `docs/STRIPE-PRODUCTS-V2-BUNDLED-OFFERINGS.md`
**Status:** NOT YET EXECUTED - This guide documents the process to follow

---

## What's Changing

**OLD Products (Archive):**
- Starter Automation Setup - $2,997
- Growth Automation Setup - $7,497
- Enterprise Automation Setup - $14,997

**NEW Products (Create):**
- Digital Storefront - Website + Automation Starter - $4,997
- Growth System - Website + Multi-Channel Automation - $9,997
- Enterprise Package - Custom AI Agent + Full-Stack Automation - $19,997

**KEEP (No Changes):**
- Maintenance Retainer - $747/month
- Partner Retainer - $2,247/month
- Claude Framework Community Monthly - $47/month
- Claude Framework Community Annual - $397/year

---

## Step-by-Step Process

### Step 1: Log into Stripe Dashboard

1. Go to: https://dashboard.stripe.com
2. Log in with: wmarceau@marceausolutions.com
3. Navigate to: Products → Product Catalog

---

### Step 2: Archive Old Automation Products

**For each old product:**

1. Click on product name
2. Click "Archive product" (top right)
3. Confirm archival

**Archive these 3 products:**
- [ ] Starter Automation Setup ($2,997)
- [ ] Growth Automation Setup ($7,497)
- [ ] Enterprise Automation Setup ($14,997)

**Why archive (not delete):**
- Preserves historical data
- Can reference old pricing if needed
- Can't accidentally charge old prices

---

### Step 3: Create Digital Storefront Product

**Product Details:**
- **Name:** `Digital Storefront - Website + Automation Starter`
- **Description:** (Copy from below, exactly as written)

```
Complete digital presence for local service businesses. Includes custom website (5-7 pages) + one core automation workflow. Perfect for businesses starting their digital transformation. Website, automation, and training - everything you need to start capturing leads and converting customers online.

What's Included:
• Custom website (5-7 pages, mobile-responsive)
• Domain + hosting setup (first year)
• SSL certificate (HTTPS)
• ONE automation workflow (choose: Voice AI OR Booking OR Quote Request)
• CRM integration (ClickUp)
• 1-hour training session
• 30-day warranty

Timeline: 4 weeks from contract to launch
```

- **Pricing:**
  - Model: One-time
  - Price: $4,997.00 USD
  - Tax: Taxable (if applicable in your jurisdiction)

- **Additional Settings:**
  - Product Images: Upload Marceau Solutions logo
  - Statement Descriptor: `MARCEAU DIGITAL`
  - Unit Label: `project`

**Create:**
1. Click "Add product"
2. Fill in details above
3. Click "Save product"
4. Verify it appears in Product Catalog

---

### Step 4: Create Growth System Product

**Product Details:**
- **Name:** `Growth System - Website + Multi-Channel Automation`
- **Description:** (Copy from below)

```
Complete growth infrastructure for scaling service businesses. Custom website + multi-step automation workflows + CRM pipeline management. Perfect for businesses ready to systematize lead capture, follow-up, and conversion. Includes voice AI, appointment booking, automated follow-ups, and CRM tracking.

What's Included:
• Professional website (up to 10 pages, SEO optimized)
• Voice AI call answering + routing
• Multi-step lead capture (forms, booking, quotes)
• Automated follow-up sequences (SMS + email)
• CRM pipeline management (ClickUp)
• 6 integrations (Twilio, Google Calendar, Email, Analytics)
• 2-hour training session + video library
• 60-day email support

Timeline: 6 weeks from contract to launch
```

- **Pricing:**
  - Model: One-time
  - Price: $9,997.00 USD
  - Tax: Taxable

- **Additional Settings:**
  - Product Images: Upload Marceau Solutions logo
  - Statement Descriptor: `MARCEAU GROWTH`
  - Unit Label: `project`

**Create:**
1. Click "Add product"
2. Fill in details above
3. Click "Save product"

---

### Step 5: Create Enterprise Package Product

**Product Details:**
- **Name:** `Enterprise Package - Custom AI Agent + Full-Stack Automation`
- **Description:** (Copy from below)

```
Complete AI-powered business operating system for established service businesses. Custom AI voice agent with advanced routing + comprehensive website + full automation stack + dedicated implementation. For businesses ready to fully automate lead capture, qualification, booking, and follow-up across all channels.

What's Included:
• Enterprise website (unlimited pages, professional copywriting, advanced SEO)
• Custom AI voice agent (trained on your business, multi-language)
• Comprehensive automation stack (multi-channel lead capture, advanced CRM, customer journey automation)
• Analytics & reporting dashboard (custom KPIs, weekly reports, A/B testing)
• 6+ system integrations (Twilio, Calendar, CRM, Stripe, Zapier, custom)
• 4 hours of team training + operations manual (50+ pages)
• 90 days of priority support

Timeline: 8-10 weeks from contract to launch

Note: Partner Retainer ($2,247/mo) required for first 6 months post-launch.
```

- **Pricing:**
  - Model: One-time
  - Price: $19,997.00 USD
  - Tax: Taxable

- **Additional Settings:**
  - Product Images: Upload Marceau Solutions logo
  - Statement Descriptor: `MARCEAU ENTERPRISE`
  - Unit Label: `project`

**Create:**
1. Click "Add product"
2. Fill in details above
3. Click "Save product"

---

### Step 6: Verify All Products

**Active Products Should Be:**
- [ ] Digital Storefront - $4,997
- [ ] Growth System - $9,997
- [ ] Enterprise Package - $19,997
- [ ] Maintenance Retainer - $747/mo
- [ ] Partner Retainer - $2,247/mo
- [ ] Claude Framework Community Monthly - $47/mo
- [ ] Claude Framework Community Annual - $397/year

**Archived Products:**
- [ ] Starter Automation Setup - $2,997
- [ ] Growth Automation Setup - $7,497
- [ ] Enterprise Automation Setup - $14,997

---

### Step 7: Create Payment Links

**For each new product, create payment link:**

1. Go to: Payment Links (left sidebar)
2. Click "New payment link"
3. Select product
4. Settings:
   - Collect customer information: ✅ (name, email, phone)
   - Allow promotion codes: ✅
   - Tax collection: ✅ (if applicable)
   - After payment: Custom success page URL: `https://marceausolutions.com/thank-you`

5. Create link
6. Copy payment link URL

**Save payment link URLs:**
- Digital Storefront: `https://buy.stripe.com/XXXXXXX`
- Growth System: `https://buy.stripe.com/XXXXXXX`
- Enterprise Package: `https://buy.stripe.com/XXXXXXX`

---

### Step 8: Document in Stripe Products Master Reference

Update `docs/STRIPE-PRODUCTS-MASTER-REFERENCE.md`:

1. Add "UPDATED: 2026-01-19" to header
2. Replace Product Line 1 section with new tiers
3. Add payment link URLs
4. Save file
5. Commit to git

---

### Step 9: Update Landing Page

Update `marceausolutions.com` pricing page:

1. Navigate to pricing section
2. Replace old tiers with new:
   - Digital Storefront ($4,997)
   - Growth System ($9,997)
   - Enterprise Package ($19,997)
3. Update "What's Included" bullets to match Stripe descriptions
4. Add payment links (from Step 7)
5. Deploy changes

---

### Step 10: Verification Checklist

**Before going live:**
- [ ] All 3 new products created in Stripe
- [ ] Descriptions match documentation exactly
- [ ] Pricing correct ($4,997, $9,997, $19,997)
- [ ] Payment links work (test with $0.01 test charge)
- [ ] Old products archived (not deleted)
- [ ] Retainers unchanged
- [ ] Documentation updated (STRIPE-PRODUCTS-MASTER-REFERENCE.md)
- [ ] Landing page updated with new pricing
- [ ] Git commit created with changes

---

## What to Do If You Need to Rollback

**If something goes wrong:**

1. **Unarchive old products:**
   - Go to Product Catalog → Archived
   - Click on product → "Unarchive product"

2. **Archive new products:**
   - Same process as Step 2

3. **Revert landing page:**
   - Use git to restore old version
   - Redeploy

---

## Post-Update Tasks

**After Stripe updated:**
1. Send email to existing prospects with new pricing
2. Update proposal templates to reference new tiers
3. Update CRM pipeline stages (if needed)
4. Create social media announcement (new pricing available)

---

## Execution Log

**Track when this is actually done:**

- [ ] Step 1-2: Archived old products - [Date/Time]
- [ ] Step 3-5: Created new products - [Date/Time]
- [ ] Step 6: Verified all products - [Date/Time]
- [ ] Step 7: Created payment links - [Date/Time]
- [ ] Step 8-9: Updated documentation + landing page - [Date/Time]
- [ ] Step 10: Final verification - [Date/Time]

**Executed by:** [Your name]
**Date Completed:** [YYYY-MM-DD]
**Time Taken:** [X hours]

---

## References

- **Pricing Documentation:** `docs/STRIPE-PRODUCTS-V2-BUNDLED-OFFERINGS.md`
- **Stripe Dashboard:** https://dashboard.stripe.com
- **Landing Page:** https://marceausolutions.com
