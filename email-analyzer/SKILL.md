# Email Analyzer Skill

Analyze promotional, financial, and newsletter emails to extract key information, compare offers, and make informed decisions.

## What This Skill Does

This skill helps you:
- **Analyze single emails** from saved HTML files
- **Batch process multiple emails** for comparison
- **Extract key details** like offers, deadlines, terms, and requirements
- **Research and verify** information through web sources
- **Compare financial offers** to find the best deal
- **Send formatted summaries** via email

## When to Use This Skill

Use this skill when you need to:
- Understand a promotional or financial offer
- Compare multiple similar offers (e.g., savings accounts, credit cards)
- Process a backlog of promotional emails
- Verify legitimacy of an offer
- Extract time-sensitive information and deadlines
- Get recommendations on which offer to choose

## Example Prompts

### Single Email Analysis
- "Analyze the email in .tmp/[filename].html"
- "What's the offer in this email?"
- "Is this email legit?"
- "Find the deadline in this promotional email"
- "Extract the key terms from this banking offer"

### Batch Analysis
- "Analyze all emails in email-analyzer/data/financial/"
- "Compare the 3 savings account offers in data/financial/"
- "Process my email backlog in data/to-process/"
- "Which of these offers is the best deal?"

### Comparison & Decision
- "Compare these bank offers and recommend the best one"
- "Calculate total value for each offer at $10,000 investment"
- "Which offer has the fewest restrictions?"
- "Show me a comparison table of these emails"

### Output & Delivery
- "Send me the analysis summary via email"
- "Create a formatted report of this analysis"
- "Generate a comparison table for these offers"

## How It Works

### 1. Single Email Analysis
**Input**: Saved email HTML file
**Process**:
- Extracts metadata (subject, sender, date)
- Identifies and extracts web links
- Fetches content from primary promotional pages
- Researches company and offer through web search
- Compares to market alternatives
- Generates comprehensive summary with sources

**Output**: Detailed analysis with:
- Email context
- Key offer details
- Terms & conditions
- Market comparison
- Action items & deadlines
- Bottom line recommendation
- Cited sources

### 2. Batch Email Analysis
**Input**: Multiple email HTML files in a folder
**Process**:
- Scans all emails for basic info
- Categorizes by type (financial, promotional, newsletter)
- Extracts comparable data points
- Creates comparison matrices
- Identifies time-sensitive items
- Generates priority list

**Output**: Batch report with:
- Executive summary
- Top recommendations
- Urgent action items
- Category comparisons
- Individual analyses
- Combined sources

### 3. Financial Offer Comparison
**Input**: 2+ financial offer emails
**Process**:
- Extracts comparable metrics (APY, bonuses, terms)
- Normalizes values for fair comparison
- Calculates total value scenarios
- Assesses risk factors
- Applies decision criteria

**Output**: Comparison analysis with:
- Side-by-side comparison table
- Total value calculations
- Risk assessment
- Clear recommendation
- Runner-up option
- Action steps

## Workflows Available

The skill includes four comprehensive workflows:

1. **[analyze-email-from-html.md](workflows/analyze-email-from-html.md)**
   - Detailed process for single email analysis
   - Web research integration
   - Source attribution

2. **[batch-email-analysis.md](workflows/batch-email-analysis.md)**
   - Multiple email processing
   - Comparison framework
   - Priority matrix

3. **[compare-financial-offers.md](workflows/compare-financial-offers.md)**
   - Financial offer comparison
   - Value calculations
   - Decision trees

4. **[send-email-summary.md](workflows/send-email-summary.md)**
   - Format for email delivery
   - Multiple delivery methods
   - Security considerations

## Supported Email Types

### Financial/Banking Emails
- Savings account bonuses
- High-yield account promotions
- Credit card offers
- Investment platform bonuses
- Mortgage/loan rates

**Extracts**: APY/APR, bonus amounts, minimum requirements, term lengths, deadlines

### Promotional/Marketing Emails
- Product sales and discounts
- Service promotions
- Membership offers
- Limited-time deals

**Extracts**: Discount amounts, promo codes, expiration dates, minimum purchase, exclusions

### Newsletter/Content Emails
- Industry news
- Educational content
- Curated resources
- Event announcements

**Extracts**: Main topics, key insights, featured articles, recommendations

## Setup Requirements

### One-Time Setup
1. Create folder structure:
   ```bash
   mkdir -p email-analyzer/data/{financial,promotional,newsletters,to-process}
   ```

2. Save emails as HTML:
   - **Gmail**: Open email → ⋮ → Download message
   - **Outlook**: File → Save As → HTML format

3. Organize in appropriate folders

### File Naming Convention (Recommended)
```
YYYY-MM-DD-sender-brief-description.html
```

Examples:
- `2026-01-10-chase-500-bonus.html`
- `2026-01-09-amazon-sale.html`

## What You'll Get

### Analysis Quality
- ✅ Comprehensive offer details
- ✅ Verified through web research
- ✅ Market context and comparisons
- ✅ Clear recommendations
- ✅ All sources cited
- ✅ Time-sensitive items flagged

### Time Savings
- **Single email**: 3-5 minutes vs 30+ minutes manual research
- **Batch (10 emails)**: 20 minutes vs 3+ hours manual work
- **Comparison**: 10 minutes vs 1+ hour spreadsheet work

### Decision Support
- Side-by-side comparisons
- Total value calculations
- Risk assessments
- Scenario analysis
- Clear next steps

## Limitations & Future Enhancements

### Current Limitations
- Requires manual email saving as HTML
- Large files (4-5MB) need special handling
- Image-heavy emails may be harder to parse
- Some domains block automated web fetching

### Planned Enhancements
- Python automation scripts for batch processing
- Direct email API integration (Gmail, Outlook)
- Automated classification and categorization
- Spam/phishing detection
- Price tracking over time
- Alert system for high-value offers

## Tips for Best Results

### Getting Better Analysis
1. **Be specific**: "Compare these 3 savings offers" vs "Look at emails"
2. **Mention deadlines**: "This expires tomorrow, prioritize it"
3. **State your goal**: "I want highest return" vs "I need flexibility"
4. **Ask follow-ups**: "Is this legit?" "How does this compare?"

### Saving Time
1. **Batch similar emails**: Process all bank offers together
2. **Use organized folders**: Easier to reference specific sets
3. **Name files clearly**: `2026-01-10-bank-offer.html`
4. **Archive after analysis**: Move to `data/processed/`

### Improving Decisions
1. **Track over time**: Keep analyses to spot trends
2. **Note what you choose**: Learn from past decisions
3. **Set criteria**: Define what matters most to you
4. **Review sources**: Verify key claims yourself

## Related Documentation

- [README.md](README.md) - Full project overview
- [QUICK-START.md](QUICK-START.md) - Common scenarios and examples
- [CHANGELOG.md](CHANGELOG.md) - Version history

## Contact & Support

For issues or questions about this skill:
- Check workflow documentation in `workflows/` folder
- Review QUICK-START.md for examples
- Ask Claude for help with specific use cases

---

**Version**: 1.0.0
**Last Updated**: 2026-01-10
**Status**: Active - Workflows operational, automation scripts in development
