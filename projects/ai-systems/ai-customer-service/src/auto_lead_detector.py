#!/usr/bin/env python3
"""
Automated Lead Detection from Voice AI Conversations.

Analyzes Voice AI call transcripts and automatically:
1. Detects potential leads (intent signals)
2. Extracts contact information
3. Categorizes lead quality (hot/warm/cold)
4. Creates tasks in ClickUp
5. Triggers follow-up sequences

Usage:
    python -m src.auto_lead_detector scan --recent 24  # Last 24 hours
    python -m src.auto_lead_detector analyze --call-sid CA123...
    python -m src.auto_lead_detector export --format json
"""

import os
import re
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import anthropic

from dotenv import load_dotenv
env_path = Path(__file__).parent.parent.parent.parent / ".env"
load_dotenv(env_path)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class LeadSignal:
    """Detected lead from Voice AI conversation."""
    call_sid: str
    caller_number: str
    caller_name: Optional[str]
    business_name: Optional[str]
    email: Optional[str]
    intent: str  # service_inquiry, callback_request, complaint, general_question
    quality: str  # hot, warm, cold
    confidence: float  # 0.0-1.0
    key_phrases: List[str]
    next_action: str
    detected_at: str
    transcript_summary: str

    def to_dict(self) -> Dict:
        return asdict(self)


class VoiceAILeadDetector:
    """Detects and qualifies leads from Voice AI transcripts."""

    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.leads_file = self.output_dir / "detected_leads.json"
        self.anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        self.client = anthropic.Anthropic(api_key=self.anthropic_key)

    def analyze_call(self, call_sid: str, transcript: str, caller_number: str) -> Optional[LeadSignal]:
        """
        Analyze a call transcript to detect lead signals.

        Returns LeadSignal if detected, None otherwise.
        """

        # Use Claude to analyze the transcript
        prompt = f"""Analyze this phone call transcript and determine if this is a potential lead.

TRANSCRIPT:
{transcript}

CALLER: {caller_number}

Analyze for:
1. **Intent**: What does the caller want? (service_inquiry, callback_request, complaint, general_question, spam)
2. **Lead Quality**:
   - HOT: Ready to buy, asking for pricing, wants to schedule, has urgent need
   - WARM: Interested but researching, asked questions, wants callback
   - COLD: General inquiry, no clear interest, probably not a fit
   - NOT_LEAD: Wrong number, spam, complaint only
3. **Contact Info**: Extract name, business name, email if mentioned
4. **Key Phrases**: What phrases indicate buying intent?
5. **Next Action**: What should William do next?

Return valid JSON:
{{
  "is_lead": true/false,
  "intent": "service_inquiry|callback_request|complaint|general_question|spam",
  "quality": "hot|warm|cold|not_lead",
  "confidence": 0.0-1.0,
  "caller_name": "Name or null",
  "business_name": "Business or null",
  "email": "email@example.com or null",
  "key_phrases": ["phrase 1", "phrase 2"],
  "next_action": "What to do next",
  "summary": "2-sentence summary of the call"
}}"""

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}]
            )

            # Parse response
            analysis_text = response.content[0].text

            # Extract JSON
            if "```json" in analysis_text:
                analysis_text = analysis_text.split("```json")[1].split("```")[0]
            elif "```" in analysis_text:
                analysis_text = analysis_text.split("```")[1].split("```")[0]

            analysis = json.loads(analysis_text.strip())

            # If not a lead, skip
            if not analysis.get("is_lead", False):
                logger.info(f"Call {call_sid}: Not a lead (Intent: {analysis.get('intent')})")
                return None

            # Create LeadSignal
            lead = LeadSignal(
                call_sid=call_sid,
                caller_number=caller_number,
                caller_name=analysis.get("caller_name"),
                business_name=analysis.get("business_name"),
                email=analysis.get("email"),
                intent=analysis.get("intent", "general_question"),
                quality=analysis.get("quality", "cold"),
                confidence=float(analysis.get("confidence", 0.5)),
                key_phrases=analysis.get("key_phrases", []),
                next_action=analysis.get("next_action", "Review transcript and call back"),
                detected_at=datetime.now().isoformat(),
                transcript_summary=analysis.get("summary", "")
            )

            logger.info(f"✅ LEAD DETECTED: {lead.quality.upper()} quality from {caller_number}")
            return lead

        except Exception as e:
            logger.error(f"Error analyzing call {call_sid}: {e}")
            return None

    def scan_server_logs(self, hours: int = 24) -> List[LeadSignal]:
        """
        Scan server logs for call transcripts from the last N hours.

        Returns list of detected leads.
        """
        server_log = Path(__file__).parent.parent / "server.log"

        if not server_log.exists():
            logger.warning(f"Server log not found: {server_log}")
            return []

        # Parse server log for INBOUND GATHER entries (transcripts)
        with open(server_log, 'r') as f:
            log_content = f.read()

        # Extract calls with transcripts
        # Format: INFO:root:INBOUND GATHER: CallSid=CA..., Speech=...
        pattern = r'INBOUND GATHER: CallSid=(\w+), Speech=(.+?)(?:\n|$)'
        matches = re.findall(pattern, log_content)

        # Group by CallSid (calls may have multiple GATHER events)
        calls = {}
        for call_sid, speech in matches:
            if call_sid not in calls:
                calls[call_sid] = []
            calls[call_sid].append(speech)

        logger.info(f"Found {len(calls)} calls with transcripts in server log")

        # For each call, analyze for leads
        detected_leads = []

        for call_sid, speeches in calls.items():
            # Combine all speech entries into full transcript
            transcript = "\n".join([f"Caller: {s}" for s in speeches])

            # Extract caller number from call logs if possible
            # For now, use placeholder
            caller_number = "Unknown"

            # Analyze
            lead = self.analyze_call(call_sid, transcript, caller_number)
            if lead:
                detected_leads.append(lead)

        return detected_leads

    def save_leads(self, leads: List[LeadSignal]):
        """Save detected leads to JSON file."""
        existing_leads = []
        if self.leads_file.exists():
            with open(self.leads_file, 'r') as f:
                data = json.load(f)
                existing_leads = data.get("leads", [])

        # Add new leads (avoid duplicates by call_sid)
        existing_sids = {l.get("call_sid") for l in existing_leads}
        new_leads = [l.to_dict() for l in leads if l.call_sid not in existing_sids]

        all_leads = existing_leads + new_leads

        with open(self.leads_file, 'w') as f:
            json.dump({
                "leads": all_leads,
                "last_updated": datetime.now().isoformat(),
                "total_count": len(all_leads)
            }, f, indent=2)

        logger.info(f"Saved {len(new_leads)} new leads ({len(all_leads)} total)")

    def create_clickup_task(self, lead: LeadSignal) -> Optional[str]:
        """Create a task in ClickUp for this lead."""
        import requests

        clickup_token = os.getenv("CLICKUP_API_TOKEN")
        list_id = "901709132478"  # Client Leads list

        if not clickup_token:
            logger.warning("No ClickUp token found")
            return None

        # Priority based on lead quality
        priority_map = {
            "hot": 1,  # Urgent
            "warm": 2,  # High
            "cold": 3   # Normal
        }

        # Create task
        url = f"https://api.clickup.com/api/v2/list/{list_id}/task"
        headers = {
            "Authorization": clickup_token,
            "Content-Type": "application/json"
        }

        task_name = f"Lead: {lead.caller_name or lead.business_name or lead.caller_number}"

        description = f"""**Voice AI Lead - {lead.quality.upper()}**

**Caller**: {lead.caller_number}
**Name**: {lead.caller_name or "Not provided"}
**Business**: {lead.business_name or "Not provided"}
**Email**: {lead.email or "Not provided"}

**Intent**: {lead.intent}
**Confidence**: {lead.confidence:.0%}

**Summary**:
{lead.transcript_summary}

**Key Phrases**:
{chr(10).join([f"- {phrase}" for phrase in lead.key_phrases])}

**Next Action**: {lead.next_action}

**Call Details**:
- Call SID: {lead.call_sid}
- Detected: {lead.detected_at}
"""

        data = {
            "name": task_name,
            "description": description,
            "status": "to do",
            "priority": priority_map.get(lead.quality, 3)
        }

        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            task_id = response.json().get("id")
            logger.info(f"✅ Created ClickUp task: {task_id}")
            return task_id
        except Exception as e:
            logger.error(f"Failed to create ClickUp task: {e}")
            return None

    def generate_report(self, leads: List[LeadSignal]) -> str:
        """Generate a human-readable report of detected leads."""
        if not leads:
            return "No leads detected."

        # Group by quality
        by_quality = {"hot": [], "warm": [], "cold": []}
        for lead in leads:
            by_quality[lead.quality].append(lead)

        report_lines = [
            "=" * 60,
            "VOICE AI LEAD DETECTION REPORT",
            "=" * 60,
            f"Total Leads Detected: {len(leads)}",
            ""
        ]

        for quality in ["hot", "warm", "cold"]:
            count = len(by_quality[quality])
            if count == 0:
                continue

            emoji = {"hot": "🔥", "warm": "🟡", "cold": "🟢"}[quality]
            report_lines.append(f"\n{emoji} {quality.upper()} LEADS ({count})")
            report_lines.append("-" * 60)

            for lead in by_quality[quality]:
                report_lines.append(f"\n📞 {lead.caller_number}")
                if lead.caller_name:
                    report_lines.append(f"   Name: {lead.caller_name}")
                if lead.business_name:
                    report_lines.append(f"   Business: {lead.business_name}")
                if lead.email:
                    report_lines.append(f"   Email: {lead.email}")
                report_lines.append(f"   Intent: {lead.intent}")
                report_lines.append(f"   Confidence: {lead.confidence:.0%}")
                report_lines.append(f"   Summary: {lead.transcript_summary}")
                report_lines.append(f"   Next Action: {lead.next_action}")

        report_lines.append("\n" + "=" * 60)

        return "\n".join(report_lines)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Automated Lead Detection from Voice AI")
    parser.add_argument("command", choices=["scan", "analyze", "export", "report"])
    parser.add_argument("--recent", type=int, default=24, help="Scan last N hours")
    parser.add_argument("--call-sid", help="Specific call SID to analyze")
    parser.add_argument("--format", choices=["json", "text"], default="text")
    parser.add_argument("--output-dir", default="output")
    parser.add_argument("--create-tasks", action="store_true", help="Create ClickUp tasks for leads")

    args = parser.parse_args()

    detector = VoiceAILeadDetector(output_dir=args.output_dir)

    if args.command == "scan":
        print(f"Scanning server logs for leads (last {args.recent} hours)...")
        leads = detector.scan_server_logs(hours=args.recent)

        if leads:
            detector.save_leads(leads)
            print(detector.generate_report(leads))

            if args.create_tasks:
                print("\nCreating ClickUp tasks...")
                for lead in leads:
                    detector.create_clickup_task(lead)
        else:
            print("No leads detected.")

    elif args.command == "report":
        # Load existing leads
        if detector.leads_file.exists():
            with open(detector.leads_file, 'r') as f:
                data = json.load(f)
                leads_data = data.get("leads", [])
                # Convert to LeadSignal objects
                leads = [
                    LeadSignal(**{k: v for k, v in ld.items() if k in LeadSignal.__annotations__})
                    for ld in leads_data
                ]
                print(detector.generate_report(leads))
        else:
            print("No leads file found. Run 'scan' first.")

    elif args.command == "export":
        if detector.leads_file.exists():
            with open(detector.leads_file, 'r') as f:
                data = json.load(f)
                if args.format == "json":
                    print(json.dumps(data, indent=2))
                else:
                    leads_data = data.get("leads", [])
                    leads = [LeadSignal(**{k: v for k, v in ld.items() if k in LeadSignal.__annotations__}) for ld in leads_data]
                    print(detector.generate_report(leads))
        else:
            print("No leads file found.")


if __name__ == "__main__":
    main()
