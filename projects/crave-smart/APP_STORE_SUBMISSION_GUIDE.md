# CraveSmart App Store Submission Guide

## Apple Developer Enrollment

| Field | Value |
|-------|-------|
| **Enrollment ID** | `5949X3CZ65` |
| **Enrollment Type** | Organization (LLC) |
| **Status** | Pending Verification |
| **Submitted** | 2026-01-18 |

**Next:** Apple will email you once they verify your authority to sign legal agreements. This typically takes 24-48 hours for organizations.

---

## Overview

This guide walks you through getting CraveSmart on the iOS App Store.

**Estimated Timeline:**
- Apple Developer enrollment: 24-48 hours
- Build & testing: 1-2 days
- App Review: 1-3 days
- **Total: 3-7 days**

---

## Step 1: Apple Developer Program Enrollment

### 1.1 Create/Use Apple ID
- Go to https://appleid.apple.com
- Use existing Apple ID or create new one
- Enable two-factor authentication (required)

### 1.2 Enroll in Apple Developer Program
- Go to https://developer.apple.com/programs/enroll/
- Choose **Individual** enrollment ($99/year)
- Complete identity verification
- Pay the $99 annual fee
- Wait for approval (usually 24-48 hours)

### 1.3 After Approval
You'll receive an email with access to:
- App Store Connect (https://appstoreconnect.apple.com)
- Developer portal (https://developer.apple.com/account)

**Save these credentials:**
- Apple Team ID (found in Membership details)
- Apple ID email

---

## Step 2: Configure EAS & Expo

### 2.1 Login to Expo
```bash
cd /Users/williammarceaujr./dev-sandbox/projects/crave-smart
npx eas login
```
Create an Expo account if you don't have one.

### 2.2 Link to Expo Project
```bash
npx eas init
```
This will create/update the project ID in app.json.

### 2.3 Update eas.json with your credentials
Edit `eas.json` and replace:
- `YOUR_APPLE_ID@email.com` → Your Apple ID email
- `YOUR_TEAM_ID` → Your Apple Team ID (from developer.apple.com/account → Membership)

The `ascAppId` will be filled in after creating the app in App Store Connect.

---

## Step 3: Create App in App Store Connect

### 3.1 Login to App Store Connect
- Go to https://appstoreconnect.apple.com
- Sign in with your Apple Developer account

### 3.2 Create New App
1. Click **My Apps** → **+** → **New App**
2. Fill in:
   - **Platform:** iOS
   - **Name:** CraveSmart - Predict Her Cravings
   - **Primary Language:** English (U.S.)
   - **Bundle ID:** com.cravesmart.app
   - **SKU:** cravesmart-001
   - **User Access:** Full Access

3. Click **Create**

### 3.3 Get App Store Connect App ID
After creation, the URL will look like:
`https://appstoreconnect.apple.com/apps/1234567890/...`

The number (1234567890) is your **ascAppId**. Add this to `eas.json`.

### 3.4 Fill in App Information
Use the content from `APP_STORE_LISTING.md`:
- Description
- Keywords
- Support URL
- Marketing URL
- Privacy Policy URL

---

## Step 4: Configure HealthKit Capability

### 4.1 In Developer Portal
1. Go to https://developer.apple.com/account/resources/identifiers
2. Find your App ID (com.cravesmart.app)
3. Click to edit
4. Enable **HealthKit** capability
5. Save

### 4.2 Already Configured in app.json
The HealthKit usage descriptions are already set:
```json
"infoPlist": {
  "NSHealthShareUsageDescription": "CraveSmart reads your menstrual cycle data...",
  "NSHealthUpdateUsageDescription": "CraveSmart may write craving logs..."
}
```

---

## Step 5: Build for App Store

### 5.1 Build Production iOS App
```bash
cd /Users/williammarceaujr./dev-sandbox/projects/crave-smart
npx eas build --platform ios --profile production
```

This will:
- Prompt you to log in to your Apple Developer account
- Create provisioning profiles automatically
- Build the app in the cloud
- Take 10-20 minutes

### 5.2 Monitor Build
The CLI will show a URL to track build progress.
When complete, you'll have a `.ipa` file.

---

## Step 6: Submit to App Store

### 6.1 Automatic Submission (Recommended)
```bash
npx eas submit --platform ios --latest
```

Or submit a specific build:
```bash
npx eas submit --platform ios --id BUILD_ID
```

### 6.2 Manual Submission (Alternative)
1. Download the `.ipa` from Expo build
2. Open **Transporter** app (free on Mac App Store)
3. Drag the `.ipa` into Transporter
4. Click **Deliver**

---

## Step 7: Complete App Store Connect Listing

### 7.1 Add Screenshots
Generate screenshots by:
1. Running the app in iOS Simulator
2. Press `Cmd + S` to save screenshot
3. Or use a tool like https://screenshots.pro

Required sizes:
- 6.7" Display: 1290 × 2796 pixels
- 6.5" Display: 1284 × 2778 pixels

### 7.2 Add App Preview Video (Optional)
Use the generated promo video:
```bash
python scripts/generate_promo_video.py story
```
Convert to App Store format (9:16, H.264, 30fps).

### 7.3 Set Pricing
1. Go to **Pricing and Availability**
2. Set price to **Free** (with in-app purchases)
3. Select countries/regions

### 7.4 Configure In-App Purchases
1. Go to **In-App Purchases**
2. Create **Auto-Renewable Subscription**
   - Reference Name: CraveSmart Premium
   - Product ID: com.cravesmart.app.premium.monthly
   - Price: $5.99/month
3. Add subscription description and features

### 7.5 Age Rating
Complete the questionnaire. CraveSmart should be **4+**.

### 7.6 App Review Information
- Add contact info
- Add notes for reviewer (see APP_STORE_LISTING.md)

---

## Step 8: Submit for Review

### 8.1 Select Build
In **App Store** tab → **iOS App** section:
1. Click **Select a build before you submit your app**
2. Choose your uploaded build
3. Click **Done**

### 8.2 Submit
1. Click **Add for Review**
2. Answer submission questions
3. Click **Submit to App Review**

---

## Step 9: Wait for Review

**Timeline:** 1-3 days (usually 24-48 hours)

### Possible Outcomes:
- **Approved:** App goes live! 🎉
- **Rejected:** Review feedback provided. Fix issues and resubmit.

### Common Rejection Reasons:
1. **Missing privacy policy** - Ensure URL is live
2. **HealthKit not properly justified** - Our descriptions should be fine
3. **Crashes on launch** - Test thoroughly before submitting
4. **Incomplete functionality** - All buttons must work

---

## Quick Reference Commands

```bash
# Login to Expo
npx eas login

# Initialize project
npx eas init

# Build for iOS App Store
npx eas build --platform ios --profile production

# Submit to App Store
npx eas submit --platform ios --latest

# Build for TestFlight (internal testing)
npx eas build --platform ios --profile preview

# Check build status
npx eas build:list
```

---

## Support

If you get stuck:
1. Expo docs: https://docs.expo.dev/submit/ios/
2. Apple developer forums: https://developer.apple.com/forums/
3. Ask me for help!

---

## Checklist

- [ ] Apple Developer account enrolled ($99 paid)
- [ ] Expo account created and logged in
- [ ] App created in App Store Connect
- [ ] eas.json updated with credentials
- [ ] HealthKit capability enabled
- [ ] Build completed successfully
- [ ] Build uploaded to App Store Connect
- [ ] Screenshots added (all required sizes)
- [ ] App description and metadata complete
- [ ] Privacy policy URL live
- [ ] Support URL live
- [ ] In-app purchase configured
- [ ] Submitted for review
