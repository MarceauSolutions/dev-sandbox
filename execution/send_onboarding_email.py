#!/usr/bin/env python3
"""
Send onboarding email to new clients for Marceau Solutions

Usage:
    python send_onboarding_email.py client@example.com
    python send_onboarding_email.py client@example.com --name "John"
    python send_onboarding_email.py client@example.com --name "John" --context "Website redesign project"
"""

import smtplib
import sys
import os
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def create_onboarding_email(client_email, client_name=None, project_context=None):
    """Create the onboarding email content for fitness coaching clients."""

    # Get configuration from environment
    sender_name = os.getenv('SENDER_NAME', 'William Marceau')
    sender_email = os.getenv('SENDER_EMAIL')
    calendly_url = os.getenv('CALENDLY_KICKOFF_URL', 'https://calendly.com/wmarceau/kickoff-call')
    intake_form_url = os.getenv('INTAKE_FORM_URL', 'https://docs.google.com/forms/d/e/1FAIpQLSfscvTEGRc7YxRiJdMslS6fj33ca3MOij1erZN6zy82JPNS4Q/viewform')

    if not sender_email:
        raise ValueError("SENDER_EMAIL not set in .env file")

    # Personalize greeting
    greeting = f"Hey {client_name}," if client_name else "Hey,"

    # Create email
    msg = MIMEMultipart('alternative')
    msg['Subject'] = "Welcome to Coaching - Here's What Happens Next"
    msg['From'] = f"{sender_name} <{sender_email}>"
    msg['To'] = client_email

    # Email body (plain text version)
    text_body = f"""{greeting}

Welcome aboard - I'm genuinely excited to work with you.

Here's what happens next (keep this email handy):


STEP 1: BOOK YOUR KICKOFF CALL
-------------------------------
This is where we map out your goals, review your training history, and design your program. 30 minutes, no fluff.

Book here: {calendly_url}


STEP 2: FILL OUT YOUR INTAKE FORM
-----------------------------------
The more I know about you upfront, the better your program will be. This covers health history, goals, equipment, schedule, and food preferences.

Fill it out here: {intake_form_url}

Please complete this BEFORE our kickoff call if possible.


STEP 3: WHAT TO EXPECT AFTER OUR CALL
---------------------------------------
Within 48 hours of our kickoff call, you'll receive:
- Your custom training program (PDF in a shared Google Drive folder)
- Nutrition protocol with macro targets
- Weekly check-in schedule
- Peptide education resources (if applicable to your goals)


HOW WE'LL COMMUNICATE
----------------------
- SMS (texts): Quick questions, weekly check-ins, reminders
- Email: Program updates, detailed recaps, documents
- Google Meet: Kickoff call + monthly progress reviews
- Google Drive: Your program files, progress tracking, resources

I respond to texts within 4 hours (Mon-Fri, 8am-7pm ET).
I respond to emails within 24 hours on business days.


WHAT I NEED FROM YOU
--------------------
- Honest Monday check-in responses (even just a number 1-10)
- Monthly progress photos (front/side/back)
- 48 hours notice for session reschedules
- Tell me when something isn't working - I'd rather adjust than have you suffer in silence


IMPORTANT DOCUMENTS
-------------------
Attached to this email or in your Drive folder:
- Liability waiver (please sign and return before our kickoff call)
- Cancellation policy (cancel anytime, no contracts)


YOUR SUBSCRIPTION
-----------------
$197/month, billed on the same day each month.
Cancel anytime through your Stripe billing portal.
No contracts. No cancellation fees. I earn your loyalty every month.


Let's get to work.

William Marceau
wmarceau@marceausolutions.com
marceausolutions.com/coaching
"""

    # Email body (HTML version)
    html_body = f"""
<html>
<head></head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif; line-height: 1.7; color: #1a1a2e; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f8f9fa;">

    <div style="background: linear-gradient(135deg, #333333, #2D2D2D); padding: 30px; border-radius: 12px 12px 0 0; text-align: center;">
        <h1 style="color: #C9963C; margin: 0; font-size: 24px;">Welcome to Coaching</h1>
        <p style="color: #94a3b8; margin: 8px 0 0;">Let's get you set up.</p>
    </div>

    <div style="background: white; padding: 30px; border-radius: 0 0 12px 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">

        <p style="font-size: 16px;">{greeting}</p>
        <p>Welcome aboard - I'm genuinely excited to work with you. Here's what happens next (keep this email handy).</p>

        <!-- Step 1 -->
        <div style="background: #FDF8EF; border-left: 4px solid #C9963C; padding: 16px 20px; margin: 24px 0; border-radius: 0 8px 8px 0;">
            <h3 style="color: #333333; margin: 0 0 8px;">Step 1: Book Your Kickoff Call</h3>
            <p style="margin: 0; color: #475569;">30 minutes to map out your goals, review your training history, and design your program.</p>
            <p style="margin: 12px 0 0;">
                <a href="{calendly_url}" style="background-color: #C9963C; color: #ffffff; padding: 10px 24px; text-decoration: none; border-radius: 6px; font-weight: 600; display: inline-block;">Book Your Kickoff Call</a>
            </p>
        </div>

        <!-- Step 2 -->
        <div style="background: #FDF8EF; border-left: 4px solid #D4AF37; padding: 16px 20px; margin: 24px 0; border-radius: 0 8px 8px 0;">
            <h3 style="color: #333333; margin: 0 0 8px;">Step 2: Fill Out Your Intake Form</h3>
            <p style="margin: 0; color: #475569;">Health history, goals, equipment, schedule, and food preferences. The more I know, the better your program.</p>
            <p style="margin: 12px 0 0;">
                <a href="{intake_form_url}" style="background-color: #D4AF37; color: #ffffff; padding: 10px 24px; text-decoration: none; border-radius: 6px; font-weight: 600; display: inline-block;">Complete Intake Form</a>
            </p>
            <p style="margin: 8px 0 0; font-size: 13px; color: #64748b;">Please complete before our kickoff call if possible.</p>
        </div>

        <!-- What You'll Receive -->
        <h3 style="color: #333333; margin: 24px 0 12px;">Within 48 Hours of Our Call, You'll Get:</h3>
        <ul style="padding-left: 0; list-style: none;">
            <li style="padding: 6px 0;">&#x2705; Custom training program (PDF in your Google Drive folder)</li>
            <li style="padding: 6px 0;">&#x2705; Nutrition protocol with macro targets</li>
            <li style="padding: 6px 0;">&#x2705; Weekly check-in schedule</li>
            <li style="padding: 6px 0;">&#x2705; Peptide education resources (if applicable)</li>
        </ul>

        <!-- Communication -->
        <h3 style="color: #333333; margin: 24px 0 12px;">How We'll Communicate</h3>
        <table style="width: 100%; border-collapse: collapse; font-size: 14px;">
            <tr style="border-bottom: 1px solid #e2e8f0;">
                <td style="padding: 8px 0; font-weight: 600;">SMS</td>
                <td style="padding: 8px 0; color: #475569;">Quick questions, weekly check-ins, reminders</td>
            </tr>
            <tr style="border-bottom: 1px solid #e2e8f0;">
                <td style="padding: 8px 0; font-weight: 600;">Email</td>
                <td style="padding: 8px 0; color: #475569;">Program updates, recaps, documents</td>
            </tr>
            <tr style="border-bottom: 1px solid #e2e8f0;">
                <td style="padding: 8px 0; font-weight: 600;">Google Meet</td>
                <td style="padding: 8px 0; color: #475569;">Kickoff + monthly progress reviews</td>
            </tr>
            <tr>
                <td style="padding: 8px 0; font-weight: 600;">Google Drive</td>
                <td style="padding: 8px 0; color: #475569;">Programs, progress tracking, resources</td>
            </tr>
        </table>
        <p style="font-size: 13px; color: #64748b; margin-top: 8px;">Texts: within 4 hours (Mon-Fri, 8am-7pm ET) &middot; Email: within 24 hours on business days</p>

        <!-- What I Need -->
        <h3 style="color: #333333; margin: 24px 0 12px;">What I Need From You</h3>
        <ul style="padding-left: 20px; color: #475569;">
            <li style="padding: 4px 0;">Honest Monday check-in responses (even just a 1-10 rating)</li>
            <li style="padding: 4px 0;">Monthly progress photos (front/side/back)</li>
            <li style="padding: 4px 0;">48 hours notice for session reschedules</li>
            <li style="padding: 4px 0;">Tell me when something isn't working</li>
        </ul>

        <!-- Billing -->
        <div style="background: #f8fafc; padding: 16px; border-radius: 8px; margin: 24px 0; text-align: center;">
            <p style="margin: 0; color: #64748b; font-size: 14px;"><strong>$197/month</strong> &middot; Cancel anytime &middot; No contracts &middot; No cancellation fees</p>
        </div>

        <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 24px 0;">

        <p style="font-size: 15px;">Let's get to work.</p>
        <p style="margin-top: 16px;">
            <strong>William Marceau</strong><br>
            <a href="mailto:wmarceau@marceausolutions.com" style="color: #C9963C;">wmarceau@marceausolutions.com</a><br>
            <a href="https://marceausolutions.com/coaching" style="color: #C9963C;">marceausolutions.com/coaching</a>
        </p>
    </div>

    <p style="text-align: center; font-size: 12px; color: #94a3b8; margin-top: 16px;">
        Disclaimer: This is not medical advice. Consult a healthcare provider before starting any fitness program.
    </p>
</body>
</html>
"""

    # Attach both versions
    part1 = MIMEText(text_body, 'plain')
    part2 = MIMEText(html_body, 'html')
    msg.attach(part1)
    msg.attach(part2)

    return msg


def send_email(msg, recipient_email):
    """Send email via Gmail SMTP"""

    smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
    smtp_port = int(os.getenv('SMTP_PORT', '587'))
    smtp_username = os.getenv('SMTP_USERNAME')
    smtp_password = os.getenv('SMTP_PASSWORD')

    if not smtp_username or not smtp_password:
        raise ValueError(
            "SMTP credentials not configured. Please set SMTP_USERNAME and SMTP_PASSWORD in .env file.\n"
            "For Gmail, you need to create an App Password: https://support.google.com/accounts/answer/185833"
        )

    try:
        # Connect to SMTP server
        server = smtplib.SMTP(smtp_host, smtp_port)
        server.ehlo()
        server.starttls()
        server.ehlo()

        # Login
        server.login(smtp_username, smtp_password)

        # Send email
        server.send_message(msg)
        server.quit()

        return True
    except smtplib.SMTPAuthenticationError:
        raise Exception(
            "SMTP Authentication failed. Please check your credentials.\n"
            "For Gmail, make sure you're using an App Password, not your regular password.\n"
            "Create one here: https://support.google.com/accounts/answer/185833"
        )
    except Exception as e:
        raise Exception(f"Failed to send email: {str(e)}")


def main():
    """Main function"""

    # Parse command line arguments
    if len(sys.argv) < 2:
        print("Usage: python send_onboarding_email.py client@example.com [--name 'Client Name'] [--context 'Project context']")
        sys.exit(1)

    client_email = sys.argv[1]
    client_name = None
    project_context = None

    # Parse optional arguments
    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == '--name' and i + 1 < len(sys.argv):
            client_name = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == '--context' and i + 1 < len(sys.argv):
            project_context = sys.argv[i + 1]
            i += 2
        else:
            i += 1

    # Validate email
    if not validate_email(client_email):
        print(f"❌ Error: Invalid email format: {client_email}")
        sys.exit(1)

    print(f"📧 Preparing onboarding email for {client_email}...")
    if client_name:
        print(f"   Client name: {client_name}")
    if project_context:
        print(f"   Project context: {project_context}")

    try:
        # Create email
        msg = create_onboarding_email(client_email, client_name, project_context)

        # Send email
        print(f"📤 Sending email...")
        send_email(msg, client_email)

        print(f"✅ Onboarding email sent successfully to {client_email}!")
        print(f"   Sent at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
