# 🔦 FaceTime Flashlight App

A simple iOS app that lets you toggle your flashlight even while on FaceTime.

## Why This Works

FaceTime uses the **front camera**, so the rear camera's torch is still available for your app to control. This app accesses AVFoundation directly to toggle the torch.

## Features

- 🔦 Big tap-to-toggle button
- 🔆 Brightness slider when on
- 📳 Haptic feedback
- 🌙 Dark UI that's easy on the eyes
- ✅ Works during FaceTime calls

## Quick Setup (Xcode)

1. Open Xcode
2. File → New → Project → iOS App
3. Name: `Flashlight`
4. Interface: **SwiftUI**
5. Bundle ID: `com.marceausolutions.flashlight`
6. Delete the default `ContentView.swift`
7. Replace with `FlashlightApp.swift` from this folder
8. Copy `Info.plist` values (especially `NSCameraUsageDescription`)
9. Build & run on your iPhone

## One-Liner Setup

Or just run this on your Mac:

```bash
cd ~/Desktop
mkdir -p Flashlight && cd Flashlight
curl -O https://raw.githubusercontent.com/MarceauSolutions/dev-sandbox/main/projects/flashlight-app/FlashlightApp.swift
# Then create new Xcode project and drop in the file
```

## Permissions

The app needs camera permission (for torch access). It will prompt on first launch.

## Usage

1. Start your FaceTime call
2. Swipe up to go home (or use App Switcher)
3. Open Flashlight app
4. Tap the button to turn on
5. Swipe back to FaceTime - light stays on! 🎉

---

Built by Clawdbot 🤖
