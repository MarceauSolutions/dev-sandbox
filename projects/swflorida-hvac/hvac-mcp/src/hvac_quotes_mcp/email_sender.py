"""
HVAC Email Sender

Sends RFQ emails to HVAC distributors via SMTP.
This validates the platform's EMAIL connectivity type - no HTTP REST API.

For testing without actual email infrastructure, includes a mock mode
that logs emails instead of sending them.
"""

import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Optional, List

from .models import RFQ, Distributor

logger = logging.getLogger(__name__)


class EmailSender:
    """
    SMTP email sender for HVAC RFQs.

    Validates EMAIL connectivity type by sending RFQs via SMTP
    instead of HTTP REST API calls.

    Configuration via environment variables:
    - SMTP_HOST: SMTP server hostname
    - SMTP_PORT: SMTP server port (default: 587)
    - SMTP_USER: SMTP username
    - SMTP_PASS: SMTP password
    - SMTP_FROM: From email address
    - HVAC_MOCK_EMAIL: Set to 'true' for testing without SMTP
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
        self.from_address = from_address or os.environ.get('SMTP_FROM', 'rfq@hvac-mcp.example.com')

        # Mock mode for testing without actual SMTP
        if mock_mode is not None:
            self.mock_mode = mock_mode
        else:
            self.mock_mode = os.environ.get('HVAC_MOCK_EMAIL', 'true').lower() == 'true'

        # Store sent emails in mock mode for verification
        self.sent_emails: List[dict] = []

    def send_rfq(self, rfq: RFQ, distributor: Distributor) -> str:
        """
        Send RFQ email to distributor.

        Args:
            rfq: The RFQ to send
            distributor: Target distributor

        Returns:
            Message ID for tracking responses

        Raises:
            EmailSendError: If email fails to send
        """
        # Generate message ID
        message_id = f"<rfq-{rfq.id}@hvac-mcp.example.com>"

        # Build email
        subject = self._format_subject(rfq)
        body = self._format_body(rfq, distributor)

        if self.mock_mode:
            return self._mock_send(rfq, distributor, subject, body, message_id)
        else:
            return self._smtp_send(rfq, distributor, subject, body, message_id)

    def _format_subject(self, rfq: RFQ) -> str:
        """Format email subject line"""
        equipment = rfq.equipment_type.replace('_', ' ').title()
        return f"RFQ #{rfq.id}: {equipment} Quote Request"

    def _format_body(self, rfq: RFQ, distributor: Distributor) -> str:
        """Format email body with RFQ details"""
        specs = rfq.specifications
        equipment = rfq.equipment_type.replace('_', ' ').title()

        body_parts = [
            f"Dear {distributor.contact_name or 'Sales Team'},",
            "",
            f"We are requesting a quote for the following HVAC equipment:",
            "",
            "=" * 50,
            f"RFQ ID: {rfq.id}",
            f"Equipment Type: {equipment}",
            f"Quantity: {rfq.quantity}",
            "=" * 50,
            "",
            "SPECIFICATIONS:",
            "-" * 30,
        ]

        # Add specifications
        if specs.tonnage:
            body_parts.append(f"  Tonnage: {specs.tonnage} tons")
        if specs.seer:
            body_parts.append(f"  SEER Rating: {specs.seer}")
        if specs.btu:
            body_parts.append(f"  BTU: {specs.btu:,}")
        if specs.voltage:
            body_parts.append(f"  Voltage: {specs.voltage}")
        if specs.phase:
            body_parts.append(f"  Phase: {specs.phase}")
        if specs.refrigerant:
            body_parts.append(f"  Refrigerant: {specs.refrigerant}")
        if specs.model_preference:
            body_parts.append(f"  Model Preference: {specs.model_preference}")
        if specs.additional_notes:
            body_parts.append(f"  Notes: {specs.additional_notes}")

        body_parts.extend([
            "",
            "DELIVERY INFORMATION:",
            "-" * 30,
            f"  Delivery Address: {rfq.delivery_address}",
        ])

        if rfq.brand_preference:
            body_parts.append(f"  Brand Preference: {rfq.brand_preference}")

        if rfq.needed_by_date:
            body_parts.append(f"  Needed By: {rfq.needed_by_date.strftime('%B %d, %Y')}")

        body_parts.extend([
            "",
            "Please reply to this email with your quote including:",
            "  - Unit price",
            "  - Availability / quantity in stock",
            "  - Lead time for delivery",
            "  - Shipping cost to delivery address",
            "  - Quote validity period",
            "",
            "Please include the RFQ ID in your response for tracking.",
            "",
            "Thank you for your prompt attention to this request.",
            "",
            "Best regards,",
            "HVAC Contractor Network",
            "",
            "-" * 50,
            "This is an automated RFQ from the HVAC MCP Aggregator.",
            f"RFQ Reference: {rfq.id}",
            "-" * 50,
        ])

        return "\n".join(body_parts)

    def _mock_send(
        self,
        rfq: RFQ,
        distributor: Distributor,
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
            'rfq_id': rfq.id,
            'to': distributor.email_address,
            'from': self.from_address,
            'subject': subject,
            'body': body,
            'distributor_id': distributor.id,
            'distributor_name': distributor.name,
            'sent_at': datetime.now().isoformat(),
            'mock': True
        }

        self.sent_emails.append(email_record)

        logger.info(
            f"[MOCK] RFQ email sent to {distributor.name} ({distributor.email_address})\n"
            f"  Subject: {subject}\n"
            f"  Message-ID: {message_id}"
        )

        return message_id

    def _smtp_send(
        self,
        rfq: RFQ,
        distributor: Distributor,
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
        msg['To'] = distributor.email_address
        msg['Subject'] = subject
        msg['Message-ID'] = message_id

        # Custom headers for tracking
        msg['X-RFQ-ID'] = rfq.id
        msg['X-Distributor-ID'] = distributor.id
        msg['X-Equipment-Type'] = rfq.equipment_type

        # Add body
        msg.attach(MIMEText(body, 'plain'))

        try:
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                if self.smtp_user and self.smtp_pass:
                    server.login(self.smtp_user, self.smtp_pass)
                server.send_message(msg)

            logger.info(
                f"RFQ email sent to {distributor.name} ({distributor.email_address})\n"
                f"  Subject: {subject}\n"
                f"  Message-ID: {message_id}"
            )

            return message_id

        except smtplib.SMTPException as e:
            logger.error(f"Failed to send RFQ email: {e}")
            raise EmailSendError(f"Failed to send email to {distributor.email_address}: {e}")

    def get_sent_emails(self) -> List[dict]:
        """Get list of sent emails (mock mode only)"""
        return self.sent_emails.copy()

    def clear_sent_emails(self) -> None:
        """Clear sent email history (mock mode only)"""
        self.sent_emails.clear()


class EmailSendError(Exception):
    """Raised when email sending fails"""
    pass


# Singleton instance
_sender_instance: Optional[EmailSender] = None


def get_email_sender() -> EmailSender:
    """Get the singleton EmailSender instance"""
    global _sender_instance
    if _sender_instance is None:
        _sender_instance = EmailSender()
    return _sender_instance
