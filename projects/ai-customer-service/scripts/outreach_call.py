"""Make an AI consulting outreach call with personalization."""

import os
import sys
import urllib.parse
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from twilio.rest import Client
from dotenv import load_dotenv

# Load environment
load_dotenv(os.path.join(os.path.dirname(__file__), "../../../.env"))

ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
AI_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
BASE_URL = "https://midi-bottom-inline-directories.trycloudflare.com"


def make_outreach_call(
    to_number: str,
    business_name: str = None,
    business_type: str = None,
    person_name: str = None,
    custom_context: str = None
):
    """
    Make an AI consulting outreach call with optional personalization.

    Args:
        to_number: Phone number to call
        business_name: Company/business name
        business_type: Type of business (medical, fitness, restaurant, etc.)
        person_name: Name of the person being called
        custom_context: Custom context for highly personalized calls
    """
    client = Client(ACCOUNT_SID, AUTH_TOKEN)

    # Store personalization in a lookup store (in-memory for now)
    # The outreach endpoint will use the To number to look up personalization
    import requests

    print(f"\n📞 Initiating AI consulting outreach call...")
    print(f"   From: {AI_PHONE_NUMBER}")
    print(f"   To: {to_number}")
    if person_name:
        print(f"   Person: {person_name}")
    if business_name:
        print(f"   Company: {business_name}")
    if business_type:
        print(f"   Type: {business_type}")
    if custom_context:
        print(f"   Context: {custom_context[:50]}...")

    # Register personalization with the server before calling
    try:
        reg_response = requests.post(
            f"{BASE_URL}/twilio/register-outreach",
            json={
                "to_number": to_number,
                "person_name": person_name,
                "business_name": business_name,
                "business_type": business_type,
                "custom_context": custom_context
            },
            timeout=5
        )
        print(f"   Personalization registered: {reg_response.status_code == 200}")
    except Exception as e:
        print(f"   Warning: Could not register personalization: {e}")

    webhook_url = f"{BASE_URL}/twilio/outreach"

    call = client.calls.create(
        url=webhook_url,
        to=to_number,
        from_=AI_PHONE_NUMBER,
        status_callback=f"{BASE_URL}/twilio/status",
        status_callback_event=["initiated", "ringing", "answered", "completed"]
    )

    print(f"\n✅ Call initiated!")
    print(f"   Call SID: {call.sid}")

    return call


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Make AI consulting outreach call")
    parser.add_argument("phone", help="Phone number to call")
    parser.add_argument("--business", "-b", help="Business/company name for personalization")
    parser.add_argument("--type", "-t", help="Business type (e.g., medical, fitness, restaurant)")
    parser.add_argument("--person", "-p", help="Person's name")
    parser.add_argument("--context", "-c", help="Custom context for personalization")

    args = parser.parse_args()

    phone = args.phone
    if not phone.startswith("+"):
        phone = "+1" + phone.replace("-", "").replace(" ", "").replace("(", "").replace(")", "")

    make_outreach_call(
        phone,
        business_name=args.business,
        business_type=args.type,
        person_name=args.person,
        custom_context=args.context
    )
