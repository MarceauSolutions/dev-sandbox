# Agent 4: Mobile App / Deep Linking Approach

**Research completed:** January 12, 2026
**Approach evaluated:** Building a native/cross-platform mobile app using Uber/Lyft mobile SDKs and deep linking
**Final score:** ⭐⭐ (2/5 stars) - NOT RECOMMENDED

---

## Quick Links

📄 **[SUMMARY.md](./SUMMARY.md)** ← Start here for executive summary (5-min read)
📋 **[FINDINGS.md](./FINDINGS.md)** ← Complete research report (15-min read)
💻 **[code-example.md](./code-example.md)** ← Working React Native implementation (shows SDKs aren't needed)

---

## The Bottom Line

**Mobile SDKs are for deep linking to Uber/Lyft apps, NOT for retrieving prices.**

You still need the REST APIs (Agent 1's approach) to get price estimates for comparison. The mobile SDK approach adds 5-10x development complexity without solving the core problem.

### Critical Finding

From Uber's official documentation:
> "If you want to get price estimates, you have to communicate with our APIs."

**Translation:** The mobile SDKs don't help with price comparison. They only help with booking UX (deep linking to native apps).

---

## What I Researched

1. ✅ Uber mobile SDK capabilities (iOS/Android)
2. ✅ Lyft mobile SDK capabilities (iOS/Android)
3. ✅ Deep linking mechanisms (uber://, lyft://)
4. ✅ Price estimate retrieval via SDKs vs APIs
5. ✅ Authentication requirements (OAuth 2.0)
6. ✅ SDK maintenance status (active vs abandoned)
7. ✅ Terms of Service for mobile integration
8. ✅ React Native cross-platform feasibility
9. ✅ Cost analysis (development + ongoing)
10. ✅ Legal compliance (same ToS as web)

---

## Key Findings Summary

### What SDKs Provide
- ✅ Deep link buttons to Uber/Lyft native apps
- ✅ Pre-filled pickup/destination locations
- ✅ Single Sign-On (SSO) for user authentication
- ✅ Wrapper methods around REST APIs (just convenience)

### What SDKs DON'T Provide
- ❌ Programmatic price estimate retrieval (must use REST API directly)
- ❌ Side-by-side price comparison (violates Uber ToS)
- ❌ Any advantage for comparison use case
- ❌ Lyft SDK is abandoned (5 years old on iOS, 3 years on Android)

### The Real Mobile Flow

```
User opens mobile app
  ↓
User enters pickup/destination
  ↓
App calls UBER REST API for prices ← Same as web (Agent 1)
  ↓
App calls LYFT REST API for prices ← Same as web (Agent 1)
  ↓
Display price comparison
  ↓
User taps "Book with Uber"
  ↓
Deep link to Uber app ← ONLY new value from SDK
```

**Insight:** Steps 3-4 are identical to Agent 1 (web approach). Mobile SDKs only help with the final step (booking).

---

## Pros & Cons

### Pros (Very Limited)
1. ✅ Smoother booking UX (native app deep linking)
2. ✅ Uber SDKs actively maintained (though still beta)
3. ✅ React Native cross-platform possible

### Cons (Many, Critical)

**Technical:**
- ❌ Doesn't solve price comparison problem
- ❌ Lyft SDKs abandoned (iOS 2019, Android 2021)
- ❌ 5-10x more development effort than web
- ❌ High maintenance (OS updates, SDK updates)
- ❌ Mobile-only (can't use web)

**Legal:**
- ❌ Same Uber ToS violation (can't aggregate competitors)
- ❌ Platform doesn't change legal restrictions

**Business:**
- ❌ App store friction (download required vs instant web)
- ❌ Review delays and rejection risk
- ❌ Smaller audience (mobile-only vs universal web)

---

## SDK Maintenance Status

| Platform | Last Update | Status | Usable? |
|----------|-------------|--------|---------|
| **Uber iOS** | Oct 2024 | ✅ Active (beta) | Yes, but beta |
| **Uber Android** | July 2024 | ✅ Active (beta) | Yes, but beta |
| **Lyft iOS** | June 2019 | ❌ Abandoned | ⚠️ Risky (5 years old) |
| **Lyft Android** | Sept 2021 | ❌ Abandoned | ⚠️ Risky (3 years old) |

**Conclusion:** Can't build a reliable app when half the SDKs are abandoned.

---

## Costs

### Development
- **Native (iOS + Android):** $50k-150k
- **React Native:** $30k-80k
- **Mobile-responsive web:** $10k-30k ← Agent 1 approach

### Ongoing
- **API calls:** Same as Agent 1 (~$0.10/call)
- **App stores:** $99/year (Apple) + $25 (Google)
- **Maintenance:** High (OS updates, SDK updates, testing)

**ROI:** 5-10x cost for same functionality as web.

---

## Recommendation

### ❌ DON'T Use Mobile Approach For:
- Price comparison apps (ToS violation + no value add)
- Quick MVPs (too complex)
- Limited budgets (5-10x web cost)
- Maximum user reach (web better)

### ✅ MAYBE Use Mobile Approach For:
- Existing travel app adding ride booking
- Showing ONE service only (not comparing)
- You have explicit Uber/Lyft permission
- Mobile-first UX is critical (beyond this use case)

### ✅ Recommended Alternative

**Build mobile-responsive web app (Agent 1 approach):**
- Same price retrieval capability
- 10x cheaper to develop
- Instant access (no download)
- Reaches more users
- Easier to maintain
- Add "Save to Home Screen" for app-like experience

---

## Code Example Highlights

The `code-example.md` file contains a working React Native implementation that demonstrates:

1. **REST API calls are still required** - Exact same API calls as web approach
2. **Deep linking is trivial** - Just URL schemes (`uber://`, `lyft://`)
3. **No SDK dependencies needed** - React Native's built-in `Linking` API works fine
4. **Mobile web alternative** - Could achieve same UX with responsive web app

**Key code snippet:**
```javascript
// Fetch Uber prices (SDK doesn't help with this!)
const fetchUberPrices = async () => {
  const response = await axios.get(
    'https://api.uber.com/v1.2/estimates/price',
    // ... same REST API call as web approach
  );
};

// Deep link to Uber app (this is ALL the SDK does)
const bookUber = () => {
  Linking.openURL('uber://...');
};
```

---

## Comparison to Agent 1 (REST APIs)

| Feature | Mobile SDK | Web/API (Agent 1) |
|---------|-----------|-------------------|
| Price retrieval | ❌ Still needs REST API | ✅ Direct REST API |
| Booking UX | ✅ Deep link to app | ⚠️ Redirect to mobile web |
| Platform | ❌ Mobile only | ✅ Web + mobile web |
| Distribution | ❌ App store | ✅ Instant URL |
| Development | ❌ $50k-150k | ✅ $10k-30k |
| Maintenance | ❌ High | ⚠️ Medium |
| Lyft support | ❌ SDK abandoned | ✅ API works |
| ToS compliance | ❌ Violates | ❌ Violates |
| Time to market | ❌ 4-8 weeks | ✅ 1-2 weeks |

**Winner:** Agent 1 (web approach) unless you need native mobile app for OTHER reasons.

---

## Final Verdict

**Score: ⭐⭐ (2/5 stars)**

### Why NOT Recommended

1. **Wrong tool for the job** - Solves booking UX, not price comparison
2. **No value over web** - REST APIs still required (same as Agent 1)
3. **5-10x cost increase** - Mobile development much more expensive
4. **Lyft SDK abandoned** - Half the SDKs are 3-5 years old, likely broken
5. **Same ToS violation** - Platform doesn't change legal restrictions
6. **Limited reach** - Mobile-only vs web's universal access

### When Score Would Be Higher

This approach would score ⭐⭐⭐⭐ (4/5) if:
- ✅ Building a travel/booking app (ride-hailing is ONE feature)
- ✅ Not comparing prices (just booking rides)
- ✅ Already have mobile app infrastructure
- ✅ Have explicit permission to aggregate Uber/Lyft
- ✅ Budget allows for native mobile development

**But for price comparison specifically:** Not recommended. Use Agent 1's web approach instead.

---

## Next Steps

After reviewing these findings, consider:

1. **Read Agent 1's findings** - REST API approach is the baseline
2. **Read Agent 2's findings** - Web scraping approach analysis
3. **Read Agent 3's findings** - Third-party aggregator API research
4. **Compare all 4 approaches** - See consolidated comparison matrix
5. **Choose best approach** - Based on your specific constraints

**Preliminary recommendation:** If Agent 1 (REST APIs) is viable, build a mobile-responsive web app instead of a native mobile app. You'll get 80% of the mobile UX with 20% of the effort.

---

## Document Navigation

### Quick Read (5 minutes)
[SUMMARY.md](./SUMMARY.md) - Executive summary with key findings

### Complete Research (15 minutes)
[FINDINGS.md](./FINDINGS.md) - Full analysis including:
- Technical details
- Cost breakdown
- Pros/cons analysis
- Legal compliance
- SDK maintenance status
- Authentication flows
- React Native feasibility

### Code Deep Dive (10 minutes)
[code-example.md](./code-example.md) - Working implementation showing:
- Full React Native app
- REST API integration (proves SDKs not needed)
- Deep linking code
- iOS/Android configuration
- Mobile web alternative

---

## Sources

All findings backed by:
- ✅ Official Uber Developer documentation
- ✅ Official Lyft Developer documentation
- ✅ GitHub repository inspection (SDK status verification)
- ✅ Terms of Service review
- ✅ Code examples and proof-of-concept testing
- ✅ 30+ web searches and documentation reviews

See [FINDINGS.md](./FINDINGS.md) for complete source list with links.

---

**Agent 4 Research Complete**
**Status:** Approach evaluated and NOT recommended for price comparison use case
**Alternative:** Use Agent 1 (REST APIs) with mobile-responsive web design
