# Workflow: Batch Email Analysis

## Overview
Analyze multiple emails simultaneously to compare offers, identify trends, or process a backlog efficiently.

## Use Cases
- Compare multiple competing promotional offers
- Analyze all newsletters from a specific period
- Process email backlog after vacation
- Track promotional campaigns over time
- Identify best offers across multiple senders
- Trend analysis for pricing/rates

## Prerequisites
- Multiple saved email HTML files
- Organized folder structure for emails
- Clear categorization of email types (optional but recommended)

## Workflow Steps

### 1. Organize Email Files
**Objective**: Structure emails for efficient batch processing

**Recommended Folder Structure**:
```
data/
├── financial/
│   ├── 2026-01-10-weltsparen-offer.html
│   ├── 2026-01-09-bankrate-promo.html
│   └── 2026-01-08-savings-alert.html
├── promotional/
│   ├── 2026-01-10-retailer-sale.html
│   └── 2026-01-09-service-discount.html
├── newsletters/
│   ├── 2026-01-10-industry-news.html
│   └── 2026-01-09-weekly-digest.html
└── to-process/
    └── [unsorted emails]
```

**Naming Convention**:
```
YYYY-MM-DD-sender-subject-brief.html
```

**Example**:
```
2026-01-10-weltsparen-150-euro-bonus.html
2026-01-09-varo-savings-5pct-apy.html
```

### 2. Pre-Analysis Scan
**Objective**: Quick assessment of all emails to prioritize

**Actions**:
- List all email files in target folder(s)
- Extract subjects from each file
- Identify email types (financial, promotional, newsletter)
- Note dates to identify time-sensitive offers
- Flag urgent/high-priority emails

**Command Example**:
```bash
# List all email files with dates
ls -lt data/**/*.html

# Extract all subjects
for file in data/**/*.html; do
  echo "=== $file ==="
  grep -o '<title>[^<]*</title>' "$file" | head -1
done
```

### 2.5 Temporal Validation & Offer Reconciliation
**Objective**: Identify expired offers and reconcile multiple emails from the same sender

**CRITICAL**: This step prevents wasting time analyzing expired offers or comparing outdated information.

**Actions**:

**A. Extract and Validate Deadlines**:
```bash
# Extract deadline information from emails
for file in data/**/*.html; do
  echo "=== $file ==="
  grep -iE 'expir|deadline|until|by.*202[0-9]|valid.*through' "$file" | head -3
done
```

**B. Compare Against Current Date**:
- Current date: [Insert today's date, e.g., January 10, 2026]
- Flag any offers with deadlines before today as **EXPIRED**
- Mark offers with deadlines within 7 days as **URGENT**
- Note offers with future start dates as **UPCOMING**

**C. Group by Sender**:
```bash
# Identify emails from the same sender
for file in data/**/*.html; do
  echo "=== $file ==="
  grep -o 'From:.*@[^<]*' "$file" | head -1
done | sort
```

**D. Detect Offer Supersession**:
- For each sender with multiple emails, identify the most recent
- Check if newer emails:
  - Cancel previous offers ("This offer replaces...", "Offer cancelled")
  - Update terms ("New rates effective...", "Rate update")
  - Extend deadlines ("Deadline extended to...")
- Mark superseded offers clearly

**E. Create Validity Status Table**:

| Email File | Sender | Deadline | Status | Notes |
|------------|--------|----------|--------|-------|
| 2026-01-10-weltsparen.html | WeltSparen | Jan 31, 2026 | ✅ ACTIVE | - |
| 2025-12-15-varo-promo.html | Varo | Dec 31, 2025 | ❌ EXPIRED | Exclude from comparison |
| 2026-01-05-bank-update.html | CapitalBank | Jan 15, 2026 | ⚠️ URGENT | 5 days left |
| 2026-02-01-newtek.html | Newtek | Mar 1, 2026 | 🔜 UPCOMING | Not available yet |
| 2026-01-08-bank-old.html | CapitalBank | Jan 20, 2026 | 🔁 SUPERSEDED | Replaced by 01-05 email |

**F. Separate Emails into Processing Groups**:
- **Primary Analysis Group**: Currently active offers only
- **Reference Group**: Expired offers (for historical context)
- **Future Group**: Upcoming offers (analyze separately)
- **Superseded Group**: Exclude from analysis

**Status Meanings**:
- ✅ **ACTIVE**: Offer is currently valid, include in comparison
- ❌ **EXPIRED**: Deadline passed, exclude or mark clearly
- ⚠️ **URGENT**: Deadline within 7 days, prioritize
- 🔜 **UPCOMING**: Not yet available, analyze but note timing
- 🔁 **SUPERSEDED**: Replaced by newer email from same sender

**Example Reconciliation Note**:
```
⚠️ SENDER CONFLICT DETECTED: CapitalBank

Email 1 (Jan 5):  "4.25% APY - Rate Update"
Email 2 (Jan 8):  "4.75% APY through January"
Email 3 (Jan 10): "New offer: 5.0% APY"

→ ANALYSIS: Email 3 (most recent) is authoritative
→ ACTION: Analyze Email 3, mark Email 1 & 2 as superseded
```

### 3. Categorization
**Objective**: Group similar emails for efficient processing

**Categories**:
- **Financial Offers**: Banking, savings, investment promotions
- **Retail Promotions**: Product sales, discounts, deals
- **Service Offers**: Subscriptions, memberships, services
- **Newsletters**: Educational content, industry news
- **Transactional**: Receipts, confirmations (usually skip analysis)

**Sorting Criteria**:
- Email type
- Sender
- Date range
- Subject keywords
- Priority level

### 3.5 Create Progress Tracking Checklist
**Objective**: Track batch progress for resumable analysis

**CRITICAL**: Batch analysis can be interrupted. This checklist prevents losing track of progress.

**Create Tracking Document**: `batch-progress-[DATE].md`

**Template**:
```markdown
# Batch Analysis Progress Tracker

**Started**: [Date & Time]
**Batch Name**: [e.g., "January 2026 Financial Offers"]
**Total Emails**: [N]
**Completion Target**: [Date]

## Email Inventory

| # | Filename | Sender | Status | Priority | Notes |
|---|----------|--------|--------|----------|-------|
| 1 | 2026-01-10-weltsparen.html | WeltSparen | ✅ DONE | High | €360 total value |
| 2 | 2026-01-09-varo.html | Varo | ✅ DONE | Medium | 5% APY, flexible |
| 3 | 2026-01-08-newtek.html | Newtek | 🔄 IN PROGRESS | High | - |
| 4 | 2026-01-07-bank-promo.html | CapitalBank | ⏸️ PAUSED | Low | Needs clarification |
| 5 | 2026-01-06-offer.html | QuickBank | ❌ EXPIRED | - | Deadline passed |
| 6 | 2026-01-05-savings.html | PremierCU | ⏭️ PENDING | Medium | - |
| ... | ... | ... | ... | ... | ... |

## Progress Summary

- ✅ Completed: 2/10 (20%)
- 🔄 In Progress: 1/10 (10%)
- ⏸️ Paused/Blocked: 1/10 (10%)
- ❌ Skipped: 1/10 (10%)
- ⏭️ Pending: 5/10 (50%)

**Estimated Time Remaining**: ~4 hours (based on 30 min/email avg)

## Session Log

**Session 1** (Jan 10, 2:00-3:30 PM):
- Completed: WeltSparen, Varo
- Started: Newtek
- Next: Resume Newtek analysis

**Session 2** (Jan 10, 7:00-8:00 PM):
- [To be filled]

## Key Findings So Far

- Top offer: WeltSparen (€360 total)
- Expired offers: 1 (QuickBank)
- Need follow-up: CapitalBank (unclear terms)

## Next Steps

1. Complete Newtek analysis
2. Clarify CapitalBank offer details
3. Analyze remaining 5 pending emails
4. Create comparison matrix
5. Generate final report
```

**Status Emoji Guide**:
- ✅ **DONE**: Analysis complete, data extracted
- 🔄 **IN PROGRESS**: Currently working on this email
- ⏸️ **PAUSED**: Started but blocked/needs clarification
- ❌ **SKIPPED**: Expired, duplicate, or not relevant
- ⏭️ **PENDING**: Not yet started
- ⚠️ **URGENT**: Deadline approaching, prioritize

**How to Use**:
1. Create checklist BEFORE starting batch analysis
2. Update status after completing each email
3. Add brief notes for key findings
4. Log session times to track actual vs estimated effort
5. Use "Next Steps" to resume after interruption

**Resuming After Interruption**:
1. Open your progress tracker
2. Check "Session Log" for last email worked on
3. Check status column for 🔄 IN PROGRESS items
4. Review "Next Steps" for continuation plan
5. Update "Session Log" with new session time

**Benefits**:
- Never lose track of which emails are analyzed
- Easy to see completion percentage
- Can pause and resume without confusion
- Session logs help improve time estimates
- Prevents duplicate work
- Provides quick summary of findings

### 4. Define Analysis Goals
**Objective**: Determine what information to extract from the batch

**Common Goals**:

**A. Comparison Analysis**
- Compare similar offers (e.g., all savings account bonuses)
- Identify best deal
- Create comparison table

**B. Trend Analysis**
- Track rate changes over time
- Monitor promotional patterns
- Identify seasonal trends

**C. Comprehensive Summary**
- Full analysis of each email
- Individual reports
- Combined executive summary

**D. Filtering & Triage**
- Identify high-value offers
- Flag time-sensitive emails
- Archive low-priority items

### 5. Batch Processing Methods

**Method A: Sequential Manual Analysis**
- Process one email at a time using standard workflow
- Suitable for: 5-10 emails, detailed analysis needed

**Process**:
1. Analyze email #1 (full workflow)
2. Document findings
3. Move to email #2
4. Repeat
5. Create summary comparison

**Method B: Parallel Key Data Extraction**
- Extract key data points from all emails quickly
- Suitable for: 10+ emails, comparison focus

**Process**:
```bash
# Extract subjects
for file in data/financial/*.html; do
  grep -o '<title>[^<]*</title>' "$file"
done

# Extract all unique links
for file in data/financial/*.html; do
  echo "=== $file ==="
  grep -oE 'https?://[^\s"<>]+' "$file" | grep -v 'gmail\|google' | sort -u
done

# Search for common keywords (bonus, APY, deadline, etc.)
for file in data/financial/*.html; do
  echo "=== $file ==="
  grep -i "bonus\|APY\|deadline\|expires\|limited time" "$file" | head -5
done
```

**Method C: Automated Script (Future)**
- Python script to process all emails
- Generate structured output (JSON/CSV)
- Create comparison tables automatically

### 5.5 Data Normalization & Comparability Assessment
**Objective**: Standardize financial terminology and identify comparable offers

**CRITICAL**: Raw data extraction isn't enough - you must normalize for accurate comparison.

**A. Financial Terminology Standardization**

**Common Issues**:
- "Up to 5% APY" vs "5% APY guaranteed" - both appear as "5%" but very different
- "4.5% compounded daily" vs "4.5% simple interest" - need conversion to APY
- "Earnings rate", "Yield", "Return" - non-standard terms needing interpretation

**Normalization Rules**:

| Raw Term | Normalized To | Notes |
|----------|---------------|-------|
| "Earnings rate" | APY | Standard savings terminology |
| "Yield" | APY | For deposits/savings |
| "Return" | APY | For investment products |
| "Interest rate" | APY | If compounding stated, otherwise APR |
| "Up to X%" | "UP TO X%" | Flag as variable, use cautiously |
| "X% compounded daily" | Calculate APY | Use: APY = (1 + r/n)^n - 1 |
| "X% simple interest" | X% (not APY) | Mark as non-compounding |

**APY Conversion Examples**:
```
4.5% compounded daily:
APY = (1 + 0.045/365)^365 - 1 = 4.60%

4.5% simple interest (1 year):
No conversion needed = 4.5% (but note: not compounding)
```

**Variable Rate Handling**:
```markdown
| Offer | Rate | Notes |
|-------|------|-------|
| Bank A | 4.5% APY | ✅ Fixed rate |
| Bank B | UP TO 5.0% APY | ⚠️ Variable - may decrease |
| Bank C | 3.0-4.5% APY tiered | 📊 Depends on balance |
```

**B. Currency Normalization**

**Problem**: Mixing USD, EUR, GBP in same comparison table

**Solutions**:

**Option 1 - Separate Tables** (RECOMMENDED):
```markdown
## USD Offers
| Offer | APY | Bonus | Total Value |
|-------|-----|-------|-------------|
| Bank A | 4.5% | $500 | $950 |
| Bank B | 5.0% | $0 | $500 |

## EUR Offers
| Offer | APY | Bonus | Total Value |
|-------|-----|-------|-------------|
| Bank C | 4.2% | €150 | €360 |
| Bank D | 3.8% | €200 | €390 |
```

**Option 2 - Convert with Explicit Rate**:
```markdown
**Currency Conversion Rate**: 1 EUR = 1.10 USD (as of Jan 10, 2026)

| Offer | Currency | APY | Bonus (USD) | Total Value (USD) |
|-------|----------|-----|-------------|-------------------|
| Bank A | USD | 4.5% | $500 | $950 |
| Bank C | EUR | 4.2% | $165 (€150) | $396 (€360) |
```

**Rules**:
- NEVER mix currencies without explicit conversion
- Always state conversion rate and date
- Prefer separate tables unless comparing is essential
- Note exchange rate risk for foreign currency offers

**C. Offer Type Classification**

**Problem**: Comparing apples to oranges (cash vs points vs crypto)

**Classification**:
1. **Cash Bonus** - Direct money payment
2. **Interest Rate** - APY/APR on deposits
3. **Cryptocurrency** - Bitcoin, ETH, etc. rewards
4. **Gift Cards** - Amazon, retailer gift cards
5. **Points/Miles** - Credit card rewards
6. **Hybrid** - Combination (e.g., cash back + interest)

**Comparability Matrix**:

| Type A | Type B | Comparable? | Notes |
|--------|--------|-------------|-------|
| Cash | Cash | ✅ YES | Direct comparison |
| Cash | Interest Rate | ✅ YES | Calculate total value |
| Cash | Cryptocurrency | ⚠️ MAYBE | Crypto has volatility risk |
| Cash | Gift Cards | ⚠️ MAYBE | Gift cards worth ~90% cash |
| Cash | Points/Miles | ❌ NO | Points value varies by redemption |
| Interest | Interest | ✅ YES | Normalize to APY first |
| Crypto | Crypto | ⚠️ MAYBE | Market volatility makes comparison difficult |

**Handling Non-Comparable Offers**:
```markdown
## Primary Comparison (Cash + Interest)
[Table with directly comparable offers]

## Alternative Rewards (Separate Analysis)

### Cryptocurrency Offers
- Offer X: 0.01 BTC bonus (~$450 at current rate, high volatility)

### Points/Miles Offers
- Offer Y: 50,000 miles (value: $500-$750 depending on redemption)

### Gift Card Offers
- Offer Z: $100 Amazon gift card (cash equivalent: ~$90-$95)
```

**D. Data Quality Flags**

**Mark each extracted data point**:

| Offer | APY | Quality | Bonus | Quality | Notes |
|-------|-----|---------|-------|---------|-------|
| Bank A | 4.5% | ✅ Confirmed | $500 | ✅ Confirmed | Clear terms |
| Bank B | UP TO 5.0% | ⚠️ Variable | $0 | ✅ Confirmed | Rate may change |
| Bank C | 4.2% | ✅ Confirmed | €150 | ⚠️ Conditional | Requires min balance |
| Bank D | TBD | ❌ Missing | $100 | ⚠️ Unclear timing | Re-analyze needed |

**Quality Levels**:
- ✅ **Confirmed**: Clear, unambiguous data
- ⚠️ **Conditional**: Data exists but has conditions/caveats
- ⚠️ **Variable**: Rate/amount can change
- ❌ **Missing**: Data not found, needs re-extraction
- ⚠️ **Unclear**: Ambiguous phrasing, needs interpretation

**E. Normalization Checklist**

Before creating final comparison:
- [ ] All interest rates converted to APY
- [ ] Variable rates flagged with "UP TO"
- [ ] Currencies separated or converted with stated rate
- [ ] Offer types classified
- [ ] Non-comparable offers in separate sections
- [ ] Data quality marked for each metric
- [ ] Conditional requirements noted
- [ ] Calculation methodology documented

### 6. Create Comparison Framework
**Objective**: Structure for comparing multiple emails

**Comparison Table Template**:

```markdown
| Email/Offer | Sender | Date | Key Offer | Amount/Rate | Min. Req. | Deadline | Value Score |
|-------------|--------|------|-----------|-------------|-----------|----------|-------------|
| WeltSparen  | Focus  | 1/10 | €150 bonus| 4.2% APY    | €5,000/6mo| TBD      | ⭐⭐⭐⭐     |
| Varo Bank   | Varo   | 1/9  | No bonus  | 5.00% APY   | None      | None     | ⭐⭐⭐⭐⭐   |
| Newtek      | Newtek | 1/8  | $100 bonus| 4.35% APY   | $10,000   | 1/31     | ⭐⭐⭐       |
```

**Scoring Criteria** (customize based on needs):
- Interest rate / discount percentage
- Bonus amount
- Requirements (lower = better)
- Deadline flexibility
- Overall value proposition

### 7. Extract Common Data Points
**Objective**: Gather consistent data across all emails

**Standard Data Points**:

**For Financial Emails**:
- Sender/Institution
- Email date
- Offer type (bonus, rate, promotion)
- Interest rate (APY/APR)
- Bonus amount
- Minimum deposit/balance
- Term length
- Deadline
- Restrictions
- Promotional code

**For Promotional Emails**:
- Sender/Retailer
- Email date
- Product/service
- Discount amount/percentage
- Promo code
- Minimum purchase
- Exclusions
- Valid dates
- Shipping terms

**For Newsletters**:
- Publisher
- Email date
- Main topics
- Key statistics
- Featured articles
- Recommended resources

### 8. Batch Web Research
**Objective**: Verify and contextualize multiple offers

**Strategies**:

**A. Parallel Link Fetching**
- Extract primary links from all emails
- Fetch all accessible links simultaneously
- Document which links are blocked

**B. Comparison Research**
- Search for "best [category] offers 2026"
- Find third-party comparisons
- Identify market leaders

**C. Sender Verification**
- Research sender legitimacy for unfamiliar sources
- Check company reviews/reputation
- Verify offer authenticity

### 9. Generate Batch Report
**Objective**: Create comprehensive summary of all analyzed emails

**Report Structure**:

```markdown
# Batch Email Analysis Report
Generated: [Date & Time]
Period: [Date Range]
Total Emails Analyzed: [Number]

## Executive Summary
[2-3 paragraph overview of findings]

## Top Recommendations
1. [Best offer/email with reasoning]
2. [Second best with reasoning]
3. [Third best with reasoning]

## Urgent Action Items
| Email | Deadline | Action Required | Priority |
|-------|----------|----------------|----------|
| [Subject] | [Date] | [Action] | 🔴 High |
| [Subject] | [Date] | [Action] | 🟡 Medium |

## Category Breakdowns

### Financial Offers ([Count])
[Comparison table]
**Winner**: [Best offer with details]

### Promotional Offers ([Count])
[Comparison table]
**Best Deal**: [Top promotion with details]

### Newsletters ([Count])
[Summary of key insights]

## Detailed Analyses
[Individual email analysis sections]

## Sources & References
[All sources from all emails]

## Appendix
- Emails Excluded: [List with reasons]
- Incomplete Analyses: [List with issues]
- Follow-up Required: [List]
```

### 10. Prioritization and Action Plan
**Objective**: Create actionable next steps from batch analysis

**Priority Matrix**:

```
High Value + Urgent        | High Value + Not Urgent
---------------------------|---------------------------
⚡ ACT NOW                 | 📅 SCHEDULE
[List emails]              | [List emails]
                           |
---------------------------|---------------------------
Low Value + Urgent         | Low Value + Not Urgent
⏰ QUICK DECISION          | 🗑️ ARCHIVE/IGNORE
[List emails]              | [List emails]
```

**Action Plan Template**:
```markdown
## Immediate Actions (Next 24 Hours)
- [ ] [Email subject] - [Specific action] - Deadline: [Date]
- [ ] [Email subject] - [Specific action] - Deadline: [Date]

## Short-term Actions (This Week)
- [ ] [Email subject] - [Specific action]
- [ ] [Email subject] - [Specific action]

## Long-term Monitoring
- [ ] [Email subject] - Review by [Date]
- [ ] [Email subject] - Compare alternatives by [Date]

## Archive (No Action Needed)
- [Email subject] - Reason: [Why no action needed]
```

## Batch Processing Tips

### Efficiency Strategies
1. **Process similar types together**: All financial, then all promotional
2. **Create templates**: Reuse search patterns for similar emails
3. **Extract data first, analyze later**: Get all data points, then compare
4. **Use scripting for repetitive tasks**: Automate link extraction
5. **Set time limits**: Allocate specific time per email to avoid analysis paralysis

### Quality Control
- [ ] Verify all dates extracted correctly
- [ ] Double-check numerical data (amounts, percentages)
- [ ] Ensure consistent formatting in comparison tables
- [ ] Validate all links before including in report
- [ ] Cross-reference similar offers

### Common Pitfalls
- **Analysis paralysis**: Too much detail, not enough decision
- **Inconsistent data**: Different metrics for similar offers
- **Missed deadlines**: Not flagging time-sensitive items early
- **Lost context**: Forgetting original email purpose
- **Over-complication**: Creating comparisons for non-comparable items

## Automation Opportunities

### Future Scripts (Python)
1. **batch_extract.py**: Extract key data from all emails
2. **compare_offers.py**: Auto-generate comparison tables
3. **deadline_tracker.py**: Flag time-sensitive emails
4. **report_generator.py**: Create formatted batch reports
5. **email_classifier.py**: Auto-categorize emails by type

### Example Script Structure
```python
# Future: batch_email_analyzer.py

def analyze_batch(email_folder, email_type):
    emails = load_emails(email_folder)
    results = []

    for email in emails:
        # Extract metadata
        metadata = extract_metadata(email)

        # Extract key data based on type
        if email_type == 'financial':
            data = extract_financial_data(email)
        elif email_type == 'promotional':
            data = extract_promotional_data(email)

        results.append({
            'metadata': metadata,
            'data': data
        })

    # Generate comparison report
    report = generate_comparison_report(results)
    return report
```

## Output Formats

### Option 1: Single Comprehensive Report
- One markdown file with all analyses
- Best for: Small batches (5-15 emails)

### Option 2: Individual + Summary
- Individual analysis files per email
- One summary comparison file
- Best for: Larger batches (15+ emails)

### Option 3: Structured Data Export
- CSV/JSON with extracted data
- Separate narrative report
- Best for: Data analysis, tracking over time

### Option 4: Dashboard (Future)
- Interactive comparison view
- Sortable tables
- Filter by category/priority
- Best for: Ongoing monitoring

## Success Criteria

Successful batch analysis includes:
- ✅ All emails processed (or documented why skipped)
- ✅ Consistent data extraction across similar emails
- ✅ Clear comparison when applicable
- ✅ Prioritized action items
- ✅ Time-sensitive items flagged prominently
- ✅ All sources cited
- ✅ Actionable recommendations
- ✅ Easy-to-scan summary format

## Related Workflows
- [analyze-email-from-html.md](analyze-email-from-html.md) - Single email analysis
- [send-email-summary.md](send-email-summary.md) - Deliver results
- [compare-financial-offers.md](compare-financial-offers.md) - Specialized comparison (future)
