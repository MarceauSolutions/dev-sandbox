# EUC Ride Tracker

The ultimate ride tracking app for electric unicycle riders. One tap to start, track your stats, conquer trails.

Built for InMotion V13, V12, S22, and all EUC riders who love off-road trails, hill climbing, and pushing limits.

## Features
- One-tap start tracking - no setup, just ride
- Real-time distance, time, pace, and speed (top & avg)
- Elevation gain/loss tracking - perfect for hill climbers
- Elevation profile chart visualization
- Route visualization with start/end markers
- Export to GPX (Strava/Relive compatible) or JSON
- Electric blue dark theme - high visibility outdoors
- Background tracking for long trail rides

## Setup Instructions

### Prerequisites
- Node.js 18+ installed
- VS Code with Claude extension (optional but helpful)

### Step 1: Install Expo CLI
```bash
npm install -g expo-cli
```

### Step 2: Navigate to project folder
```bash
cd GoTracker
```

### Step 3: Install dependencies
```bash
npm install
```

### Step 4: Create assets folder and placeholder images
```bash
mkdir assets
```
You'll need to add:
- `assets/icon.png` (1024x1024 app icon)
- `assets/splash.png` (1284x2778 splash screen)
- `assets/adaptive-icon.png` (1024x1024 for Android)

Or just create simple placeholder images for now.

### Step 5: Start the development server
```bash
npx expo start
```

### Step 6: Run on your device
- **iOS**: Scan QR code with Camera app (requires Expo Go from App Store)
- **Android**: Scan QR code with Expo Go app (from Play Store)
- **Simulator**: Press `i` for iOS simulator or `a` for Android emulator

## Building for Production

### iOS (requires Mac + Apple Developer account)
```bash
npx expo build:ios
```

### Android
```bash
npx expo build:android
```

Or use EAS Build (recommended):
```bash
npm install -g eas-cli
eas build --platform all
```

## Project Structure
```
GoTracker/
├── App.js          # Main app component
├── app.json        # Expo configuration
├── package.json    # Dependencies
└── assets/         # Icons and splash screens
```

## Target Audience
- Electric unicycle (EUC) riders
- InMotion V13, V12, S22, V11, V8 owners
- Begode, Kingsong, Veteran riders
- Off-road trail enthusiasts
- Hill climbers and elevation chasers
- Extreme sports athletes

## Stats That Matter for EUC
- **Top Speed** - How fast did you push it?
- **Distance** - How far did you ride?
- **Elevation Gain** - How much did you climb?
- **Pace** - Minutes per mile for endurance tracking

## Notes
- GPS accuracy depends on device hardware
- Elevation data requires barometric altimeter for best results
- Background tracking works on iOS with proper permissions
- GPX exports can be imported directly to Strava, Garmin Connect, Relive
