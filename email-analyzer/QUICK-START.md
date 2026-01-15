# Email Analyzer - Quick Start Guide

## 30-Second Overview

Email Analyzer helps you extract key information from promotional, financial, and newsletter emails, then summarize and compare them to make better decisions.

## The Basics

### What Can It Do?

1. **Analyze one email** - Extract offers, deadlines, terms
2. **Analyze many emails** - Batch process and compare
3. **Send summaries** - Email yourself the results
4. **Compare offers** - Find the best financial deal

### What Do You Need?

- Saved email HTML files (from Gmail, Outlook, etc.)
- Claude (that's me!)
- The workflows in this project

## Common Scenarios

### Scenario 1: "I got a promotional email. Is it a good deal?"

**What to say**: "Analyze this email in .tmp/[filename]"

**What happens**:
1. Claude extracts the offer details
2. Researches the company and offer online
3. Compares to market alternatives
4. Gives you a summary with recommendation

**Workflow**: [analyze-email-from-html.md](workflows/analyze-email-from-html.md)

**Time**: 3-5 minutes

---

### Scenario 2: "I have 3 bank offers. Which is best?"

**What to say**: "Compare the savings offers in data/financial/"

**What happens**:
1. Claude analyzes all 3 emails
2. Extracts rates, bonuses, requirements
3. Calculates total value for each
4. Creates comparison table
5. Recommends the best one for you

**Workflow**: [compare-financial-offers.md](workflows/compare-financial-offers.md)

**Time**: 10-15 minutes

---

### Scenario 3: "I was on vacation. Now I have 20 promotional emails."

**What to say**: "Process all emails in data/to-process/"

**What happens**:
1. Claude scans all 20 emails
2. Categorizes them (financial, promotional, newsletter)
3. Flags time-sensitive items
4. Creates priority list
5. Generates batch report

**Workflow**: [batch-email-analysis.md](workflows/batch-email-analysis.md)

**Time**: 20-30 minutes for 20 emails

---

### Scenario 4: "Send me the summary of that analysis"

**What to say**: "Send me the analysis via email"

**What happens**:
1. Claude formats the analysis for email
2. Creates clear subject line
3. Adds executive summary at top
4. Formats for easy mobile reading
5. You copy/paste and send to yourself

**Workflow**: [send-email-summary.md](workflows/send-email-summary.md)

**Time**: 2 minutes

---

## Setup (One-Time)

### Step 1: Create Folders
```bash
cd email-analyzer
mkdir -p data/{financial,promotional,newsletters,to-process}
```

### Step 2: Save Your First Email

**Gmail**:
1. Open the email
2. Click three dots (⋮)
3. Click "Download message"
4. Move to `email-analyzer/data/to-process/`

**Outlook**:
1. Open the email
2. File → Save As
3. Choose "HTML" format
4. Save to `email-analyzer/data/to-process/`

### Step 3: Ask Claude

Just tell me to analyze it!

---

## File Organization Tips

### Naming Convention (Recommended)
```
YYYY-MM-DD-sender-brief-subject.html
```

**Examples**:
```
2026-01-10-chase-500-bonus.html
2026-01-09-amazon-prime-day.html
2026-01-08-nerdwallet-weekly.html
```

### Folder Structure
```
data/
├── financial/          # Banks, credit cards, investments
│   ├── 2026-01-10-weltsparen-150-bonus.html
│   └── 2026-01-09-varo-5pct-apy.html
├── promotional/        # Sales, discounts, deals
│   └── 2026-01-10-retailer-sale.html
├── newsletters/        # Industry news, digests
│   └── 2026-01-10-fintech-news.html
└── to-process/         # Unsorted, needs categorization
    └── [new emails here]
```

---

## What You'll Get

### Single Email Analysis Output

```markdown
# Email Analysis Report

## Email Subject & Context
- Subject: [Email subject]
- Sender: [Who sent it]
- Date: [When received]

## Key Offer Details
- Main offer: [What they're offering]
- Value: [How much/what percentage]
- Requirements: [What you need to do]

## Terms & Conditions
- Minimum: [Required amount/action]
- Deadline: [When it expires]
- Restrictions: [Important limitations]

## Context & Background
[Industry context, company info, market comparison]

## Action Items
- [ ] [What to do]
- [ ] [By when]

## Bottom Line
[Clear recommendation]

## Sources
[All research links]
```

### Batch Analysis Output

```markdown
# Batch Email Analysis Report

## Executive Summary
[Overview of all emails analyzed]

## Top Recommendations
1. [Best offer]
2. [Second best]
3. [Third best]

## Urgent Actions
[Time-sensitive items with deadlines]

## Comparison Tables
[Side-by-side comparison of similar offers]

## Detailed Analyses
[Individual reports for each email]
```

---

## Pro Tips

### 🎯 Get Better Results

1. **Be specific**: "Compare these 3 savings offers" vs "Look at these emails"
2. **Mention deadlines**: "This expires tomorrow, prioritize it"
3. **State your goal**: "I want the highest total return" vs "I need flexibility"
4. **Ask questions**: "Is this legit?" or "How does this compare?"

### ⚡ Save Time

1. **Batch similar emails**: Process all bank offers together
2. **Use the data/ folders**: Organized inputs = faster processing
3. **Name files clearly**: Easier to reference specific emails
4. **Archive after analysis**: Move to `data/processed/` when done

### 🎓 Level Up

1. **Track over time**: Keep analyses to spot trends
2. **Build templates**: Reuse patterns for recurring senders
3. **Create checklists**: Standard criteria for common decisions
4. **Set alerts**: Note deadlines in calendar

---

## Troubleshooting

### "File too large to read"
**Problem**: Email HTML is 4-5MB
**Solution**: This is normal! Claude will use Grep instead of Read

### "Can't find the offer details"
**Problem**: Email is mostly images
**Solution**: Check the web link in the email and fetch that page

### "Links are blocked"
**Problem**: WebFetch can't access the domain
**Solution**: Claude will use WebSearch as fallback

### "Too many emails to process"
**Problem**: 50+ emails seems overwhelming
**Solution**: Start with high-priority/time-sensitive ones first

---

## Next Steps

### After Your First Analysis

1. **Review the output** - Does it answer your questions?
2. **Refine your request** - Ask follow-ups if needed
3. **Take action** - Use the recommendations
4. **Save the analysis** - For future reference

### Build Your System

1. **Regular processing**: Weekly email review habit
2. **Create shortcuts**: Common prompts you use often
3. **Track decisions**: Note which offers you took
4. **Measure results**: Did the analysis help you save/earn money?

---

## Get Help

### Within This Project

- **Detailed workflows**: See `workflows/` directory
- **Full README**: See [README.md](README.md)
- **Change history**: See [CHANGELOG.md](CHANGELOG.md)

### Ask Claude

- "How do I [specific task]?"
- "Show me an example of [workflow]"
- "What's the best way to [goal]?"

### Learn More

- Main project docs: `/dev-sandbox/docs/`
- Prompting guide: `/dev-sandbox/docs/prompting-guide.md`
- System architecture: `/dev-sandbox/CLAUDE.md`

---

## Real Example

**Your email**: "Analyze the WeltSparen email in .tmp/"

**Claude's response**:
- ✅ Extracts: €150 bonus, 4.2% APY, €5K minimum, 12-month term
- ✅ Researches: Compares to market (Varo 5% APY, Newtek 4.35% APY)
- ✅ Calculates: Total value = €360 (€210 interest + €150 bonus)
- ✅ Recommends: Good deal if you can commit €5K for 1 year
- ✅ Warns: EU only, must be new customer
- ✅ Cites: 6 sources for verification

**Time saved**: 30+ minutes of manual research

**Value added**: Confident decision with full context

---

**Ready to start?** Just save an email as HTML and tell Claude to analyze it!
