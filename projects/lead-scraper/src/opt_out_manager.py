#!/usr/bin/env python3
"""
Opt-Out Management System for Lead Scraper

Centralizes all opt-out handling for SMS and Email campaigns:
1. Maintains opt_out_list.json with suppressed numbers/emails
2. Parses common opt-out phrases from SMS replies
3. Handles email bounces and unsubscribe requests
4. Integrates with sms_campaigns.json to mark opted-out contacts
5. Provides lookup methods to check before sending

Usage:
    # Check if a contact is opted out
    python -m src.opt_out_manager check --phone "+12395551234"
    python -m src.opt_out_manager check --email "test@example.com"

    # Add contact to opt-out list
    python -m src.opt_out_manager add --phone "+12395551234" --reason "SMS STOP"
    python -m src.opt_out_manager add --email "test@example.com" --reason "email_bounce"

    # Process SMS replies for opt-outs
    python -m src.opt_out_manager process-replies

    # Sync opt-outs to campaigns
    python -m src.opt_out_manager sync-campaigns

    # Show statistics
    python -m src.opt_out_manager stats

    # Export opt-out list
    python -m src.opt_out_manager export --format csv
"""

import json
import re
import logging
from datetime import datetime
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional, List, Dict, Any, Set, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


# =============================================================================
# Opt-Out Phrase Detection
# =============================================================================

class OptOutReason(Enum):
    """Reasons for opt-out."""
    SMS_STOP = "sms_stop"                    # Reply with STOP keyword
    SMS_UNSUBSCRIBE = "sms_unsubscribe"      # Reply with unsubscribe request
    EMAIL_BOUNCE = "email_bounce"             # Hard bounce
    EMAIL_UNSUBSCRIBE = "email_unsubscribe"   # Clicked unsubscribe link
    EMAIL_COMPLAINT = "email_complaint"       # Marked as spam
    MANUAL = "manual"                         # Manually added
    DNC_LIST = "dnc_list"                     # Do Not Call list
    LEGAL_REQUEST = "legal_request"           # Legal/compliance request
    INVALID_NUMBER = "invalid_number"         # Invalid phone number
    INVALID_EMAIL = "invalid_email"           # Invalid email address


# Common opt-out phrases (case-insensitive)
# Ranked by specificity - more specific patterns first
OPT_OUT_PATTERNS = [
    # Explicit stop/unsubscribe keywords
    (r'\bstop\b', OptOutReason.SMS_STOP),
    (r'\bunsubscribe\b', OptOutReason.SMS_UNSUBSCRIBE),
    (r'\bremove\s*me\b', OptOutReason.SMS_UNSUBSCRIBE),
    (r'\bremove\b', OptOutReason.SMS_UNSUBSCRIBE),
    (r'\bopt\s*-?\s*out\b', OptOutReason.SMS_UNSUBSCRIBE),
    (r'\bcancel\b', OptOutReason.SMS_UNSUBSCRIBE),
    (r'\bend\b', OptOutReason.SMS_STOP),
    (r'\bquit\b', OptOutReason.SMS_STOP),

    # Negative responses that indicate opt-out intent
    (r'\bno\s+thanks\b', OptOutReason.SMS_UNSUBSCRIBE),
    (r'\bnot\s+interested\b', OptOutReason.SMS_UNSUBSCRIBE),
    (r'\bdon\'?t\s+contact\b', OptOutReason.SMS_UNSUBSCRIBE),
    (r'\bdo\s+not\s+contact\b', OptOutReason.SMS_UNSUBSCRIBE),
    (r'\bstop\s+texting\b', OptOutReason.SMS_STOP),
    (r'\bstop\s+messaging\b', OptOutReason.SMS_STOP),
    (r'\bstop\s+sending\b', OptOutReason.SMS_STOP),
    (r'\bleave\s+me\s+alone\b', OptOutReason.SMS_UNSUBSCRIBE),
    (r'\btake\s+me\s+off\b', OptOutReason.SMS_UNSUBSCRIBE),
    (r'\bdelete\s+my\s+number\b', OptOutReason.SMS_UNSUBSCRIBE),
    (r'\bwrong\s+number\b', OptOutReason.INVALID_NUMBER),
]


def detect_opt_out(message: str) -> Optional[Tuple[bool, OptOutReason, str]]:
    """
    Detect if a message contains an opt-out request.

    Args:
        message: The SMS or email body to analyze

    Returns:
        Tuple of (is_opt_out, reason, matched_phrase) or None if not an opt-out
    """
    if not message:
        return None

    message_lower = message.lower().strip()

    # Check against opt-out patterns
    for pattern, reason in OPT_OUT_PATTERNS:
        match = re.search(pattern, message_lower, re.IGNORECASE)
        if match:
            return (True, reason, match.group(0))

    return None


def is_opt_out_message(message: str) -> bool:
    """Simple boolean check if message is an opt-out."""
    result = detect_opt_out(message)
    return result is not None and result[0]


# =============================================================================
# Opt-Out Record
# =============================================================================

@dataclass
class OptOutRecord:
    """Represents an opted-out contact."""
    # Identifier (phone or email, normalized)
    identifier: str
    identifier_type: str  # "phone" or "email"

    # Original value before normalization
    original_value: str

    # Reason and context
    reason: str  # OptOutReason value
    reason_detail: str = ""  # Additional context (e.g., the actual message)

    # Business association (if known)
    business_name: str = ""
    lead_id: str = ""

    # Timestamps
    opted_out_at: str = ""
    source_message_sid: str = ""  # If from SMS reply

    # Status
    is_active: bool = True  # Can be reactivated if they opt back in

    def __post_init__(self):
        if not self.opted_out_at:
            self.opted_out_at = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OptOutRecord":
        return cls(**data)


# =============================================================================
# Opt-Out Manager
# =============================================================================

class OptOutManager:
    """
    Centralized opt-out management for SMS and Email campaigns.

    Features:
    - Maintains persistent opt-out list
    - Normalizes phone numbers and emails for consistent matching
    - Detects opt-out phrases in messages
    - Syncs opt-outs to campaign records
    - Provides fast lookup for send-time checks
    """

    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # File paths
        self.optout_file = self.output_dir / "opt_out_list.json"
        self.campaigns_file = self.output_dir / "sms_campaigns.json"
        self.replies_file = self.output_dir / "sms_replies.json"

        # In-memory data structures for fast lookup
        self.opt_outs: Dict[str, OptOutRecord] = {}  # identifier -> record
        self._phone_set: Set[str] = set()  # Normalized phones for fast lookup
        self._email_set: Set[str] = set()  # Normalized emails for fast lookup

        # Load existing data
        self._load_opt_outs()

    # =========================================================================
    # Normalization
    # =========================================================================

    def normalize_phone(self, phone: str) -> str:
        """
        Normalize phone number for consistent matching.
        Removes formatting, adds country code if missing.
        """
        if not phone:
            return ""

        # Remove all non-digit characters except leading +
        cleaned = ''.join(c for c in phone if c.isdigit() or c == '+')

        # Remove leading + for processing
        if cleaned.startswith('+'):
            cleaned = cleaned[1:]

        # Handle US numbers
        if len(cleaned) == 10:
            cleaned = '1' + cleaned
        elif len(cleaned) == 11 and cleaned.startswith('1'):
            pass  # Already has country code

        # Return in consistent format (digits only, no +)
        return cleaned

    def normalize_email(self, email: str) -> str:
        """Normalize email for consistent matching."""
        if not email:
            return ""
        return email.lower().strip()

    def normalize_identifier(self, value: str, identifier_type: str) -> str:
        """Normalize any identifier based on its type."""
        if identifier_type == "phone":
            return self.normalize_phone(value)
        elif identifier_type == "email":
            return self.normalize_email(value)
        return value.lower().strip()

    # =========================================================================
    # Persistence
    # =========================================================================

    def _load_opt_outs(self) -> None:
        """Load opt-out list from file."""
        if not self.optout_file.exists():
            return

        try:
            with open(self.optout_file, 'r') as f:
                data = json.load(f)

            # Handle old format (simple list of identifiers)
            if isinstance(data, list):
                self._migrate_old_format(data)
                return

            # New format with full records
            for record_data in data.get("records", []):
                record = OptOutRecord.from_dict(record_data)
                self.opt_outs[record.identifier] = record

                # Update lookup sets
                if record.identifier_type == "phone":
                    self._phone_set.add(record.identifier)
                elif record.identifier_type == "email":
                    self._email_set.add(record.identifier)

        except Exception as e:
            logger.error(f"Error loading opt-out list: {e}")

    def _migrate_old_format(self, old_list: list) -> None:
        """Migrate from old simple list format to new record format."""
        logger.info(f"Migrating {len(old_list)} old opt-out entries to new format")

        for item in old_list:
            if not item:
                continue

            # Detect type based on format
            if '@' in str(item):
                identifier_type = "email"
                normalized = self.normalize_email(str(item))
            else:
                identifier_type = "phone"
                normalized = self.normalize_phone(str(item))

            if normalized:
                record = OptOutRecord(
                    identifier=normalized,
                    identifier_type=identifier_type,
                    original_value=str(item),
                    reason=OptOutReason.MANUAL.value,
                    reason_detail="Migrated from old format"
                )
                self.opt_outs[normalized] = record

                if identifier_type == "phone":
                    self._phone_set.add(normalized)
                else:
                    self._email_set.add(normalized)

        # Save in new format
        self._save_opt_outs()

    def _save_opt_outs(self) -> None:
        """Save opt-out list to file."""
        data = {
            "records": [r.to_dict() for r in self.opt_outs.values()],
            "summary": self.get_statistics(),
            "updated_at": datetime.now().isoformat()
        }

        with open(self.optout_file, 'w') as f:
            json.dump(data, f, indent=2)

    # =========================================================================
    # Core Operations
    # =========================================================================

    def is_opted_out(self, phone: str = "", email: str = "") -> bool:
        """
        Check if a contact is on the opt-out list.
        Fast O(1) lookup.

        Args:
            phone: Phone number to check
            email: Email address to check

        Returns:
            True if contact is opted out
        """
        if phone:
            normalized_phone = self.normalize_phone(phone)
            if normalized_phone in self._phone_set:
                return True

        if email:
            normalized_email = self.normalize_email(email)
            if normalized_email in self._email_set:
                return True

        return False

    def get_opt_out_record(self, phone: str = "", email: str = "") -> Optional[OptOutRecord]:
        """Get the full opt-out record for a contact."""
        if phone:
            normalized = self.normalize_phone(phone)
            if normalized in self.opt_outs:
                return self.opt_outs[normalized]

        if email:
            normalized = self.normalize_email(email)
            if normalized in self.opt_outs:
                return self.opt_outs[normalized]

        return None

    def add_opt_out(
        self,
        phone: str = "",
        email: str = "",
        reason: OptOutReason = OptOutReason.MANUAL,
        reason_detail: str = "",
        business_name: str = "",
        lead_id: str = "",
        message_sid: str = ""
    ) -> OptOutRecord:
        """
        Add a contact to the opt-out list.

        Args:
            phone: Phone number to opt out
            email: Email to opt out
            reason: Reason for opt-out
            reason_detail: Additional context
            business_name: Associated business name
            lead_id: Associated lead ID
            message_sid: Source message SID (if from SMS)

        Returns:
            The created OptOutRecord
        """
        if not phone and not email:
            raise ValueError("Must provide either phone or email")

        # Determine identifier type and normalize
        if phone:
            identifier_type = "phone"
            normalized = self.normalize_phone(phone)
            original = phone
            self._phone_set.add(normalized)
        else:
            identifier_type = "email"
            normalized = self.normalize_email(email)
            original = email
            self._email_set.add(normalized)

        # Create or update record
        if normalized in self.opt_outs:
            # Update existing record
            record = self.opt_outs[normalized]
            record.reason = reason.value
            record.reason_detail = reason_detail
            record.is_active = True
            logger.info(f"Updated opt-out for {normalized}")
        else:
            # Create new record
            record = OptOutRecord(
                identifier=normalized,
                identifier_type=identifier_type,
                original_value=original,
                reason=reason.value,
                reason_detail=reason_detail,
                business_name=business_name,
                lead_id=lead_id,
                source_message_sid=message_sid
            )
            self.opt_outs[normalized] = record
            logger.info(f"Added opt-out for {normalized} ({reason.value})")

        # Persist
        self._save_opt_outs()

        return record

    def remove_opt_out(self, phone: str = "", email: str = "") -> bool:
        """
        Remove a contact from opt-out list (for re-subscription).

        Returns:
            True if contact was removed, False if not found
        """
        normalized = None
        if phone:
            normalized = self.normalize_phone(phone)
            self._phone_set.discard(normalized)
        elif email:
            normalized = self.normalize_email(email)
            self._email_set.discard(normalized)

        if normalized and normalized in self.opt_outs:
            # Mark as inactive rather than delete (for audit trail)
            self.opt_outs[normalized].is_active = False
            self._save_opt_outs()
            logger.info(f"Removed opt-out for {normalized}")
            return True

        return False

    # =========================================================================
    # SMS Reply Processing
    # =========================================================================

    def process_sms_reply(
        self,
        from_phone: str,
        message_body: str,
        business_name: str = "",
        lead_id: str = "",
        message_sid: str = ""
    ) -> Optional[OptOutRecord]:
        """
        Process an incoming SMS reply for opt-out detection.

        Args:
            from_phone: Sender's phone number
            message_body: The SMS content
            business_name: Associated business name
            lead_id: Associated lead ID
            message_sid: Twilio message SID

        Returns:
            OptOutRecord if message was an opt-out, None otherwise
        """
        result = detect_opt_out(message_body)

        if result is None:
            return None

        is_opt_out, reason, matched_phrase = result

        if not is_opt_out:
            return None

        # Add to opt-out list
        record = self.add_opt_out(
            phone=from_phone,
            reason=reason,
            reason_detail=f"Message: '{message_body}' (matched: '{matched_phrase}')",
            business_name=business_name,
            lead_id=lead_id,
            message_sid=message_sid
        )

        return record

    def process_all_replies(self, force: bool = False) -> Dict[str, Any]:
        """
        Process all SMS replies for opt-outs.

        Args:
            force: If True, process all replies including already-categorized opt-outs

        Returns:
            Summary of processing results
        """
        if not self.replies_file.exists():
            return {"processed": 0, "new_opt_outs": 0, "error": "No replies file found"}

        with open(self.replies_file, 'r') as f:
            data = json.load(f)

        replies = data.get("replies", [])
        new_opt_outs = 0
        already_in_list = 0
        skipped = 0

        for reply in replies:
            from_phone = reply.get("from_phone", "")
            body = reply.get("body", "")
            business_name = reply.get("business_name", "")
            message_sid = reply.get("message_sid", "")

            # Check if already in our list
            if self.is_opted_out(phone=from_phone):
                already_in_list += 1
                continue

            # Check category or detect opt-out
            is_opt_out = reply.get("category") == "opt_out"

            if not is_opt_out and not force:
                # Try to detect from message body
                result = detect_opt_out(body)
                is_opt_out = result is not None and result[0]

            if is_opt_out or (force and reply.get("category") == "opt_out"):
                # Determine reason from body if possible
                result = detect_opt_out(body)
                if result:
                    reason = result[1]
                else:
                    reason = OptOutReason.SMS_STOP

                self.add_opt_out(
                    phone=from_phone,
                    reason=reason,
                    reason_detail=f"From SMS reply: '{body[:100]}'",
                    business_name=business_name,
                    message_sid=message_sid
                )
                new_opt_outs += 1
            else:
                skipped += 1

        return {
            "processed": len(replies),
            "new_opt_outs": new_opt_outs,
            "already_in_list": already_in_list,
            "skipped": skipped,
            "total_opt_outs": len(self.opt_outs)
        }

    def import_from_replies(self) -> Dict[str, Any]:
        """
        Import all opt-out categorized replies into the opt-out list.
        This ensures all historically marked opt-outs are in the centralized list.

        Returns:
            Summary of import results
        """
        if not self.replies_file.exists():
            return {"imported": 0, "error": "No replies file found"}

        with open(self.replies_file, 'r') as f:
            data = json.load(f)

        replies = data.get("replies", [])
        imported = 0
        already_exists = 0

        for reply in replies:
            # Only process replies categorized as opt_out
            if reply.get("category") != "opt_out":
                continue

            from_phone = reply.get("from_phone", "")
            body = reply.get("body", "")
            business_name = reply.get("business_name", "")
            message_sid = reply.get("message_sid", "")

            # Skip if already in list
            if self.is_opted_out(phone=from_phone):
                already_exists += 1
                continue

            # Determine reason from body
            result = detect_opt_out(body)
            if result:
                reason = result[1]
            else:
                reason = OptOutReason.SMS_STOP

            self.add_opt_out(
                phone=from_phone,
                reason=reason,
                reason_detail=f"Imported from reply: '{body[:100]}'",
                business_name=business_name,
                message_sid=message_sid
            )
            imported += 1

        return {
            "total_replies": len(replies),
            "opt_out_replies": sum(1 for r in replies if r.get("category") == "opt_out"),
            "imported": imported,
            "already_exists": already_exists,
            "total_opt_outs": len(self.opt_outs)
        }

    # =========================================================================
    # Email Handling
    # =========================================================================

    def add_email_bounce(self, email: str, bounce_type: str = "hard") -> OptOutRecord:
        """Add an email that bounced."""
        reason = OptOutReason.EMAIL_BOUNCE if bounce_type == "hard" else OptOutReason.INVALID_EMAIL
        return self.add_opt_out(
            email=email,
            reason=reason,
            reason_detail=f"Bounce type: {bounce_type}"
        )

    def add_email_unsubscribe(self, email: str, source: str = "link_click") -> OptOutRecord:
        """Add an email that unsubscribed."""
        return self.add_opt_out(
            email=email,
            reason=OptOutReason.EMAIL_UNSUBSCRIBE,
            reason_detail=f"Unsubscribe source: {source}"
        )

    def add_email_complaint(self, email: str) -> OptOutRecord:
        """Add an email that marked as spam."""
        return self.add_opt_out(
            email=email,
            reason=OptOutReason.EMAIL_COMPLAINT,
            reason_detail="Marked as spam"
        )

    # =========================================================================
    # Campaign Sync
    # =========================================================================

    def sync_to_campaigns(self) -> Dict[str, Any]:
        """
        Update sms_campaigns.json to mark opted-out contacts.

        Returns:
            Summary of updates made
        """
        if not self.campaigns_file.exists():
            return {"error": "No campaigns file found", "updated": 0}

        with open(self.campaigns_file, 'r') as f:
            data = json.load(f)

        records = data.get("records", [])
        updated_count = 0

        for record in records:
            phone = record.get("phone", "")
            current_status = record.get("status", "")

            # Skip if already marked as opted out
            if current_status == "opted_out":
                continue

            # Check if phone is in opt-out list
            if self.is_opted_out(phone=phone):
                record["status"] = "opted_out"
                record["opted_out_at"] = datetime.now().isoformat()
                updated_count += 1

        # Save updated campaigns
        data["records"] = records
        data["updated_at"] = datetime.now().isoformat()

        with open(self.campaigns_file, 'w') as f:
            json.dump(data, f, indent=2)

        logger.info(f"Updated {updated_count} campaign records to opted_out status")

        return {
            "total_records": len(records),
            "updated": updated_count,
            "already_opted_out": sum(1 for r in records if r.get("status") == "opted_out")
        }

    # =========================================================================
    # Statistics and Export
    # =========================================================================

    def get_statistics(self) -> Dict[str, Any]:
        """Get opt-out statistics."""
        by_reason = {}
        by_type = {"phone": 0, "email": 0}
        active_count = 0

        for record in self.opt_outs.values():
            # Count by reason
            reason = record.reason
            by_reason[reason] = by_reason.get(reason, 0) + 1

            # Count by type
            by_type[record.identifier_type] = by_type.get(record.identifier_type, 0) + 1

            # Count active
            if record.is_active:
                active_count += 1

        return {
            "total_opt_outs": len(self.opt_outs),
            "active_opt_outs": active_count,
            "by_reason": by_reason,
            "by_type": by_type
        }

    def export_csv(self, filename: str = "opt_out_export.csv") -> str:
        """Export opt-out list to CSV."""
        import csv

        filepath = self.output_dir / filename

        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                "Identifier", "Type", "Original Value", "Reason",
                "Business Name", "Opted Out At", "Is Active"
            ])

            for record in self.opt_outs.values():
                writer.writerow([
                    record.identifier,
                    record.identifier_type,
                    record.original_value,
                    record.reason,
                    record.business_name,
                    record.opted_out_at,
                    record.is_active
                ])

        return str(filepath)

    def get_opt_out_list(self, identifier_type: str = "all") -> List[str]:
        """
        Get list of opted-out identifiers.

        Args:
            identifier_type: "phone", "email", or "all"

        Returns:
            List of normalized identifiers
        """
        if identifier_type == "phone":
            return list(self._phone_set)
        elif identifier_type == "email":
            return list(self._email_set)
        else:
            return list(self._phone_set | self._email_set)


# =============================================================================
# Helper Functions for Integration
# =============================================================================

def check_before_send(phone: str = "", email: str = "", output_dir: str = "output") -> bool:
    """
    Quick helper to check if a contact can be messaged.

    Args:
        phone: Phone number to check
        email: Email to check
        output_dir: Path to output directory

    Returns:
        True if OK to send (not opted out), False if opted out
    """
    manager = OptOutManager(output_dir=output_dir)
    return not manager.is_opted_out(phone=phone, email=email)


def filter_opted_out_contacts(
    contacts: List[Dict[str, Any]],
    phone_field: str = "phone",
    email_field: str = "email",
    output_dir: str = "output"
) -> Tuple[List[Dict], List[Dict]]:
    """
    Filter a list of contacts, separating opted-out from sendable.

    Args:
        contacts: List of contact dicts
        phone_field: Key for phone number in contact dict
        email_field: Key for email in contact dict
        output_dir: Path to output directory

    Returns:
        Tuple of (sendable_contacts, opted_out_contacts)
    """
    manager = OptOutManager(output_dir=output_dir)

    sendable = []
    opted_out = []

    for contact in contacts:
        phone = contact.get(phone_field, "")
        email = contact.get(email_field, "")

        if manager.is_opted_out(phone=phone, email=email):
            opted_out.append(contact)
        else:
            sendable.append(contact)

    return sendable, opted_out


# =============================================================================
# CLI
# =============================================================================

def main():
    import argparse

    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    parser = argparse.ArgumentParser(description="Opt-Out Management System")
    parser.add_argument("--output-dir", "-o", default="output", help="Output directory")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Check command
    check_parser = subparsers.add_parser("check", help="Check if contact is opted out")
    check_parser.add_argument("--phone", "-p", help="Phone number to check")
    check_parser.add_argument("--email", "-e", help="Email to check")

    # Add command
    add_parser = subparsers.add_parser("add", help="Add contact to opt-out list")
    add_parser.add_argument("--phone", "-p", help="Phone number to add")
    add_parser.add_argument("--email", "-e", help="Email to add")
    add_parser.add_argument("--reason", "-r", default="manual", help="Reason for opt-out")
    add_parser.add_argument("--business", "-b", help="Business name")

    # Remove command
    remove_parser = subparsers.add_parser("remove", help="Remove contact from opt-out list")
    remove_parser.add_argument("--phone", "-p", help="Phone number to remove")
    remove_parser.add_argument("--email", "-e", help="Email to remove")

    # Process replies command
    process_parser = subparsers.add_parser("process-replies", help="Process SMS replies for opt-outs")

    # Import from replies command
    import_parser = subparsers.add_parser("import-replies", help="Import opt-out categorized replies into opt-out list")

    # Sync campaigns command
    sync_parser = subparsers.add_parser("sync-campaigns", help="Sync opt-outs to campaign records")

    # Stats command
    stats_parser = subparsers.add_parser("stats", help="Show opt-out statistics")

    # Export command
    export_parser = subparsers.add_parser("export", help="Export opt-out list")
    export_parser.add_argument("--format", "-f", choices=["csv", "json"], default="csv", help="Export format")

    # List command
    list_parser = subparsers.add_parser("list", help="List all opted-out contacts")
    list_parser.add_argument("--type", "-t", choices=["phone", "email", "all"], default="all", help="Type to list")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    manager = OptOutManager(output_dir=args.output_dir)

    if args.command == "check":
        if not args.phone and not args.email:
            print("Error: Must provide --phone or --email")
            return 1

        is_opted_out = manager.is_opted_out(phone=args.phone or "", email=args.email or "")
        identifier = args.phone or args.email

        if is_opted_out:
            record = manager.get_opt_out_record(phone=args.phone or "", email=args.email or "")
            print(f"OPTED OUT: {identifier}")
            if record:
                print(f"  Reason: {record.reason}")
                print(f"  Business: {record.business_name or 'Unknown'}")
                print(f"  Date: {record.opted_out_at}")
        else:
            print(f"OK TO SEND: {identifier} is not on the opt-out list")

    elif args.command == "add":
        if not args.phone and not args.email:
            print("Error: Must provide --phone or --email")
            return 1

        try:
            reason = OptOutReason(args.reason)
        except ValueError:
            reason = OptOutReason.MANUAL

        record = manager.add_opt_out(
            phone=args.phone or "",
            email=args.email or "",
            reason=reason,
            business_name=args.business or ""
        )
        print(f"Added to opt-out list: {record.identifier}")
        print(f"  Type: {record.identifier_type}")
        print(f"  Reason: {record.reason}")

    elif args.command == "remove":
        if not args.phone and not args.email:
            print("Error: Must provide --phone or --email")
            return 1

        success = manager.remove_opt_out(phone=args.phone or "", email=args.email or "")
        if success:
            print(f"Removed from opt-out list: {args.phone or args.email}")
        else:
            print(f"Not found in opt-out list: {args.phone or args.email}")

    elif args.command == "process-replies":
        result = manager.process_all_replies()
        print("\n=== SMS Reply Processing Results ===")
        print(f"  Replies processed: {result.get('processed', 0)}")
        print(f"  New opt-outs found: {result.get('new_opt_outs', 0)}")
        print(f"  Already in list: {result.get('already_in_list', 0)}")
        print(f"  Skipped (not opt-out): {result.get('skipped', 0)}")
        print(f"  Total opt-outs: {result.get('total_opt_outs', 0)}")

    elif args.command == "import-replies":
        result = manager.import_from_replies()
        print("\n=== Import From Replies Results ===")
        print(f"  Total replies: {result.get('total_replies', 0)}")
        print(f"  Opt-out replies: {result.get('opt_out_replies', 0)}")
        print(f"  Imported: {result.get('imported', 0)}")
        print(f"  Already exists: {result.get('already_exists', 0)}")
        print(f"  Total opt-outs: {result.get('total_opt_outs', 0)}")

    elif args.command == "sync-campaigns":
        result = manager.sync_to_campaigns()
        print("\n=== Campaign Sync Results ===")
        print(f"  Total records: {result.get('total_records', 0)}")
        print(f"  Updated to opted_out: {result.get('updated', 0)}")
        print(f"  Already opted_out: {result.get('already_opted_out', 0)}")

    elif args.command == "stats":
        stats = manager.get_statistics()
        print("\n=== Opt-Out Statistics ===")
        print(f"  Total opt-outs: {stats['total_opt_outs']}")
        print(f"  Active opt-outs: {stats['active_opt_outs']}")
        print("\n  By Type:")
        for t, count in stats['by_type'].items():
            print(f"    {t}: {count}")
        print("\n  By Reason:")
        for reason, count in stats['by_reason'].items():
            print(f"    {reason}: {count}")

    elif args.command == "export":
        if args.format == "csv":
            filepath = manager.export_csv()
            print(f"Exported to: {filepath}")
        else:
            print(json.dumps([r.to_dict() for r in manager.opt_outs.values()], indent=2))

    elif args.command == "list":
        opt_outs = manager.get_opt_out_list(identifier_type=args.type)
        print(f"\n=== Opted-Out Contacts ({args.type}) ===")
        print(f"Total: {len(opt_outs)}\n")
        for identifier in sorted(opt_outs):
            record = manager.opt_outs.get(identifier)
            if record:
                print(f"  {identifier} ({record.reason}) - {record.business_name or 'Unknown'}")
            else:
                print(f"  {identifier}")

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
