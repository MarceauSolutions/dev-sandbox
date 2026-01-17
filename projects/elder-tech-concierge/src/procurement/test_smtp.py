#!/usr/bin/env python3
"""
SMTP Connection Test

Use this script to test your SMTP credentials before sending real emails.
"""

import os
import sys
import smtplib
from email.mime.text import MIMEText
from pathlib import Path

# Load .env file
env_path = Path(__file__).parent.parent.parent / '.env'
if env_path.exists():
    print(f"Loading environment from: {env_path}")
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value
else:
    print(f"Warning: No .env file found at {env_path}")
    print("Using environment variables directly.")


def test_smtp_connection():
    """Test basic SMTP connection without sending"""
    host = os.environ.get('SMTP_HOST', 'smtp.gmail.com')
    port = int(os.environ.get('SMTP_PORT', '587'))
    user = os.environ.get('SMTP_USER', '')
    password = os.environ.get('SMTP_PASS', '')

    print("\n" + "="*60)
    print("SMTP Configuration")
    print("="*60)
    print(f"Host: {host}")
    print(f"Port: {port}")
    print(f"User: {user}")
    print(f"Password: {'*' * len(password) if password else '(not set)'}")

    if not user or not password or password == 'REPLACE_WITH_APP_PASSWORD':
        print("\n" + "!"*60)
        print("ERROR: SMTP credentials not configured!")
        print("!"*60)
        print("\nTo configure:")
        print("1. Go to https://myaccount.google.com/apppasswords")
        print("2. Generate an App Password for 'Mail'")
        print("3. Update SMTP_PASS in .env file")
        return False

    print("\n" + "-"*60)
    print("Testing connection...")
    print("-"*60)

    try:
        with smtplib.SMTP(host, port) as server:
            print(f"[OK] Connected to {host}:{port}")

            server.starttls()
            print("[OK] TLS encryption established")

            server.login(user, password)
            print("[OK] Authentication successful!")

            print("\n" + "="*60)
            print("SUCCESS: SMTP credentials are working!")
            print("="*60)
            return True

    except smtplib.SMTPAuthenticationError as e:
        print(f"\n[FAIL] Authentication failed: {e}")
        print("\nTips:")
        print("- Make sure you're using an App Password, not your regular password")
        print("- Verify the email address is correct")
        print("- Check if 2-factor authentication is enabled")
        return False

    except smtplib.SMTPException as e:
        print(f"\n[FAIL] SMTP error: {e}")
        return False

    except Exception as e:
        print(f"\n[FAIL] Connection error: {e}")
        return False


def send_test_email(to_address: str = None):
    """Send a test email to verify full functionality"""
    host = os.environ.get('SMTP_HOST', 'smtp.gmail.com')
    port = int(os.environ.get('SMTP_PORT', '587'))
    user = os.environ.get('SMTP_USER', '')
    password = os.environ.get('SMTP_PASS', '')
    from_addr = os.environ.get('SMTP_FROM', user)

    # Default to sending to self
    if not to_address:
        to_address = user

    print(f"\nSending test email to: {to_address}")

    msg = MIMEText("""
This is a test email from Elder Tech Concierge Procurement System.

If you received this email, your SMTP configuration is working correctly!

Configuration tested:
- SMTP Host: smtp.gmail.com
- SMTP Port: 587
- From: wmarceau@marceausolutions.com

You can now send real bulk pricing inquiries to wholesalers.

Best regards,
Elder Tech Concierge
""")

    msg['Subject'] = '[TEST] Elder Tech Procurement - SMTP Configuration Test'
    msg['From'] = from_addr
    msg['To'] = to_address

    try:
        with smtplib.SMTP(host, port) as server:
            server.starttls()
            server.login(user, password)
            server.send_message(msg)

        print("[OK] Test email sent successfully!")
        print(f"    Check inbox at: {to_address}")
        return True

    except Exception as e:
        print(f"[FAIL] Failed to send: {e}")
        return False


if __name__ == '__main__':
    print("\n" + "="*60)
    print("Elder Tech Procurement - SMTP Test")
    print("="*60)

    # Test connection first
    if test_smtp_connection():
        # Ask if user wants to send test email
        if len(sys.argv) > 1 and sys.argv[1] == '--send':
            to_addr = sys.argv[2] if len(sys.argv) > 2 else None
            send_test_email(to_addr)
        else:
            print("\nTo send a test email, run:")
            print(f"  python {sys.argv[0]} --send")
            print(f"  python {sys.argv[0]} --send your@email.com")
