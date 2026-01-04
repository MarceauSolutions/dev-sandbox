# Directive: Onboard New Client

## Goal
Send a professional onboarding email to a new client that introduces Marceau Solutions, provides background, and invites them to a kickoff call.

## Inputs
- **Client email**: Email address of the new client (e.g., client@example.com)
- **Client name** (optional): First name or company name for personalization
- **Project context** (optional): Any specific details about their project or needs

## Tools
- `execution/send_onboarding_email.py` - Sends the onboarding email via Gmail SMTP

## Process
1. **Validate input**: Confirm the email address is valid format
2. **Personalize message**: Use client name if provided, otherwise use generic greeting
3. **Send email**: Execute the email script with client details
4. **Confirm delivery**: Verify email was sent successfully
5. **Log the onboarding**: Record the client email and timestamp (optional: could save to a Google Sheet)

## Email Template Structure

**Subject**: Welcome to Marceau Solutions - Let's Get Started!

**Body includes**:
- Warm welcome and thank you for choosing Marceau Solutions
- Brief company background (web/software development expertise)
- What they can expect from working together
- Call-to-action: Schedule kickoff call via Calendly link
- Contact information for questions

## Outputs
- **Sent email**: Client receives professional onboarding email
- **Confirmation**: Success/failure message returned to orchestrator
- **Optional**: Log entry in tracking sheet

## Edge Cases
- **Invalid email format**: Validate email before sending, prompt for correction
- **SMTP authentication failure**: Check .env credentials, provide helpful error message
- **Rate limiting**: Gmail has sending limits (500/day for free, 2000/day for Workspace)
- **Missing Calendly link**: Warn if CALENDLY_URL not set in .env
- **Bounced email**: Can't detect immediately, but could implement webhook for bounce tracking
- **Client already onboarded**: Check if email was already sent (if logging to sheet)

## Configuration Required

In `.env`:
```
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@marceausolutions.com
SMTP_PASSWORD=your-app-password
SENDER_NAME=Marceau Solutions
SENDER_EMAIL=your-email@marceausolutions.com
CALENDLY_URL=https://calendly.com/your-link
```

## Learnings
(Updated as system self-anneals)
- Initial creation: 2026-01-03
