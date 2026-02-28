# Domain Setup Guide

## Flames of Passion Entertainment

**Prepared by:** Marceau Solutions
**Date:** February 2026

---

## What This Guide Does

This will connect your domain name (e.g., `flamesofpassionentertainment.com`) to your live website. After completing these steps, visitors who type your domain into their browser will see your website.

---

## Step 1: Log Into Your Domain Registrar

Go to the website where you purchased your domain (e.g., Namecheap, GoDaddy, Google Domains) and log in.

- **Namecheap:** namecheap.com > Sign In > Dashboard
- **GoDaddy:** godaddy.com > Sign In > My Products
- **Google Domains:** domains.google.com

---

## Step 2: Find DNS Settings

Navigate to your domain's DNS management page:

- **Namecheap:** Domain List > click your domain > "Advanced DNS" tab
- **GoDaddy:** My Products > Domains > DNS > "Manage DNS"
- **Google Domains:** Click your domain > DNS

---

## Step 3: Add A Records

These records point your domain to GitHub's servers where your website is hosted.

**Add these 4 A records** (delete any existing A records first):

| Type | Host | Value | TTL |
|------|------|-------|-----|
| A | @ | `185.199.108.153` | Automatic |
| A | @ | `185.199.109.153` | Automatic |
| A | @ | `185.199.110.153` | Automatic |
| A | @ | `185.199.111.153` | Automatic |

**Note:** The `@` symbol means "root domain" (e.g., `flamesofpassionentertainment.com` without any prefix).

---

## Step 4: Add CNAME Record

This makes `www.yourdomain.com` also work:

| Type | Host | Value | TTL |
|------|------|-------|-----|
| CNAME | www | `marceausolutions.github.io` | Automatic |

---

## Step 5: Remove Conflicting Records

If you see any of these existing records, **delete them** (they'll conflict with the new ones):

- Any existing **A records** pointing to different IP addresses
- Any **URL Redirect** or **URL Frame** records
- Any existing **CNAME** for `www` pointing somewhere else

**Keep** any existing MX records (email) and TXT records (email verification) — those are separate and won't conflict.

---

## Step 6: Wait for Propagation

DNS changes can take **up to 48 hours** to propagate worldwide, but usually complete within **15-30 minutes**.

---

## Step 7: Verify It's Working

After waiting 15-30 minutes:

1. Open a browser and go to your domain (e.g., `flamesofpassionentertainment.com`)
2. You should see your Flames of Passion website
3. Also try `www.flamesofpassionentertainment.com` — this should work too

**If it's not working after 30 minutes:**
- Double-check all IP addresses are entered correctly
- Make sure there are no conflicting A records
- Try clearing your browser cache or using an incognito window
- DNS can take up to 48 hours in rare cases

---

## Step 8: Let Us Know

Once your domain is pointing to the site, send a message so we can:
- Enable HTTPS (free SSL certificate via GitHub Pages)
- Verify the booking form is working on your domain
- Set up any custom email addresses if needed

---

## Need Help?

Contact William Marceau:
- **Email:** wmarceau@marceausolutions.com
- **Phone:** (239) 398-5676

---

## Quick Reference

| What | Value |
|------|-------|
| A Record IPs | `185.199.108.153`, `185.199.109.153`, `185.199.110.153`, `185.199.111.153` |
| CNAME for www | `marceausolutions.github.io` |
| Website host | GitHub Pages |
| DNS propagation | 15 min - 48 hours |
