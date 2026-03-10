"""
HVAC Email Receiver

Polls for quote responses via IMAP or processes webhook callbacks.
Parses quote emails and stores them in the database.

This validates the async nature of EMAIL connectivity - responses
take 24-48 hours, not milliseconds like HTTP REST APIs.
"""

import os
import re
import imaplib
import email
from email.header import decode_header
import logging
from datetime import datetime, date, timedelta
from decimal import Decimal, InvalidOperation
from typing import List, Optional, Dict, Any, Tuple
import uuid

from models import Quote, RFQ
from quote_tracker import QuoteTracker, get_quote_tracker
from distributor_db import DistributorDB, get_distributor_db

logger = logging.getLogger(__name__)


class EmailReceiver:
    """
    Receive and parse quote emails from distributors.

    Two modes:
    1. IMAP polling: Check inbox periodically for replies
    2. Webhook: Receive parsed emails from SendGrid/Mailgun (future)

    For MVP, uses mock mode that simulates received emails.

    Configuration via environment variables:
    - IMAP_HOST: IMAP server hostname
    - IMAP_PORT: IMAP server port (default: 993)
    - IMAP_USER: IMAP username
    - IMAP_PASS: IMAP password
    - HVAC_MOCK_EMAIL: Set to 'true' for testing without IMAP
    """

    def __init__(
        self,
        imap_host: Optional[str] = None,
        imap_port: int = 993,
        imap_user: Optional[str] = None,
        imap_pass: Optional[str] = None,
        mock_mode: Optional[bool] = None,
        quote_tracker: Optional[QuoteTracker] = None,
        distributor_db: Optional[DistributorDB] = None
    ):
        self.imap_host = imap_host or os.environ.get('IMAP_HOST', 'imap.example.com')
        self.imap_port = imap_port or int(os.environ.get('IMAP_PORT', '993'))
        self.imap_user = imap_user or os.environ.get('IMAP_USER', '')
        self.imap_pass = imap_pass or os.environ.get('IMAP_PASS', '')

        # Mock mode for testing without actual IMAP
        if mock_mode is not None:
            self.mock_mode = mock_mode
        else:
            self.mock_mode = os.environ.get('HVAC_MOCK_EMAIL', 'true').lower() == 'true'

        self.quote_tracker = quote_tracker or get_quote_tracker()
        self.distributor_db = distributor_db or get_distributor_db()

        # Store mock emails for testing
        self.mock_inbox: List[Dict[str, Any]] = []

    def poll_for_quotes(self, since: Optional[datetime] = None) -> List[Quote]:
        """
        Poll inbox for new quote responses.

        Filters for:
        - Subject containing "RE: RFQ #" or similar patterns
        - In-Reply-To header matching sent RFQ message IDs
        - From addresses matching known distributors

        Args:
            since: Only check emails after this time (default: last 48 hours)

        Returns:
            List of parsed and stored quotes
        """
        if since is None:
            since = datetime.now() - timedelta(hours=48)

        if self.mock_mode:
            return self._mock_poll(since)
        else:
            return self._imap_poll(since)

    def _mock_poll(self, since: datetime) -> List[Quote]:
        """
        Poll mock inbox for testing.

        Process any mock emails that haven't been processed yet.
        """
        quotes = []

        for mock_email in self.mock_inbox:
            if mock_email.get('processed'):
                continue

            if mock_email.get('received_at', datetime.now()) < since:
                continue

            try:
                quote = self._parse_quote_email(
                    subject=mock_email.get('subject', ''),
                    body=mock_email.get('body', ''),
                    from_address=mock_email.get('from', ''),
                    in_reply_to=mock_email.get('in_reply_to'),
                    raw_content=mock_email.get('raw', '')
                )

                if quote:
                    self.quote_tracker.add_quote(quote)
                    quotes.append(quote)
                    mock_email['processed'] = True
                    logger.info(f"Processed mock quote for RFQ {quote.rfq_id}")

            except Exception as e:
                logger.error(f"Failed to process mock email: {e}")

        return quotes

    def _imap_poll(self, since: datetime) -> List[Quote]:
        """
        Poll IMAP inbox for quote emails.

        Production implementation for actual email infrastructure.
        """
        quotes = []

        try:
            # Connect to IMAP
            mail = imaplib.IMAP4_SSL(self.imap_host, self.imap_port)
            mail.login(self.imap_user, self.imap_pass)
            mail.select('INBOX')

            # Search for RFQ replies
            # Search criteria: Subject contains "RFQ" and received after since date
            date_str = since.strftime('%d-%b-%Y')
            _, message_ids = mail.search(None, f'(SINCE "{date_str}" SUBJECT "RFQ")')

            for msg_id in message_ids[0].split():
                try:
                    _, msg_data = mail.fetch(msg_id, '(RFC822)')
                    email_body = msg_data[0][1]
                    msg = email.message_from_bytes(email_body)

                    # Extract email components
                    subject = self._decode_header(msg['Subject'])
                    from_addr = self._decode_header(msg['From'])
                    in_reply_to = msg.get('In-Reply-To', '')

                    # Get body
                    body = self._get_email_body(msg)

                    # Parse and store quote
                    quote = self._parse_quote_email(
                        subject=subject,
                        body=body,
                        from_address=from_addr,
                        in_reply_to=in_reply_to,
                        raw_content=body
                    )

                    if quote:
                        self.quote_tracker.add_quote(quote)
                        quotes.append(quote)
                        logger.info(f"Processed quote from {from_addr} for RFQ {quote.rfq_id}")

                except Exception as e:
                    logger.error(f"Failed to process email {msg_id}: {e}")

            mail.logout()

        except imaplib.IMAP4.error as e:
            logger.error(f"IMAP connection failed: {e}")

        return quotes

    def _parse_quote_email(
        self,
        subject: str,
        body: str,
        from_address: str,
        in_reply_to: Optional[str] = None,
        raw_content: str = ""
    ) -> Optional[Quote]:
        """
        Parse a quote email and extract pricing information.

        Attempts to extract:
        - RFQ ID (from subject or In-Reply-To)
        - Unit price
        - Quantity available
        - Lead time
        - Shipping cost

        Uses regex patterns and heuristics for parsing.
        """
        # Extract RFQ ID
        rfq_id = self._extract_rfq_id(subject, body, in_reply_to)
        if not rfq_id:
            logger.warning(f"Could not extract RFQ ID from email: {subject}")
            return None

        # Verify RFQ exists
        rfq = self.quote_tracker.get_rfq(rfq_id)
        if not rfq:
            logger.warning(f"RFQ {rfq_id} not found in database")
            return None

        # Get distributor info
        distributor = self.distributor_db.get_distributor(rfq.distributor_id)
        distributor_name = distributor.name if distributor else "Unknown Distributor"

        # Extract pricing info from body
        unit_price = self._extract_price(body)
        quantity = self._extract_quantity(body)
        lead_time = self._extract_lead_time(body)
        shipping = self._extract_shipping(body)
        model = self._extract_model(body)
        brand = self._extract_brand(body)
        valid_until = self._extract_valid_until(body)

        if unit_price is None:
            logger.warning(f"Could not extract price from email for RFQ {rfq_id}")
            return None

        # Create quote
        quote = Quote(
            id=str(uuid.uuid4())[:8],
            rfq_id=rfq_id,
            distributor_id=rfq.distributor_id,
            distributor_name=distributor_name,
            equipment_model=model or "See email for details",
            brand=brand or "Unknown",
            unit_price=unit_price,
            quantity_available=quantity or 1,
            lead_time_days=lead_time or 7,
            shipping_cost=shipping or Decimal('0'),
            valid_until=valid_until,
            raw_email_content=raw_content
        )

        return quote

    def _extract_rfq_id(
        self,
        subject: str,
        body: str,
        in_reply_to: Optional[str]
    ) -> Optional[str]:
        """Extract RFQ ID from email"""
        # Try In-Reply-To header first (most reliable)
        if in_reply_to:
            match = re.search(r'rfq-([a-f0-9-]+)@', in_reply_to)
            if match:
                return match.group(1)

        # Try subject line
        match = re.search(r'RFQ\s*#?\s*([a-f0-9-]+)', subject, re.IGNORECASE)
        if match:
            return match.group(1)

        # Try body
        match = re.search(r'RFQ\s*(?:ID|Reference|#)?\s*:?\s*([a-f0-9-]+)', body, re.IGNORECASE)
        if match:
            return match.group(1)

        return None

    def _extract_price(self, body: str) -> Optional[Decimal]:
        """Extract unit price from email body"""
        # Common patterns:
        # $1,234.56
        # Unit Price: $1234.56
        # Price per unit: $1,234
        # Each: $1234.56
        patterns = [
            r'(?:unit\s*price|price\s*per\s*unit|each|per\s*unit)[\s:]*\$?([\d,]+\.?\d*)',
            r'\$\s*([\d,]+\.?\d*)\s*(?:per\s*unit|each|/unit)',
            r'price[\s:]*\$?([\d,]+\.?\d*)',
            r'\$([\d,]+\.?\d*)'  # Fallback: any dollar amount
        ]

        for pattern in patterns:
            match = re.search(pattern, body, re.IGNORECASE)
            if match:
                try:
                    price_str = match.group(1).replace(',', '')
                    return Decimal(price_str)
                except (InvalidOperation, ValueError):
                    continue

        return None

    def _extract_quantity(self, body: str) -> Optional[int]:
        """Extract quantity available from email body"""
        patterns = [
            r'(?:quantity|qty|stock|available|in\s*stock)[\s:]*(\d+)',
            r'(\d+)\s*(?:units?|available|in\s*stock)',
        ]

        for pattern in patterns:
            match = re.search(pattern, body, re.IGNORECASE)
            if match:
                try:
                    return int(match.group(1))
                except ValueError:
                    continue

        return None

    def _extract_lead_time(self, body: str) -> Optional[int]:
        """Extract lead time (days) from email body"""
        patterns = [
            r'(?:lead\s*time|delivery|ship)[\s:]*(\d+)\s*(?:day|business)',
            r'(\d+)\s*(?:day|business)\s*(?:lead|delivery)',
            r'(?:within|in)\s*(\d+)\s*(?:day|business)',
            r'(\d+)-(\d+)\s*(?:day|business)',  # Range: 5-7 days
        ]

        for pattern in patterns:
            match = re.search(pattern, body, re.IGNORECASE)
            if match:
                try:
                    # If range, take the higher number
                    if len(match.groups()) > 1 and match.group(2):
                        return int(match.group(2))
                    return int(match.group(1))
                except ValueError:
                    continue

        return None

    def _extract_shipping(self, body: str) -> Optional[Decimal]:
        """Extract shipping cost from email body"""
        patterns = [
            r'(?:shipping|freight|delivery\s*cost)[\s:]*\$?([\d,]+\.?\d*)',
            r'\$([\d,]+\.?\d*)\s*(?:shipping|freight)',
        ]

        for pattern in patterns:
            match = re.search(pattern, body, re.IGNORECASE)
            if match:
                try:
                    price_str = match.group(1).replace(',', '')
                    return Decimal(price_str)
                except (InvalidOperation, ValueError):
                    continue

        return None

    def _extract_model(self, body: str) -> Optional[str]:
        """Extract equipment model from email body"""
        patterns = [
            r'(?:model|part\s*(?:number|#))[\s:]*([A-Z0-9][\w-]+)',
            r'([A-Z]{2,}[\d][\w-]+)',  # Common model format: XX123-456
        ]

        for pattern in patterns:
            match = re.search(pattern, body, re.IGNORECASE)
            if match:
                return match.group(1)

        return None

    def _extract_brand(self, body: str) -> Optional[str]:
        """Extract brand from email body"""
        known_brands = [
            'Carrier', 'Trane', 'Lennox', 'Rheem', 'Goodman',
            'Bryant', 'American Standard', 'Amana', 'Ruud',
            'Mitsubishi', 'Daikin', 'Fujitsu', 'LG', 'Samsung'
        ]

        body_lower = body.lower()
        for brand in known_brands:
            if brand.lower() in body_lower:
                return brand

        return None

    def _extract_valid_until(self, body: str) -> Optional[date]:
        """Extract quote validity date from email body"""
        patterns = [
            r'(?:valid|expires?|good)\s*(?:until|through|thru)[\s:]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\s*(?:expir|valid)',
        ]

        for pattern in patterns:
            match = re.search(pattern, body, re.IGNORECASE)
            if match:
                try:
                    date_str = match.group(1)
                    # Try common date formats
                    for fmt in ['%m/%d/%Y', '%m-%d-%Y', '%m/%d/%y', '%m-%d-%y']:
                        try:
                            return datetime.strptime(date_str, fmt).date()
                        except ValueError:
                            continue
                except Exception:
                    continue

        # Default: 30 days from now
        return (datetime.now() + timedelta(days=30)).date()

    def _decode_header(self, header_value: str) -> str:
        """Decode email header value"""
        if not header_value:
            return ""

        decoded_parts = decode_header(header_value)
        result = []
        for part, encoding in decoded_parts:
            if isinstance(part, bytes):
                result.append(part.decode(encoding or 'utf-8', errors='replace'))
            else:
                result.append(part)
        return ''.join(result)

    def _get_email_body(self, msg: email.message.Message) -> str:
        """Extract body text from email message"""
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type == 'text/plain':
                    payload = part.get_payload(decode=True)
                    if payload:
                        return payload.decode('utf-8', errors='replace')
        else:
            payload = msg.get_payload(decode=True)
            if payload:
                return payload.decode('utf-8', errors='replace')
        return ""

    def add_mock_email(
        self,
        rfq_id: str,
        from_address: str,
        body: str,
        subject: Optional[str] = None
    ) -> None:
        """
        Add a mock email to the inbox for testing.

        Args:
            rfq_id: RFQ this email replies to
            from_address: Sender email address
            body: Email body content
            subject: Email subject (auto-generated if not provided)
        """
        if subject is None:
            subject = f"RE: RFQ #{rfq_id}: Quote Response"

        self.mock_inbox.append({
            'subject': subject,
            'from': from_address,
            'body': body,
            'in_reply_to': f"<rfq-{rfq_id}@hvac-mcp.example.com>",
            'received_at': datetime.now(),
            'raw': body,
            'processed': False
        })

        logger.info(f"Added mock email for RFQ {rfq_id}")

    def clear_mock_inbox(self) -> None:
        """Clear mock inbox"""
        self.mock_inbox.clear()


# Singleton instance
_receiver_instance: Optional[EmailReceiver] = None


def get_email_receiver() -> EmailReceiver:
    """Get the singleton EmailReceiver instance"""
    global _receiver_instance
    if _receiver_instance is None:
        _receiver_instance = EmailReceiver()
    return _receiver_instance
