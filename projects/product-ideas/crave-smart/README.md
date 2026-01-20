# CraveSmart

> Finally understand why you crave what you crave

A mobile app that predicts food cravings based on your menstrual cycle, time of day, and personal patterns.

## The Problem

91.78% of menstruating women report food cravings tied to their cycle ([PMC research](https://pmc.ncbi.nlm.nih.gov/articles/PMC10316899/)). Yet no app exists to help them understand and anticipate these patterns.

## The Solution

CraveSmart connects to your existing period tracker (via Apple Health) and learns your personal craving patterns. It predicts what you might want to eat based on:

- **Cycle phase** (luteal phase = sweet/carb cravings)
- **Time of day** (afternoon slump = caffeine/sugar)
- **Day of week** (Friday = comfort food)
- **Weather** (cold = warm comfort foods)
- **Your history** (you always want Thai on Thursdays)

## Features

### Free Tier
- Basic craving logging
- Pattern visualization
- Simple predictions

### Premium ($5.99/month)
- Cycle-aware predictions
- Partner sharing
- Restaurant recommendations
- Detailed analytics

## Tech Stack

- **Frontend**: React Native + Expo
- **Backend**: Supabase
- **Health Data**: Apple HealthKit
- **Payments**: RevenueCat

## Development

```bash
# Install dependencies
npm install

# Start development
npx expo start

# Run on iOS simulator
npx expo start --ios

# Run on Android emulator
npx expo start --android
```

## Project Status

- [x] Market research complete
- [x] Kickoff documentation
- [ ] Landing page validation
- [ ] MVP development
- [ ] Beta testing
- [ ] App Store submission

## Research Backing

This app is informed by peer-reviewed research:

- [Food Intake and Cravings During Menstrual Cycle (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC10316899/)
- [UCLA Health: Menstrual Cravings Are Real](https://www.uclahealth.org/news/article/menstrual-cravings-are-all-your-head-your-brain)
- [Scientific American: Period Food Cravings](https://www.scientificamerican.com/article/period-food-cravings-are-real-a-new-brain-finding-could-explain-why-they-happen/)

## Privacy

- Your health data never leaves your device without explicit consent
- We use Apple HealthKit's privacy-first architecture
- No data sold to third parties
- GDPR compliant

## License

Proprietary - All rights reserved

---

*Built in dev-sandbox*
