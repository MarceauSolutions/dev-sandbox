# IP Protection Strategy: CraveSmart

## The Risk: Partnership Discussions Can Leak Innovation

When approaching Flo, Clue, or other established period tracking apps for partnership, there's a real risk:

**Scenario**: You pitch "cycle-aware food craving predictions" to Clue. They say "interesting, we'll get back to you." Six months later, Clue launches the feature themselves without you.

This is not paranoia - it's a documented pattern in tech:
- Snapchat pitched to Facebook → Facebook copied Stories
- Snap Maps → Instagram copied exact feature
- Many startups have had features absorbed by larger partners

---

## Protection Layers

### Layer 1: Prove Prior Art (Timestamp Everything)

**Actions to take BEFORE any partnership discussions:**

1. **Git commits with dated evidence**
   ```bash
   # All code, designs, and documentation in version control
   git log --oneline --since="2026-01-01" projects/decide-for-her/
   # Shows timestamped development history
   ```

2. **Public README with `mcp-name` line**
   - Already done for MCP projects
   - Creates public timestamped claim

3. **Blog post / Twitter thread announcing concept**
   - Public timestamped record of innovation
   - Even a draft saved as email to yourself creates evidence

4. **File with Copyright Office (optional, $45)**
   - Register software copyright for code
   - Creates federal timestamp
   - Useful for litigation if needed

### Layer 2: Patents (Expensive but Strongest)

**Provisional Patent Application ($1,500-3,000 with lawyer)**

What can be patented:
- The specific METHOD of predicting food cravings from cycle phase
- The ALGORITHM combining time-of-day, weather, cycle, and order history
- The USER INTERFACE for presenting predictions to partner

What cannot be patented:
- The idea of "cycle affects cravings" (scientific fact)
- General concept of food recommendation apps
- Integrating with Apple Health (standard API)

**Recommendation**: File provisional patent BEFORE partnership discussions. This gives 12-month window to file full patent, and creates dated legal record.

### Layer 3: Trade Secrets (Free but Risky)

**Protect your secret sauce:**

| Reveal | Don't Reveal |
|--------|--------------|
| "We predict cravings based on cycle phase" | Specific algorithm weights |
| "We integrate with period tracking apps" | Exact data processing pipeline |
| "We use ML for predictions" | Model architecture, training data |
| "Users see partner preferences" | Engagement mechanics, retention hooks |

**NDA Strategy** (see below for template)

### Layer 4: Speed to Market (Best Protection)

**The real moat:**
- Flo/Clue have 70M+ users but are SLOW
- They have regulatory, legal, and PR concerns
- A feature like this would take them 12-18 months to launch
- You can launch in 2-3 months

**First-mover advantages:**
- Brand recognition ("the craving app")
- User data moat (preferences accumulate)
- App store reviews and SEO
- Integration partnerships with restaurants

---

## Partnership Discussion Protocol

### Phase 1: Initial Contact (Reveal Minimum)

**DO say:**
- "We're building a food craving prediction tool"
- "We'd like to integrate with cycle tracking data"
- "We have a working prototype"
- "We see mutual benefit in partnership"

**DON'T say:**
- Specific algorithm details
- Unique UX innovations
- Your full feature roadmap
- Pricing strategy or business model details

### Phase 2: NDA Before Deep Dive

**BEFORE showing:**
- Detailed product demos
- Technical architecture
- Business model
- User research findings

**REQUIRE:**
- Mutual NDA signed
- Specific scope of discussions defined
- Time limit on confidentiality (2-3 years)

### Phase 3: Partnership Agreement Terms

If they want to partner, protect yourself:

| Protection | Purpose |
|------------|---------|
| Non-compete clause | They can't launch competing feature during partnership |
| Exclusivity window | 12-24 months before they can build internally |
| Revenue share | You get % of any feature they build based on your ideas |
| IP ownership | You retain all IP, they license for specific use |
| Termination rights | You can exit if they breach terms |

---

## NDA Template for Partnership Discussions

```
MUTUAL NON-DISCLOSURE AGREEMENT

This Agreement is entered into as of [DATE] between:

[YOUR COMPANY/NAME] ("Disclosing Party")
and
[PARTNER COMPANY] ("Receiving Party")

1. CONFIDENTIAL INFORMATION
"Confidential Information" includes:
- Product specifications, algorithms, and technical architecture
- Business plans, pricing, and financial projections
- User research, market analysis, and competitive intelligence
- Any information marked "Confidential" or disclosed in confidence

2. OBLIGATIONS
Receiving Party agrees to:
- Not disclose Confidential Information to third parties
- Not use Confidential Information except for evaluating partnership
- Not develop competing products based on Confidential Information
- Return or destroy Confidential Information upon request

3. EXCLUSIONS
This Agreement does not apply to information that:
- Was publicly known before disclosure
- Becomes publicly known through no fault of Receiving Party
- Was independently developed by Receiving Party
- Was lawfully obtained from a third party

4. TERM
This Agreement remains in effect for [3] years from the date of disclosure.

5. NON-COMPETE (OPTIONAL BUT RECOMMENDED)
During the term of this Agreement and for [12] months thereafter,
Receiving Party agrees not to develop, launch, or acquire any
product that directly competes with the disclosed product concept.

6. REMEDIES
Receiving Party acknowledges that breach may cause irreparable harm
and agrees that Disclosing Party may seek injunctive relief.

AGREED:

[Your Signature]                    [Partner Signature]
[Your Name]                         [Partner Name]
[Date]                              [Date]
```

---

## What Can They Actually Steal?

### High Risk (Protect Aggressively)
- Specific prediction algorithm
- Novel UX patterns
- Engagement mechanics
- Data architecture decisions

### Medium Risk (NDA Sufficient)
- General product concept
- Partnership integration approach
- Target market positioning

### Low Risk (No Protection Needed)
- The idea that cycles affect cravings (public science)
- Food recommendation as a category (commoditized)
- Mobile app development (standard practice)

---

## Realistic Assessment

**Why Flo/Clue might NOT copy you:**

1. **Privacy backlash risk** - They just settled a $56M lawsuit. Adding food tracking could trigger more scrutiny.

2. **Mission creep** - They're period trackers, not food apps. Expanding scope confuses their brand.

3. **Engineering prioritization** - They have roadmaps 18+ months out. New features are slow.

4. **Partnership is easier** - Revenue share with you is simpler than building in-house.

5. **Your expertise** - You understand food/restaurants. They understand menstrual health. Different domains.

**Why they MIGHT copy:**

1. **Feature is obvious once shown** - "Cycle + cravings" is easy to conceptualize.

2. **They have the data** - They already have cycle data; adding food is incremental.

3. **No switching cost** - Users wouldn't need your app if Clue has the feature built-in.

4. **Aggregator advantage** - Built-in feature beats third-party integration.

---

## Recommended Protection Strategy

### Timeline

| Timing | Action |
|--------|--------|
| Before partnership outreach | File provisional patent ($2K) |
| Before partnership outreach | Create public timestamp (blog/tweet) |
| Before partnership outreach | Ensure all code is in git with dates |
| At first contact | Reveal concept only, no details |
| Before demo/deep dive | Require mutual NDA |
| During negotiation | Demand non-compete and exclusivity |
| At partnership signing | IP ownership and revenue share terms |

### Budget for IP Protection

| Protection | Cost | Value |
|------------|------|-------|
| Git history (free) | $0 | Evidence of development |
| Blog post / tweet | $0 | Public timestamp |
| Copyright registration | $45 | Federal timestamp |
| Provisional patent | $1,500-3,000 | 12-month protection window |
| Full patent | $10,000-15,000 | 20-year protection |
| Lawyer review of NDA | $500-1,000 | Professional protection |

**Minimum recommended**: $2,000-4,000 (provisional patent + copyright + lawyer)

---

## Alternative: Build First, Partner Later

The safest strategy might be:

1. **Launch MVP without partnership** (Apple Health bridge only)
2. **Get 10,000+ users** (prove the concept works)
3. **THEN approach Clue/Flo** (from position of strength)

Why this works:
- You have a live product (harder to claim they invented it)
- You have user data (valuable to partners)
- You're a real business (not just an idea to steal)
- Negotiating leverage is higher

**Risk**: Slower time to market, but stronger position.

---

## Summary

| Risk | Mitigation |
|------|------------|
| Partner steals idea | Provisional patent + NDA + public timestamp |
| Partner launches competing feature | Non-compete clause in agreement |
| Partner claims they invented it | Git history + copyright registration |
| Partner uses your research | Limit disclosure until NDA signed |
| Legal costs if dispute | Factor $5-10K litigation reserve |

**Bottom Line**: File provisional patent ($2K) before any partnership discussions. This creates a 12-month legal shield and shows you're serious about IP protection.

---

*Strategy Document: January 18, 2026*
*CraveSmart IP Protection*
