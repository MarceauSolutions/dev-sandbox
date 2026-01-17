#!/usr/bin/env python3
"""
Calendly/Calendar Booking Monitor

PURPOSE: Monitor Google Calendar for new Calendly bookings and alert immediately.
SOLVES: Missing hot lead meetings because they weren't noticed in time.

FEATURES:
1. Check for new calendar events (Calendly creates events automatically)
2. Match events to pending leads (by name, email, or company)
3. Send immediate SMS/email notification when booking detected
4. Track which bookings have been notified

USAGE:
    # Check for new bookings
    python calendly_monitor.py check

    # Check and send SMS alert
    python calendly_monitor.py check --notify-sms "+12395551234"

    # Run continuous monitoring (every 5 minutes)
    python calendly_monitor.py watch --interval 300

HOW IT WORKS:
- Calendly automatically creates Google Calendar events when someone books
- This script polls your calendar for new events
- Matches events against pending leads in form_submissions.json
- Sends notifications when a pending lead books a call
"""

import os
import sys
import json
import argparse
import smtplib
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time

from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

# Try to import Google and Twilio
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    from twilio.rest import Client as TwilioClient
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False


@dataclass
class CalendarBooking:
    """Represents a calendar booking."""
    event_id: str
    summary: str
    start_time: str
    end_time: str
    attendees: List[str]
    description: str
    location: str
    created: str
    is_calendly: bool = False
    matched_lead: Optional[str] = None
    notified: bool = False


class CalendlyMonitor:
    """Monitor Google Calendar for Calendly bookings."""

    def __init__(self):
        # Google Auth
        self.token_path = Path("projects/lead-scraper/output/google_token.json")
        self.access_token = None

        # Twilio
        self.twilio_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.twilio_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.twilio_number = os.getenv('TWILIO_PHONE_NUMBER')
        self.twilio_client = None

        if TWILIO_AVAILABLE and self.twilio_sid and self.twilio_token:
            self.twilio_client = TwilioClient(self.twilio_sid, self.twilio_token)

        # Email
        self.smtp_user = os.getenv('SMTP_USER')
        self.smtp_pass = os.getenv('SMTP_PASSWORD')
        self.notification_email = os.getenv('NOTIFICATION_EMAIL')

        # Data files
        self.form_submissions_file = Path("projects/lead-scraper/output/form_submissions.json")
        self.bookings_file = Path("projects/lead-scraper/output/calendar_bookings.json")

        # Calendly detection keywords
        self.calendly_indicators = [
            'calendly',
            'scheduled',
            'booking',
            '30 min',
            '15 min',
            '30min',
            '15min',
            'consultation',
            'discovery call',
            'intro call'
        ]

        self._load_access_token()

    def _load_access_token(self):
        """Load and refresh Google access token."""
        if not self.token_path.exists():
            print("❌ No Google token found. Run google_auth_setup.py first.")
            return

        with open(self.token_path) as f:
            token_data = json.load(f)

        self.access_token = token_data.get("token")

        # Check if token needs refresh
        expiry_str = token_data.get("expiry")
        if expiry_str:
            try:
                expiry = datetime.fromisoformat(expiry_str.replace("Z", "+00:00"))
                now = datetime.now(expiry.tzinfo) if expiry.tzinfo else datetime.now()

                if now >= expiry:
                    print("🔄 Refreshing Google token...")
                    response = requests.post(
                        token_data.get("token_uri", "https://oauth2.googleapis.com/token"),
                        data={
                            "grant_type": "refresh_token",
                            "refresh_token": token_data.get("refresh_token"),
                            "client_id": token_data.get("client_id"),
                            "client_secret": token_data.get("client_secret")
                        }
                    )

                    if response.status_code == 200:
                        new_data = response.json()
                        self.access_token = new_data["access_token"]

                        # Update stored token
                        token_data["token"] = self.access_token
                        new_expiry = datetime.now() + timedelta(seconds=new_data.get("expires_in", 3600))
                        token_data["expiry"] = new_expiry.isoformat() + "Z"

                        with open(self.token_path, "w") as f:
                            json.dump(token_data, f)
                        print("✅ Token refreshed")
                    else:
                        print(f"❌ Token refresh failed: {response.text}")
            except Exception as e:
                print(f"⚠️ Token check error: {e}")

    def get_pending_leads(self) -> List[Dict]:
        """Get list of pending leads from form submissions."""
        if not self.form_submissions_file.exists():
            return []

        with open(self.form_submissions_file) as f:
            data = json.load(f)

        # Filter to leads without a meeting booked
        pending = []
        for sub in data.get("submissions", []):
            # Skip test entries
            if "@example.com" in sub.get("email", "") or "@test.com" in sub.get("email", ""):
                continue

            # Check if already has a meeting
            if not sub.get("meeting_booked"):
                pending.append(sub)

        return pending

    def fetch_recent_events(self, hours_back: int = 48) -> List[CalendarBooking]:
        """Fetch recent calendar events."""
        if not self.access_token:
            return []

        # Time range
        time_min = (datetime.utcnow() - timedelta(hours=hours_back)).isoformat() + "Z"
        time_max = (datetime.utcnow() + timedelta(days=14)).isoformat() + "Z"

        url = "https://www.googleapis.com/calendar/v3/calendars/primary/events"
        params = {
            "timeMin": time_min,
            "timeMax": time_max,
            "singleEvents": True,
            "orderBy": "startTime"
        }
        headers = {"Authorization": f"Bearer {self.access_token}"}

        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()

            events = response.json().get("items", [])
            bookings = []

            for event in events:
                booking = CalendarBooking(
                    event_id=event.get("id", ""),
                    summary=event.get("summary", ""),
                    start_time=event.get("start", {}).get("dateTime", event.get("start", {}).get("date", "")),
                    end_time=event.get("end", {}).get("dateTime", event.get("end", {}).get("date", "")),
                    attendees=[a.get("email", "") for a in event.get("attendees", [])],
                    description=event.get("description", ""),
                    location=event.get("location", ""),
                    created=event.get("created", "")
                )

                # Check if this looks like a Calendly booking
                search_text = f"{booking.summary} {booking.description} {booking.location}".lower()
                booking.is_calendly = any(ind in search_text for ind in self.calendly_indicators)

                bookings.append(booking)

            return bookings

        except Exception as e:
            print(f"❌ Calendar API error: {e}")
            return []

    def match_booking_to_lead(self, booking: CalendarBooking, leads: List[Dict]) -> Optional[Dict]:
        """Try to match a calendar booking to a pending lead."""
        booking_text = f"{booking.summary} {booking.description} {' '.join(booking.attendees)}".lower()

        for lead in leads:
            name = lead.get("name", "").lower()
            email = lead.get("email", "").lower()
            company = lead.get("company", "").lower()

            # Check for matches
            if name and name in booking_text:
                return lead
            if email and email in booking_text:
                return lead
            if company and company in booking_text:
                return lead
            if email and email in [a.lower() for a in booking.attendees]:
                return lead

        return None

    def get_notified_bookings(self) -> set:
        """Get set of already-notified booking IDs."""
        if not self.bookings_file.exists():
            return set()

        with open(self.bookings_file) as f:
            data = json.load(f)

        return set(b.get("event_id") for b in data.get("notified_bookings", []))

    def save_notified_booking(self, booking: CalendarBooking, lead: Dict):
        """Save a booking as notified."""
        data = {"notified_bookings": []}

        if self.bookings_file.exists():
            with open(self.bookings_file) as f:
                data = json.load(f)

        data["notified_bookings"].append({
            "event_id": booking.event_id,
            "summary": booking.summary,
            "start_time": booking.start_time,
            "matched_lead": lead.get("name"),
            "notified_at": datetime.now().isoformat()
        })

        with open(self.bookings_file, "w") as f:
            json.dump(data, f, indent=2)

    def send_sms_notification(self, booking: CalendarBooking, lead: Dict, phone: str) -> bool:
        """Send SMS notification for new booking."""
        if not self.twilio_client:
            print("⚠️ Twilio not configured")
            return False

        message = f"""🎉 NEW MEETING BOOKED!

{lead.get('name', 'Lead')} from {lead.get('company', 'Unknown')} just scheduled!

📅 {booking.summary}
🕐 {booking.start_time}
📧 {lead.get('email', '')}

This is from your cold outreach campaign!"""

        try:
            self.twilio_client.messages.create(
                body=message,
                from_=self.twilio_number,
                to=phone
            )
            print(f"✅ SMS notification sent to {phone}")
            return True
        except Exception as e:
            print(f"❌ SMS failed: {e}")
            return False

    def send_email_notification(self, booking: CalendarBooking, lead: Dict) -> bool:
        """Send email notification for new booking."""
        if not all([self.smtp_user, self.smtp_pass, self.notification_email]):
            return False

        subject = f"🎉 MEETING BOOKED: {lead.get('name', 'Lead')} from {lead.get('company', 'Unknown')}"

        body = f"""
🎉 NEW CALENDLY BOOKING DETECTED!

A lead from your cold outreach just scheduled a meeting!

LEAD DETAILS:
- Name: {lead.get('name', 'Unknown')}
- Company: {lead.get('company', 'Unknown')}
- Email: {lead.get('email', '')}
- Phone: {lead.get('phone', '')}
- Original Message: {lead.get('message', '')}

MEETING DETAILS:
- Title: {booking.summary}
- When: {booking.start_time}
- Location: {booking.location or 'TBD'}

This lead originally submitted on {lead.get('submitted_at', 'Unknown')}.

Time to prepare! 🚀
"""

        try:
            msg = MIMEMultipart()
            msg['From'] = self.smtp_user
            msg['To'] = self.notification_email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))

            with smtplib.SMTP('smtp.gmail.com', 587) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_pass)
                server.send_message(msg)

            print(f"✅ Email notification sent to {self.notification_email}")
            return True
        except Exception as e:
            print(f"❌ Email failed: {e}")
            return False

    def check_for_new_bookings(self, notify_sms: str = None) -> List[Dict]:
        """
        Check for new bookings that match pending leads.

        Returns:
            List of new bookings with matched leads
        """
        print("📅 Checking calendar for new bookings...")

        # Get pending leads
        leads = self.get_pending_leads()
        if not leads:
            print("ℹ️ No pending leads to match against")
            return []

        print(f"   Found {len(leads)} pending leads")

        # Get recent events
        events = self.fetch_recent_events(hours_back=72)
        print(f"   Found {len(events)} calendar events")

        # Get already-notified bookings
        notified = self.get_notified_bookings()

        # Check for matches
        new_bookings = []

        for event in events:
            # Skip if already notified
            if event.event_id in notified:
                continue

            # Try to match to a lead
            matched_lead = self.match_booking_to_lead(event, leads)

            if matched_lead:
                print(f"\n🔥 MATCH FOUND!")
                print(f"   Event: {event.summary}")
                print(f"   Lead: {matched_lead.get('name')} ({matched_lead.get('company')})")
                print(f"   When: {event.start_time}")

                # Send notifications
                self.send_email_notification(event, matched_lead)

                if notify_sms:
                    self.send_sms_notification(event, matched_lead, notify_sms)

                # Mark as notified
                self.save_notified_booking(event, matched_lead)

                new_bookings.append({
                    "booking": asdict(event),
                    "lead": matched_lead
                })

        if not new_bookings:
            print("\n✓ No new lead bookings found")
        else:
            print(f"\n✅ Found {len(new_bookings)} new booking(s)!")

        return new_bookings

    def watch(self, interval: int = 300, notify_sms: str = None):
        """
        Continuously watch for new bookings.

        Args:
            interval: Check interval in seconds (default 5 minutes)
            notify_sms: Phone number for SMS notifications
        """
        print(f"👀 Starting calendar watch (checking every {interval}s)")
        print("   Press Ctrl+C to stop\n")

        while True:
            try:
                self.check_for_new_bookings(notify_sms)
                print(f"\n⏰ Next check in {interval} seconds...")
                time.sleep(interval)
            except KeyboardInterrupt:
                print("\n\n👋 Watch stopped")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                time.sleep(60)  # Wait 1 minute on error


def main():
    parser = argparse.ArgumentParser(description="Monitor Calendly bookings")
    parser.add_argument("command", choices=["check", "watch"],
                       help="Command to run")
    parser.add_argument("--notify-sms",
                       help="Phone number for SMS notifications")
    parser.add_argument("--interval", type=int, default=300,
                       help="Watch interval in seconds (default: 300)")

    args = parser.parse_args()

    monitor = CalendlyMonitor()

    if args.command == "check":
        monitor.check_for_new_bookings(args.notify_sms)

    elif args.command == "watch":
        monitor.watch(args.interval, args.notify_sms)


if __name__ == "__main__":
    main()
