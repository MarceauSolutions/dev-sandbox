"""Make a test call to the AI Customer Service."""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from twilio.rest import Client
from dotenv import load_dotenv

# Load environment
load_dotenv(os.path.join(os.path.dirname(__file__), "../../../.env"))

ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
AI_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")  # The AI answers this


def make_test_call(to_number: str):
    """
    Make a test call FROM the AI number TO a real phone.

    This lets you test the AI by having it call YOU.
    """
    client = Client(ACCOUNT_SID, AUTH_TOKEN)

    # The AI's webhook URL
    webhook_url = "https://cuddly-bryn-fiduciarily.ngrok-free.dev/twilio/voice"

    print(f"\n📞 Initiating call...")
    print(f"   From: {AI_PHONE_NUMBER} (AI)")
    print(f"   To: {to_number} (You)")
    print(f"   Webhook: {webhook_url}")

    call = client.calls.create(
        url=webhook_url,
        to=to_number,
        from_=AI_PHONE_NUMBER,
        status_callback="https://cuddly-bryn-fiduciarily.ngrok-free.dev/twilio/status",
        status_callback_event=["initiated", "ringing", "answered", "completed"]
    )

    print(f"\n✅ Call initiated!")
    print(f"   Call SID: {call.sid}")
    print(f"   Status: {call.status}")
    print(f"\n📱 Answer your phone when it rings!")

    return call


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Make a test call")
    parser.add_argument("phone", help="Your phone number (e.g., +12395551234)")

    args = parser.parse_args()

    # Validate phone number format
    phone = args.phone
    if not phone.startswith("+"):
        phone = "+1" + phone.replace("-", "").replace(" ", "")

    make_test_call(phone)


if __name__ == "__main__":
    main()
