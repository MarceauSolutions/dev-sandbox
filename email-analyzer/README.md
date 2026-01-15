# Email Analyzer

Comprehensive email analysis tool for extracting key information from saved email HTML files and generating detailed summaries with web research.

## Purpose

Analyze promotional, financial, and newsletter emails to extract:
- Key offers and promotions
- Financial details (interest rates, bonuses, terms)
- Important deadlines and requirements
- Relevant context through web research
- Actionable insights and recommendations

## Project Structure

```
email-analyzer/
├── README.md                             # This file
├── CHANGELOG.md                          # Version history
├── .gitignore                            # Excludes sensitive email files
├── workflows/
│   ├── analyze-email-from-html.md       # Analyze single email from HTML file
│   ├── batch-email-analysis.md          # Process multiple emails at once
│   ├── send-email-summary.md            # Email the analysis results
│   └── compare-financial-offers.md      # Compare multiple financial offers
├── src/                                  # Future: Python scripts for automation
└── data/                                 # Email files organized by type
    ├── financial/                        # Banking, investment, savings offers
    ├── promotional/                      # Retail, service promotions
    ├── newsletters/                      # Industry news, digests
    └── to-process/                       # Unsorted emails
```

## Quick Start

### Analyzing a Single Email

1. **Save the email as HTML**
   - Gmail: Open email → Three dots → Download message
   - Outlook: File → Save As → HTML format

2. **Place in .tmp folder or data/ directory**

3. **Follow the workflow**: [analyze-email-from-html.md](workflows/analyze-email-from-html.md)

4. **Key steps**:
   - Extract email metadata (subject, sender, date)
   - Identify and extract web links
   - Fetch content from primary links
   - Research context via web search
   - Generate comprehensive summary
   - Cite all sources

### Analyzing Multiple Emails (Batch)

1. **Save multiple emails as HTML files**

2. **Organize in data/ folder by type**:
   ```
   data/financial/2026-01-10-bank-offer.html
   data/promotional/2026-01-09-sale.html
   ```

3. **Follow the batch workflow**: [batch-email-analysis.md](workflows/batch-email-analysis.md)

4. **Key steps**:
   - Pre-scan all emails
   - Categorize by type
   - Extract comparable data
   - Generate comparison tables
   - Create unified report

### Sending Analysis Results

1. **Complete your email analysis**

2. **Follow the send workflow**: [send-email-summary.md](workflows/send-email-summary.md)

3. **Key steps**:
   - Format for email delivery
   - Create clear subject line
   - Structure with executive summary
   - Send via your preferred method

### Comparing Financial Offers

1. **Analyze 2+ financial emails**

2. **Follow the comparison workflow**: [compare-financial-offers.md](workflows/compare-financial-offers.md)

3. **Key steps**:
   - Define your criteria
   - Extract comparable metrics
   - Calculate total values
   - Create comparison matrix
   - Make recommendation

## Supported Email Types

### Financial/Banking Emails
- Interest rate promotions
- Bonus/incentive offers
- Investment opportunities
- Account updates with offers

### Promotional/Marketing Emails
- Product launches
- Discount offers
- Limited-time deals
- Membership promotions

### Newsletter/Content Emails
- Industry news
- Educational content
- Curated resources
- Event announcements

## Output Format

Generated analyses include:

1. **Email Subject & Context**
2. **Key Offer/Content Details**
3. **Important Terms & Conditions**
4. **Context & Background**
5. **Action Items & Deadlines**
6. **Bottom Line Summary**
7. **Cited Sources**

## Example Use Cases

- **"Should I take this offer?"** - Get full terms, compare to alternatives
- **"What's the deadline?"** - Extract time-sensitive information
- **"Is this legitimate?"** - Verify through web research
- **"What are the requirements?"** - Complete eligibility details
- **"How does this compare?"** - Market context and alternatives

## Common William Prompts

| You Say | Claude Does | Workflow Used |
|---------|-------------|---------------|
| "Analyze this email in .tmp" | Full single email analysis | analyze-email-from-html.md |
| "Analyze all emails in data/financial/" | Batch process multiple emails | batch-email-analysis.md |
| "Compare these savings offers" | Create comparison matrix | compare-financial-offers.md |
| "Send me the analysis" | Format and send summary | send-email-summary.md |
| "What's the offer?" | Extract key promotional details | analyze-email-from-html.md |
| "Find the deadline" | Focus on time-sensitive info | analyze-email-from-html.md |
| "Is this legit?" | Verify sender and research offer | analyze-email-from-html.md |
| "Which offer is better?" | Compare and recommend | compare-financial-offers.md |
| "Process my email backlog" | Batch analysis with priorities | batch-email-analysis.md |

## Technical Notes

### Handling Large Email Files
- Email HTML files can be 4-5MB (scripts, styles, tracking)
- Use Grep instead of Read for files >256KB
- Focus on content areas, ignore embedded code

### Link Extraction
- Filter out infrastructure (Gmail, Google, social icons)
- Identify primary CTA links
- Extract promotional/landing page URLs

### Web Research
- Use WebFetch for accessible links
- Fall back to WebSearch for blocked domains
- Verify information across multiple sources

## Future Enhancements

### Planned Features
- [ ] Python script for automated HTML parsing
- [ ] Email classification (promotional, transactional, newsletter)
- [ ] Spam/phishing detection indicators
- [ ] Batch email analysis
- [ ] Email comparison tool (e.g., compare competing offers)
- [ ] Integration with email APIs (Gmail, Outlook)
- [ ] Structured JSON output option
- [ ] Database for tracking analyzed emails

### Potential Automation
- Auto-extract common patterns (promo codes, expiration dates)
- Template-based analysis for common senders
- Alert system for high-value offers
- Price/rate tracking over time

## Related Documentation

- [Workflow: Analyze Email from HTML](workflows/analyze-email-from-html.md) - Detailed step-by-step process
- Main CLAUDE.md - DOE architecture and operating principles
- docs/prompting-guide.md - How to request email analysis

## Version History

- **v1.0.0** (2026-01-10) - Initial workflow documentation
  - Complete email analysis workflow
  - Support for financial, promotional, and newsletter emails
  - Web research integration
  - Source attribution system

---

**Status**: Active Development
**Owner**: William Marceau Jr.
**Last Updated**: 2026-01-10
