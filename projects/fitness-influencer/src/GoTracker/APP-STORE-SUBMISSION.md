# EUC Ride Tracker - App Store Submission Guide

## Prerequisites Checklist

- [ ] Apple Developer Account ($99/year) - https://developer.apple.com
- [ ] Expo account - https://expo.dev
- [ ] EAS CLI installed

## Step 1: Create App Assets

You need these images before submitting:

| Asset | Size | Description |
|-------|------|-------------|
| `assets/icon.png` | 1024x1024 | App icon (no transparency, no rounded corners) |
| `assets/splash.png` | 1284x2778 | Splash screen (dark background #18181b recommended) |
| `assets/adaptive-icon.png` | 1024x1024 | Android adaptive icon foreground |

**Design notes**: Use electric blue (#00d4ff) accent color, dark background, modern EUC-inspired design

## Step 2: Install Dependencies & EAS CLI

```bash
cd /Users/williammarceaujr./dev-sandbox/projects/go-tracker/GoTracker

# Install project dependencies
npm install

# Install EAS CLI globally
npm install -g eas-cli

# Login to Expo
eas login
```

## Step 3: Create EAS Project

```bash
# Initialize EAS project (links to Expo account)
eas init

# This will give you a projectId - update app.json with it
```

After running `eas init`, update `app.json`:
- Replace `REPLACE_WITH_EAS_PROJECT_ID` with the actual project ID

## Step 4: Configure Apple Credentials

```bash
# Configure iOS credentials (will prompt for Apple ID)
eas credentials --platform ios
```

This will:
1. Ask for your Apple ID
2. Create/select certificates
3. Create/select provisioning profiles

## Step 5: Create App in App Store Connect

1. Go to https://appstoreconnect.apple.com
2. Click "My Apps" > "+" > "New App"
3. Fill in:
   - Platform: iOS
   - Name: EUC Ride Tracker
   - Primary Language: English (U.S.)
   - Bundle ID: com.marceausolutions.gotracker
   - SKU: euctracker-001
4. Note the **App Store Connect App ID** (numeric, in URL after /app/)
5. Update `eas.json` with `ascAppId`

## Step 6: Build for App Store

```bash
# Build production iOS app
eas build --platform ios --profile production
```

This will:
- Build in the cloud (~15-30 min)
- Create an .ipa file
- Sign with your certificates

## Step 7: Submit to App Store

```bash
# Submit the build to App Store Connect
eas submit --platform ios --latest
```

Or submit manually:
1. Download the .ipa from Expo dashboard
2. Use Transporter app on Mac to upload

## Step 8: Complete App Store Listing

In App Store Connect, fill in:

### App Information
- **Name**: EUC Ride Tracker
- **Subtitle**: Track Your Electric Unicycle Rides
- **Category**: Health & Fitness
- **Secondary Category**: Sports

### Description
```
EUC Ride Tracker is the ultimate ride tracking app built specifically for electric unicycle riders.

One tap to start. Track your stats. Conquer trails.

Built for InMotion V13, V12, S22 and all EUC riders who love pushing limits on off-road trails.

FEATURES:
• One-tap start - no setup, just ride
• Real-time speed tracking (top speed & average)
• Distance and pace monitoring
• Elevation gain/loss - perfect for hill climbers
• Elevation profile chart visualization
• Route mapping with start/end markers
• Export to GPX (Strava/Relive compatible) or JSON
• Electric blue dark theme - high visibility outdoors
• Background tracking for long trail rides

BUILT FOR EUC RIDERS:
Track the stats that matter - top speed, distance, and elevation gain. Export your rides to Strava, Relive, or Garmin Connect to share your adventures with the EUC community.

Whether you're carving trails on your InMotion, conquering hills on your Begode, or exploring new routes on your Kingsong - EUC Ride Tracker has you covered.

PRIVACY FOCUSED:
Your ride data stays on your device. Export when you want, where you want. No accounts required. No data collection.

Join thousands of EUC riders tracking their adventures!
```

### Keywords
```
EUC, electric unicycle, InMotion, ride tracker, trail riding, off-road, Begode, Kingsong, Veteran, GPS tracker, elevation, top speed, hill climb, extreme sports, one wheel
```

### Screenshots Required
- 6.7" display (iPhone 14 Pro Max): 1290 x 2796 px
- 6.5" display (iPhone 11 Pro Max): 1242 x 2688 px
- 5.5" display (iPhone 8 Plus): 1242 x 2208 px

Take screenshots of:
1. Main GO button screen (electric blue button)
2. Active tracking screen with stats showing
3. Results screen with route map and elevation
4. Elevation profile view
5. Export options (GPX/JSON)

### Privacy Policy
Required. Create a simple privacy policy stating:
- Location data is used only for ride tracking
- Data stays on device
- No data is collected or sent to servers
- GPX/JSON exports are user-controlled

Host at: https://marceausolutions.com/euc-ride-tracker/privacy

### Age Rating
- Set to 4+ (no objectionable content)

## Step 9: Submit for Review

1. Add build to the version
2. Complete all required metadata
3. Answer export compliance (No encryption = No)
4. Submit for review

Review typically takes 24-48 hours.

## App Store Optimization (ASO) Tips

### Primary Keywords (high priority)
- EUC
- electric unicycle
- ride tracker
- InMotion
- trail riding

### Secondary Keywords
- Begode
- Kingsong
- Veteran
- one wheel
- off-road
- GPS tracker
- elevation tracker
- top speed

### Competitive Positioning
- Simpler than generic fitness apps (Strava, etc.)
- Built specifically for EUC community
- No subscription required
- Privacy focused (no account needed)

## Commands Quick Reference

```bash
# Full submission flow
cd /Users/williammarceaujr./dev-sandbox/projects/go-tracker/GoTracker
npm install
eas login
eas init
eas credentials --platform ios
eas build --platform ios --profile production
eas submit --platform ios --latest
```
