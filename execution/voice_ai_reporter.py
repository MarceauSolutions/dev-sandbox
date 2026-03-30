#!/usr/bin/env python3
"""
Voice AI Conversation Reporter for Telegram.

Polls ElevenLabs for new conversations, analyzes them with CallInsightsEngine
and AutoLeadDetector, then sends reports to Telegram.

Usage:
    python voice_ai_reporter.py              # Process new conversations
    python voice_ai_reporter.py --digest     # Send daily digest
    python voice_ai_reporter.py --test       # Test with mock data
"""

import os
import sys
import json
import logging
import argparse
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import anthropic

# Load environment
from dotenv import load_dotenv
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_AGENT_ID = os.getenv("ELEVENLABS_AGENT_ID", "agent_9801kmgjg670fb7bdv5z9r96y66d")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = "5692454753"  # William's chat
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# State file
STATE_FILE = Path(__file__).parent / "voice_ai_state.json"
DAILY_LOG_DIR = Path(__file__).parent / "voice_ai_logs"

# Tower labels for display
TOWER_LABELS = {
    "digital-ai-services": "🤖 AI Services",
    "digital-web-dev": "🌐 Web Development",
    "fitness-coaching": "💪 Fitness Coaching",
    "fitness-influencer": "📸 Social Media / Influencer"
}

# Service keywords for tower detection (aligned with marceau_solutions.py)
SERVICE_KEYWORDS = {
    "digital-ai-services": [
        "ai", "phone system", "voice ai", "calls", "answer calls", "missed calls",
        "text back", "chatbot", "appointment booking", "24/7", "after hours",
        "lead generation", "leads", "scraping", "outreach", "automation",
        "answering service", "receptionist", "booking", "schedule"
    ],
    "digital-web-dev": [
        "website", "web design", "landing page", "redesign", "seo",
        "online presence", "ecommerce", "e-commerce", "mobile site",
        "web development", "new site", "build a site", "update my site"
    ],
    "fitness-influencer": [
        "social media", "instagram", "tiktok", "twitter", "x posts",
        "content creation", "influencer", "posting", "brand", "sponsorship",
        "social presence", "followers", "engagement"
    ],
    "fitness-coaching": [
        "personal training", "fitness coaching", "workout", "gym membership",
        "nutrition", "weight loss", "muscle", "training program"
    ]
}


@dataclass
class ConversationReport:
    """Processed conversation report."""
    conversation_id: str
    caller_number: str
    duration_seconds: int
    message_count: int
    timestamp: str
    call_title: str
    transcript_summary: str
    intent: str
    lead_quality: str  # hot, warm, cold, not_lead
    next_action: str
    transcript: List[Dict]
    raw_data: Dict
    # Tower routing fields
    detected_tower: str = "digital-ai-services"
    tower_confidence: float = 0.5
    secondary_tower: Optional[str] = None
    detected_services: List[str] = None


class VoiceAIReporter:
    """Reports Voice AI conversations to Telegram."""
    
    def __init__(self):
        self.state = self._load_state()
        self.anthropic = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        DAILY_LOG_DIR.mkdir(parents=True, exist_ok=True)
        self._lock_file = STATE_FILE.with_suffix('.lock')
    
    def _acquire_lock(self) -> bool:
        """Acquire file lock to prevent concurrent runs."""
        import fcntl
        try:
            self._lock_fd = open(self._lock_file, 'w')
            fcntl.flock(self._lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return True
        except (IOError, OSError):
            logger.warning("Another instance is running, skipping")
            return False
    
    def _release_lock(self):
        """Release file lock."""
        import fcntl
        try:
            if hasattr(self, '_lock_fd') and self._lock_fd:
                fcntl.flock(self._lock_fd, fcntl.LOCK_UN)
                self._lock_fd.close()
        except Exception:
            pass
    
    def _load_state(self) -> Dict:
        """Load processed conversation state."""
        if STATE_FILE.exists():
            try:
                with open(STATE_FILE, 'r') as f:
                    state = json.load(f)
                    logger.info(f"Loaded state with {len(state.get('processed_ids', []))} processed IDs")
                    return state
            except (json.JSONDecodeError, IOError) as e:
                logger.error(f"Failed to load state: {e}")
        return {
            "processed_ids": [],
            "last_check": None,
            "daily_stats": {}
        }
    
    def _save_state(self):
        """Save state to disk atomically."""
        import tempfile
        try:
            # Write to temp file first, then rename (atomic)
            fd, tmp_path = tempfile.mkstemp(dir=STATE_FILE.parent, suffix='.tmp')
            with os.fdopen(fd, 'w') as f:
                json.dump(self.state, f, indent=2)
            os.replace(tmp_path, STATE_FILE)
            logger.info(f"Saved state with {len(self.state.get('processed_ids', []))} processed IDs")
        except Exception as e:
            logger.error(f"Failed to save state: {e}")
    
    def fetch_conversations(self, limit: int = 20) -> List[Dict]:
        """Fetch recent conversations from ElevenLabs."""
        url = f"https://api.elevenlabs.io/v1/convai/conversations"
        headers = {"xi-api-key": ELEVENLABS_API_KEY}
        params = {"agent_id": ELEVENLABS_AGENT_ID}
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            return data.get("conversations", [])
        except Exception as e:
            logger.error(f"Failed to fetch conversations: {e}")
            return []
    
    def fetch_conversation_details(self, conversation_id: str) -> Optional[Dict]:
        """Fetch full conversation details including transcript."""
        url = f"https://api.elevenlabs.io/v1/convai/conversations/{conversation_id}"
        headers = {"xi-api-key": ELEVENLABS_API_KEY}
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to fetch conversation {conversation_id}: {e}")
            return None
    
    def detect_service_tower(self, transcript: List[Dict]) -> Tuple[str, float, Optional[str], List[str]]:
        """
        Detect which service tower the caller is interested in.
        
        Returns:
            Tuple of (primary_tower, confidence, secondary_tower, detected_services)
        """
        # Combine all caller messages
        caller_text = " ".join([
            t.get("message", "")
            for t in transcript
            if t.get("role") != "agent"
        ]).lower()
        
        # Score each tower
        scores = {}
        for tower_id, keywords in SERVICE_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in caller_text)
            scores[tower_id] = score
        
        # Rank towers
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        total_score = sum(s for _, s in ranked) or 1.0
        
        primary = ranked[0][0] if ranked and ranked[0][1] > 0 else "digital-ai-services"
        primary_score = ranked[0][1] if ranked else 0
        
        # Calculate confidence (0.5 = default, higher if clear signal)
        if primary_score == 0:
            confidence = 0.5
        elif primary_score >= 3:
            confidence = 0.9
        elif primary_score >= 2:
            confidence = 0.75
        else:
            confidence = 0.6
        
        # Secondary tower
        secondary = None
        if len(ranked) > 1 and ranked[1][1] > 0:
            secondary = ranked[1][0]
        
        # Extract detected services
        detected_services = []
        service_patterns = {
            "Voice AI": ["voice ai", "ai phone", "phone system", "answering"],
            "Lead Generation": ["lead gen", "leads", "scraping", "outreach"],
            "Website": ["website", "web design", "landing page", "seo"],
            "Social Media": ["social media", "instagram", "tiktok", "content"]
        }
        for service, patterns in service_patterns.items():
            if any(p in caller_text for p in patterns):
                detected_services.append(service)
        
        return primary, confidence, secondary, detected_services
    
    def analyze_conversation(self, details: Dict) -> ConversationReport:
        """Analyze conversation and extract insights."""
        transcript = details.get("transcript", [])
        analysis = details.get("analysis", {})
        metadata = details.get("metadata", {})
        phone_call = metadata.get("phone_call", {})
        
        # Format transcript for analysis
        transcript_text = "\n".join([
            f"{'AI' if t['role'] == 'agent' else 'Caller'}: {t['message']}"
            for t in transcript
        ])
        
        # Use Claude to analyze for lead quality and intent
        prompt = f"""Analyze this phone call to Marceau Solutions (AI consulting firm):

TRANSCRIPT:
{transcript_text}

CALLER: {phone_call.get('external_number', 'Unknown')}
DURATION: {metadata.get('call_duration_secs', 0)} seconds

Analyze:
1. **Intent**: service_inquiry, callback_request, scheduling, general_question, wrong_number, spam
2. **Lead Quality**:
   - HOT: Ready to buy, urgent need, wants pricing, scheduling appointment
   - WARM: Interested, asking questions, wants callback
   - COLD: General inquiry, no clear buying intent
   - NOT_LEAD: Wrong number, spam, family/personal call
3. **Next Action**: What William should do

Return JSON:
{{
  "intent": "...",
  "lead_quality": "hot|warm|cold|not_lead",
  "next_action": "..."
}}"""
        
        try:
            response = self.anthropic.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=200,
                messages=[{"role": "user", "content": prompt}]
            )
            
            result_text = response.content[0].text
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0]
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0]
            
            result = json.loads(result_text.strip())
        except Exception as e:
            logger.warning(f"Analysis failed: {e}")
            result = {
                "intent": "unknown",
                "lead_quality": "cold",
                "next_action": "Review transcript"
            }
        
        # Detect service tower interest
        detected_tower, tower_confidence, secondary_tower, detected_services = \
            self.detect_service_tower(transcript)
        
        # Build report
        return ConversationReport(
            conversation_id=details.get("conversation_id"),
            caller_number=phone_call.get("external_number", "Unknown"),
            duration_seconds=metadata.get("call_duration_secs", 0),
            message_count=len(transcript),
            timestamp=datetime.fromtimestamp(
                metadata.get("start_time_unix_secs", 0)
            ).strftime("%Y-%m-%d %H:%M UTC"),
            call_title=analysis.get("call_summary_title", "Unknown"),
            transcript_summary=analysis.get("transcript_summary", "No summary available"),
            intent=result.get("intent", "unknown"),
            lead_quality=result.get("lead_quality", "cold"),
            next_action=result.get("next_action", "Review"),
            transcript=transcript,
            raw_data=details,
            detected_tower=detected_tower,
            tower_confidence=tower_confidence,
            secondary_tower=secondary_tower,
            detected_services=detected_services or []
        )
    
    def format_telegram_message(self, report: ConversationReport) -> str:
        """Format report for Telegram."""
        # Lead quality emoji
        quality_emoji = {
            "hot": "🔥 HOT",
            "warm": "🟡 WARM",
            "cold": "⚪ COLD",
            "not_lead": "👤 NOT LEAD"
        }.get(report.lead_quality, "❓ UNKNOWN")
        
        # Duration formatting
        minutes = report.duration_seconds // 60
        seconds = report.duration_seconds % 60
        duration_str = f"{minutes}m {seconds}s" if minutes else f"{seconds}s"
        
        # Intent formatting
        intent_map = {
            "service_inquiry": "💼 Service Inquiry",
            "callback_request": "📞 Callback Request",
            "scheduling": "📅 Scheduling",
            "general_question": "❓ General Question",
            "wrong_number": "❌ Wrong Number",
            "spam": "🚫 Spam",
            "unknown": "❓ Unknown"
        }
        intent_str = intent_map.get(report.intent, report.intent)
        
        # Tower/Service interest formatting
        tower_str = TOWER_LABELS.get(report.detected_tower, report.detected_tower)
        confidence_pct = int(report.tower_confidence * 100)
        
        # Build service interest line
        service_interest = f"{tower_str}"
        if report.detected_services:
            service_interest += f" ({', '.join(report.detected_services)})"
        if report.secondary_tower:
            secondary_label = TOWER_LABELS.get(report.secondary_tower, report.secondary_tower)
            service_interest += f"\n   Also interested in: {secondary_label}"
        
        message = f"""📞 <b>AI CALL REPORT</b>

<b>Caller:</b> {report.caller_number}
<b>Duration:</b> {duration_str}
<b>Time:</b> {report.timestamp}

<b>Intent:</b> {intent_str}
<b>Lead Quality:</b> {quality_emoji}
<b>Service Interest:</b> {service_interest}

<b>Summary:</b>
{report.transcript_summary}

<b>Next Action:</b> {report.next_action}
<b>Route To:</b> {report.detected_tower} tower ({confidence_pct}% confidence)"""
        
        return message
    
    def send_telegram_message(self, message: str, priority: str = "normal") -> bool:
        """Send message to Telegram."""
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "HTML"
        }
        
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            logger.info(f"Sent Telegram message (priority: {priority})")
            return True
        except Exception as e:
            logger.error(f"Failed to send Telegram: {e}")
            return False
    
    def process_new_conversations(self) -> Tuple[int, List[ConversationReport]]:
        """Process all new conversations."""
        # Acquire lock to prevent concurrent runs
        if not self._acquire_lock():
            return 0, []
        
        try:
            # Reload state fresh to catch any updates from other runs
            self.state = self._load_state()
            
            conversations = self.fetch_conversations()
            processed = []
            hot_leads = []
            
            for conv in conversations:
                conv_id = conv.get("conversation_id")
                
                # Skip if already processed (double-check with fresh state)
                if conv_id in self.state["processed_ids"]:
                    logger.debug(f"Skipping already processed: {conv_id}")
                    continue
                
                # Skip very short calls (< 5 seconds, just hangups)
                if conv.get("call_duration_secs", 0) < 5:
                    self.state["processed_ids"].append(conv_id)
                    continue
                
                logger.info(f"Processing new conversation: {conv_id}")
                
                # Fetch full details
                details = self.fetch_conversation_details(conv_id)
                if not details:
                    continue
                
                # Analyze
                report = self.analyze_conversation(details)
                processed.append(report)
                
                # Mark as processed IMMEDIATELY after analysis
                self.state["processed_ids"].append(conv_id)
                
                # Track daily stats
                today = datetime.now().strftime("%Y-%m-%d")
                if today not in self.state["daily_stats"]:
                    self.state["daily_stats"][today] = {
                        "total_calls": 0,
                        "hot_leads": 0,
                        "warm_leads": 0,
                        "cold_leads": 0,
                        "total_duration": 0
                    }
                
                self.state["daily_stats"][today]["total_calls"] += 1
                self.state["daily_stats"][today]["total_duration"] += report.duration_seconds
                
                if report.lead_quality == "hot":
                    self.state["daily_stats"][today]["hot_leads"] += 1
                    hot_leads.append(report)
                elif report.lead_quality == "warm":
                    self.state["daily_stats"][today]["warm_leads"] += 1
                elif report.lead_quality == "cold":
                    self.state["daily_stats"][today]["cold_leads"] += 1
                
                # Send report via notification policy
                # Only HOT leads get immediate notification, rest queued for digest
                from execution.notification_policy import notify, queue_for_digest
                
                message = self.format_telegram_message(report)
                
                if report.lead_quality == "hot":
                    # Hot leads get immediate notification
                    notify(
                        "hot_lead",
                        f"🔥 HOT LEAD: {report.caller_number}",
                        message,
                        metadata={"lead_quality": "hot", "caller": report.caller_number},
                        force_immediate=True
                    )
                else:
                    # Everything else queued for digest
                    queue_for_digest(
                        "voice_call_report",
                        f"Call from {report.caller_number}",
                        report.transcript_summary[:200],
                        metadata={
                            "lead_quality": report.lead_quality,
                            "caller": report.caller_number,
                            "duration": report.duration_seconds,
                            "tower": report.detected_tower
                        }
                    )
                
                # Auto-route to pipeline (create lead)
                lead_id = self.create_lead_from_call(report)
                if lead_id:
                    logger.info(f"Created/updated lead #{lead_id} → {report.detected_tower}")
                
                # Log to daily file
                self._log_conversation(report)
                
                # Save state after EACH conversation to prevent duplicates on crash
                self._save_state()
            
            # Final state update
            self.state["last_check"] = datetime.now().isoformat()
            self._save_state()
            
            return len(processed), processed
        finally:
            self._release_lock()
    
    def create_lead_from_call(self, report: ConversationReport) -> Optional[int]:
        """
        Create a lead in pipeline_db from a call report.
        Auto-routes to the detected tower.
        
        Returns:
            Deal ID if created, None if skipped or failed
        """
        # Skip non-leads
        if report.lead_quality == "not_lead":
            logger.info(f"Skipping non-lead: {report.caller_number}")
            return None
        
        try:
            # Import pipeline_db
            import sys
            sys.path.insert(0, str(Path(__file__).parent))
            import pipeline_db
            
            # Check if lead already exists by phone number
            conn = pipeline_db.get_db()
            existing = conn.execute(
                "SELECT id FROM deals WHERE contact_phone = ?",
                (report.caller_number,)
            ).fetchone()
            
            if existing:
                # Update existing lead with new call info
                logger.info(f"Lead already exists for {report.caller_number}, updating")
                conn.execute("""
                    UPDATE deals 
                    SET notes = notes || ?,
                        recommended_tower = ?,
                        updated_at = datetime('now')
                    WHERE id = ?
                """, (
                    f"\n\n[Call {report.timestamp}] {report.transcript_summary}",
                    report.detected_tower,
                    existing["id"]
                ))
                conn.commit()
                conn.close()
                return existing["id"]
            
            # Create new lead
            # Extract caller name from transcript if available
            caller_name = self._extract_caller_name(report.transcript)
            caller_company = self._extract_company_name(report.transcript)
            
            # Build pain points from transcript summary
            pain_points = report.transcript_summary
            
            # Set stage based on lead quality
            stage_map = {
                "hot": "Qualified",
                "warm": "Discovery",
                "cold": "New Lead"
            }
            stage = stage_map.get(report.lead_quality, "New Lead")
            
            cursor = conn.execute("""
                INSERT INTO deals (
                    company, contact_name, contact_phone, industry,
                    lead_source, stage, tower, recommended_tower,
                    pain_points, notes, next_action, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
            """, (
                caller_company or f"Call: {report.caller_number}",
                caller_name or "Unknown",
                report.caller_number,
                "Other",  # Will be enriched later
                "Voice AI Inbound",
                stage,
                report.detected_tower,
                report.detected_tower,
                pain_points,
                f"[Voice AI Call {report.timestamp}]\n{report.transcript_summary}\n\nServices: {', '.join(report.detected_services or ['General'])}",
                report.next_action
            ))
            
            deal_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            logger.info(f"Created lead #{deal_id} from call, routed to {report.detected_tower}")
            return deal_id
            
        except Exception as e:
            logger.error(f"Failed to create lead from call: {e}")
            return None
    
    def _extract_caller_name(self, transcript: List[Dict]) -> Optional[str]:
        """Try to extract caller's name from transcript."""
        import re
        
        for entry in transcript:
            if entry.get("role") != "agent":
                msg = entry.get("message", "")
                # Common patterns: "This is John", "My name is Sarah", "I'm Mike"
                patterns = [
                    r"(?:this is|my name is|i'?m|i am)\s+([A-Z][a-z]+)",
                    r"^([A-Z][a-z]+)\s+(?:here|calling|from)",
                ]
                for pattern in patterns:
                    match = re.search(pattern, msg, re.IGNORECASE)
                    if match:
                        return match.group(1).title()
        return None
    
    def _extract_company_name(self, transcript: List[Dict]) -> Optional[str]:
        """Try to extract company name from transcript."""
        import re
        
        for entry in transcript:
            if entry.get("role") != "agent":
                msg = entry.get("message", "")
                # Patterns: "from ABC Company", "with XYZ Corp", "at Acme Inc"
                patterns = [
                    r"(?:from|with|at)\s+([A-Z][A-Za-z0-9\s&]+(?:LLC|Inc|Corp|Company|Co\.?)?)",
                    r"(?:i own|i run|my company is|my business is)\s+([A-Z][A-Za-z0-9\s&]+)",
                ]
                for pattern in patterns:
                    match = re.search(pattern, msg, re.IGNORECASE)
                    if match:
                        return match.group(1).strip()
        return None
    
    def _log_conversation(self, report: ConversationReport):
        """Log conversation to daily file."""
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = DAILY_LOG_DIR / f"{today}.json"
        
        logs = []
        if log_file.exists():
            with open(log_file, 'r') as f:
                logs = json.load(f)
        
        logs.append(asdict(report))
        
        with open(log_file, 'w') as f:
            json.dump(logs, f, indent=2, default=str)
    
    def send_daily_digest(self):
        """Send daily digest summary."""
        today = datetime.now().strftime("%Y-%m-%d")
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        
        # Combine today and yesterday stats
        stats = {"total_calls": 0, "hot_leads": 0, "warm_leads": 0, "cold_leads": 0, "total_duration": 0}
        
        for day in [yesterday, today]:
            if day in self.state.get("daily_stats", {}):
                day_stats = self.state["daily_stats"][day]
                stats["total_calls"] += day_stats.get("total_calls", 0)
                stats["hot_leads"] += day_stats.get("hot_leads", 0)
                stats["warm_leads"] += day_stats.get("warm_leads", 0)
                stats["cold_leads"] += day_stats.get("cold_leads", 0)
                stats["total_duration"] += day_stats.get("total_duration", 0)
        
        if stats["total_calls"] == 0:
            # No calls, no digest needed
            return
        
        # Format duration
        total_mins = stats["total_duration"] // 60
        
        message = f"""📊 <b>AI PHONE AGENT - DAILY DIGEST</b>

📞 <b>Total Calls:</b> {stats['total_calls']}
⏱️ <b>Total Duration:</b> {total_mins} minutes

<b>Lead Breakdown:</b>
🔥 Hot: {stats['hot_leads']}
🟡 Warm: {stats['warm_leads']}
⚪ Cold: {stats['cold_leads']}

"""
        
        # Add action items if hot leads
        if stats["hot_leads"] > 0:
            message += f"\n⚡ <b>ACTION NEEDED:</b> {stats['hot_leads']} hot lead(s) require follow-up!"
        
        self.send_telegram_message(message)
    
    def cleanup_old_state(self, days: int = 30):
        """Remove old conversation IDs and stats."""
        # Keep only recent stats
        cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        
        self.state["daily_stats"] = {
            k: v for k, v in self.state.get("daily_stats", {}).items()
            if k >= cutoff
        }
        
        # Keep only recent 1000 processed IDs
        if len(self.state["processed_ids"]) > 1000:
            self.state["processed_ids"] = self.state["processed_ids"][-500:]
        
        self._save_state()


def main():
    parser = argparse.ArgumentParser(description="Voice AI Conversation Reporter")
    parser.add_argument("--digest", action="store_true", help="Send daily digest")
    parser.add_argument("--test", action="store_true", help="Test mode with mock data")
    parser.add_argument("--cleanup", action="store_true", help="Cleanup old state")
    args = parser.parse_args()
    
    reporter = VoiceAIReporter()
    
    if args.digest:
        logger.info("Sending daily digest...")
        reporter.send_daily_digest()
    elif args.cleanup:
        logger.info("Cleaning up old state...")
        reporter.cleanup_old_state()
    elif args.test:
        # Test with a simple message
        reporter.send_telegram_message(
            "🧪 <b>Test Message</b>\n\nVoice AI Reporter is working!",
            priority="normal"
        )
        print("Test message sent!")
    else:
        logger.info("Processing new conversations...")
        count, reports = reporter.process_new_conversations()
        logger.info(f"Processed {count} new conversation(s)")
        
        if count > 0:
            hot = sum(1 for r in reports if r.lead_quality == "hot")
            warm = sum(1 for r in reports if r.lead_quality == "warm")
            logger.info(f"  🔥 Hot: {hot}, 🟡 Warm: {warm}")


if __name__ == "__main__":
    main()
