# DumbPhone Lock

**Status**: Pre-launch (Market Validation) | **Type**: iOS App (SwiftUI)
**Bundle ID**: com.marceausolutions.dumbphone
**Landing Page**: marceausolutions.com/dumbphone

## What It Does
Turns an iPhone into a distraction-free focus machine. Blocks apps using Apple's Screen Time / FamilyControls API with a minimal launcher UI, focus presets, and timed sessions.

## Project Structure
```
dumbphone-lock/
├── CLAUDE.md              # This file
├── KICKOFF.md             # SOP 0 decisions
├── VERSION                # Current version
├── CHANGELOG.md           # Version history
├── src/
│   ├── ios-launcher/      # Custom launcher app (SwiftUI, free signing)
│   │   ├── DumbPhoneApp.swift      # Main app (~620 lines)
│   │   ├── DumbPhone.xcodeproj/    # Xcode project
│   │   └── setup/                  # .mobileconfig + install server
│   └── ios-familycontrols/         # FamilyControls blocking (requires $99 dev account)
│       ├── AppBlocker.swift        # ManagedSettings + DeviceActivity
│       ├── ContentView.swift       # Authorization + config UI
│       ├── DumbPhoneLock.entitlements
│       ├── DumbPhoneLockMonitor/   # DeviceActivity extension
│       └── DumbPhoneLockShield/    # Shield configuration extension
├── marketing/
│   ├── dumbphone-launch-copy.md    # Ready-to-paste social media posts
│   └── dumbphone-ad-briefs.md     # Paid ad specs (Meta, TikTok, Reddit)
└── workflows/
```

## Key Locations
| What | Where |
|------|-------|
| **Launcher app (active, installed)** | `src/ios-launcher/DumbPhoneApp.swift` |
| **FamilyControls code (blocked by $99)** | `src/ios-familycontrols/` |
| **Landing page** | `projects/marceau-solutions/website/dumbphone.html` |
| **Link-in-bio page** | `projects/marceau-solutions/website/links.html` |
| **Desktop build directory** | `~/Desktop/DumbPhone/` (Xcode builds from here) |
| **Launch copy** | `marketing/dumbphone-launch-copy.md` |
| **Ad briefs** | `marketing/dumbphone-ad-briefs.md` |

## n8n Workflows (3 active)
| Workflow | ID | Webhook Path |
|----------|-----|-------------|
| DumbPhone-Waitlist-Capture | A9TdMLSIjUBXYXiI | `/webhook/dumbphone-waitlist` |
| DumbPhone-Email-Confirm | ilNn24FqfZcYGxcT | `/webhook/dumbphone-email-confirm` |
| DumbPhone-SMS-Drip | 4GKRU7i0JOh01yVT | `/webhook/dumbphone-sms-drip` |

## Google Sheets
- **Spreadsheet**: Challenge Leads (`13bEJ2eEdgRN3vM-wAOv1CrEp-7AtlKnAQTCnutP535E`)
- **Tab**: "DumbPhone Waitlist"
- **Columns**: Name, Email, Phone, Source, Medium, Campaign, Date, Status

## Build Commands
```bash
# Build and install launcher app (free signing)
cd ~/Desktop/DumbPhone && xcodebuild -project DumbPhone.xcodeproj -scheme DumbPhone \
  -destination 'id=00008140-00045D391AE8801C' -allowProvisioningUpdates \
  DEVELOPMENT_TEAM=Y4DDZ3ZJX5 build

# Install on device
xcrun devicectl device install app --device 00008140-00045D391AE8801C build/...

# Deploy landing page
./scripts/deploy_website.sh marceau
```

## Technical Notes
- **Free signing**: Team ID `Y4DDZ3ZJX5`, cert `AD3JMV9KG2`, 7-day expiry
- **FamilyControls**: Requires paid $99 Apple Developer account
- **iOS 26**: Settings deep links (`App-prefs://`, `prefs:root=`) are all broken
- **URL schemes**: `mobilephone://`, `sms:`, `facetime://`, `googlegmail://`, `googlecalendar://`, `comgooglemaps://`, `ddgQuickLink://`, `claude://`, `grok://`, `tg://resolve`

## Current Phase
Market validation via landing page + waitlist. Decision to buy $99 Apple Developer account depends on hitting 100+ signups in 48 hours from organic posting.
