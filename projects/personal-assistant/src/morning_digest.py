#!/usr/bin/env python3
"""
morning_digest.py - Morning Digest Generator with Email Delivery

Generates a formatted morning digest email combining:
- Email inbox summary
- SMS reply notifications
- Form submissions
- Today's calendar
- Action items

Sends via SMTP to configured recipient.

Usage:
    python -m src.morning_digest                    # Generate and send
    python -m src.morning_digest --preview          # Preview without sending
    python -m src.morning_digest --hours 48         # Custom lookback period
"""

import os
import sys
import json
import argparse
import smtplib
from datetime import datetime
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Add parent path for imports
sys.path.insert(0, str(Path(__file__).parent))
from digest_aggregator import DigestAggregator, DigestData


class MorningDigest:
    """
    Generates and sends morning digest emails.
    """

    def __init__(self):
        """Initialize with environment configuration."""
        # SMTP configuration
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.sender_name = os.getenv("SENDER_NAME", "Personal Assistant")
        self.sender_email = os.getenv("SENDER_EMAIL", self.smtp_username)
        self.recipient_email = os.getenv("NOTIFICATION_EMAIL", "")

        # Output directory
        self.output_dir = Path(__file__).parent.parent / "output" / "digests"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def format_text_digest(self, digest: DigestData) -> str:
        """
        Format digest as plain text.

        Args:
            digest: Aggregated digest data

        Returns:
            Plain text formatted digest
        """
        lines = []

        # Header
        lines.append("=" * 60)
        lines.append(f"MORNING DIGEST - {datetime.now().strftime('%A, %B %d, %Y')}")
        lines.append(f"Data from last {digest.hours_covered} hours")
        lines.append("=" * 60)
        lines.append("")

        # Email Summary
        lines.append("📧 EMAIL SUMMARY")
        lines.append("-" * 40)
        lines.append(f"Total: {digest.email.total} emails")
        if digest.email.urgent > 0:
            lines.append(f"  🔴 Urgent: {digest.email.urgent}")
        if digest.email.sponsorship > 0:
            lines.append(f"  💼 Sponsorship: {digest.email.sponsorship}")
        if digest.email.business > 0:
            lines.append(f"  💰 Business: {digest.email.business}")
        if digest.email.customer > 0:
            lines.append(f"  👤 Customer: {digest.email.customer}")
        if digest.email.other > 0:
            lines.append(f"  📬 Other: {digest.email.other}")

        if digest.email.action_required:
            lines.append("")
            lines.append("  Action Required:")
            for item in digest.email.action_required[:3]:
                lines.append(f"    • {item.get('subject', 'No Subject')[:50]}")
                lines.append(f"      From: {item.get('from', 'Unknown')[:40]}")
        lines.append("")

        # SMS Replies
        lines.append("📱 SMS REPLIES")
        lines.append("-" * 40)
        lines.append(f"Total: {digest.sms.total} replies")
        if digest.sms.hot_leads > 0:
            lines.append(f"  🔥 Hot Leads: {digest.sms.hot_leads}")
        if digest.sms.warm_leads > 0:
            lines.append(f"  ☀️  Warm Leads: {digest.sms.warm_leads}")
        if digest.sms.questions > 0:
            lines.append(f"  ❓ Questions: {digest.sms.questions}")
        if digest.sms.callbacks_requested > 0:
            lines.append(f"  📞 Callbacks Requested: {digest.sms.callbacks_requested}")
        if digest.sms.opt_outs > 0:
            lines.append(f"  🚫 Opt-outs: {digest.sms.opt_outs}")

        if digest.sms.action_required:
            lines.append("")
            lines.append("  Action Required:")
            for item in digest.sms.action_required[:3]:
                business = item.get('business', 'Unknown')
                category = item.get('category', 'unknown')
                lines.append(f"    • [{category.upper()}] {business}")
                lines.append(f"      \"{item.get('message', '')[:60]}...\"")
        lines.append("")

        # Form Submissions
        lines.append("📝 FORM SUBMISSIONS")
        lines.append("-" * 40)
        lines.append(f"Total: {digest.forms.total} new inquiries")
        if digest.forms.sources:
            lines.append("  By Source:")
            for source, count in digest.forms.sources.items():
                lines.append(f"    • {source}: {count}")

        if digest.forms.new_inquiries:
            lines.append("")
            lines.append("  New Inquiries:")
            for inquiry in digest.forms.new_inquiries[:3]:
                lines.append(f"    • {inquiry.get('name', 'Unknown')}")
                lines.append(f"      Email: {inquiry.get('email', 'N/A')}")
                lines.append(f"      Source: {inquiry.get('source', 'Unknown')}")
        lines.append("")

        # Today's Calendar
        lines.append("📅 TODAY'S CALENDAR")
        lines.append("-" * 40)
        if digest.calendar.today_events:
            for event in digest.calendar.today_events:
                start_time = event.get('start', '')
                if 'T' in start_time:
                    # Parse datetime
                    try:
                        dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                        start_time = dt.strftime('%I:%M %p')
                    except:
                        pass
                lines.append(f"  • {start_time}: {event.get('summary', 'No Title')}")
                if event.get('location'):
                    lines.append(f"    📍 {event.get('location')}")
        else:
            lines.append("  No events scheduled for today")
        lines.append("")

        # Campaign Metrics
        if digest.campaign.total_contacted > 0:
            lines.append("📊 CAMPAIGN METRICS")
            lines.append("-" * 40)
            lines.append(f"  Total Contacted: {digest.campaign.total_contacted}")
            lines.append(f"  Total Responded: {digest.campaign.total_responded}")
            lines.append(f"  Response Rate: {digest.campaign.response_rate:.1f}%")
            lines.append("")

        # Priority Follow-ups (from followup_prioritizer)
        try:
            import importlib.util
            from pathlib import Path
            repo_root = Path(__file__).resolve().parent.parent.parent.parent
            spec = importlib.util.spec_from_file_location(
                "followup_prioritizer", repo_root / "execution" / "followup_prioritizer.py"
            )
            fp = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(fp)
            priority_list = fp.get_daily_priorities_for_digest()
            if priority_list and "No high-priority" not in priority_list:
                lines.append("=" * 60)
                lines.append("📞 PRIORITY FOLLOW-UPS")
                lines.append("=" * 60)
                lines.append(priority_list)
                lines.append("")
        except Exception as e:
            lines.append(f"[Priority list unavailable: {e}]")
            lines.append("")

        # Action Items
        lines.append("=" * 60)
        lines.append("⚠️  ACTION ITEMS")
        lines.append("=" * 60)
        for action in digest.action_items:
            lines.append(f"  {action}")
        lines.append("")

        # Footer
        lines.append("-" * 60)
        lines.append(f"Generated at {datetime.now().strftime('%I:%M %p')}")
        lines.append("Reply to this email with actions to add to calendar")
        lines.append("-" * 60)

        return "\n".join(lines)

    def format_html_digest(self, digest: DigestData) -> str:
        """
        Format digest as HTML email.

        Args:
            digest: Aggregated digest data

        Returns:
            HTML formatted digest
        """
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
        }}
        .header h1 {{
            margin: 0;
            font-size: 24px;
        }}
        .header p {{
            margin: 5px 0 0;
            opacity: 0.9;
        }}
        .section {{
            background: #f8f9fa;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 15px;
        }}
        .section h2 {{
            margin: 0 0 10px;
            font-size: 16px;
            color: #495057;
        }}
        .metric {{
            display: inline-block;
            background: white;
            padding: 8px 15px;
            border-radius: 5px;
            margin: 3px;
            font-size: 14px;
        }}
        .metric.urgent {{ background: #fee2e2; color: #dc2626; }}
        .metric.hot {{ background: #fef3c7; color: #d97706; }}
        .action-item {{
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 10px 15px;
            margin: 10px 0;
            border-radius: 0 5px 5px 0;
        }}
        .calendar-event {{
            background: white;
            padding: 8px 12px;
            margin: 5px 0;
            border-radius: 5px;
            border-left: 3px solid #667eea;
        }}
        .footer {{
            text-align: center;
            color: #6b7280;
            font-size: 12px;
            margin-top: 20px;
            padding-top: 20px;
            border-top: 1px solid #e5e7eb;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>☀️ Morning Digest</h1>
        <p>{datetime.now().strftime('%A, %B %d, %Y')} | Last {digest.hours_covered} hours</p>
    </div>

    <div class="section">
        <h2>📧 Email Summary ({digest.email.total} total)</h2>
        {"<span class='metric urgent'>🔴 " + str(digest.email.urgent) + " Urgent</span>" if digest.email.urgent else ""}
        {"<span class='metric'>💼 " + str(digest.email.sponsorship) + " Sponsorship</span>" if digest.email.sponsorship else ""}
        {"<span class='metric'>💰 " + str(digest.email.business) + " Business</span>" if digest.email.business else ""}
        {"<span class='metric'>👤 " + str(digest.email.customer) + " Customer</span>" if digest.email.customer else ""}
        {"<span class='metric'>📬 " + str(digest.email.other) + " Other</span>" if digest.email.other else ""}
    </div>

    <div class="section">
        <h2>📱 SMS Replies ({digest.sms.total} total)</h2>
        {"<span class='metric hot'>🔥 " + str(digest.sms.hot_leads) + " Hot Leads</span>" if digest.sms.hot_leads else ""}
        {"<span class='metric'>❓ " + str(digest.sms.questions) + " Questions</span>" if digest.sms.questions else ""}
        {"<span class='metric'>📞 " + str(digest.sms.callbacks_requested) + " Callbacks</span>" if digest.sms.callbacks_requested else ""}
        {"<span class='metric'>🚫 " + str(digest.sms.opt_outs) + " Opt-outs</span>" if digest.sms.opt_outs else ""}
        {("<p>No new replies</p>" if digest.sms.total == 0 else "")}
    </div>

    <div class="section">
        <h2>📝 Form Submissions ({digest.forms.total} total)</h2>
        {"".join([f"<span class='metric'>{source}: {count}</span>" for source, count in digest.forms.sources.items()]) or "<p>No new submissions</p>"}
    </div>

    <div class="section">
        <h2>📅 Today's Calendar ({len(digest.calendar.today_events)} events)</h2>
        {"".join([f'''<div class="calendar-event">
            <strong>{self._format_time(event.get('start', ''))}</strong>: {event.get('summary', 'No Title')}
            {"<br><small>📍 " + event.get('location') + "</small>" if event.get('location') else ""}
        </div>''' for event in digest.calendar.today_events]) or "<p>No events scheduled</p>"}
    </div>

    {"<div class='section'><h2>📊 Campaign Metrics</h2><span class='metric'>Contacted: " + str(digest.campaign.total_contacted) + "</span><span class='metric'>Responded: " + str(digest.campaign.total_responded) + "</span><span class='metric'>Rate: " + f"{digest.campaign.response_rate:.1f}%" + "</span></div>" if digest.campaign.total_contacted > 0 else ""}

    <div class="section" style="background: #fef3c7;">
        <h2>⚠️ Action Items</h2>
        {"".join([f"<div class='action-item'>{action}</div>" for action in digest.action_items])}
    </div>

    <div class="footer">
        <p>Generated at {datetime.now().strftime('%I:%M %p')}</p>
        <p>Reply with actions to add to your calendar</p>
    </div>
</body>
</html>
"""
        return html

    def _format_time(self, iso_time: str) -> str:
        """Format ISO time to readable format."""
        if not iso_time:
            return "All day"
        try:
            if 'T' in iso_time:
                dt = datetime.fromisoformat(iso_time.replace('Z', '+00:00'))
                return dt.strftime('%I:%M %p')
            return iso_time
        except:
            return iso_time

    def send_digest(self, digest: DigestData) -> bool:
        """
        Send digest via SMTP email.

        Args:
            digest: Aggregated digest data

        Returns:
            True if sent successfully
        """
        if not self.smtp_username or not self.smtp_password:
            print("ERROR: SMTP credentials not configured")
            print("Set SMTP_USERNAME and SMTP_PASSWORD environment variables")
            return False

        if not self.recipient_email:
            print("ERROR: Recipient email not configured")
            print("Set NOTIFICATION_EMAIL environment variable")
            return False

        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"☀️ Morning Digest - {datetime.now().strftime('%b %d')}"
            msg["From"] = f"{self.sender_name} <{self.sender_email}>"
            msg["To"] = self.recipient_email

            # Add both text and HTML versions
            text_content = self.format_text_digest(digest)
            html_content = self.format_html_digest(digest)

            msg.attach(MIMEText(text_content, "plain"))
            msg.attach(MIMEText(html_content, "html"))

            # Send
            print(f"Sending digest to {self.recipient_email}...")
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.sendmail(self.sender_email, self.recipient_email, msg.as_string())

            print("✓ Digest sent successfully!")
            return True

        except Exception as e:
            print(f"ERROR sending digest: {e}")
            return False

    def save_digest(self, digest: DigestData, text: str, html: str) -> Path:
        """
        Save digest to file for history.

        Args:
            digest: Digest data
            text: Text version
            html: HTML version

        Returns:
            Path to saved file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"digest_{timestamp}"

        # Save JSON data
        json_path = self.output_dir / f"{filename}.json"
        with open(json_path, 'w') as f:
            from digest_aggregator import DigestAggregator
            aggregator = DigestAggregator()
            json.dump(aggregator.to_dict(digest), f, indent=2)

        # Save HTML
        html_path = self.output_dir / f"{filename}.html"
        with open(html_path, 'w') as f:
            f.write(html)

        print(f"Digest saved to: {self.output_dir}")
        return json_path

    def generate_and_send(self, hours_back: int = 24, preview: bool = False, save: bool = True) -> bool:
        """
        Generate digest and send via email.

        Args:
            hours_back: Hours to look back for data
            preview: If True, preview only without sending
            save: If True, save digest to file

        Returns:
            True if successful
        """
        # Initialize aggregator
        aggregator = DigestAggregator()

        # Authenticate with Google
        print("Authenticating with Google APIs...")
        if not aggregator.authenticate():
            print("Warning: Google auth failed, using local data only")

        # Aggregate data
        digest = aggregator.aggregate(hours_back)

        # Format outputs
        text_content = self.format_text_digest(digest)
        html_content = self.format_html_digest(digest)

        # Save to history
        if save:
            self.save_digest(digest, text_content, html_content)

        # Preview mode
        if preview:
            print("\n" + "=" * 60)
            print("PREVIEW MODE - Email not sent")
            print("=" * 60)
            print(text_content)
            return True

        # Send email
        return self.send_digest(digest)


def main():
    """CLI for morning digest."""
    parser = argparse.ArgumentParser(description='Generate and send morning digest')
    parser.add_argument('--hours', type=int, default=24, help='Hours to look back')
    parser.add_argument('--preview', action='store_true', help='Preview without sending')
    parser.add_argument('--no-save', action='store_true', help='Do not save to history')
    parser.add_argument('--credentials', default='credentials.json', help='Google credentials file')
    parser.add_argument('--token', default='token.json', help='Google token file')

    args = parser.parse_args()

    # Create digest generator
    digest = MorningDigest()

    # Generate and send
    success = digest.generate_and_send(
        hours_back=args.hours,
        preview=args.preview,
        save=not args.no_save
    )

    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
