"""
Apollo → ClickUp Direct Integration

Sync Apollo leads directly to ClickUp CRM without Zapier.
Supports filtering, scoring thresholds, and batch operations.

Usage:
    from src.apollo_to_clickup import ApolloClickUpSync

    sync = ApolloClickUpSync()

    # Sync qualified leads only (score >= 8, verified email)
    results = sync.sync_apollo_leads(
        leads=apollo_leads,
        campaign_name="Naples Gyms Q1",
        min_score=8,
        require_verified_email=True,
        dry_run=True
    )

CLI:
    python -m src.apollo_to_clickup sync --campaign "Naples Gyms" --dry-run
    python -m src.apollo_to_clickup sync --campaign "Naples Gyms" --for-real
"""

import os
import json
import requests
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from root .env
load_dotenv(Path(__file__).parent.parent.parent.parent.parent / ".env")
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class LeadQualification(str, Enum):
    """Lead qualification levels based on Apollo data"""
    HOT = "hot"          # Score >= 8, verified email, phone available
    WARM = "warm"        # Score >= 6, has email
    COLD = "cold"        # Score < 6 or missing contact info
    UNQUALIFIED = "unqualified"  # No email, no phone, or excluded title


@dataclass
class ApolloLeadData:
    """Structured Apollo lead data for ClickUp sync"""
    # Core identifiers
    apollo_id: str
    first_name: str
    last_name: str

    # Contact info
    email: str
    email_status: str  # verified, guessed, bounced, etc.
    phone: str
    phone_type: str  # mobile, direct, corporate

    # Company info
    company_name: str
    company_domain: str
    company_size: int
    industry: str

    # Professional info
    title: str
    seniority: str
    linkedin_url: str

    # Scoring & metadata
    apollo_score: float  # 0-10 scale
    qualification: LeadQualification
    search_profile: str  # Which profile was used
    campaign_name: str

    # Location
    city: str
    state: str

    # Timestamps
    scraped_at: str

    def to_clickup_description(self) -> str:
        """Format lead data for ClickUp task description"""
        lines = [
            "## Contact Information",
            f"**Name:** {self.first_name} {self.last_name}",
            f"**Title:** {self.title}",
            f"**Seniority:** {self.seniority}" if self.seniority else "",
            f"**Email:** {self.email} ({self.email_status})",
            f"**Phone:** {self.phone} ({self.phone_type})" if self.phone else "**Phone:** N/A",
            f"**LinkedIn:** {self.linkedin_url}" if self.linkedin_url else "",
            "",
            "## Company Information",
            f"**Company:** {self.company_name}",
            f"**Website:** {self.company_domain}" if self.company_domain else "",
            f"**Industry:** {self.industry}",
            f"**Size:** {self.company_size} employees" if self.company_size else "",
            f"**Location:** {self.city}, {self.state}" if self.city else "",
            "",
            "## Lead Scoring",
            f"**Apollo Score:** {self.apollo_score}/10",
            f"**Qualification:** {self.qualification.value.upper()}",
            f"**Email Verified:** {'✅ Yes' if self.email_status == 'verified' else '❌ No'}",
            f"**Phone Available:** {'✅ Yes' if self.phone else '❌ No'}",
            "",
            "## Source",
            f"**Data Source:** Apollo",
            f"**Campaign:** {self.campaign_name}",
            f"**Search Profile:** {self.search_profile}",
            f"**Apollo ID:** {self.apollo_id}",
            f"**Scraped:** {self.scraped_at}",
        ]
        return "\n".join([l for l in lines if l])  # Remove empty lines


class ApolloClickUpSync:
    """
    Direct Apollo → ClickUp integration.

    Handles:
    - Lead qualification and scoring
    - Deduplication (by email/phone)
    - Batch task creation
    - Custom field mapping
    - Sync logging
    """

    # Default qualification thresholds
    HOT_SCORE_THRESHOLD = 8.0
    WARM_SCORE_THRESHOLD = 6.0

    # ClickUp list IDs (from setup_custom_fields.py)
    PIPELINE_LISTS = {
        "Intake": "901709133703",
        "Qualification": "901709133704",
        "Meeting Booked": "901709133705",
        "Proposal Sent": "901709133706",
        "Negotiation": "901709133707",
        "Closed Won": "901709133708",
        "Closed Lost": "901709133709"
    }

    def __init__(
        self,
        api_token: str = None,
        list_id: str = None,
        custom_field_ids: Dict[str, str] = None
    ):
        """
        Initialize Apollo → ClickUp sync.

        Args:
            api_token: ClickUp API token (defaults to CLICKUP_API_TOKEN env var)
            list_id: ClickUp list ID for new leads (defaults to CLICKUP_LIST_ID or Intake list)
            custom_field_ids: Dict mapping field names to ClickUp field IDs
        """
        self.api_token = api_token or os.getenv('CLICKUP_API_TOKEN')
        self.list_id = list_id or os.getenv('CLICKUP_LIST_ID') or self.PIPELINE_LISTS["Intake"]

        if not self.api_token:
            raise ValueError("CLICKUP_API_TOKEN environment variable required")

        self.base_url = "https://api.clickup.com/api/v2"
        self.headers = {
            "Authorization": self.api_token,
            "Content-Type": "application/json"
        }

        # Load custom field IDs
        self.custom_field_ids = custom_field_ids or self._load_custom_field_ids()

        # Sync log
        self.project_root = Path(__file__).parent.parent
        self.sync_log_file = self.project_root / "output" / "apollo_clickup_sync.json"
        self.sync_log_file.parent.mkdir(parents=True, exist_ok=True)
        self._load_sync_log()

    def _load_custom_field_ids(self) -> Dict[str, str]:
        """Load custom field IDs from saved config or fetch from API"""
        config_file = Path(__file__).parent.parent.parent.parent.parent / "execution" / "custom_field_ids.json"

        if config_file.exists():
            with open(config_file, 'r') as f:
                return json.load(f)

        # If no config, return empty (will use description instead of custom fields)
        logger.warning("custom_field_ids.json not found - using description-only mode")
        return {}

    def _load_sync_log(self):
        """Load sync log for deduplication tracking"""
        if self.sync_log_file.exists():
            with open(self.sync_log_file, 'r') as f:
                self.sync_log = json.load(f)
        else:
            self.sync_log = {
                "synced_apollo_ids": [],
                "synced_emails": [],
                "synced_phones": [],
                "sync_history": []
            }

    def _save_sync_log(self):
        """Save sync log"""
        with open(self.sync_log_file, 'w') as f:
            json.dump(self.sync_log, f, indent=2, default=str)

    def qualify_lead(
        self,
        apollo_person: Dict[str, Any],
        campaign_name: str,
        search_profile: str
    ) -> ApolloLeadData:
        """
        Convert raw Apollo person data to structured ApolloLeadData with qualification.

        Args:
            apollo_person: Raw person dict from Apollo API
            campaign_name: Name of the campaign
            search_profile: Name of the search profile used

        Returns:
            ApolloLeadData with qualification level set
        """
        # Extract organization data
        org = apollo_person.get("organization", {}) or {}

        # Extract phone (prefer mobile > direct > corporate)
        phone = ""
        phone_type = ""
        phone_numbers = apollo_person.get("phone_numbers", []) or []
        for pn in phone_numbers:
            if pn.get("type") == "mobile":
                phone = pn.get("raw_number", "")
                phone_type = "mobile"
                break
            elif pn.get("type") == "direct_dial" and not phone:
                phone = pn.get("raw_number", "")
                phone_type = "direct"
            elif pn.get("type") == "corporate" and not phone:
                phone = pn.get("raw_number", "")
                phone_type = "corporate"

        # Get email status
        email = apollo_person.get("email", "")
        email_status = apollo_person.get("email_status", "unknown")

        # Calculate score (0-10 scale)
        score = self._calculate_lead_score(apollo_person, org)

        # Determine qualification
        qualification = self._determine_qualification(
            score=score,
            email=email,
            email_status=email_status,
            phone=phone,
            title=apollo_person.get("title", "")
        )

        return ApolloLeadData(
            apollo_id=apollo_person.get("id", ""),
            first_name=apollo_person.get("first_name", ""),
            last_name=apollo_person.get("last_name", ""),
            email=email,
            email_status=email_status,
            phone=phone,
            phone_type=phone_type,
            company_name=org.get("name", ""),
            company_domain=org.get("website_url", "") or org.get("primary_domain", ""),
            company_size=org.get("estimated_num_employees", 0) or 0,
            industry=org.get("industry", ""),
            title=apollo_person.get("title", ""),
            seniority=apollo_person.get("seniority", ""),
            linkedin_url=apollo_person.get("linkedin_url", ""),
            apollo_score=score,
            qualification=qualification,
            search_profile=search_profile,
            campaign_name=campaign_name,
            city=apollo_person.get("city", "") or org.get("city", ""),
            state=apollo_person.get("state", "") or org.get("state", ""),
            scraped_at=datetime.now().isoformat()
        )

    def _calculate_lead_score(self, person: Dict, org: Dict) -> float:
        """
        Calculate lead score (0-10) based on Apollo data.

        Scoring factors:
        - Email verified: +2
        - Has phone: +2
        - Decision maker title: +2
        - Small business (1-50 employees): +2
        - Has LinkedIn: +1
        - Has company website: +1
        """
        score = 0.0

        # Email quality (max 2 points)
        if person.get("email_status") == "verified":
            score += 2.0
        elif person.get("email_status") == "guessed":
            score += 1.0

        # Phone availability (max 2 points)
        phone_numbers = person.get("phone_numbers", []) or []
        if any(p.get("type") == "mobile" for p in phone_numbers):
            score += 2.0
        elif any(p.get("type") == "direct_dial" for p in phone_numbers):
            score += 1.5
        elif phone_numbers:
            score += 1.0

        # Decision maker title (max 2 points)
        seniority = person.get("seniority", "").lower()
        title = person.get("title", "").lower()

        if seniority in ["owner", "founder", "c_suite"]:
            score += 2.0
        elif seniority in ["vp", "director"]:
            score += 1.5
        elif seniority == "manager":
            score += 1.0
        elif any(t in title for t in ["owner", "ceo", "founder", "president"]):
            score += 2.0

        # Company size - prefer small businesses (max 2 points)
        employees = org.get("estimated_num_employees", 0) or 0
        if 1 <= employees <= 10:
            score += 2.0
        elif 11 <= employees <= 50:
            score += 1.5
        elif 51 <= employees <= 200:
            score += 1.0

        # LinkedIn presence (1 point)
        if person.get("linkedin_url"):
            score += 1.0

        # Company website (1 point)
        if org.get("website_url") or org.get("primary_domain"):
            score += 1.0

        return min(score, 10.0)  # Cap at 10

    def _determine_qualification(
        self,
        score: float,
        email: str,
        email_status: str,
        phone: str,
        title: str
    ) -> LeadQualification:
        """Determine lead qualification level"""

        # Unqualified: no contact method
        if not email and not phone:
            return LeadQualification.UNQUALIFIED

        # Exclude certain titles
        excluded_titles = ["intern", "assistant", "coordinator", "receptionist"]
        if any(t in title.lower() for t in excluded_titles):
            return LeadQualification.UNQUALIFIED

        # Hot: high score + verified email + phone
        if score >= self.HOT_SCORE_THRESHOLD and email_status == "verified" and phone:
            return LeadQualification.HOT

        # Warm: decent score + has email
        if score >= self.WARM_SCORE_THRESHOLD and email:
            return LeadQualification.WARM

        # Cold: everything else with contact info
        if email or phone:
            return LeadQualification.COLD

        return LeadQualification.UNQUALIFIED

    def _is_duplicate(self, lead: ApolloLeadData) -> bool:
        """Check if lead already synced (by Apollo ID, email, or phone)"""
        if lead.apollo_id in self.sync_log["synced_apollo_ids"]:
            return True
        if lead.email and lead.email.lower() in [e.lower() for e in self.sync_log["synced_emails"]]:
            return True
        if lead.phone and lead.phone in self.sync_log["synced_phones"]:
            return True
        return False

    def _load_existing_tasks_cache(self) -> Dict[str, str]:
        """
        Fetch all existing tasks from ClickUp ONCE and build a cache.
        Returns dict mapping email/phone -> task_id for quick lookup.

        This is called once at the start of sync, not per-lead.
        """
        cache = {"emails": {}, "phones": {}}

        try:
            url = f"{self.base_url}/list/{self.list_id}/task"
            params = {"archived": "false", "page": 0}

            all_tasks = []
            while True:
                response = requests.get(url, headers=self.headers, params=params)
                response.raise_for_status()
                tasks = response.json().get("tasks", [])

                if not tasks:
                    break

                all_tasks.extend(tasks)
                params["page"] += 1

                # Safety limit
                if params["page"] > 50:
                    break

            print(f"  Loaded {len(all_tasks)} existing ClickUp tasks for deduplication")

            for task in all_tasks:
                description = task.get("description", "").lower()
                task_id = task["id"]

                # Extract emails from description (simple pattern)
                import re
                emails = re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', description)
                for email in emails:
                    cache["emails"][email.lower()] = task_id

                # Extract phone numbers (digits only for matching)
                phones = re.findall(r'\+?[\d\s\-\(\)]{10,}', description)
                for phone in phones:
                    clean_phone = re.sub(r'[^\d]', '', phone)
                    if len(clean_phone) >= 10:
                        cache["phones"][clean_phone] = task_id

            return cache

        except Exception as e:
            logger.warning(f"Failed to load ClickUp tasks cache: {e}")
            return {"emails": {}, "phones": {}}

    def _search_existing_task_cached(self, lead: ApolloLeadData, cache: Dict) -> Optional[str]:
        """
        Check if lead exists in ClickUp using pre-loaded cache.
        Much faster than API call per lead.
        """
        # Check email
        if lead.email:
            email_lower = lead.email.lower()
            if email_lower in cache.get("emails", {}):
                return cache["emails"][email_lower]

        # Check phone
        if lead.phone:
            import re
            clean_phone = re.sub(r'[^\d]', '', lead.phone)
            if clean_phone in cache.get("phones", {}):
                return cache["phones"][clean_phone]

        return None

    def _search_existing_task(self, lead: ApolloLeadData) -> Optional[str]:
        """
        DEPRECATED: Search ClickUp for existing task with same email/phone.
        Use _search_existing_task_cached() with pre-loaded cache instead.
        """
        try:
            url = f"{self.base_url}/list/{self.list_id}/task"
            params = {"archived": "false"}

            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()

            tasks = response.json().get("tasks", [])

            for task in tasks:
                description = task.get("description", "").lower()

                # Check for email match
                if lead.email and lead.email.lower() in description:
                    return task["id"]

                # Check for phone match
                if lead.phone and lead.phone in description:
                    return task["id"]

            return None

        except Exception as e:
            logger.warning(f"ClickUp search failed: {e}")
            return None

    def _create_task(self, lead: ApolloLeadData, use_custom_fields: bool = True) -> Dict[str, Any]:
        """Create ClickUp task for lead

        Args:
            lead: ApolloLeadData object
            use_custom_fields: Whether to include custom fields (set False if plan limit reached)
        """

        # Task name format: "First Last - Company (Qualification)"
        task_name = f"{lead.first_name} {lead.last_name} - {lead.company_name}"
        if lead.qualification == LeadQualification.HOT:
            task_name += " 🔥"

        # Priority based on qualification
        priority_map = {
            LeadQualification.HOT: 2,      # High
            LeadQualification.WARM: 3,     # Normal
            LeadQualification.COLD: 4,     # Low
            LeadQualification.UNQUALIFIED: 4
        }

        # Build payload
        payload = {
            "name": task_name,
            "description": lead.to_clickup_description(),
            "priority": priority_map.get(lead.qualification, 3),
            "tags": [
                "apollo",
                lead.campaign_name.replace(" ", "-").lower(),
                lead.qualification.value,
                lead.search_profile.replace("_", "-") if lead.search_profile else "custom"
            ]
        }

        # Add custom fields if IDs are available and enabled
        if not use_custom_fields:
            # Skip custom fields - ClickUp plan limit
            pass
        elif self.custom_field_ids:
            custom_fields = []

            # Basic contact fields
            if "Email" in self.custom_field_ids and lead.email:
                custom_fields.append({
                    "id": self.custom_field_ids["Email"],
                    "value": lead.email
                })

            if "Phone" in self.custom_field_ids and lead.phone:
                custom_fields.append({
                    "id": self.custom_field_ids["Phone"],
                    "value": lead.phone
                })

            if "Company" in self.custom_field_ids and lead.company_name:
                custom_fields.append({
                    "id": self.custom_field_ids["Company"],
                    "value": lead.company_name
                })

            # Apollo-specific fields
            if "Apollo ID" in self.custom_field_ids and lead.apollo_id:
                custom_fields.append({
                    "id": self.custom_field_ids["Apollo ID"],
                    "value": lead.apollo_id
                })

            if "Apollo Score" in self.custom_field_ids:
                custom_fields.append({
                    "id": self.custom_field_ids["Apollo Score"],
                    "value": lead.apollo_score
                })

            if "Email Verified" in self.custom_field_ids:
                custom_fields.append({
                    "id": self.custom_field_ids["Email Verified"],
                    "value": lead.email_status == "verified"
                })

            if "Phone Available" in self.custom_field_ids:
                custom_fields.append({
                    "id": self.custom_field_ids["Phone Available"],
                    "value": bool(lead.phone)
                })

            if "Campaign Name" in self.custom_field_ids and lead.campaign_name:
                custom_fields.append({
                    "id": self.custom_field_ids["Campaign Name"],
                    "value": lead.campaign_name
                })

            if "Industry" in self.custom_field_ids and lead.industry:
                custom_fields.append({
                    "id": self.custom_field_ids["Industry"],
                    "value": lead.industry
                })

            if "Company Size" in self.custom_field_ids and lead.company_size:
                custom_fields.append({
                    "id": self.custom_field_ids["Company Size"],
                    "value": lead.company_size
                })

            if "LinkedIn" in self.custom_field_ids and lead.linkedin_url:
                custom_fields.append({
                    "id": self.custom_field_ids["LinkedIn"],
                    "value": lead.linkedin_url
                })

            if "Website" in self.custom_field_ids and lead.company_domain:
                custom_fields.append({
                    "id": self.custom_field_ids["Website"],
                    "value": lead.company_domain
                })

            # Map qualification to Lead Temperature (dropdown)
            if "Lead Temperature" in self.custom_field_ids:
                temp_map = {
                    LeadQualification.HOT: 0,      # First option index
                    LeadQualification.WARM: 1,    # Second option index
                    LeadQualification.COLD: 2     # Third option index
                }
                if lead.qualification in temp_map:
                    custom_fields.append({
                        "id": self.custom_field_ids["Lead Temperature"],
                        "value": temp_map[lead.qualification]
                    })

            # Map seniority (dropdown) - need option index
            if "Seniority" in self.custom_field_ids and lead.seniority:
                seniority_map = {
                    "owner": 0,
                    "founder": 1,
                    "c_suite": 2,
                    "vp": 3,
                    "director": 4,
                    "manager": 5,
                    "senior": 6,
                    "entry": 7
                }
                seniority_lower = lead.seniority.lower()
                if seniority_lower in seniority_map:
                    custom_fields.append({
                        "id": self.custom_field_ids["Seniority"],
                        "value": seniority_map[seniority_lower]
                    })

            # Map search profile (dropdown)
            if "Search Profile" in self.custom_field_ids and lead.search_profile:
                profile_map = {
                    "naples_gyms": 0,
                    "naples_hvac": 1,
                    "naples_restaurants": 2,
                    "small_business_owners": 3,
                    "verified_contacts_only": 4,
                    "decision_makers_all_sizes": 5,
                    "local_service_businesses": 6,
                    "custom": 7
                }
                profile_lower = lead.search_profile.lower()
                if profile_lower in profile_map:
                    custom_fields.append({
                        "id": self.custom_field_ids["Search Profile"],
                        "value": profile_map[profile_lower]
                    })

            # Data Source = apollo (dropdown index 0)
            if "Data Source" in self.custom_field_ids:
                custom_fields.append({
                    "id": self.custom_field_ids["Data Source"],
                    "value": 0  # "apollo" is first option
                })

            if custom_fields:
                payload["custom_fields"] = custom_fields

        # Create task
        url = f"{self.base_url}/list/{self.list_id}/task"
        response = requests.post(url, headers=self.headers, json=payload)

        if response.status_code >= 400:
            error_detail = response.text
            logger.error(f"ClickUp API error: {error_detail}")
            raise Exception(f"ClickUp error: {error_detail}")

        return response.json()

    def _add_comment(self, task_id: str, comment: str):
        """Add comment to existing task"""
        url = f"{self.base_url}/task/{task_id}/comment"
        payload = {"comment_text": comment}

        response = requests.post(url, headers=self.headers, json=payload)
        response.raise_for_status()

    def _record_sync(self, lead: ApolloLeadData, task_id: str, action: str):
        """Record sync in log for deduplication AND save to disk immediately"""
        self._record_sync_memory(lead, task_id, action)
        self._save_sync_log()

    def _record_sync_memory(self, lead: ApolloLeadData, task_id: str, action: str):
        """Record sync in memory only (for batched saves)"""
        if lead.apollo_id and lead.apollo_id not in self.sync_log["synced_apollo_ids"]:
            self.sync_log["synced_apollo_ids"].append(lead.apollo_id)

        if lead.email and lead.email not in self.sync_log["synced_emails"]:
            self.sync_log["synced_emails"].append(lead.email)

        if lead.phone and lead.phone not in self.sync_log["synced_phones"]:
            self.sync_log["synced_phones"].append(lead.phone)

        self.sync_log["sync_history"].append({
            "timestamp": datetime.now().isoformat(),
            "apollo_id": lead.apollo_id,
            "name": f"{lead.first_name} {lead.last_name}",
            "company": lead.company_name,
            "qualification": lead.qualification.value,
            "score": lead.apollo_score,
            "task_id": task_id,
            "action": action,
            "campaign": lead.campaign_name
        })

    def sync_apollo_leads(
        self,
        leads: List[Dict[str, Any]],
        campaign_name: str,
        search_profile: str = "custom",
        min_score: float = None,
        min_qualification: LeadQualification = None,
        require_verified_email: bool = False,
        require_phone: bool = False,
        dry_run: bool = True,
        use_custom_fields: bool = False,
        batch_size: int = None,
        delay_seconds: float = 0.5
    ) -> Dict[str, Any]:
        """
        Sync Apollo leads to ClickUp with filtering.

        Args:
            leads: List of raw Apollo person dicts
            campaign_name: Campaign name for tracking
            search_profile: Search profile name used
            min_score: Minimum score to sync (0-10)
            min_qualification: Minimum qualification level (HOT, WARM, COLD)
            require_verified_email: Only sync verified emails
            require_phone: Only sync leads with phone numbers
            dry_run: If True, don't actually create tasks
            use_custom_fields: Whether to populate custom fields (False if plan limit)
            batch_size: Max number of leads to sync (None = all qualified leads)
            delay_seconds: Delay between API calls to avoid rate limits (default 0.5s)

        Returns:
            Sync results summary
        """
        import time
        results = {
            "campaign": campaign_name,
            "search_profile": search_profile,
            "dry_run": dry_run,
            "timestamp": datetime.now().isoformat(),
            "total_leads": len(leads),
            "qualified": [],
            "filtered_out": [],
            "duplicates": [],
            "synced": [],
            "errors": []
        }

        # Set default filters
        if min_score is None:
            min_score = self.WARM_SCORE_THRESHOLD

        if min_qualification is None:
            min_qualification = LeadQualification.WARM

        qualification_order = [
            LeadQualification.UNQUALIFIED,
            LeadQualification.COLD,
            LeadQualification.WARM,
            LeadQualification.HOT
        ]
        min_qual_index = qualification_order.index(min_qualification)

        # Pre-load existing tasks cache ONCE (not per lead)
        clickup_task_cache = {}
        if not dry_run:
            print("  Loading existing ClickUp tasks for deduplication...")
            clickup_task_cache = self._load_existing_tasks_cache()

        for apollo_person in leads:
            try:
                # Convert to structured data
                lead = self.qualify_lead(apollo_person, campaign_name, search_profile)

                # Apply filters
                filter_reasons = []

                if lead.apollo_score < min_score:
                    filter_reasons.append(f"score {lead.apollo_score:.1f} < {min_score}")

                qual_index = qualification_order.index(lead.qualification)
                if qual_index < min_qual_index:
                    filter_reasons.append(f"qualification {lead.qualification.value} < {min_qualification.value}")

                if require_verified_email and lead.email_status != "verified":
                    filter_reasons.append(f"email not verified ({lead.email_status})")

                if require_phone and not lead.phone:
                    filter_reasons.append("no phone number")

                if filter_reasons:
                    results["filtered_out"].append({
                        "name": f"{lead.first_name} {lead.last_name}",
                        "company": lead.company_name,
                        "score": lead.apollo_score,
                        "qualification": lead.qualification.value,
                        "reasons": filter_reasons
                    })
                    continue

                # Check for duplicates
                if self._is_duplicate(lead):
                    results["duplicates"].append({
                        "name": f"{lead.first_name} {lead.last_name}",
                        "company": lead.company_name,
                        "email": lead.email
                    })
                    continue

                results["qualified"].append({
                    "name": f"{lead.first_name} {lead.last_name}",
                    "company": lead.company_name,
                    "score": lead.apollo_score,
                    "qualification": lead.qualification.value,
                    "email": lead.email,
                    "phone": lead.phone
                })

                if not dry_run:
                    # Check batch limit
                    if batch_size and len(results["synced"]) >= batch_size:
                        results["batch_limit_reached"] = True
                        results["remaining_qualified"] = len(results["qualified"]) - len(results["synced"])
                        break

                    # Check for existing task in ClickUp using CACHED lookup (no API call)
                    existing_task_id = self._search_existing_task_cached(lead, clickup_task_cache)

                    if existing_task_id:
                        # Add comment to existing task
                        comment = f"**New touchpoint from Apollo campaign:** {campaign_name}\n\nScore: {lead.apollo_score}/10"
                        self._add_comment(existing_task_id, comment)
                        action = "added_comment"
                        task_id = existing_task_id
                    else:
                        # Create new task
                        task = self._create_task(lead, use_custom_fields=use_custom_fields)
                        task_id = task["id"]
                        action = "created_task"

                        # Add to cache so subsequent leads can find it
                        if lead.email:
                            clickup_task_cache.setdefault("emails", {})[lead.email.lower()] = task_id
                        if lead.phone:
                            import re
                            clean_phone = re.sub(r'[^\d]', '', lead.phone)
                            clickup_task_cache.setdefault("phones", {})[clean_phone] = task_id

                    # Record sync (but don't save to disk yet - batch at end)
                    self._record_sync_memory(lead, task_id, action)

                    results["synced"].append({
                        "name": f"{lead.first_name} {lead.last_name}",
                        "company": lead.company_name,
                        "task_id": task_id,
                        "action": action
                    })

                    # Progress update every 10 synced
                    if len(results["synced"]) % 10 == 0:
                        print(f"  Progress: {len(results['synced'])} synced...")

                    # Rate limiting delay
                    if delay_seconds > 0:
                        time.sleep(delay_seconds)

            except Exception as e:
                logger.error(f"Error processing lead: {e}")
                results["errors"].append({
                    "apollo_id": apollo_person.get("id", "unknown"),
                    "error": str(e)
                })

        # Save sync log once at the end (batched, not per-lead)
        if not dry_run and results["synced"]:
            self._save_sync_log()
            print(f"  Sync log saved ({len(results['synced'])} entries)")

        # Summary
        results["summary"] = {
            "total": len(leads),
            "qualified": len(results["qualified"]),
            "filtered_out": len(results["filtered_out"]),
            "duplicates": len(results["duplicates"]),
            "synced": len(results["synced"]),
            "errors": len(results["errors"])
        }

        return results


def main():
    """CLI for Apollo → ClickUp sync"""
    import sys
    import argparse

    parser = argparse.ArgumentParser(description="Sync Apollo leads to ClickUp")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Sync command
    sync_parser = subparsers.add_parser("sync", help="Sync Apollo leads to ClickUp")
    sync_parser.add_argument("--campaign", help="Campaign name", default="Apollo Import")
    sync_parser.add_argument("--profile", help="Search profile used", default="custom")
    sync_parser.add_argument("--min-score", type=float, default=6.0, help="Minimum score (0-10)")
    sync_parser.add_argument("--dry-run", action="store_true", help="Don't actually sync")
    sync_parser.add_argument("--for-real", action="store_true", help="Actually sync to ClickUp")
    sync_parser.add_argument("--hot-only", action="store_true", help="Only sync HOT leads")
    sync_parser.add_argument("--verified-only", action="store_true", help="Only verified emails")
    sync_parser.add_argument("--no-custom-fields", action="store_true", help="Skip custom fields (use if ClickUp plan limit reached)")
    sync_parser.add_argument("--batch-size", type=int, help="Max leads to sync in this run (for large imports)")
    sync_parser.add_argument("--delay", type=float, default=0.5, help="Delay between API calls in seconds (default 0.5)")
    sync_parser.add_argument("--input", help="JSON file with Apollo leads")

    # Status command
    status_parser = subparsers.add_parser("status", help="Show sync status and history")

    # Clear-log command
    clear_parser = subparsers.add_parser("clear-log", help="Clear sync log (reset deduplication)")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "sync":
        # Verify mode
        if not args.dry_run and not args.for_real:
            print("Specify --dry-run or --for-real")
            sys.exit(1)

        dry_run = args.dry_run or not args.for_real

        # Load leads
        if args.input:
            with open(args.input, 'r') as f:
                data = json.load(f)
                leads = data.get("people", data) if isinstance(data, dict) else data
        else:
            print("No input file specified. Use --input <file.json>")
            print("\nExample: Export Apollo search results to JSON first:")
            print("  python -m src.apollo search --profile naples_gyms --output leads.json")
            print("  python -m src.apollo_to_clickup sync --input leads.json --dry-run")
            sys.exit(1)

        # Initialize sync
        try:
            sync = ApolloClickUpSync()
        except ValueError as e:
            print(f"Error: {e}")
            print("\nSet these environment variables:")
            print("  export CLICKUP_API_TOKEN='your_token'")
            print("  export CLICKUP_LIST_ID='your_list_id'  # optional")
            sys.exit(1)

        # Set filters
        min_qual = LeadQualification.HOT if args.hot_only else LeadQualification.WARM

        # Run sync
        use_custom_fields = not getattr(args, 'no_custom_fields', False)
        batch_size = getattr(args, 'batch_size', None)
        delay = getattr(args, 'delay', 0.5)

        if batch_size:
            print(f"\n⚙️  Batch mode: syncing up to {batch_size} leads")
        if delay > 0:
            print(f"⚙️  Rate limiting: {delay}s delay between API calls")

        results = sync.sync_apollo_leads(
            leads=leads,
            campaign_name=args.campaign,
            search_profile=args.profile,
            min_score=args.min_score,
            min_qualification=min_qual,
            require_verified_email=args.verified_only,
            dry_run=dry_run,
            use_custom_fields=use_custom_fields,
            batch_size=batch_size,
            delay_seconds=delay
        )

        # Print results
        mode = "DRY RUN" if dry_run else "LIVE SYNC"
        print(f"\n{'='*60}")
        print(f"APOLLO → CLICKUP SYNC: {mode}")
        print(f"{'='*60}")
        print(f"Campaign: {results['campaign']}")
        print(f"Profile: {results['search_profile']}")
        print(f"Filters: min_score={args.min_score}, min_qual={min_qual.value}")
        if args.verified_only:
            print(f"         verified_email=True")

        print(f"\n📊 Summary:")
        print(f"  Total leads:    {results['summary']['total']}")
        print(f"  Qualified:      {results['summary']['qualified']}")
        print(f"  Filtered out:   {results['summary']['filtered_out']}")
        print(f"  Duplicates:     {results['summary']['duplicates']}")
        if not dry_run:
            print(f"  Synced:         {results['summary']['synced']}")
        print(f"  Errors:         {results['summary']['errors']}")

        if results["qualified"]:
            print(f"\n✅ Qualified Leads ({len(results['qualified'])}):")
            for lead in results["qualified"][:10]:  # Show first 10
                print(f"  • {lead['name']} @ {lead['company']}")
                print(f"    Score: {lead['score']:.1f} | {lead['qualification'].upper()}")
                print(f"    Email: {lead['email']} | Phone: {lead['phone'] or 'N/A'}")
            if len(results["qualified"]) > 10:
                print(f"  ... and {len(results['qualified']) - 10} more")

        if results["filtered_out"] and dry_run:
            print(f"\n❌ Filtered Out ({len(results['filtered_out'])}):")
            for lead in results["filtered_out"][:5]:
                print(f"  • {lead['name']} @ {lead['company']}")
                print(f"    Reasons: {', '.join(lead['reasons'])}")
            if len(results["filtered_out"]) > 5:
                print(f"  ... and {len(results['filtered_out']) - 5} more")

        if not dry_run and results["synced"]:
            print(f"\n🚀 Synced to ClickUp ({len(results['synced'])}):")
            for lead in results["synced"]:
                print(f"  • {lead['name']} @ {lead['company']}")
                print(f"    Task: {lead['task_id']} ({lead['action']})")

        # Batch limit info
        if results.get("batch_limit_reached"):
            remaining = results.get("remaining_qualified", 0)
            print(f"\n⚠️  Batch limit reached ({batch_size} leads synced)")
            print(f"   Remaining qualified leads: {remaining}")
            print(f"   Run again to continue syncing the next batch")

        # Save results to file
        output_file = Path(__file__).parent.parent / "output" / "last_sync_results.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\n📁 Full results saved to: {output_file}")

    elif args.command == "status":
        sync = ApolloClickUpSync()

        print("\n=== APOLLO → CLICKUP SYNC STATUS ===\n")
        print(f"Synced Apollo IDs: {len(sync.sync_log['synced_apollo_ids'])}")
        print(f"Synced Emails: {len(sync.sync_log['synced_emails'])}")
        print(f"Synced Phones: {len(sync.sync_log['synced_phones'])}")
        print(f"Total Sync Operations: {len(sync.sync_log['sync_history'])}")

        # Recent syncs
        recent = sync.sync_log['sync_history'][-10:]
        if recent:
            print("\nRecent Syncs:")
            for entry in recent:
                print(f"  {entry['timestamp'][:16]} - {entry['name']} ({entry['action']})")

    elif args.command == "clear-log":
        sync = ApolloClickUpSync()
        sync.sync_log = {
            "synced_apollo_ids": [],
            "synced_emails": [],
            "synced_phones": [],
            "sync_history": []
        }
        sync._save_sync_log()
        print("Sync log cleared!")


if __name__ == "__main__":
    main()
