# X (Twitter) Account Setup Guide for Client Businesses

## Overview

This guide walks through creating dedicated X accounts for:
1. **Square Foot Shipping & Storage** - @SquareFootShip (suggested)
2. **SW Florida Comfort HVAC** - @SWFLComfortHVAC (suggested)

---

## Prerequisites

You'll need for each account:
- Unique email address (can use Gmail + trick: wmarceau+squarefoot@gmail.com)
- Phone number for verification (can reuse after 24 hours between accounts)
- Profile picture (logo) - already generated
- Banner image (optional, can create later)

---

## Step 1: Create X Accounts

### For Square Foot Shipping:

1. **Go to**: https://twitter.com/i/flow/signup
2. **Email**: Use `wmarceau+squarefoot@marceausolutions.com` or dedicated email
3. **Name**: Square Foot Shipping
4. **Username**: Try `@SquareFootShip` or `@SqFtShipping`
5. **Complete verification** with phone number
6. **Skip** premium offers for now

### For SW Florida Comfort HVAC:

1. **Go to**: https://twitter.com/i/flow/signup (in incognito or different browser)
2. **Email**: Use `wmarceau+hvac@marceausolutions.com` or dedicated email
3. **Name**: SW Florida Comfort HVAC
4. **Username**: Try `@SWFLComfortHVAC` or `@SWFLComfortAC`
5. **Complete verification** with phone number (wait 24h if same number)
6. **Skip** premium offers

---

## Step 2: Set Up Profiles

### Profile Pictures (Logos)

The logos have been generated and are located at:

**HVAC Logo:**
```
/Users/williammarceaujr./swflorida-comfort-hvac/assets/logo-grok.png
```

**Square Foot Logo:**
```
/Users/williammarceaujr./squarefoot-shipping-website/assets/logo-grok.png
```

Upload these as profile pictures in X Settings > Profile.

### Profile Information

**Square Foot Shipping & Storage:**
```
Name: Square Foot Shipping & Storage
Bio: Professional logistics, warehouse storage & fulfillment in SW Florida. Climate-controlled storage, same-day delivery, 99% on-time rate. Your Space, Our Priority.
Location: Southwest Florida
Website: https://wmarceau.github.io/squarefoot-shipping-website/
Phone in bio: (239) 880-3365
```

**SW Florida Comfort HVAC:**
```
Name: SW Florida Comfort HVAC
Bio: AC repair, installation & maintenance in Naples, Fort Myers, Cape Coral. 24/7 emergency service, no overtime. Your Comfort, Our Mission. ❄️
Location: Naples, FL
Website: https://wmarceau.github.io/swflorida-comfort-hvac/
Phone in bio: (239) 766-6129
```

---

## Step 3: Get API Credentials (For Automation)

After creating each account, you need API access:

1. **Go to**: https://developer.twitter.com/en/portal/dashboard
2. **Sign in** with the business account
3. **Create a new App** for each business
4. **Get credentials**:
   - API Key (Consumer Key)
   - API Secret (Consumer Secret)
   - Access Token
   - Access Token Secret
   - Bearer Token

5. **Add to .env file**:

```bash
# Square Foot Shipping X Credentials
SQUAREFOOT_X_API_KEY=your_key
SQUAREFOOT_X_API_SECRET=your_secret
SQUAREFOOT_X_ACCESS_TOKEN=your_token
SQUAREFOOT_X_ACCESS_TOKEN_SECRET=your_token_secret

# SW Florida HVAC X Credentials
SWFLHVAC_X_API_KEY=your_key
SWFLHVAC_X_API_SECRET=your_secret
SWFLHVAC_X_ACCESS_TOKEN=your_token
SWFLHVAC_X_ACCESS_TOKEN_SECRET=your_token_secret
```

---

## Step 4: First Posts (Manual)

Before automation, post a few manual tweets to establish the accounts:

**Square Foot Shipping - First Tweet:**
```
Welcome to Square Foot Shipping & Storage! 📦

We provide professional logistics, warehouse storage, and fulfillment services across Southwest Florida.

✅ Climate-controlled storage
✅ Same-day local delivery
✅ 99% on-time rate

Get a free quote: (239) 880-3365

#Logistics #SWFL #SmallBusiness
```

**SW Florida Comfort HVAC - First Tweet:**
```
Welcome to SW Florida Comfort HVAC! ❄️

Keeping Naples, Fort Myers & Cape Coral cool since day one.

✅ 24/7 emergency service
✅ Same-day repairs
✅ No overtime charges

AC problems? Call now: (239) 766-6129

#HVAC #ACRepair #Naples #FortMyers
```

---

## Step 5: Enable Automation

Once API credentials are obtained, update the social media automation config:

```bash
# Edit the config file
nano /Users/williammarceaujr./dev-sandbox/projects/social-media-automation/config/businesses.json
```

Update the `social_accounts` section for each business with the actual handle and set `use_main_account: false`.

---

## Checklist

### Square Foot Shipping
- [ ] Create X account
- [ ] Set username (@SquareFootShip or similar)
- [ ] Upload profile picture (logo-grok.png)
- [ ] Complete bio with phone and website
- [ ] Post first welcome tweet
- [ ] Apply for developer access
- [ ] Get API credentials
- [ ] Add credentials to .env

### SW Florida Comfort HVAC
- [ ] Create X account
- [ ] Set username (@SWFLComfortHVAC or similar)
- [ ] Upload profile picture (logo-grok.png)
- [ ] Complete bio with phone and website
- [ ] Post first welcome tweet
- [ ] Apply for developer access
- [ ] Get API credentials
- [ ] Add credentials to .env

---

## Notes

- X Free tier allows 1,500 posts/month per account
- API access may take 24-48 hours to approve
- Can request elevated access later for higher limits
- Consider X Premium ($8/mo) for verification checkmark (builds trust)

---

Last Updated: 2026-01-18
