#!/usr/bin/env python3
"""
config.py - Configuration for Elder Tech Concierge

WHAT: Central configuration for API keys, contacts, and settings
WHY: Keep all settings in one place for easy management
"""

import os
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@dataclass
class Contact:
    """Contact information for family members or emergency contacts."""
    name: str
    phone: str
    email: Optional[str] = None
    relationship: str = "Family"
    is_emergency: bool = False


@dataclass
class Config:
    """Main configuration class for Elder Tech Concierge."""

    # Claude API
    claude_api_key: str = field(default_factory=lambda: os.getenv('ANTHROPIC_API_KEY', ''))
    claude_model: str = "claude-sonnet-4-20250514"

    # Twilio SMS
    twilio_account_sid: str = field(default_factory=lambda: os.getenv('TWILIO_ACCOUNT_SID', ''))
    twilio_auth_token: str = field(default_factory=lambda: os.getenv('TWILIO_AUTH_TOKEN', ''))
    twilio_phone_number: str = field(default_factory=lambda: os.getenv('TWILIO_PHONE_NUMBER', ''))

    # Google APIs (Gmail, Calendar)
    google_credentials_path: str = "credentials.json"
    google_token_path: str = "token.json"

    # Application settings
    app_name: str = "Elder Tech Assistant"
    app_host: str = "0.0.0.0"
    app_port: int = 8080
    debug: bool = True

    # UI Settings (Senior-friendly defaults)
    min_font_size: int = 24  # pixels
    default_font_size: int = 32  # pixels
    min_button_size: int = 88  # pixels (Apple HIG recommendation)
    default_button_size: int = 120  # pixels
    high_contrast: bool = True

    # Voice settings
    speech_rate: float = 0.8  # Slower speech for clarity
    voice_volume: float = 1.0

    # Emergency contacts (populated from environment or set manually)
    emergency_contacts: List[Contact] = field(default_factory=list)
    family_contacts: List[Contact] = field(default_factory=list)

    # Paths
    base_dir: Path = field(default_factory=lambda: Path(__file__).parent)
    templates_dir: Path = field(default_factory=lambda: Path(__file__).parent / "templates")
    static_dir: Path = field(default_factory=lambda: Path(__file__).parent / "static")

    def __post_init__(self):
        """Load contacts from environment variables."""
        self._load_emergency_contacts()
        self._load_family_contacts()

    def _load_emergency_contacts(self):
        """Load emergency contacts from environment variables."""
        # Format: EMERGENCY_CONTACT_1="Name|Phone|Email|Relationship"
        for i in range(1, 6):  # Up to 5 emergency contacts
            contact_str = os.getenv(f'EMERGENCY_CONTACT_{i}', '')
            if contact_str:
                parts = contact_str.split('|')
                if len(parts) >= 2:
                    self.emergency_contacts.append(Contact(
                        name=parts[0],
                        phone=parts[1],
                        email=parts[2] if len(parts) > 2 else None,
                        relationship=parts[3] if len(parts) > 3 else "Emergency Contact",
                        is_emergency=True
                    ))

    def _load_family_contacts(self):
        """Load family contacts from environment variables."""
        # Format: FAMILY_CONTACT_1="Name|Phone|Email|Relationship"
        for i in range(1, 11):  # Up to 10 family contacts
            contact_str = os.getenv(f'FAMILY_CONTACT_{i}', '')
            if contact_str:
                parts = contact_str.split('|')
                if len(parts) >= 2:
                    self.family_contacts.append(Contact(
                        name=parts[0],
                        phone=parts[1],
                        email=parts[2] if len(parts) > 2 else None,
                        relationship=parts[3] if len(parts) > 3 else "Family"
                    ))

    def get_all_contacts(self) -> List[Contact]:
        """Get all contacts (family + emergency)."""
        return self.family_contacts + self.emergency_contacts

    def validate(self) -> Dict[str, bool]:
        """Validate configuration - check which services are available."""
        return {
            'claude_api': bool(self.claude_api_key),
            'twilio_sms': bool(self.twilio_account_sid and self.twilio_auth_token and self.twilio_phone_number),
            'google_apis': Path(self.google_credentials_path).exists(),
            'emergency_contacts': len(self.emergency_contacts) > 0,
            'family_contacts': len(self.family_contacts) > 0
        }

    def print_status(self):
        """Print configuration status."""
        validation = self.validate()

        print("\n" + "=" * 60)
        print("ELDER TECH CONCIERGE - Configuration Status")
        print("=" * 60 + "\n")

        status_map = {True: "[OK]", False: "[MISSING]"}

        print(f"  Claude API:        {status_map[validation['claude_api']]}")
        print(f"  Twilio SMS:        {status_map[validation['twilio_sms']]}")
        print(f"  Google APIs:       {status_map[validation['google_apis']]}")
        print(f"  Emergency Contacts:{status_map[validation['emergency_contacts']]} ({len(self.emergency_contacts)} configured)")
        print(f"  Family Contacts:   {status_map[validation['family_contacts']]} ({len(self.family_contacts)} configured)")

        print("\n" + "=" * 60 + "\n")


# Global configuration instance
config = Config()


# Default system prompt for Claude when helping seniors
ELDER_ASSISTANT_SYSTEM_PROMPT = """You are a friendly, patient, and helpful assistant for an elderly person using a tablet device.

COMMUNICATION STYLE:
- Use simple, clear language
- Speak in short sentences
- Be warm, patient, and reassuring
- Never use jargon or technical terms
- If something is complex, break it into simple steps
- Always confirm understanding before proceeding

RESPONSE FORMAT:
- Keep responses brief (2-3 sentences when possible)
- For instructions, number each step clearly
- Speak as if you're talking to a friend
- Use encouraging language

SAFETY FIRST:
- If the user mentions feeling unwell, dizzy, or having chest pain, immediately suggest calling emergency services
- Never give medical advice - suggest calling their doctor or 911
- For any emergency, help them contact their emergency contacts

AVAILABLE ACTIONS YOU CAN HELP WITH:
1. Send text messages to family members
2. Read recent emails aloud
3. Check today's calendar/schedule
4. Call family members
5. Get help in an emergency

Remember: Be patient, kind, and reassuring. Many seniors may feel anxious about technology - your calm, friendly demeanor helps them feel comfortable."""


if __name__ == "__main__":
    config.print_status()
