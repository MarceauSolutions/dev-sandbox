# Mobile App Development Guide

A systematic framework for deciding when and how to build iOS/Android mobile applications as part of our product portfolio.

## When to Use This Guide

Use this guide when:
- Considering building a consumer-facing mobile app
- Evaluating whether an existing product should become a mobile app
- Planning a new product that might benefit from mobile distribution

**This guide integrates with:**
- SOP 0 (Project Kickoff)
- SOP 17 (Market Viability Analysis)
- `app-type-decision-guide.md` (now includes Mobile App type)

---

## Part 1: Should This Be a Mobile App?

### Mobile App Viability Scorecard

Score each factor 1-5 to determine if mobile is the right choice:

| Factor | 1 (Poor Fit) | 3 (Moderate) | 5 (Excellent Fit) |
|--------|--------------|--------------|-------------------|
| **Location Dependency** | Desktop-only use | Sometimes mobile | Always on-the-go |
| **Frequency of Use** | Weekly/monthly | Few times/week | Daily/multiple times |
| **Session Length** | 30+ minutes | 5-15 minutes | <5 minutes quick tasks |
| **Offline Need** | Never needed | Nice to have | Critical |
| **Push Notifications** | No value | Some value | Core to experience |
| **Camera/GPS/Sensors** | Not needed | Optional | Essential |
| **Competition** | No mobile apps | Some mobile apps | Mobile-first market |
| **Revenue Model** | Enterprise/B2B | Prosumer | Consumer subscription |

**Scoring:**
- **32-40**: Strong mobile candidate - proceed with mobile-first
- **24-31**: Consider mobile - may be worth pursuing
- **16-23**: Hybrid approach - web app with PWA might suffice
- **8-15**: Not a mobile fit - build web or desktop instead

---

### Decision Matrix: Mobile vs Other Platforms

```
START: New Product Idea
    │
    ▼
Is the primary user on-the-go?
    │
    ├─ YES → Does it need device features (camera, GPS, sensors)?
    │           │
    │           ├─ YES → BUILD NATIVE/CROSS-PLATFORM MOBILE APP
    │           │
    │           └─ NO → Consider PWA first (lower cost, faster)
    │
    └─ NO → Is this B2B or enterprise?
              │
              ├─ YES → BUILD WEB APP (desktop-first)
              │
              └─ NO → Does user need rich, frequent interaction?
                        │
                        ├─ YES → Consider mobile app OR web app
                        │
                        └─ NO → BUILD CLI/MCP/SKILL
```

---

## Part 2: Mobile App Economics

### Development Costs (2026)

| Approach | Dev Time (MVP) | Cost (Solo Dev) | Cost (Outsource) |
|----------|----------------|-----------------|------------------|
| **React Native + Expo** | 4-8 weeks | $0 (your time) | $15,000-40,000 |
| **Flutter** | 4-8 weeks | $0 (your time) | $18,000-50,000 |
| **Native (iOS + Android)** | 12-20 weeks | $0 (your time) | $40,000-120,000 |
| **PWA (Web App)** | 2-4 weeks | $0 (your time) | $8,000-20,000 |

### Ongoing Costs

| Cost Type | Monthly | Annual |
|-----------|---------|--------|
| Apple Developer Program | - | $99 |
| Google Play Console | - | $25 (one-time) |
| Expo (Pro tier) | $19 | $228 |
| Backend hosting | $20-100 | $240-1,200 |
| Push notifications (Firebase) | $0-25 | $0-300 |
| Analytics (Mixpanel/Amplitude) | $0-50 | $0-600 |
| **Total Minimum** | ~$20 | ~$350 |
| **Total Realistic** | ~$100 | ~$1,500 |

### Revenue Expectations (Consumer Apps)

| Model | Typical Revenue | Time to $1K MRR |
|-------|----------------|-----------------|
| **Freemium + IAP** | $0.50-2 ARPU | 6-12 months |
| **Subscription** | $5-15/mo | 3-6 months (with marketing) |
| **One-time purchase** | $2-10 | High volume needed |
| **Ad-supported** | $1-5 eCPM | Very high DAU needed |

**Reality check**: Most indie apps make <$500/month. Budget accordingly.

---

## Part 3: Framework Selection

### Recommended: React Native + Expo

**Why for solo developer:**
- JavaScript/TypeScript (familiar if you know web)
- Expo handles 90% of native complexity
- Free tier sufficient for MVP
- OTA updates (bypass app store for bug fixes)
- Large package ecosystem (25,000+ on npm)

**Limitations:**
- Some native modules require "ejecting"
- Slightly larger app size than native
- Performance ceiling for very complex apps

### Alternative: Flutter

**Consider when:**
- Need pixel-perfect custom UI
- Performance is critical (games, animations)
- Starting fresh (Dart learning curve acceptable)
- Google ecosystem integration

### When to Go Native

**Only if:**
- App Store featured placement is goal
- Maximum performance required (AR/VR, games)
- Deep OS integration needed
- Budget allows 2x development time

---

## Part 4: Mobile App Development SOP

### SOP 25: Mobile App Development

**When**: Building a mobile app for iOS/Android distribution

**Prerequisites**:
- ✅ SOP 17 (Market Viability) completed with GO decision
- ✅ Mobile App Viability Score ≥24
- ✅ Cost-benefit analysis shows positive ROI in 12 months

**Phase 1: Setup (Day 1)**

1. **Create accounts**:
   ```bash
   # Apple Developer ($99/year)
   # Visit: https://developer.apple.com/programs/enroll/

   # Google Play Console ($25 one-time)
   # Visit: https://play.google.com/console/signup

   # Expo account (free)
   npm install -g eas-cli
   eas login
   ```

2. **Initialize project**:
   ```bash
   npx create-expo-app@latest [app-name] --template tabs
   cd [app-name]

   # Configure for both platforms
   eas build:configure
   ```

3. **Project structure**:
   ```
   projects/[app-name]/
   ├── app/                    # Expo Router pages
   ├── components/             # Reusable components
   ├── hooks/                  # Custom hooks
   ├── services/               # API clients
   ├── store/                  # State management
   ├── app.json                # Expo config
   ├── eas.json                # Build config
   └── package.json
   ```

**Phase 2: Development (Weeks 1-4)**

4. **Core screens** (minimum viable):
   - Onboarding/Auth
   - Main feature (1-2 screens)
   - Settings/Profile
   - Error states

5. **Backend integration**:
   - Use existing FastAPI backend OR
   - Firebase/Supabase for rapid MVP
   - Implement offline-first if needed

6. **Testing**:
   ```bash
   # Development
   npx expo start

   # Preview builds (real device)
   eas build --profile preview --platform all
   ```

**Phase 3: Launch Prep (Week 5)**

7. **App Store assets**:
   - Icon (1024x1024)
   - Screenshots (6.5", 5.5" iPhone, Android phone/tablet)
   - Feature graphic (Android)
   - App preview video (optional but helps)

8. **Store listings**:
   - Title (30 chars)
   - Subtitle (30 chars)
   - Description (4000 chars)
   - Keywords (100 chars, iOS only)
   - Privacy policy URL (required)

**Phase 4: Submission (Week 6)**

9. **Build and submit**:
   ```bash
   # Production builds
   eas build --profile production --platform all

   # Submit to stores
   eas submit --platform ios
   eas submit --platform android
   ```

10. **Review timeline**:
    - iOS: 24-48 hours (first submission may take longer)
    - Android: 2-7 days (first app review is stricter)

**Phase 5: Post-Launch**

11. **Analytics setup**:
    - Mixpanel or Amplitude for events
    - Crash reporting (Sentry)
    - Store analytics

12. **Update strategy**:
    - OTA for bug fixes (instant)
    - Store update for native changes

---

## Part 5: Mobile App Candidates (Existing Products)

### Evaluation of Current Portfolio

| Product | Mobile Score | Recommendation | Rationale |
|---------|-------------|----------------|-----------|
| **Restaurant Finder** | 38/40 | BUILD | Location-based, quick sessions, daily use |
| **Fitness Influencer** | 28/40 | CONSIDER | Content creators use phones, but editing is desktop |
| **Voice AI Receptionist** | 12/40 | SKIP | Backend service, no user-facing mobile need |
| **Interview Prep** | 20/40 | PWA | Occasional use, mostly document generation |
| **Amazon Seller** | 18/40 | SKIP | Dashboard/analytics better on desktop |
| **Lead Scraper** | 10/40 | SKIP | B2B tool, desktop workflow |

### Highest Priority: Restaurant/Food Finder App

**Why this first:**
- Location is core (GPS)
- Frequent use (daily meals)
- Quick sessions (<2 min to decide)
- Clear monetization (affiliate, sponsored listings)
- Large existing market (validates demand)

**Unique angle**: AI-powered healthy + affordable + dietary preferences

---

## Part 6: Parallel Applications & Ecosystem

### Mobile Apps That Leverage Existing Backend

| Mobile App | Existing Backend | Shared Components |
|------------|------------------|-------------------|
| **Healthy Eats Finder** | Google Places API, Yelp API | Location services, reviews |
| **AI Voice Assistant** | Voice AI engine | Call transcripts, lead data |
| **Fitness Content Manager** | Fitness Influencer API | Video metadata, scheduling |
| **Price Compare** | MCP Aggregator | Rideshare, delivery prices |

### Build Once, Use Everywhere

```
┌─────────────────────────────────────────────────────┐
│                  SHARED BACKEND                      │
│  (FastAPI, existing APIs, Google/Yelp/etc)          │
└─────────────────────────────────────────────────────┘
         │              │              │
         ▼              ▼              ▼
    ┌─────────┐   ┌─────────┐   ┌─────────┐
    │ Mobile  │   │   Web   │   │  Claude │
    │   App   │   │   App   │   │  Skill  │
    └─────────┘   └─────────┘   └─────────┘
```

---

## Part 7: When NOT to Build Mobile

### Red Flags

- **Market saturated**: 100+ competing apps with millions of downloads
- **No clear monetization**: "We'll figure it out later"
- **Desktop-first workflow**: Users sit at computers to use it
- **Enterprise/B2B**: Decision makers use laptops, not phones
- **Complex data entry**: Forms, spreadsheets, document editing
- **One-time use**: Install, use once, delete

### Better Alternatives

| Scenario | Instead of Mobile App | Build This |
|----------|----------------------|------------|
| Occasional use | Native app | PWA (Progressive Web App) |
| Developer tool | Mobile app | CLI tool |
| AI-powered service | Consumer app | MCP + Claude integration |
| Internal tool | Mobile app | Web dashboard |
| B2B SaaS | Mobile app | Web app + mobile-responsive |

---

## Part 8: Integration with Existing SOPs

### Updated Decision Flow

```
New Product Idea
    │
    ▼
SOP 17: Market Viability (if new product)
    │
    ▼
SOP 0: Project Kickoff
    │
    ├─ Q11: Primary platform? → If "Mobile" → Use this guide
    │
    ▼
Mobile App Viability Scorecard (≥24 to proceed)
    │
    ▼
Framework Selection (React Native + Expo recommended)
    │
    ▼
SOP 25: Mobile App Development
    │
    ▼
SOP 3: Version Control & Deployment (app store submission)
```

### New Communication Patterns

| William Says | Claude Does |
|--------------|-------------|
| "Should this be a mobile app?" | Run Mobile App Viability Scorecard |
| "Build mobile app for X" | Run SOP 25 (Mobile App Development) |
| "Publish to app stores" | Run eas build + eas submit workflow |
| "Update the app" | OTA update via Expo or store submission |

---

## Quick Reference: Mobile Development Commands

```bash
# Setup
npm install -g eas-cli
npx create-expo-app@latest [name] --template tabs
cd [name] && eas build:configure

# Development
npx expo start                           # Start dev server
npx expo start --ios                     # iOS simulator
npx expo start --android                 # Android emulator

# Building
eas build --profile development          # Dev build
eas build --profile preview --platform all  # Test builds
eas build --profile production --platform all  # Store builds

# Submitting
eas submit --platform ios               # Submit to App Store
eas submit --platform android           # Submit to Play Store

# OTA Updates (no store review needed)
eas update --branch production          # Push update to users
```

---

## Resources

- [Expo Documentation](https://docs.expo.dev/)
- [React Native Documentation](https://reactnative.dev/)
- [App Store Review Guidelines](https://developer.apple.com/app-store/review/guidelines/)
- [Google Play Policy Center](https://play.google.com/console/about/guides/releasewithconfidence/)

---

*Guide Version: 1.0.0*
*Created: January 18, 2026*
*Next Review: April 18, 2026*
