# Amazon SP-API Authorization - Manual Workaround

Since the authorization page isn't loading, here are alternative approaches:

## Option 1: Check Application Status in Developer Console

The blank page usually means the app isn't properly set up. Let's verify:

### Step 1: Go to Developer Console
Visit: https://developer.amazonservices.com

### Step 2: Navigate to Your App
1. Sign in with Seller Central credentials
2. Go to **"Apps & Services"** → **"Login with Amazon"**
3. Look for your application in the list

### Step 3: Verify App Settings
Click on your app and check:

**Required Settings:**
- ✅ **Client ID**: Should match `AMAZON_LWA_APP_ID` in your `.env`
- ✅ **Allowed Return URLs**: Must include `http://localhost:8080` or `https://localhost`
- ✅ **Allowed JavaScript Origins**: Can be empty or include `http://localhost:8080`

**If Return URL is missing:**
1. Click **"Edit App Configuration"** or **"Web Settings"**
2. Add **Allowed Return URLs**:
   ```
   http://localhost:8080
   http://localhost:8080/callback
   https://localhost
   ```
3. Save changes

### Step 4: Get Authorization URL
After fixing settings, the authorization URL format is:
```
https://sellercentral.amazon.com/apps/authorize/consent?application_id=YOUR_LWA_APP_ID&version=beta
```

Replace `YOUR_LWA_APP_ID` with your actual app ID from `.env`

---

## Option 2: Re-Register the Application

If the app doesn't exist or is broken, create a new one:

### Step 1: Create New SP-API Application

1. Go to https://developer.amazonservices.com
2. Navigate to **"Apps & Services"** → **"Add a new app client"**

### Step 2: App Configuration

**App Name**: Marceau Solutions Seller Automation
**Description**: Inventory optimization and seller automation

**Privacy Notice URL**: Your website or `https://example.com/privacy`
**Logo**: Optional (can skip)

**Allowed Return URLs**:
```
http://localhost:8080
http://localhost:8080/callback
https://localhost
```

**Allowed JavaScript Origins**:
```
http://localhost:8080
```

### Step 3: Note Your Credentials

After creating, you'll get:
- **Client ID** (LWA App ID)
- **Client Secret** (LWA Client Secret)

**Update your `.env`:**
```bash
AMAZON_LWA_APP_ID=amzn1.application-oa2-client.XXXXX
AMAZON_LWA_CLIENT_SECRET=amzn1.oa2-cs.v1.XXXXX
```

### Step 4: Register for SP-API

1. Still in Developer Console, go to **"Selling Partner API"** section
2. Click **"Register"** or **"Add a new application"**
3. Link it to the LWA app you just created
4. Add your **IAM Role ARN** (from your `.env`)

---

## Option 3: Use Existing Self-Authorization (If Available)

Some Amazon Seller accounts allow self-authorization:

### Check if Self-Authorization is Available

1. Go to Seller Central: https://sellercentral.amazon.com
2. Navigate to **"Apps & Services"** → **"Manage Your Apps"**
3. Look for **"SP-API"** or **"Developer Applications"**
4. Check if there's a **"Self Authorize"** or **"Generate Credentials"** option

If available:
1. Click **"Self Authorize"** or **"Authorize"**
2. You'll get a refresh token directly
3. Copy it to your `.env` as `AMAZON_REFRESH_TOKEN`

---

## Option 4: Contact Amazon SP-API Support

If none of the above work:

1. **SP-API Support**: https://developer.amazonservices.com/support
2. **Issue**: "Cannot access app authorization page - getting blank screen"
3. **Provide**:
   - Your Seller ID
   - Application ID
   - Screenshot of blank page

---

## Temporary Workaround: Use Demo Mode

While fixing auth, you can still test the optimizer logic:

```bash
# This won't call real APIs but will show you how the tool works
python execution/amazon_inventory_optimizer.py --asin B08N5WRWNW --demo
```

---

## Quick Diagnostic Checklist

Run through this to identify the exact issue:

- [ ] **App exists** in Developer Console
- [ ] **Client ID** matches `.env`
- [ ] **Client Secret** matches `.env`
- [ ] **Return URLs** include `localhost` variants
- [ ] **App is active** (not disabled)
- [ ] **SP-API access** is enabled for the app
- [ ] **IAM Role ARN** is correct
- [ ] **IAM Role** has proper trust policy

---

## What's Most Likely

Based on the blank page, the most probable causes are:

1. **Missing Return URL** - App doesn't have `localhost` in allowed URLs
2. **App not registered** - Application doesn't exist or was deleted
3. **Wrong App ID** - The `application_id` in URL doesn't match an active app

**Next immediate step**: Check Developer Console to see if the app exists and has proper settings.

---

## Need the Application ID?

Check your `.env`:
```bash
grep "AMAZON_LWA_APP_ID" .env
```

This should be the same ID in the authorization URL.
