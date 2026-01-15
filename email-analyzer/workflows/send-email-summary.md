# Workflow: Send Email Summary

## Overview
After analyzing an email, send a formatted summary via email to yourself or others for easy reference and action.

## Use Cases
- Forward analysis to decision makers
- Save analysis to email for future reference
- Share promotional offers with family/friends
- Archive important financial offer details
- Send comparison analysis to stakeholders

## Prerequisites
- Completed email analysis (see `analyze-email-from-html.md`)
- Summary report generated in markdown format
- Recipient email address(es)
- Email sending method configured

## Workflow Steps

### 1. Prepare Summary for Email
**Objective**: Format the analysis for email delivery

**Actions**:
- Convert markdown to email-friendly format
- Ensure links are properly formatted
- Add email header (To, Subject, etc.)
- Include analysis date and original email subject

**Format Considerations**:
- Use plain text or HTML depending on email client
- Preserve bullet points and formatting
- Ensure clickable links
- Add clear section headers

### 2. Create Email Subject Line
**Objective**: Craft informative subject line

**Template**:
```
Email Analysis: [Original Email Subject] - [Date]
```

**Examples**:
- `Email Analysis: WeltSparen €150 Bonus Offer - Jan 10, 2026`
- `Email Analysis: High-Yield Savings Comparison - Jan 10, 2026`
- `Email Analysis: Limited Time Promotion - Jan 10, 2026`

### 3. Structure Email Body
**Objective**: Organize content for email delivery

**Email Template**:
```
Subject: Email Analysis: [Original Subject] - [Date]

------------------------------------------------------------
EMAIL ANALYSIS REPORT
Generated: [Current Date & Time]
Original Email: [Subject]
Sender: [Sender Name/Email]
Received: [Date]
------------------------------------------------------------

QUICK SUMMARY
[2-3 sentence executive summary]

KEY HIGHLIGHTS
• [Most important point 1]
• [Most important point 2]
• [Most important point 3]
• [Deadline or time-sensitive info if applicable]

------------------------------------------------------------

[Full detailed analysis sections...]

1. EMAIL SUBJECT & CONTEXT
2. KEY OFFER/CONTENT DETAILS
3. IMPORTANT TERMS & CONDITIONS
4. CONTEXT & BACKGROUND
5. ACTION ITEMS & DEADLINES
6. BOTTOM LINE

------------------------------------------------------------

SOURCES & REFERENCES
[Bulleted list of all sources with links]

------------------------------------------------------------
Analysis Type: [Financial/Promotional/Newsletter]
Confidence Level: [High/Medium/Low based on source quality]
Recommendation: [If applicable]
------------------------------------------------------------
```

### 4. Choose Email Sending Method
**Objective**: Select appropriate delivery method

**Option A: Manual Email Client**
- Copy formatted summary
- Open email client (Gmail, Outlook, etc.)
- Paste content
- Send to recipient(s)

**Option B: Command-Line Email (macOS/Linux)**
```bash
# Using mail command
cat summary.txt | mail -s "Email Analysis: Subject" recipient@email.com

# Using sendmail
sendmail recipient@email.com < summary.txt
```

**Option C: Python Script (Future Enhancement)**
```python
# Using smtplib or email service API
# See src/send_email.py (to be developed)
```

**Option D: Email Service API**
- Gmail API
- SendGrid
- Mailgun
- AWS SES

### 5. Add Recipients
**Objective**: Specify who should receive the analysis

**Recipient Types**:
- **Self**: For archival and reference
- **Decision Makers**: For action/approval
- **Collaborators**: For shared decision making
- **Team Members**: For awareness

**Example Recipients**:
```
To: wmarceau26@gmail.com
CC: [family member, business partner, financial advisor]
```

### 6. Review and Send
**Objective**: Final check before sending

**Checklist**:
- [ ] All links are clickable
- [ ] Formatting is preserved
- [ ] No sensitive information exposed (if forwarding)
- [ ] Subject line is clear
- [ ] Recipients are correct
- [ ] Sources are cited
- [ ] Executive summary is accurate
- [ ] Action items are highlighted

### 7. Confirmation and Tracking
**Objective**: Verify delivery and track follow-up

**Actions**:
- Confirm email sent successfully
- Save copy to "Sent" folder
- Set reminder for time-sensitive items
- Add to tracking system if needed

## Email Format Options

### Plain Text Format
**Pros**:
- Universal compatibility
- Fast to send
- No HTML rendering issues

**Cons**:
- Limited formatting
- Links may not be clickable in all clients

**Best For**: Quick summaries, internal team communication

### HTML Format
**Pros**:
- Rich formatting (colors, fonts, tables)
- Clickable buttons and links
- Professional appearance

**Cons**:
- May be blocked by some email filters
- Requires HTML knowledge
- More complex to generate

**Best For**: Client-facing summaries, formal reports

### Markdown with Conversion
**Pros**:
- Easy to write and maintain
- Can convert to HTML for sending
- Preserves structure

**Cons**:
- Requires conversion step
- May lose some formatting

**Best For**: Technical audiences, documentation

## Example Email Templates

### Template 1: Financial Offer Analysis
```
Subject: Email Analysis: WeltSparen €150 Bonus - Action Required by [Date]

Hi [Name],

I analyzed the WeltSparen promotional email. Here's what you need to know:

⚡ QUICK DECISION POINTS:
• Bonus Amount: €150 for new customers
• Minimum Investment: €5,000
• Minimum Term: 6-12 months
• Deadline: [If specified]
• Current Market: High-yield accounts offering 4-5% APY

💰 IS THIS A GOOD DEAL?
[Your assessment based on the analysis]

📋 FULL ANALYSIS BELOW
[Insert complete analysis sections]

Questions? Reply to this email.

Sources: [List of links]
```

### Template 2: Promotional Offer Summary
```
Subject: Email Analysis: [Product] Limited Time Offer

Quick Summary:
[2-3 sentences on the offer]

Worth It? [Yes/No/Maybe with reasoning]

Details:
• Discount: [Amount/Percentage]
• Valid Until: [Date]
• Restrictions: [Key limitations]
• Promo Code: [If applicable]

[Full analysis follows]
```

### Template 3: Newsletter Digest
```
Subject: Email Analysis: [Newsletter Name] - Key Insights

Top Insights:
1. [First key insight]
2. [Second key insight]
3. [Third key insight]

Recommended Actions:
• [Action item 1]
• [Action item 2]

[Full content analysis follows]
```

## Automation Ideas

### Future Enhancements
1. **Auto-send on completion**: Automatically email summary after analysis
2. **Template library**: Pre-built templates for different email types
3. **Distribution lists**: Pre-configured recipient groups
4. **Scheduling**: Send summary at optimal time
5. **Follow-up reminders**: Auto-reminder for deadlines
6. **Integration with calendar**: Add deadlines to calendar automatically

## Security Considerations

### Before Sending
- [ ] Remove any personal account numbers
- [ ] Redact sensitive financial details if forwarding
- [ ] Verify recipient email addresses
- [ ] Check if email contains confidential information
- [ ] Consider using BCC for multiple recipients

### Best Practices
- Don't forward full original HTML (may contain tracking)
- Strip tracking pixels and analytics codes
- Be cautious with promotional links (affiliate codes)
- Verify sender authenticity before sharing offers

## Troubleshooting

### Links Not Clickable
- Ensure proper URL formatting: `https://...`
- Use HTML anchor tags: `<a href="...">Link Text</a>`
- Check email client settings

### Formatting Lost
- Use HTML format instead of plain text
- Simplify markdown conversion
- Test with common email clients

### Email Blocked/Filtered
- Avoid spam trigger words in subject
- Don't use ALL CAPS excessively
- Include plain text version
- Verify sender reputation

## Success Criteria

A successful email summary includes:
- ✅ Clear, actionable subject line
- ✅ Executive summary at the top
- ✅ All key information highlighted
- ✅ Clickable source links
- ✅ Delivered to correct recipients
- ✅ Readable on mobile devices
- ✅ Action items clearly marked

## Related Workflows
- [analyze-email-from-html.md](analyze-email-from-html.md) - Generate the analysis
- [batch-email-analysis.md](batch-email-analysis.md) - Process multiple emails
