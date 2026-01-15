# Workflow: Analyze Email from HTML File

## Overview
This workflow extracts key information from saved email HTML files and generates comprehensive summaries by analyzing content and fetching relevant web links.

## Use Cases
- Analyzing promotional emails with offers and deadlines
- Extracting financial information from banking/investment emails
- Summarizing newsletter content with external links
- Reviewing marketing emails for key details and CTAs

## Input Requirements
- Path to saved email HTML file (typically from Gmail, Outlook, etc.)
- Email files are usually large (can be 4-5MB due to embedded scripts and styles)

## Workflow Steps

### 1. Initial File Assessment
**Objective**: Understand the email file structure and size

**Actions**:
- Attempt to read the email HTML file
- If file is too large (>256KB), use alternative methods:
  - Use Grep to search for specific content patterns
  - Use Bash commands to extract targeted information

**Tools**: `Read`, `Grep`, `Bash`

### 1.5 Detect Analysis Meta-Documents
**Objective**: Identify if this email is already an analysis output (not a promotional email)

**CRITICAL**: Prevent circular analysis - analyzing an analysis report instead of the original email.

**Check for indicators**:
```bash
# Check for analysis report patterns
grep -i "Email Analysis:\|Analysis Report\|SOURCES & REFERENCES" [file_path]
grep -i "Generated:\|Analysis Type:\|Confidence Level:" [file_path]
grep -i "KEY HIGHLIGHTS\|BOTTOM LINE\|QUICK SUMMARY" [file_path]
```

**Detection patterns**:
- Subject line contains "Email Analysis:" or "Analysis Report"
- Body contains "SOURCES & REFERENCES" section
- Contains phrases like "Generated:", "Analysis Type:", "Confidence Level:"
- Has structured sections like "KEY HIGHLIGHTS", "BOTTOM LINE", "QUICK SUMMARY"
- Contains markdown formatting with multiple ### headers
- Has bulleted lists of extracted data points

**Action if meta-document detected**:
1. Alert user: "⚠️ This appears to be a previously generated analysis report, not an original promotional email"
2. Offer options:
   - **Option A**: Re-analyze the ORIGINAL email (if path/reference is in the report)
     - Look for "Original Email:" field in the analysis
     - Look for file path references
   - **Option B**: Extract just the sources for further research
     - Parse the "Sources & References" section
     - Use those URLs for additional context
   - **Option C**: Skip analysis (already completed)
     - No need to analyze an analysis
     - User can directly read the existing report

**Example meta-document markers**:
```
Subject: Email Analysis: WeltSparen €150 Bonus Offer - Jan 10, 2026

Content contains:
## QUICK SUMMARY
⭐ **Bottom Line**: [recommendation]

## KEY HIGHLIGHTS
- Bullet points of extracted data

## SOURCES & REFERENCES
- [Source 1](url)
- [Source 2](url)

Generated: [Date]
Analysis Type: Financial Offer
```

**How to identify original email**:
```bash
# Look for original email reference in analysis
grep -i "Original Email:\|Source Email:\|Analyzed File:" [file_path]

# If found, use that path instead
# If not found, ask user for original email location
```

**Preventing meta-analysis**:
- Analysis reports are documentation, not source data
- Always analyze the original promotional email
- If someone forwards you an analysis summary, locate the original
- Analysis reports contain sources, not offers

### 2. Extract Email Metadata
**Objective**: Identify basic email information

**Search for**:
- Email subject line (usually in `<title>` tag)
- Sender information
- Date received
- Recipient

**Tools**: `Grep` with patterns like:
```bash
grep -o '<title>[^<]*</title>' [file_path]
```

### 2.5 Detect Forwarded/Multi-Offer Emails
**Objective**: Identify emails containing multiple promotional offers

**Check for indicators**:
- Multiple "Forwarded message" headers
- Multiple promotional links to different domains
- Multiple distinct offers with different deadlines
- Forwarding metadata (From:, Date:, Subject: in email body)

**Detection commands**:
```bash
# Check for forwarded message headers
grep -i "forwarded message" [file_path] | wc -l

# Count unique promotional domains (excluding common platforms)
grep -oE 'https?://[^/]+' [file_path] | grep -v 'gmail\|google\|facebook\|twitter\|instagram' | sort -u | wc -l

# Look for multiple bank/financial institution domains
grep -oE 'https?://[^/]+' [file_path] | grep -E 'bank|credit|financial|savings' | sort -u
```

**Action if multiple offers detected**:
1. Alert user: "⚠️ This email contains multiple forwarded offers"
2. List all offers detected:
   - Offer 1: [Bank/Company Name] - [Subject/Description] - [Deadline if visible]
   - Offer 2: [Bank/Company Name] - [Subject/Description] - [Deadline if visible]
   - Offer 3: [Bank/Company Name] - [Subject/Description] - [Deadline if visible]
3. Ask user: "Which offer would you like to analyze?"
   - **Option A**: "Analyze all separately" (creates mini-batch analysis)
   - **Option B**: "Just the newest/outermost offer" (top-level forwarded email)
   - **Option C**: "The most urgent" (soonest deadline)

**For forwarded emails - Metadata extraction adjustments**:
- Extract sender from the forwarded message body, not email headers
- Look for "From: [institution]@domain.com" in the body text
- Identify the original promotional email's subject line (not "Fwd: Fwd: ...")
- Extract the actual offer deadline from the forwarded content

**Example forwarded email structure**:
```
---------- Forwarded message ---------
From: offers@capitalbank.com
Date: Wed, Jan 8, 2026 at 10:22 AM
Subject: LIMITED TIME: $500 Bonus + 5.2% APY!
```

**Grep pattern for original sender**:
```bash
grep -A 3 "Forwarded message" [file_path] | grep "From:"
```

### 3. Extract Web Links
**Objective**: Find all relevant URLs in the email

**Actions**:
- Extract all HTTP/HTTPS links from the email
- Filter out common infrastructure links (Gmail, Google, social media icons)
- Identify the primary call-to-action links
- Focus on content-relevant URLs

**Tools**: `Grep` with regex patterns:
```bash
# Extract all links with comprehensive tracking filter
grep -oE 'https?://[^\s"<>]+' [file_path] | \
  grep -v 'gmail\|google\|facebook\|twitter\|instagram\|linkedin' | \
  grep -v 'track\|analytics\|pixel\|doubleclick\|googleadservices\|googletagmanager' | \
  grep -v '\\.png\|\\.jpg\|\\.gif\|\\.jpeg' | \
  sort -u
```

**Common filters to exclude**:
- **Email platforms**: gmail.com, google.com, outlook.com, yahoo.com
- **Social media**: facebook.com, twitter.com, instagram.com, linkedin.com (social icons)
- **Tracking domains**:
  - Pattern-based: Any URL with `track`, `analytics`, `pixel`, `stats` in domain or path
  - Specific: doubleclick, googleadservices, googletagmanager, mixpanel
- **Image files**: .png, .jpg, .gif, .jpeg (often tracking pixels)
- **Unsubscribe/settings**: unsubscribe, preferences, settings links

**To find the promotional link**:
- Look for domains matching the sender's institution
- If email is from "capitalbank.com", prioritize "capitalbank.com" links
- Promotional links usually have paths like: `/offer`, `/promo`, `/savings`, `/bonus`, `/campaign`
- Should be HTTPS and go to a real webpage, not a pixel

### 4. Identify Primary Content Links
**Objective**: Determine which links contain the main content

**Actions**:
- Look for unique, non-Google domains in the email
- Identify the primary landing page or promotional link
- Extract any special offer pages or campaign URLs

**Pattern recognition**:
- Links appearing multiple times are likely important CTAs
- Links in `<a href>` tags near the main content area
- Links that aren't unsubscribe/settings/social media

### 5. Fetch Web Content
**Objective**: Retrieve detailed information from primary links

**Actions**:
- Use `WebFetch` to retrieve content from main promotional/content links
- Extract key details based on email type:
  - **Financial emails**: Interest rates, bonus amounts, terms, deadlines
  - **Promotional emails**: Offer details, discount codes, expiration dates
  - **Newsletter emails**: Article summaries, key points

**Prompt templates for WebFetch**:
```
"Extract the main offer details, key financial information, interest rates,
promotion details, terms and conditions, and any important deadlines or requirements"

"Summarize the main article content, key points, important statistics,
and any calls to action"
```

**Tools**: `WebFetch`

**Fallback**: If WebFetch fails (blocked domain), use `WebSearch` with relevant keywords

### 6. Web Search for Context (if needed)
**Objective**: Gather additional information if links are inaccessible

**Actions**:
- Extract key terms from the email (company name, offer details, dates)
- Perform targeted web searches
- Find alternative sources discussing the same offer/content

**Search query construction**:
- Include: Brand name, offer type, specific amounts/percentages, year
- Example: `"[Company] [Offer Amount] bonus [Year] [Key Terms]"`

**Tools**: `WebSearch`

### 7. Content Analysis and Organization
**Objective**: Structure the extracted information logically

**Organize information into sections**:
1. **Email Subject & Context**
   - Subject line
   - Sender
   - Date received

2. **Key Offer/Content Details**
   - Main proposition or offer
   - Specific amounts, percentages, or key metrics
   - Product/service details
   - Eligibility requirements

3. **Important Terms & Conditions**
   - Minimum requirements
   - Deadlines or expiration dates
   - Restrictions or limitations
   - Required actions or codes

4. **Context & Background**
   - Industry/market context
   - Company background if relevant
   - Comparison to alternatives (if applicable)

5. **Action Items & Deadlines**
   - What the recipient needs to do
   - Time-sensitive information
   - Required codes or steps

6. **Bottom Line**
   - Clear summary of the value proposition
   - Key decision factors
   - Overall recommendation or assessment

### 8. Source Attribution
**Objective**: Provide verifiable sources for all claims

**Actions**:
- Compile all URLs used for research
- Format as markdown links with descriptive titles
- Include both primary (email links) and secondary (research) sources
- Add "Sources:" section at the end with bulleted list

**Format**:
```markdown
### Sources:
- [Descriptive Title](https://url1.com)
- [Descriptive Title](https://url2.com)
```

## Common Patterns by Email Type

### Financial/Banking Emails
**Focus on**:
- Interest rates (APY/APR)
- Bonus amounts and requirements
- Minimum deposits/balances
- Term lengths
- Fees or penalties
- Comparison to market alternatives

### Promotional/Marketing Emails
**Focus on**:
- Discount percentages or amounts
- Promo codes
- Expiration dates
- Exclusions or limitations
- Product/service features
- Shipping/delivery terms

### Newsletter/Content Emails
**Focus on**:
- Main article topics
- Key statistics or findings
- Expert quotes or insights
- Related resources
- Subscription or membership details

## Troubleshooting

### Large File Sizes
- Email HTML files often exceed 256KB due to embedded JavaScript, CSS, and tracking code
- **Solution**: Use Grep instead of Read to extract specific content
- Focus searches on visible content areas

### Omitted Lines in Output
- Grep may show "[Omitted long matching line]" for very long lines
- **Solution**: These are usually CSS/JavaScript; focus on shorter, content-rich matches
- Use `-A` (after) and `-B` (before) context flags to see surrounding lines

### Blocked Web Fetches
- Some domains block automated fetching
- **Solution**: Fall back to WebSearch with specific keywords extracted from email
- Look for news articles or official announcements about the offer

### Email Appears Empty / No Content Found
**Problem**: Grep/Read shows only `<script>` tags, no visible text

**Likely cause**: Email uses JavaScript to render content (common with modern marketing platforms)

**Detection**:
```bash
# Check if email is JavaScript-heavy
grep -c '<script' [file_path]  # If > 5, likely JS-rendered

# Check for visible text outside script tags
grep -v '<script' [file_path] | grep -v '</script>' | grep -i 'bonus\|offer\|apy\|rate' | head -5
```

**Solutions** (in order of preference):

**Option 1 - Find "View in Browser" Link** (RECOMMENDED):
```bash
grep -i "view.*browser\|web version\|online version" [file_path]
```
- Look for "View this email in your browser" link
- Use WebFetch on that URL instead
- Web version usually has full HTML content without JavaScript
- This is the most reliable solution

**Option 2 - Extract JSON Data**:
```bash
# Look for JSON objects in the HTML
grep -o '{[^}]*"apy"[^}]*}' [file_path]
grep -o '{[^}]*"bonus"[^}]*}' [file_path]
grep -o '{[^}]*"offer"[^}]*}' [file_path]
```
- Modern emails often embed offer data in JSON structures
- Search for keys like: "apy", "bonus", "offer", "rate", "amount", "deadline"
- Manually extract values from JSON objects

**Option 3 - Check Email Headers for Plain Text Version**:
```bash
grep -i "Content-Type: text/plain" [file_path] -A 50
```
- Many emails include plain-text alternative
- Look for "Content-Type: text/plain" section
- May contain offer details in simple text format

**Option 4 - Search the Sender's Website**:
- If email is from "offers@bank.com"
- Go to bank.com/offers or bank.com/promotions
- Find the current promotion manually using WebSearch
- Search: "[Bank name] current promotions [year]"

**Prevention tip**:
- When saving emails in the future, look for "View in browser" link first
- Save the web version instead of the raw email HTML
- Web versions are cleaner and easier to parse

### Multiple Languages
- Some emails may be in foreign languages (German, French, etc.)
- **Solution**: Identify the language and provide translations of key terms
- Note the original language in the summary

## Output Format

Generate a comprehensive markdown report with:
- Clear section headers
- Bullet points for easy scanning
- **Bold** for important numbers and dates
- Tables for comparisons (if applicable)
- Warning symbols (⚠️) for important deadlines or conditions
- Footnotes or source attribution at the end

## Success Criteria

A successful email analysis includes:
- ✅ Clear identification of the email's purpose
- ✅ All key numerical data (amounts, percentages, dates)
- ✅ Complete terms and conditions
- ✅ Actionable next steps if applicable
- ✅ Relevant market context
- ✅ Verifiable sources cited
- ✅ Easy-to-scan formatting

## Example Command Sequence

```bash
# 1. Try to read the file
Read: [email_file_path]

# 2. If too large, extract title
grep -o '<title>[^<]*</title>' [email_file_path] | head -1

# 3. Extract unique links, filter noise
grep -o 'href="[^"]*"' [email_file_path] | grep -v 'gmail\|google\|facebook\|twitter' | sort -u | head -20

# 4. Extract URL patterns
grep -oE 'https?://[^\s"<>]+' [email_file_path] | grep -v 'gmail\|google' | sort -u | head -30

# 5. Search for keywords in content
grep -i "keyword" [email_file_path] | head -20
```

Then proceed with WebFetch/WebSearch based on findings.
