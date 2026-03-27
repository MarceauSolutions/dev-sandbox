"""Call Insights and Follow-up Recommendations Engine."""

import json
from datetime import datetime
from typing import Optional
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
