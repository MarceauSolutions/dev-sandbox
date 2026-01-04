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
    """Create the onboarding email content"""

    # Get configuration from environment
    sender_name = os.getenv('SENDER_NAME', 'Marceau Solutions')
    sender_email = os.getenv('SENDER_EMAIL')
    calendly_url = os.getenv('CALENDLY_URL')

    if not sender_email:
        raise ValueError("SENDER_EMAIL not set in .env file")

    if not calendly_url:
        print("⚠️  Warning: CALENDLY_URL not set in .env file. Using placeholder.")
        calendly_url = "[YOUR_CALENDLY_LINK]"

    # Personalize greeting
    if client_name:
        greeting = f"Hi {client_name},"
    else:
        greeting = "Hello,"

    # Create email
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"Welcome to {sender_name} - Let's Get Started!"
    msg['From'] = f"{sender_name} <{sender_email}>"
    msg['To'] = client_email

    # Email body (plain text version)
    text_body = f"""{greeting}

Thanks for coming to work with us - we're excited to have you onboard.

About Us
--------
At Marceau Solutions, we specialize in building high-quality web applications and software solutions that help businesses grow and succeed.

What to Expect
--------------
✓ Collaborative approach - We work closely with you to understand your vision
✓ Regular updates - You'll receive daily updates until the project is complete
✓ Quality focus - Clean code, modern design, and robust functionality
✓ On-time delivery - We respect your timeline and budget

Next Steps
----------
- We'll hop on a quick kickoff call to align on your goals
- You'll meet the team and get familiar with the culture
- From there we'll map out a plan tailored to you (on the call)

Book your kickoff call here: {calendly_url}

Best regards,

{sender_name}
{sender_email}
"""

    # Email body (HTML version)
    html_body = f"""
<html>
<head></head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <p>{greeting}</p>

    <p>Thanks for coming to work with us - we're excited to have you onboard.</p>

    <h2 style="color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px;">About Us</h2>
    <p>At Marceau Solutions, we specialize in building high-quality web applications and software solutions that help businesses grow and succeed.</p>

    <h2 style="color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px;">What to Expect</h2>
    <ul style="list-style-type: none; padding-left: 0;">
        <li>✓ <strong>Collaborative approach</strong> - We work closely with you to understand your vision</li>
        <li>✓ <strong>Regular updates</strong> - You'll receive daily updates until the project is complete</li>
        <li>✓ <strong>Quality focus</strong> - Clean code, modern design, and robust functionality</li>
        <li>✓ <strong>On-time delivery</strong> - We respect your timeline and budget</li>
    </ul>

    <h2 style="color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px;">Next Steps</h2>
    <ul style="padding-left: 20px;">
        <li>We'll hop on a quick kickoff call to align on your goals</li>
        <li>You'll meet the team and get familiar with the culture</li>
        <li>From there we'll map out a plan tailored to you (on the call)</li>
    </ul>

    <p><strong>Book your kickoff call here:</strong></p>
    <p style="margin: 30px 0;">
        <a href="{calendly_url}" style="background-color: #3498db; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block;">📅 Schedule Your Kickoff Call</a>
    </p>

    <p style="margin-top: 30px;">
        Best regards,<br><br>
        <strong>{sender_name}</strong><br>
        <a href="mailto:{sender_email}">{sender_email}</a>
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
