# 🔒 DumbPhone Lock

**Actually enforce Focus Mode** — blocks apps at the system level so you can't cheat.

## What It Does

When you start a Focus session, DumbPhone Lock uses Apple's **Screen Time APIs** to shield selected apps. If you try to open Instagram, Twitter, etc., you'll see a block screen instead of the app.

No more "just quickly checking" — the apps are locked until you end the session.

## Features

- 🚫 **Real app blocking** using FamilyControls/ManagedSettings
- 🎯 **Pick specific apps** or entire categories to block
- ⏱️ **Timed sessions** or manual control
- 🎨 **Custom block screen** with your "Embrace the Pain" branding
- 🔐 **Unlock friction** — confirmation required to end early

## Architecture

The app uses three Apple frameworks:

1. **FamilyControls** — Authorization for Screen Time access
2. **ManagedSettings** — Applies shields to apps/categories
3. **DeviceActivity** — Monitors usage and enforces rules

Plus two app extensions:
- **DumbPhoneLockMonitor** — DeviceActivity extension
- **DumbPhoneLockShield** — Custom block screen UI

## Xcode Setup

### 1. Create New Project

1. File → New → Project → iOS App
2. Name: `DumbPhoneLock`
3. Bundle ID: `com.marceausolutions.dumbphonelock`
4. Interface: **SwiftUI**
5. Language: **Swift**

### 2. Add Capabilities

1. Select project → Signing & Capabilities
2. Click **+ Capability**
3. Add **Family Controls**

### 3. Add Extensions

For **DeviceActivityMonitor**:
1. File → New → Target → Device Activity Monitor Extension
2. Name: `DumbPhoneLockMonitor`
3. Copy `DeviceActivityMonitorExtension.swift` code

For **ShieldConfiguration**:
1. File → New → Target → Shield Configuration Extension  
2. Name: `DumbPhoneLockShield`
3. Copy `ShieldConfigurationExtension.swift` code

### 4. Copy Source Files

Replace generated files with:
- `DumbPhoneLockApp.swift`
- `AppBlocker.swift`
- `ContentView.swift`
- Add `DumbPhoneLock.entitlements`

### 5. Build & Run

1. Connect iPhone
2. Select your Apple ID team
3. Cmd+R to build
4. Trust developer in Settings if needed

## Usage

1. **Authorize** — Grant Screen Time access on first launch
2. **Select apps** — Tap to choose apps/categories to block
3. **Start focus** — Apps are now shielded
4. **Try opening blocked app** — See the custom block screen
5. **End session** — Confirm to unlock

## Requirements

- iOS 16.0+
- iPhone (not simulator — FamilyControls needs real device)
- Free Apple ID (sideload expires in 7 days)

## Integrating with Existing DumbPhone

If you have a DumbPhone shortcut/app already:
1. This app handles the blocking
2. Your existing setup handles the minimal home screen
3. They work together — DumbPhone for the look, this for the enforcement

## Limitations

- **First-party apps**: Some Apple apps can't be blocked
- **Phone/Messages**: Essential apps are always accessible
- **Settings app**: Can't be blocked (by design)

---

Built by Clawdbot 🤖 | "Embrace the Pain & Defy the Odds"
