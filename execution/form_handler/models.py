"""
Data models for form submissions and leads.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
import json
import uuid


class LeadSource(Enum):
    """Source pages for form submissions."""
    HOME_PAGE = "home-page"
    CONTACT_PAGE = "contact-page"
    FITNESS_INFLUENCER = "fitness_influencer_landing"
    INTERVIEW_PREP = "interview_prep_landing"
    AMAZON_SELLER = "amazon_seller_landing"
    MEDTECH = "medtech_landing"
    OTHER = "other"


class LeadStatus(Enum):
    """Lead status in CRM pipeline."""
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    PROPOSAL_SENT = "proposal_sent"
    NEGOTIATING = "negotiating"
    WON = "won"
    LOST = "lost"


class InterestArea(Enum):
    """Project interest areas."""
    FITNESS_INFLUENCER = "Fitness Influencer AI"
    INTERVIEW_PREP = "Interview Prep AI"
    AMAZON_SELLER = "Amazon Seller AI"
    MEDTECH = "MedTech Solutions"
    CUSTOM = "Custom AI Solution"
    GENERAL = "General Inquiry"


@dataclass
class FormSubmission:
    """
    Represents a form submission from any page.

    Attributes:
        name: Full name of the submitter
        email: Email address (required)
        phone: Phone number (optional)
        message: Free-form message or question
        source: Which page the form was submitted from
        interest: Which project they're interested in
        email_opt_in: Consented to email marketing
        sms_opt_in: Consented to SMS marketing

        # Fitness-specific fields
        social_handle: Social media handle (for fitness influencers)
        followers: Approximate follower count

        # Metadata
        submission_id: Unique identifier
        timestamp: When the form was submitted
        ip_address: Submitter's IP (for fraud detection)
        user_agent: Browser info
        utm_source: Marketing attribution
        utm_medium: Marketing attribution
        utm_campaign: Marketing attribution

        # Processing status
        processed: Whether all integrations completed
        clickup_task_id: Created ClickUp task ID
        google_sheet_row: Row number in Google Sheets
        errors: Any errors during processing
    """
    # Required fields
    email: str

    # Common optional fields
    name: str = ""
    phone: str = ""
    message: str = ""
    source: str = LeadSource.OTHER.value
    interest: str = ""

    # Consent fields
    email_opt_in: bool = True
    sms_opt_in: bool = False

    # Fitness influencer specific
    social_handle: str = ""
    followers: str = ""

    # Metadata (auto-populated)
    submission_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    ip_address: str = ""
    user_agent: str = ""
    utm_source: str = ""
    utm_medium: str = ""
    utm_campaign: str = ""

    # Processing status
    processed: bool = False
    clickup_task_id: str = ""
    google_sheet_row: int = 0
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FormSubmission':
        """Create FormSubmission from dictionary."""
        # Filter to only known fields
        known_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered_data = {k: v for k, v in data.items() if k in known_fields}
        return cls(**filtered_data)

    @classmethod
    def from_json(cls, json_str: str) -> 'FormSubmission':
        """Create FormSubmission from JSON string."""
        return cls.from_dict(json.loads(json_str))

    def get_display_name(self) -> str:
        """Get display name for CRM/notifications."""
        if self.name:
            return self.name
        if self.social_handle:
            return self.social_handle
        return self.email.split('@')[0]

    def get_source_label(self) -> str:
        """Get human-readable source label."""
        source_labels = {
            "home-page": "Home Page",
            "contact-page": "Contact Page",
            "fitness_influencer_landing": "Fitness Influencer Landing",
            "interview_prep_landing": "Interview Prep Landing",
            "amazon_seller_landing": "Amazon Seller Landing",
            "medtech_landing": "MedTech Landing",
            "coming-soon-page": "Coming Soon Page",
        }
        return source_labels.get(self.source, self.source)

    def to_clickup_description(self) -> str:
        """Generate formatted description for ClickUp task."""
        lines = [
            f"**Lead Source:** {self.get_source_label()}",
            f"**Submitted:** {self.timestamp}",
            "",
            "## Contact Information",
            f"- **Name:** {self.name or 'Not provided'}",
            f"- **Email:** {self.email}",
            f"- **Phone:** {self.phone or 'Not provided'}",
        ]

        if self.social_handle or self.followers:
            lines.extend([
                "",
                "## Social Media",
                f"- **Handle:** {self.social_handle or 'Not provided'}",
                f"- **Followers:** {self.followers or 'Not provided'}",
            ])

        if self.interest:
            lines.extend([
                "",
                f"## Interest Area",
                f"{self.interest}",
            ])

        if self.message:
            lines.extend([
                "",
                "## Message",
                self.message,
            ])

        lines.extend([
            "",
            "## Marketing Consent",
            f"- Email opt-in: {'Yes' if self.email_opt_in else 'No'}",
            f"- SMS opt-in: {'Yes' if self.sms_opt_in else 'No'}",
        ])

        if self.utm_source or self.utm_campaign:
            lines.extend([
                "",
                "## Attribution",
                f"- Source: {self.utm_source or 'Direct'}",
                f"- Medium: {self.utm_medium or 'N/A'}",
                f"- Campaign: {self.utm_campaign or 'N/A'}",
            ])

        return "\n".join(lines)

    def to_sheet_row(self) -> List[Any]:
        """Convert to a row for Google Sheets."""
        return [
            self.timestamp,
            self.submission_id,
            self.name,
            self.email,
            self.phone,
            self.source,
            self.interest,
            self.message,
            self.social_handle,
            self.followers,
            "Yes" if self.email_opt_in else "No",
            "Yes" if self.sms_opt_in else "No",
            self.utm_source,
            self.utm_medium,
            self.utm_campaign,
            self.clickup_task_id,
            "Processed" if self.processed else "Pending",
        ]

    @staticmethod
    def get_sheet_headers() -> List[str]:
        """Get column headers for Google Sheets."""
        return [
            "Timestamp",
            "Submission ID",
            "Name",
            "Email",
            "Phone",
            "Source",
            "Interest",
            "Message",
            "Social Handle",
            "Followers",
            "Email Opt-In",
            "SMS Opt-In",
            "UTM Source",
            "UTM Medium",
            "UTM Campaign",
            "ClickUp Task ID",
            "Status",
        ]
