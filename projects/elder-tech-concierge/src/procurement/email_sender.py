"""
Elder Tech Procurement - Email Sender

Sends price inquiry emails to device wholesalers via SMTP.
Based on the HVAC email_sender.py pattern.

For testing without actual email infrastructure, includes a mock mode
that logs emails instead of sending them.
"""

import os
import smtplib
import logging
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Optional, List

from models import PriceInquiry, Wholesaler, DeviceSpecifications

logger = logging.getLogger(__name__)


class EmailSender:
    """
    SMTP email sender for device procurement inquiries.

    Sends price inquiries to wholesalers via email.

    Configuration via environment variables:
    - SMTP_HOST: SMTP server hostname
    - SMTP_PORT: SMTP server port (default: 587)
    - SMTP_USER: SMTP username
    - SMTP_PASS: SMTP password
    - SMTP_FROM: From email address
    - PROCUREMENT_MOCK_EMAIL: Set to 'true' for testing without SMTP
    """

    def __init__(
        self,
        smtp_host: Optional[str] = None,
        smtp_port: int = 587,
        smtp_user: Optional[str] = None,
        smtp_pass: Optional[str] = None,
        from_address: Optional[str] = None,
        mock_mode: Optional[bool] = None
    ):
        self.smtp_host = smtp_host or os.environ.get('SMTP_HOST', 'smtp.example.com')
        self.smtp_port = smtp_port or int(os.environ.get('SMTP_PORT', '587'))
        self.smtp_user = smtp_user or os.environ.get('SMTP_USER', '')
        self.smtp_pass = smtp_pass or os.environ.get('SMTP_PASS', '')
        self.from_address = from_address or os.environ.get('SMTP_FROM', 'procurement@eldertech.example.com')

        # Mock mode for testing without actual SMTP
        if mock_mode is not None:
            self.mock_mode = mock_mode
        else:
            self.mock_mode = os.environ.get('PROCUREMENT_MOCK_EMAIL', 'true').lower() == 'true'

        # Store sent emails in mock mode for verification
        self.sent_emails: List[dict] = []

    def send_inquiry(self, inquiry: PriceInquiry, wholesaler: Wholesaler) -> str:
        """
        Send price inquiry email to wholesaler.

        Args:
            inquiry: The price inquiry to send
            wholesaler: Target wholesaler

        Returns:
            Message ID for tracking responses

        Raises:
            EmailSendError: If email fails to send
            NoEmailError: If wholesaler has no email address
        """
        if not wholesaler.email_address:
            raise NoEmailError(
                f"Wholesaler {wholesaler.name} has no email address. "
                f"Use contact form at: {wholesaler.contact_form_url}"
            )

        # Generate message ID
        message_id = f"<inquiry-{inquiry.id}@eldertech.example.com>"

        # Build email
        subject = self._format_subject(inquiry)
        body = self._format_body(inquiry, wholesaler)

        if self.mock_mode:
            return self._mock_send(inquiry, wholesaler, subject, body, message_id)
        else:
            return self._smtp_send(inquiry, wholesaler, subject, body, message_id)

    def _format_subject(self, inquiry: PriceInquiry) -> str:
        """Format email subject line"""
        device = inquiry.device_type.replace('_', ' ').title()
        qty = f"x{inquiry.quantity}" if inquiry.quantity > 1 else ""
        return f"Bulk Pricing Inquiry #{inquiry.id}: {device} {qty}"

    def _format_body(self, inquiry: PriceInquiry, wholesaler: Wholesaler) -> str:
        """Format email body with inquiry details"""
        specs = inquiry.specifications
        device = inquiry.device_type.replace('_', ' ').title()

        body_parts = [
            f"Dear {wholesaler.contact_name or 'Sales Team'},",
            "",
            "We are a tech services company setting up tablet devices for elderly clients.",
            "We are requesting bulk pricing information for the following devices:",
            "",
            "=" * 60,
            f"Inquiry Reference: {inquiry.id}",
            f"Device Type: {device}",
            f"Quantity Needed: {inquiry.quantity}",
            "=" * 60,
            "",
            "SPECIFICATIONS:",
            "-" * 40,
        ]

        # Add specifications
        if specs.model:
            body_parts.append(f"  Model: {specs.model}")
        if specs.storage_gb:
            body_parts.append(f"  Storage: {specs.storage_gb}GB")
        if specs.color:
            body_parts.append(f"  Color Preference: {specs.color}")
        if specs.connectivity:
            conn = "WiFi + Cellular" if specs.connectivity == 'wifi_cellular' else "WiFi Only"
            body_parts.append(f"  Connectivity: {conn}")

        body_parts.append(f"  Condition: {specs.condition.replace('_', ' ').title()}")

        if specs.accessories_needed:
            body_parts.append(f"  Accessories Needed: {', '.join(specs.accessories_needed)}")

        if specs.additional_notes:
            body_parts.append(f"  Notes: {specs.additional_notes}")

        body_parts.extend([
            "",
            "DELIVERY INFORMATION:",
            "-" * 40,
        ])

        if inquiry.ship_to_address:
            body_parts.append(f"  Ship To: {inquiry.ship_to_address}")

        if inquiry.needed_by_date:
            body_parts.append(f"  Needed By: {inquiry.needed_by_date.strftime('%B %d, %Y')}")

        # Get sender details from environment
        sender_name = os.environ.get('SENDER_NAME', 'William Marceau')
        company_name = os.environ.get('COMPANY_NAME', 'Marceau Solutions')

        body_parts.extend([
            "",
            "PLEASE PROVIDE:",
            "-" * 40,
            "  - Unit price (bulk pricing if available)",
            "  - Quantity in stock / availability",
            "  - Lead time for delivery",
            "  - Shipping cost to delivery address",
            "  - Warranty terms",
            "  - Quote validity period",
            "",
            "ABOUT OUR BUSINESS:",
            "-" * 40,
            "  We deploy pre-configured tablets to elderly clients as part of",
            "  a tech assistance service. We expect ongoing orders of 5-20 units",
            "  per month as our business grows.",
            "",
            "Please include the Inquiry Reference in your response for tracking.",
            "",
            "Thank you for your prompt attention to this request.",
            "",
            "Best regards,",
            f"{sender_name}",
            f"{company_name}",
            "wmarceau@marceausolutions.com",
            "",
            f"Inquiry Reference: {inquiry.id}",
        ])

        return "\n".join(body_parts)

    def _mock_send(
        self,
        inquiry: PriceInquiry,
        wholesaler: Wholesaler,
        subject: str,
        body: str,
        message_id: str
    ) -> str:
        """
        Mock email sending for testing.

        Logs the email and stores it for verification.
        """
        email_record = {
            'message_id': message_id,
            'inquiry_id': inquiry.id,
            'to': wholesaler.email_address,
            'from': self.from_address,
            'subject': subject,
            'body': body,
            'wholesaler_id': wholesaler.id,
            'wholesaler_name': wholesaler.name,
            'sent_at': datetime.now().isoformat(),
            'mock': True
        }

        self.sent_emails.append(email_record)

        logger.info(
            f"[MOCK] Inquiry email sent to {wholesaler.name} ({wholesaler.email_address})\n"
            f"  Subject: {subject}\n"
            f"  Message-ID: {message_id}"
        )

        # Also print to console for visibility during testing
        print(f"\n{'='*60}")
        print(f"[MOCK EMAIL] To: {wholesaler.email_address}")
        print(f"Subject: {subject}")
        print(f"{'='*60}")
        print(body[:500] + "..." if len(body) > 500 else body)
        print(f"{'='*60}\n")

        return message_id

    def _smtp_send(
        self,
        inquiry: PriceInquiry,
        wholesaler: Wholesaler,
        subject: str,
        body: str,
        message_id: str
    ) -> str:
        """
        Send email via SMTP.

        For production use with actual email infrastructure.
        """
        msg = MIMEMultipart()
        msg['From'] = self.from_address
        msg['To'] = wholesaler.email_address
        msg['Subject'] = subject
        msg['Message-ID'] = message_id

        # Custom headers for tracking
        msg['X-Inquiry-ID'] = inquiry.id
        msg['X-Wholesaler-ID'] = wholesaler.id
        msg['X-Device-Type'] = inquiry.device_type

        # Add body
        msg.attach(MIMEText(body, 'plain'))

        try:
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                if self.smtp_user and self.smtp_pass:
                    server.login(self.smtp_user, self.smtp_pass)
                server.send_message(msg)

            logger.info(
                f"Inquiry email sent to {wholesaler.name} ({wholesaler.email_address})\n"
                f"  Subject: {subject}\n"
                f"  Message-ID: {message_id}"
            )

            # Register for response tracking
            self._register_for_tracking(inquiry, wholesaler, subject)

            return message_id

        except smtplib.SMTPException as e:
            logger.error(f"Failed to send inquiry email: {e}")
            raise EmailSendError(f"Failed to send email to {wholesaler.email_address}: {e}")

    def _register_for_tracking(
        self,
        inquiry: PriceInquiry,
        wholesaler: Wholesaler,
        subject: str
    ) -> None:
        """Register outreach email for response monitoring."""
        try:
            # Import monitor (lazy load to avoid circular imports)
            import sys
            sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / 'execution'))
            from email_response_monitor import EmailResponseMonitor

            monitor = EmailResponseMonitor()
            monitor.register_outreach(
                inquiry_id=inquiry.id,
                project='elder-tech',
                recipient_email=wholesaler.email_address,
                recipient_name=wholesaler.contact_name or wholesaler.name,
                subject=subject,
                inquiry_type='bulk_pricing',
                metadata={
                    'wholesaler_id': wholesaler.id,
                    'device_type': inquiry.device_type,
                    'quantity': inquiry.quantity,
                }
            )
            logger.info(f"Registered inquiry {inquiry.id} for response tracking")
        except Exception as e:
            # Don't fail the email send if tracking registration fails
            logger.warning(f"Failed to register for tracking: {e}")

    def generate_contact_form_text(self, inquiry: PriceInquiry, wholesaler: Wholesaler) -> str:
        """
        Generate text suitable for pasting into a contact form.

        Use when wholesaler doesn't have direct email.

        Args:
            inquiry: The price inquiry
            wholesaler: Target wholesaler

        Returns:
            Formatted text for contact form
        """
        specs = inquiry.specifications
        device = inquiry.device_type.replace('_', ' ').title()

        text_parts = [
            f"BULK PRICING INQUIRY - Reference: {inquiry.id}",
            "",
            f"We are requesting pricing for {inquiry.quantity}x {device}",
            "",
            "Specifications:",
        ]

        if specs.model:
            text_parts.append(f"- Model: {specs.model}")
        if specs.storage_gb:
            text_parts.append(f"- Storage: {specs.storage_gb}GB")
        if specs.connectivity:
            text_parts.append(f"- Connectivity: {specs.connectivity}")
        text_parts.append(f"- Condition: {specs.condition}")

        text_parts.extend([
            "",
            "We are a tech services company deploying tablets to elderly clients.",
            "We expect ongoing orders of 5-20 units/month.",
            "",
            "Please provide:",
            "- Unit price (bulk pricing if available)",
            "- Availability / lead time",
            "- Shipping cost",
            "- Warranty terms",
            "",
            f"Please reference inquiry #{inquiry.id} in your response.",
            "",
            "Thank you!"
        ])

        return "\n".join(text_parts)

    def get_sent_emails(self) -> List[dict]:
        """Get list of sent emails (mock mode only)"""
        return self.sent_emails.copy()

    def clear_sent_emails(self) -> None:
        """Clear sent email history (mock mode only)"""
        self.sent_emails.clear()


class EmailSendError(Exception):
    """Raised when email sending fails"""
    pass


class NoEmailError(Exception):
    """Raised when wholesaler has no email address"""
    pass


# Singleton instance
_sender_instance: Optional[EmailSender] = None


def get_email_sender() -> EmailSender:
    """Get the singleton EmailSender instance"""
    global _sender_instance
    if _sender_instance is None:
        _sender_instance = EmailSender()
    return _sender_instance


# CLI for testing
if __name__ == '__main__':
    from wholesaler_db import get_wholesaler_db
    from models import DeviceSpecifications, PriceInquiry
    import uuid

    print("Elder Tech Procurement - Email Sender Test\n")

    # Create test inquiry
    specs = DeviceSpecifications(
        model='iPad 11th Generation',
        storage_gb=64,
        color='Space Gray',
        connectivity='wifi',
        condition='new',
        accessories_needed=['case', 'charger']
    )

    inquiry = PriceInquiry(
        id=str(uuid.uuid4())[:8],
        requester_id='eldertech-001',
        wholesaler_id='wesellcellular',
        device_type='ipad',
        specifications=specs,
        quantity=5,
        ship_to_address='Naples, FL 34102'
    )

    # Get wholesaler
    db = get_wholesaler_db()
    wholesaler = db.get_wholesaler('wesellcellular')

    if wholesaler:
        print(f"Sending test inquiry to: {wholesaler.name}")
        print(f"Email: {wholesaler.email_address}")
        print()

        sender = EmailSender(mock_mode=True)
        message_id = sender.send_inquiry(inquiry, wholesaler)

        print(f"\nMessage ID: {message_id}")

    # Also test contact form generation for wholesaler without email
    print("\n" + "="*60)
    print("CONTACT FORM TEXT (for wholesalers without email):")
    print("="*60)

    todays_closeout = db.get_wholesaler('todays-closeout')
    if todays_closeout:
        sender = EmailSender()
        form_text = sender.generate_contact_form_text(inquiry, todays_closeout)
        print(f"\nFor: {todays_closeout.name}")
        print(f"Contact Form: {todays_closeout.contact_form_url}")
        print("\nText to paste:")
        print("-"*40)
        print(form_text)
