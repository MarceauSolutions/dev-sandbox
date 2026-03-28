"""Call Insights and Follow-up Recommendations Engine."""

import json
import re
from datetime import datetime
from typing import Optional, Dict, List, Tuple
import anthropic

from .config import get_settings
from .models import Call, TranscriptEntry


class CallInsightsEngine:
    """Analyzes calls and generates insights with follow-up recommendations."""

    def __init__(self):
        self.settings = get_settings()
        self.client = anthropic.Anthropic(api_key=self.settings.anthropic_api_key)

    def analyze_call(self, call: Call) -> dict:
        """
        Analyze a completed call and generate insights.

        Returns dict with:
        - summary: Brief summary of the call
        - caller_intent: What the caller wanted
        - sentiment: positive/neutral/negative
        - key_topics: List of topics discussed
        - follow_up_needed: bool
        - follow_up_priority: high/medium/low
        - follow_up_actions: List of recommended actions
        - best_contact_time: Suggested callback time (if applicable)
        """
        if not call.transcript:
            return {"error": "No transcript available"}

        # Format transcript for analysis
        transcript_text = self._format_transcript(call.transcript)

        # Use Claude to analyze the call
        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=500,
            system="""You are a call analysis expert. Analyze phone call transcripts and provide actionable insights.

Return your analysis as valid JSON with these fields:
{
  "summary": "2-3 sentence summary of the call",
  "caller_intent": "What the caller wanted or was calling about",
  "sentiment": "positive | neutral | negative",
  "key_topics": ["topic1", "topic2"],
  "caller_name": "Name if provided, or null",
  "caller_company": "Company if provided, or null",
  "follow_up_needed": true | false,
  "follow_up_priority": "high | medium | low",
  "follow_up_actions": ["action1", "action2"],
  "follow_up_timeframe": "within 1 hour | today | within 24 hours | this week | no rush",
  "callback_number": "Number if provided, or null",
  "notes": "Any other important observations"
}

Be concise but thorough. Focus on actionable insights.""",
            messages=[{
                "role": "user",
                "content": f"Analyze this phone call:\n\n{transcript_text}"
            }]
        )

        # Parse the response
        try:
            analysis_text = response.content[0].text
            # Extract JSON from response (handle markdown code blocks)
            if "```json" in analysis_text:
                analysis_text = analysis_text.split("```json")[1].split("```")[0]
            elif "```" in analysis_text:
                analysis_text = analysis_text.split("```")[1].split("```")[0]

            insights = json.loads(analysis_text.strip())
        except (json.JSONDecodeError, IndexError):
            # Fallback to raw analysis
            insights = {
                "summary": response.content[0].text,
                "raw_analysis": True
            }

        # Add metadata
        insights["call_id"] = call.id
        insights["twilio_sid"] = call.twilio_sid
        insights["caller_number"] = call.caller_number
        insights["call_duration"] = call.duration_seconds
        insights["analyzed_at"] = datetime.utcnow().isoformat()

        return insights

    def _format_transcript(self, transcript: list[TranscriptEntry]) -> str:
        """Format transcript entries for analysis."""
        lines = []
        for entry in transcript:
            role = "AI" if entry.role == "ai" else "Caller"
            lines.append(f"{role}: {entry.content}")
        return "\n".join(lines)

    def generate_follow_up_email(self, insights: dict) -> str:
        """Generate a follow-up email draft based on call insights."""
        if not insights.get("follow_up_needed"):
            return None

        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=300,
            system="""Write a brief, professional follow-up email based on call insights.
Keep it short (2-3 paragraphs max). Reference specific things from the call to show you listened.
Sign off as William Marceau.""",
            messages=[{
                "role": "user",
                "content": f"Write a follow-up email based on this call:\n\n{json.dumps(insights, indent=2)}"
            }]
        )

        return response.content[0].text

    def generate_sms_follow_up(self, insights: dict) -> str:
        """Generate a brief SMS follow-up based on call insights."""
        if not insights.get("follow_up_needed"):
            return None

        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=100,
            system="""Write a brief SMS follow-up (under 160 characters) based on call insights.
Be warm and reference the call. Sign as William.""",
            messages=[{
                "role": "user",
                "content": f"Write SMS follow-up for:\n\n{json.dumps(insights, indent=2)}"
            }]
        )

        return response.content[0].text

    def format_insights_for_display(self, insights: dict) -> str:
        """Format insights for human-readable display."""
        if insights.get("error"):
            return f"Error: {insights['error']}"

        lines = [
            "=" * 60,
            "CALL INSIGHTS",
            "=" * 60,
            "",
            f"📞 Call from: {insights.get('caller_number', 'Unknown')}",
            f"⏱️  Duration: {insights.get('call_duration', 0)} seconds",
            "",
            "📝 SUMMARY:",
            f"   {insights.get('summary', 'No summary available')}",
            "",
            f"🎯 CALLER INTENT: {insights.get('caller_intent', 'Unknown')}",
            f"😊 SENTIMENT: {insights.get('sentiment', 'neutral').upper()}",
            "",
        ]

        if insights.get("caller_name"):
            lines.append(f"👤 CALLER: {insights.get('caller_name')}")
        if insights.get("caller_company"):
            lines.append(f"🏢 COMPANY: {insights.get('caller_company')}")

        if insights.get("key_topics"):
            lines.append("")
            lines.append("📌 KEY TOPICS:")
            for topic in insights["key_topics"]:
                lines.append(f"   • {topic}")

        lines.append("")
        lines.append("-" * 60)
        lines.append("FOLLOW-UP RECOMMENDATIONS")
        lines.append("-" * 60)

        follow_up = insights.get("follow_up_needed", False)
        priority = insights.get("follow_up_priority", "low")
        timeframe = insights.get("follow_up_timeframe", "no rush")

        priority_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(priority, "⚪")

        lines.append(f"   Follow-up needed: {'✅ YES' if follow_up else '❌ NO'}")
        if follow_up:
            lines.append(f"   Priority: {priority_emoji} {priority.upper()}")
            lines.append(f"   Timeframe: {timeframe}")
            lines.append("")
            lines.append("   📋 RECOMMENDED ACTIONS:")
            for action in insights.get("follow_up_actions", []):
                lines.append(f"      • {action}")

        if insights.get("callback_number"):
            lines.append(f"\n   📱 Callback: {insights['callback_number']}")

        if insights.get("notes"):
            lines.append(f"\n   📝 Notes: {insights['notes']}")

        lines.append("")
        lines.append("=" * 60)

        return "\n".join(lines)


class ServiceIntentDetector:
    """Detects which service/tower a caller is interested in from transcripts."""
    
    # Service-to-tower mapping with keywords
    SERVICE_KEYWORDS = {
        "digital-ai-services": {
            "label": "AI Services",
            "keywords": [
                "ai", "phone system", "voice ai", "calls", "answer calls", "missed calls",
                "text back", "chatbot", "appointment booking", "24/7", "after hours",
                "lead generation", "leads", "scraping", "outreach", "automation",
                "answering service", "receptionist", "booking", "schedule"
            ],
            "weight": 1.0
        },
        "digital-web-dev": {
            "label": "Web Development",
            "keywords": [
                "website", "web design", "landing page", "redesign", "seo",
                "online presence", "ecommerce", "e-commerce", "mobile site",
                "web development", "new site", "build a site", "update my site"
            ],
            "weight": 1.0
        },
        "fitness-influencer": {
            "label": "Social Media / Influencer",
            "keywords": [
                "social media", "instagram", "tiktok", "twitter", "x posts",
                "content creation", "influencer", "posting", "brand", "sponsorship",
                "social presence", "followers", "engagement"
            ],
            "weight": 1.0
        },
        "fitness-coaching": {
            "label": "Fitness Coaching",
            "keywords": [
                "personal training", "fitness coaching", "workout", "gym membership",
                "nutrition", "weight loss", "muscle", "training program"
            ],
            "weight": 0.8  # Lower weight since less common for business calls
        }
    }
    
    def __init__(self):
        self.settings = get_settings()
        self.client = anthropic.Anthropic(api_key=self.settings.anthropic_api_key)
    
    def detect_from_transcript(self, transcript: List[Dict]) -> Dict:
        """
        Detect service intent from a call transcript.
        
        Args:
            transcript: List of transcript entries (role + message)
            
        Returns:
            Dict with:
            - primary_tower: Most likely tower ID
            - primary_confidence: 0.0 to 1.0
            - secondary_tower: Second most likely (if any)
            - secondary_confidence: 0.0 to 1.0
            - detected_services: List of specific services mentioned
            - raw_scores: All tower scores for debugging
        """
        # Combine all caller messages for analysis
        caller_text = " ".join([
            t.get("message", "") or t.get("content", "")
            for t in transcript 
            if t.get("role") in ("customer", "user", "human")
        ]).lower()
        
        # Also include AI responses for context
        full_text = " ".join([
            t.get("message", "") or t.get("content", "")
            for t in transcript
        ]).lower()
        
        # Score each tower based on keyword matches
        scores = self._score_keywords(caller_text, full_text)
        
        # If scores are ambiguous, use Claude for deeper analysis
        if self._is_ambiguous(scores):
            scores = self._analyze_with_claude(transcript, scores)
        
        # Rank towers by score
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        # Calculate confidence (normalized to sum=1.0)
        total_score = sum(s for _, s in ranked) or 1.0
        
        result = {
            "primary_tower": ranked[0][0] if ranked else "digital-ai-services",
            "primary_confidence": round(ranked[0][1] / total_score, 2) if ranked else 0.5,
            "secondary_tower": ranked[1][0] if len(ranked) > 1 and ranked[1][1] > 0 else None,
            "secondary_confidence": round(ranked[1][1] / total_score, 2) if len(ranked) > 1 else 0.0,
            "detected_services": self._extract_services(caller_text),
            "raw_scores": scores
        }
        
        return result
    
    def _score_keywords(self, caller_text: str, full_text: str) -> Dict[str, float]:
        """Score each tower based on keyword matches."""
        scores = {}
        
        for tower_id, config in self.SERVICE_KEYWORDS.items():
            score = 0.0
            keywords = config["keywords"]
            weight = config["weight"]
            
            for keyword in keywords:
                # Caller mentions are worth more
                if keyword in caller_text:
                    score += 2.0 * weight
                # AI mentions also count (context)
                elif keyword in full_text:
                    score += 0.5 * weight
            
            scores[tower_id] = score
        
        return scores
    
    def _is_ambiguous(self, scores: Dict[str, float]) -> bool:
        """Check if scores are too close to call."""
        sorted_scores = sorted(scores.values(), reverse=True)
        if len(sorted_scores) < 2:
            return False
        
        # If top two scores are within 20% of each other, it's ambiguous
        if sorted_scores[0] == 0:
            return False  # No signal at all, not ambiguous just empty
        
        ratio = sorted_scores[1] / sorted_scores[0]
        return ratio > 0.8
    
    def _analyze_with_claude(self, transcript: List[Dict], 
                             initial_scores: Dict[str, float]) -> Dict[str, float]:
        """Use Claude to disambiguate service intent."""
        transcript_text = "\n".join([
            f"{'Caller' if t.get('role') in ('customer', 'user', 'human') else 'AI'}: {t.get('message', '') or t.get('content', '')}"
            for t in transcript
        ])
        
        prompt = f"""Analyze this call transcript to determine which service the caller is most interested in.

AVAILABLE SERVICES:
1. digital-ai-services: Voice AI phone systems, missed call text-back, lead generation automation
2. digital-web-dev: Website design, landing pages, web development, SEO
3. fitness-influencer: Social media automation, content creation for Instagram/TikTok
4. fitness-coaching: Personal training, fitness programs (rare for business calls)

TRANSCRIPT:
{transcript_text}

Based on what the caller is asking about, return JSON:
{{
  "primary_service": "tower-id",
  "confidence": 0.0-1.0,
  "secondary_service": "tower-id or null",
  "reasoning": "brief explanation"
}}"""
        
        try:
            response = self.client.messages.create(
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
            
            # Update scores based on Claude's analysis
            primary = result.get("primary_service", "digital-ai-services")
            confidence = result.get("confidence", 0.7)
            
            # Boost the identified tower
            if primary in initial_scores:
                initial_scores[primary] = max(initial_scores[primary], 10.0 * confidence)
            
            secondary = result.get("secondary_service")
            if secondary and secondary in initial_scores:
                initial_scores[secondary] = max(initial_scores[secondary], 5.0 * (1 - confidence))
                
        except Exception as e:
            pass  # Fall back to keyword-based scores
        
        return initial_scores
    
    def _extract_services(self, text: str) -> List[str]:
        """Extract specific services mentioned in the text."""
        services = []
        
        service_patterns = {
            "Voice AI": r"voice ai|ai phone|phone system|answering",
            "Lead Generation": r"lead gen|leads|scraping|outreach",
            "Website": r"website|web design|landing page|seo",
            "Social Media": r"social media|instagram|tiktok|content"
        }
        
        for service, pattern in service_patterns.items():
            if re.search(pattern, text, re.IGNORECASE):
                services.append(service)
        
        return services


def detect_service_intent(transcript: List[Dict]) -> Dict:
    """
    Convenience function to detect service intent from a transcript.
    
    Args:
        transcript: List of transcript entries
        
    Returns:
        Service intent detection result
    """
    detector = ServiceIntentDetector()
    return detector.detect_from_transcript(transcript)


async def analyze_recent_calls(limit: int = 5) -> list[dict]:
    """Analyze the most recent calls and return insights."""
    # This would pull from the active_calls store
    # For now, import from twilio_handler
    from .twilio_handler import active_calls

    engine = CallInsightsEngine()
    results = []

    for call_sid, call in list(active_calls.items())[-limit:]:
        if call.transcript:
            insights = engine.analyze_call(call)
            results.append(insights)

    return results


if __name__ == "__main__":
    # Test the insights engine with a mock call
    from .models import Call, CallStatus

    mock_call = Call(
        id="test-123",
        restaurant_id="william_assistant",
        twilio_sid="CA123456789",
        caller_number="+12345678901",
        status=CallStatus.COMPLETED,
        duration_seconds=120,
        transcript=[
            TranscriptEntry(role="ai", content="Hi! You've reached William Marceau's office. How can I help you?"),
            TranscriptEntry(role="customer", content="Hi, this is Sarah from TechCorp. I'm interested in your AI consulting services."),
            TranscriptEntry(role="ai", content="Great to hear from you, Sarah! What kind of AI solutions are you looking for?"),
            TranscriptEntry(role="customer", content="We need help automating our customer support. We get about 500 tickets a day."),
            TranscriptEntry(role="ai", content="That's definitely something William specializes in! Can I get your callback number?"),
            TranscriptEntry(role="customer", content="Sure, it's 555-123-4567. I'm available tomorrow afternoon."),
        ]
    )

    engine = CallInsightsEngine()
    insights = engine.analyze_call(mock_call)
    print(engine.format_insights_for_display(insights))
