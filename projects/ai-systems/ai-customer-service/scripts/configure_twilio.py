"""Configure Twilio phone number webhook."""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from twilio.rest import Client
from dotenv import load_dotenv

# Load environment
load_dotenv(os.path.join(os.path.dirname(__file__), "../../../.env"))

ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")


def get_current_config():
    """Get current phone number configuration."""
    client = Client(ACCOUNT_SID, AUTH_TOKEN)

    # Find the phone number
    numbers = client.incoming_phone_numbers.list(phone_number=PHONE_NUMBER)

    if not numbers:
        print(f"Phone number {PHONE_NUMBER} not found in account")
        return None

    number = numbers[0]
    print(f"\nPhone Number: {number.phone_number}")
    print(f"Friendly Name: {number.friendly_name}")
    print(f"Voice URL: {number.voice_url}")
    print(f"Voice Method: {number.voice_method}")
    print(f"Status Callback: {number.status_callback}")

    return number


def configure_webhook(base_url: str):
    """Configure the webhook URL for voice calls."""
    client = Client(ACCOUNT_SID, AUTH_TOKEN)

    # Find the phone number
    numbers = client.incoming_phone_numbers.list(phone_number=PHONE_NUMBER)

    if not numbers:
        print(f"Phone number {PHONE_NUMBER} not found")
        return False

    number = numbers[0]

    # Update webhook URLs
    voice_url = f"{base_url}/twilio/voice"
    status_url = f"{base_url}/twilio/status"

    updated = client.incoming_phone_numbers(number.sid).update(
        voice_url=voice_url,
        voice_method="POST",
        status_callback=status_url,
        status_callback_method="POST"
    )

    print(f"\n✅ Webhook configured!")
    print(f"   Voice URL: {updated.voice_url}")
    print(f"   Status URL: {updated.status_callback}")
    print(f"\n📞 Call {PHONE_NUMBER} to test!")

    return True


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Configure Twilio webhook")
    parser.add_argument("--url", help="Base URL (e.g., https://abc123.ngrok.io)")
    parser.add_argument("--show", action="store_true", help="Show current config")

    args = parser.parse_args()

    if args.show or not args.url:
        get_current_config()

    if args.url:
        configure_webhook(args.url)


if __name__ == "__main__":
    main()
