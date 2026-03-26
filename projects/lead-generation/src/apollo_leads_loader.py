#!/usr/bin/env python3
"""
Apollo Leads Loader - Loads Apollo.io leads and converts to Lead model for SMS outreach.

Apollo leads are B2B contacts with:
- first_name, last_name (decision makers)
- title (Owner, CEO, etc.)
- phone_numbers (corporate/direct)
- organization info (company name, website, industry)

This module bridges Apollo data to the follow-up sequence system.

Usage:
    python -m src.apollo_leads_loader list --limit 10
    python -m src.apollo_leads_loader enroll --limit 20 --dry-run
    python -m src.apollo_leads_loader enroll --limit 20 --for-real
"""

import os
import json
import logging
import argparse
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import re

from dotenv import load_dotenv
env_path = Path(__file__).parent.parent.parent.parent.parent / ".env"
load_dotenv(env_path)

from .models import Lead
from .follow_up_sequence import FollowUpSequenceManager
from .opt_out_manager import OptOutManager

logger = logging.getLogger(__name__)


class ApolloLeadsLoader:
    """
    Loads Apollo.io leads and prepares them for SMS outreach.

    Features:
    - Filters leads with valid phone numbers
    - Normalizes phone to E.164 format
    - Converts to Lead model for sequence enrollment
    - Tracks already-enrolled leads to avoid duplicates
    """

    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.apollo_file = self.output_dir / "apollo_csv_leads.json"
        self.enrolled_file = self.output_dir / "apollo_enrolled_leads.json"

        # Track which Apollo leads have been enrolled
        self.enrolled_ids: set = set()
        self._load_enrolled()

        # Opt-out manager for compliance
        self.opt_out_manager = OptOutManager(output_dir=output_dir)

    def _load_enrolled(self) -> None:
        """Load previously enrolled Apollo lead IDs."""
        if self.enrolled_file.exists():
            with open(self.enrolled_file, 'r') as f:
                data = json.load(f)
                self.enrolled_ids = set(data.get("enrolled_ids", []))

    def _save_enrolled(self) -> None:
        """Save enrolled Apollo lead IDs."""
        data = {
            "enrolled_ids": list(self.enrolled_ids),
            "updated_at": datetime.now().isoformat()
        }
        with open(self.enrolled_file, 'w') as f:
            json.dump(data, f, indent=2)

    def _normalize_phone(self, phone: str) -> Optional[str]:
        """
        Normalize phone number to E.164 format.
        Returns None if invalid.
        """
        if not phone:
            return None

        # Remove common formatting and quotes
        cleaned = re.sub(r"[^\d+]", "", phone)
        cleaned = cleaned.lstrip("'+")  # Remove leading + or '

        # Validate and format
        if cleaned.startswith('1') and len(cleaned) == 11:
            return '+' + cleaned
        elif len(cleaned) == 10:
            return '+1' + cleaned
        elif cleaned.startswith('+1') and len(cleaned) == 12:
            return cleaned

        return None  # Invalid format

    def _extract_best_phone(self, person: Dict[str, Any]) -> Optional[str]:
        """Extract and normalize the best phone number from Apollo contact."""
        phone_numbers = person.get("phone_numbers", [])

        if not phone_numbers:
            return None

        # Prefer direct/mobile over corporate
        for ptype in ["direct", "mobile", "corporate"]:
            for pn in phone_numbers:
                if pn.get("type") == ptype:
                    normalized = self._normalize_phone(pn.get("raw_number", ""))
                    if normalized:
                        return normalized

        # Fall back to any number
        for pn in phone_numbers:
            normalized = self._normalize_phone(pn.get("raw_number", ""))
            if normalized:
                return normalized

        return None

    def load_apollo_leads(self) -> List[Dict[str, Any]]:
        """Load all Apollo leads from JSON file."""
        if not self.apollo_file.exists():
            logger.error(f"Apollo leads file not found: {self.apollo_file}")
            return []

        with open(self.apollo_file, 'r') as f:
            data = json.load(f)

        # Handle both formats: {"people": [...]} or just [...]
        if isinstance(data, dict):
            return data.get("people", [])
        return data

    def get_qualified_leads(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get qualified Apollo leads ready for outreach.

        Filters:
        - Has valid phone number
        - Not already enrolled
        - Not opted out
        """
        all_leads = self.load_apollo_leads()
        qualified = []

        for person in all_leads:
            # Skip already enrolled
            if person.get("id") in self.enrolled_ids:
                continue

            # Extract phone
            phone = self._extract_best_phone(person)
            if not phone:
                continue

            # Skip opted out
            if self.opt_out_manager.is_opted_out(phone=phone):
                continue

            # Add normalized phone to person data
            person["_normalized_phone"] = phone
            qualified.append(person)

            if limit and len(qualified) >= limit:
                break

        return qualified

    def apollo_to_lead(self, person: Dict[str, Any]) -> Lead:
        """Convert Apollo person record to Lead model."""
        org = person.get("organization", {})

        # Build business name from org or person name
        business_name = org.get("name") or f"{person.get('first_name', '')} {person.get('last_name', '')}".strip()

        # Build address from org location
        city = org.get("city", person.get("city", ""))
        state = org.get("state", person.get("state", ""))
        address = f"{city}, {state}" if city else ""

        return Lead(
            id=person.get("id", ""),
            business_name=business_name,
            address=address,
            phone=person.get("_normalized_phone", ""),
            website=org.get("website_url", ""),
            rating=0.0,
            review_count=0,
            pain_points=["apollo_b2b"],  # Special tag for Apollo leads
            source="apollo",
            first_name=person.get("first_name", ""),
            last_name=person.get("last_name", ""),
            title=person.get("title", ""),
            email=person.get("email", ""),
            industry=org.get("industry", ""),
        )

    def enroll_leads(self, limit: int = 10, dry_run: bool = True) -> Dict[str, Any]:
        """
        Enroll Apollo leads into follow-up sequence.

        Args:
            limit: Max leads to enroll
            dry_run: If True, don't actually enroll

        Returns:
            Stats dict with enrolled count, skipped, etc.
        """
        qualified = self.get_qualified_leads(limit=limit)

        stats = {
            "total_qualified": len(qualified),
            "enrolled": 0,
            "skipped": 0,
            "errors": [],
            "leads_enrolled": []
        }

        if not qualified:
            logger.info("No qualified Apollo leads to enroll")
            return stats

        # Initialize sequence manager
        sequence_manager = FollowUpSequenceManager(output_dir=str(self.output_dir))

        for person in qualified:
            try:
                lead = self.apollo_to_lead(person)

                if dry_run:
                    logger.info(f"[DRY RUN] Would enroll: {lead.first_name} {lead.last_name} @ {lead.business_name} ({lead.phone})")
                    stats["enrolled"] += 1
                    stats["leads_enrolled"].append({
                        "id": lead.id,
                        "name": f"{lead.first_name} {lead.last_name}",
                        "business": lead.business_name,
                        "phone": lead.phone
                    })
                else:
                    # Actually enroll in sequence
                    sequence = sequence_manager.enroll_lead(lead, business_id="marceau-solutions")

                    # Mark as enrolled
                    self.enrolled_ids.add(person.get("id"))

                    logger.info(f"Enrolled: {lead.first_name} @ {lead.business_name}")
                    stats["enrolled"] += 1
                    stats["leads_enrolled"].append({
                        "id": lead.id,
                        "name": f"{lead.first_name} {lead.last_name}",
                        "business": lead.business_name,
                        "phone": lead.phone
                    })

            except Exception as e:
                logger.error(f"Error enrolling {person.get('id')}: {e}")
                stats["errors"].append(str(e))
                stats["skipped"] += 1

        # Save enrolled IDs
        if not dry_run:
            self._save_enrolled()

        return stats


def main():
    """CLI for Apollo leads loader."""
    parser = argparse.ArgumentParser(description="Apollo Leads Loader for SMS Outreach")
    parser.add_argument("command", choices=["list", "enroll", "stats"],
                        help="Command to run")
    parser.add_argument("--limit", type=int, default=10,
                        help="Max leads to process")
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview without enrolling")
    parser.add_argument("--for-real", action="store_true",
                        help="Actually enroll leads")

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    # Change to project directory
    project_dir = Path(__file__).parent.parent
    os.chdir(project_dir)

    loader = ApolloLeadsLoader()

    if args.command == "list":
        qualified = loader.get_qualified_leads(limit=args.limit)
        print(f"\n=== Qualified Apollo Leads ({len(qualified)}) ===\n")

        for p in qualified:
            org = p.get("organization", {})
            print(f"  {p.get('first_name')} {p.get('last_name')} - {p.get('title')}")
            print(f"    Company: {org.get('name')}")
            print(f"    Phone: {p.get('_normalized_phone')}")
            print(f"    Industry: {org.get('industry')}")
            print()

    elif args.command == "enroll":
        dry_run = not args.for_real

        if dry_run:
            print("\n=== DRY RUN - No leads will be enrolled ===\n")
        else:
            print("\n=== ENROLLING LEADS FOR REAL ===\n")

        stats = loader.enroll_leads(limit=args.limit, dry_run=dry_run)

        print(f"\n=== Enrollment Results ===")
        print(f"  Qualified: {stats['total_qualified']}")
        print(f"  Enrolled: {stats['enrolled']}")
        print(f"  Skipped: {stats['skipped']}")

        if stats['errors']:
            print(f"  Errors: {len(stats['errors'])}")

    elif args.command == "stats":
        all_leads = loader.load_apollo_leads()
        qualified = loader.get_qualified_leads()

        print(f"\n=== Apollo Leads Stats ===")
        print(f"  Total leads: {len(all_leads)}")
        print(f"  With phone: {len([p for p in all_leads if loader._extract_best_phone(p)])}")
        print(f"  Already enrolled: {len(loader.enrolled_ids)}")
        print(f"  Qualified (unenrolled with phone): {len(qualified)}")


if __name__ == "__main__":
    main()
