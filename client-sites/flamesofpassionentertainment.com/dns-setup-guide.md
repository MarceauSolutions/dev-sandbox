# Domain Setup Guide

## Flames of Passion Entertainment

**Prepared by:** Marceau Solutions
**Date:** March 2026

---

## What This Guide Does

This guide walks you through pointing your domain (`flamesofpassionentertainment.com`) to your website. Your website is already built and hosted for free — we just need to update a few settings in your Google Admin Console.

**Time needed:** ~10 minutes
**Difficulty:** Easy — just copying and pasting values

---

## Where Your Domain Lives

Your domain is registered through Squarespace, but your DNS (the settings that control where your domain points) is managed through **Google Workspace**. That's why you can see it in your Google Admin Console. All the steps below are done in Google.

---

## Step 1: Log Into Google Admin Console

1. Go to **admin.google.com**
2. Sign in with your Google Workspace account

---

## Step 2: Navigate to DNS Settings

1. In the left sidebar, click **Domains**
2. Click **Manage domains**
3. Find `flamesofpassionentertainment.com` and click on it
4. Look for **DNS** or **Advanced DNS settings**

If you see a link that says "Manage DNS" or "Google Domains" — click it. It may open a separate DNS management page.

---

## Step 3: Remove Any Existing A Records

Before adding new records, look for any existing **A records** in the list.

- If you see any A records, delete them by clicking the **trash icon** or **X**
- **DO NOT delete** any MX records (those are for your email)
- **DO NOT delete** any TXT records (those verify your domain)

---

## Step 4: Add the 4 A Records

Click **Add new record** (or **Create new record**) and select type **A**.

You need to add 4 records, one at a time:

| Record # | Host name | Type | Data (copy exactly) |
|----------|-----------|------|---------------------|
| 1 | `@` | A | `185.199.108.153` |
| 2 | `@` | A | `185.199.109.153` |
| 3 | `@` | A | `185.199.110.153` |
| 4 | `@` | A | `185.199.111.153` |

Click **Save** after each one.

---

## Step 5: Add the CNAME Record

Click **Add new record** one more time:

| Host name | Type | Data (copy exactly) |
|-----------|------|---------------------|
| `www` | CNAME | `marceausolutions.github.io` |

Click **Save**.

---

## Step 6: Check Your Work

Your DNS records should now include these 5 new entries:

| Type | Host | Data |
|------|------|------|
| A | @ | 185.199.108.153 |
| A | @ | 185.199.109.153 |
| A | @ | 185.199.110.153 |
| A | @ | 185.199.111.153 |
| CNAME | www | marceausolutions.github.io |

(You'll also see MX and TXT records — leave those alone, they're for email.)

---

## Step 7: Wait & Test

DNS changes take a little time to spread across the internet:

- **Usually:** 15–30 minutes
- **Worst case:** Up to 48 hours (rare)

After waiting 15–30 minutes:

1. Open a browser in incognito/private mode
2. Go to `flamesofpassionentertainment.com`
3. You should see your Flames of Passion website!
4. Also try `www.flamesofpassionentertainment.com`

**If it's not working after 30 minutes:**
- Double-check the IP addresses for typos
- Make sure old A records are deleted
- Clear your browser cache or try a different browser

---

## Step 8: Text William When It's Working!

Once you see your website on your domain, text me so I can:

- Turn on HTTPS (the padlock icon in the browser)
- Make sure everything looks perfect

---

## Need Help?

If you get stuck, just text or call:

**William Marceau**
Phone: (239) 398-5676
Email: wmarceau@marceausolutions.com

---

## Quick Reference — All Values

| What | Value |
|------|-------|
| A Record IP #1 | `185.199.108.153` |
| A Record IP #2 | `185.199.109.153` |
| A Record IP #3 | `185.199.110.153` |
| A Record IP #4 | `185.199.111.153` |
| CNAME Host | `www` |
| CNAME Points To | `marceausolutions.github.io` |
