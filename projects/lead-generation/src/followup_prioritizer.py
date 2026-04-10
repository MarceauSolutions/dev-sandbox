#!/usr/bin/env python3
"""
followup_prioritizer.py — High-ROI Follow-up Prioritization Engine

Scores each pending follow-up by expected value and outputs a ranked daily action list.
Designed for William's limited time/energy — surfaces only the highest-impact actions.

SCORING FACTORS:
1. Deal Stage (weights different pipeline positions)
2. Days Since Contact (decay + urgency)
3. Response History (engagement signals)
4. Deal Value (proposal_amount + monthly_fee * 12)
5. Industry Conversion Rate (learned from outcomes)
6. Time-Sensitivity (hot lead decay, meeting follow-ups)

OUTPUT:
- Daily Top 5 "must contact" list with talking points
- Integration with PA handle_next() command
- Morning digest inclusion

Usage:
    python execution/followup_prioritizer.py                    # Show top 5
    python execution/followup_prioritizer.py --all              # Show all ranked
    python execution/followup_prioritizer.py --json             # JSON output
    python execution/followup_prioritizer.py --telegram         # Send to Telegram
    python execution/followup_prioritizer.py --learn            # Update learnings from outcomes
"""

import argparse
import json
import os
import sqlite3
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple

# Add repo root to path
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "execution"))

# Database path
DB_PATH = Path("/home/clawdbot/data/pipeline.db")
if not DB_PATH.exists():
    DB_PATH = REPO_ROOT / "projects" / "shared" / "sales-pipeline" / "data" / "pipeline.db"

# Learnings file for industry conversion rates
LEARNINGS_FILE = REPO_ROOT / "execution" / "followup_learnings.json"


# =============================================================================
# STAGE WEIGHTS — Higher = More Valuable
# =============================================================================
STAGE_WEIGHTS = {
    "Trial Active": 100,      # Highest — conversion is imminent
    "Proposal Sent": 85,      # Very close — need to follow up
    "Meeting Booked": 75,     # Committed interest
    "Qualified": 60,          # Phone-ready leads
    "Replied": 50,            # Showed interest
    "Outreached": 30,         # In progress
    "Contacted": 25,          # Old terminology (backwards compat)
    "Intake": 10,             # Not yet contacted
    "Prospect": 5,            # Raw leads
    "Closed Won": 0,          # Already converted
    "Closed Lost": 0,         # Dead
}

# Response type weights (from outreach_log.response field)
RESPONSE_WEIGHTS = {
    "interested": 40,
    "callback": 45,
    "hot_lead": 50,
    "warm_lead": 30,
    "question": 25,
    "meeting_booked": 60,
    "proposal_requested": 55,
    "positive": 35,
    "neutral": 10,
    "gatekeeper": 15,
    "has_ai_already": 5,
    "not_interested": -20,
    "opt_out": -50,
    "do_not_contact": -100,
}

# Industry base conversion rates (updated by learn_from_outcomes)
DEFAULT_INDUSTRY_RATES = {
    "Automotive": 0.15,
    "HVAC": 0.18,
    "Medical": 0.12,
    "Restaurant": 0.10,
    "Fitness": 0.20,
    "Real Estate": 0.14,
    "Legal": 0.08,
    "Dental": 0.16,
    "Chiropractic": 0.14,
    "Plumbing": 0.17,
    "Electrical": 0.16,
    "Roofing": 0.13,
    "Home Services": 0.15,
    "Other": 0.12,
}


@dataclass
class PrioritizedLead:
    """A lead with its priority score and reasoning."""
    deal_id: int
    company: str
    contact_name: str
    contact_phone: str
    contact_email: str
    industry: str
    stage: str
    expected_value: float
    priority_score: float
    days_since_contact: int
    last_response: str
    talking_points: List[str]
    reason: str
    urgency: str  # "critical", "high", "medium", "low"
    decay_rate: float  # How fast this lead is cooling
    
    def to_dict(self) -> Dict:
        return asdict(self)


class FollowupPrioritizer:
    """
    Scores and ranks leads for follow-up based on expected ROI.
    """
    
    def __init__(self, db_path: Path = None):
        self.db_path = db_path or DB_PATH
        self.industry_rates = self._load_industry_rates()
        
    def _load_industry_rates(self) -> Dict[str, float]:
        """Load learned industry conversion rates."""
        if LEARNINGS_FILE.exists():
            try:
                with open(LEARNINGS_FILE) as f:
                    data = json.load(f)
                    return data.get("industry_rates", DEFAULT_INDUSTRY_RATES)
            except:
                pass
        return DEFAULT_INDUSTRY_RATES.copy()
    
    def _save_learnings(self, learnings: Dict):
        """Save updated learnings to file."""
        LEARNINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(LEARNINGS_FILE, "w") as f:
            json.dump(learnings, f, indent=2)
    
    def get_db(self) -> sqlite3.Connection:
        """Get database connection."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn
    
    def calculate_decay_score(self, days_since_contact: int, stage: str, 
                               last_response: str) -> Tuple[float, float]:
        """
        Calculate time-based decay and urgency multiplier.
        
        Hot leads decay fast if not contacted. Cold leads have slower decay.
        
        Returns: (decay_penalty, decay_rate)
        """
        # Base decay rates by stage (daily loss %)
        stage_decay = {
            "Trial Active": 5.0,      # Lose 5% per day
            "Proposal Sent": 4.0,
            "Meeting Booked": 3.5,
            "Qualified": 2.0,
            "Replied": 3.0,
            "Outreached": 1.0,
            "Contacted": 1.0,
            "Intake": 0.5,
            "Prospect": 0.3,
        }
        
        # Response-based decay modifiers
        response_decay_mod = {
            "interested": 1.5,    # Hot leads cool faster
            "callback": 2.0,      # Callback requests are time-critical
            "hot_lead": 2.0,
            "warm_lead": 1.2,
            "question": 1.3,
            "meeting_booked": 1.0,
            "gatekeeper": 0.8,
            "neutral": 1.0,
        }
        
        base_decay = stage_decay.get(stage, 1.0)
        response_mod = response_decay_mod.get(last_response, 1.0)
        
        decay_rate = base_decay * response_mod
        
        # Calculate cumulative decay penalty
        # Formula: penalty = 1 - (1 - decay_rate/100)^days
        # Capped at 80% penalty
        if days_since_contact <= 0:
            decay_penalty = 0
        else:
            decay_penalty = 1 - pow(1 - decay_rate/100, days_since_contact)
            decay_penalty = min(decay_penalty, 0.80)
        
        return decay_penalty, decay_rate
    
    def calculate_expected_value(self, deal: Dict) -> float:
        """
        Calculate expected value of a deal.
        
        EV = (setup_fee + monthly_fee * 12) * conversion_probability
        """
        setup_fee = deal.get("setup_fee") or 0
        monthly_fee = deal.get("monthly_fee") or 0
        proposal_amount = deal.get("proposal_amount") or 0
        
        # Use proposal amount if set, otherwise estimate
        if proposal_amount > 0:
            base_value = proposal_amount
        else:
            base_value = setup_fee + (monthly_fee * 12)
        
        # If no value set, use industry average
        if base_value == 0:
            industry = deal.get("industry", "Other")
            # Average deal values by industry
            industry_avgs = {
                "Automotive": 3500,
                "HVAC": 4000,
                "Medical": 5000,
                "Restaurant": 2500,
                "Fitness": 3000,
                "Real Estate": 4500,
                "Dental": 4000,
                "Chiropractic": 3500,
                "Plumbing": 3000,
                "Electrical": 3500,
                "Other": 3000,
            }
            base_value = industry_avgs.get(industry, 3000)
        
        # Get industry conversion rate
        industry = deal.get("industry", "Other")
        conv_rate = self.industry_rates.get(industry, 0.12)
        
        # Adjust by stage (stages closer to close have higher probability)
        stage_multipliers = {
            "Trial Active": 0.70,
            "Proposal Sent": 0.40,
            "Meeting Booked": 0.25,
            "Qualified": 0.15,
            "Replied": 0.10,
            "Outreached": 0.05,
            "Contacted": 0.05,
            "Intake": 0.02,
            "Prospect": 0.01,
        }
        stage_mult = stage_multipliers.get(deal.get("stage", "Prospect"), 0.05)
        
        # Final conversion probability is industry rate adjusted by stage
        final_prob = min(conv_rate * (stage_mult / 0.12), 0.90)  # Cap at 90%
        
        return base_value * final_prob
    
    def calculate_priority_score(self, deal: Dict, outreach_history: List[Dict]) -> float:
        """
        Calculate overall priority score for a lead.
        
        Score components:
        1. Stage weight (0-100)
        2. Expected value (scaled 0-50)
        3. Response history (0-50)
        4. Decay adjustment (reduces score)
        5. Urgency boost (recent activity)
        """
        score = 0.0
        
        # 1. Stage weight
        stage = deal.get("stage", "Prospect")
        stage_score = STAGE_WEIGHTS.get(stage, 5)
        score += stage_score
        
        # 2. Expected value (scaled to 0-50)
        ev = self.calculate_expected_value(deal)
        ev_score = min(ev / 100, 50)  # $5000 EV = 50 points max
        score += ev_score
        
        # 3. Response history
        response_score = 0
        last_response = ""
        for entry in outreach_history[:3]:  # Last 3 interactions
            resp = (entry.get("response") or "").lower().replace(" ", "_")
            for key, weight in RESPONSE_WEIGHTS.items():
                if key in resp:
                    response_score += weight
                    if not last_response:
                        last_response = key
                    break
        response_score = max(min(response_score, 50), -20)  # Clamp -20 to 50
        score += response_score
        
        # 4. Calculate days since contact
        days_since = 999
        if outreach_history:
            last_contact = outreach_history[0].get("created_at", "")
            if last_contact:
                try:
                    last_dt = datetime.fromisoformat(last_contact.replace("Z", ""))
                    days_since = (datetime.now() - last_dt).days
                except:
                    pass
        
        # 5. Apply decay
        decay_penalty, decay_rate = self.calculate_decay_score(days_since, stage, last_response)
        score = score * (1 - decay_penalty)
        
        # 6. Urgency boost — sweet spot is 1-3 days for follow-up
        if 1 <= days_since <= 3 and stage in ["Qualified", "Replied", "Proposal Sent"]:
            score *= 1.2  # 20% boost for optimal follow-up timing
        elif days_since == 0:
            score *= 0.5  # Penalize same-day re-contact
        
        return round(score, 2)
    
    def generate_talking_points(self, deal: Dict, outreach_history: List[Dict]) -> List[str]:
        """Generate personalized talking points for this lead."""
        points = []
        
        name = deal.get("contact_name", "").split()[0] if deal.get("contact_name") else "there"
        company = deal.get("company", "your business")
        industry = deal.get("industry", "local business")
        stage = deal.get("stage", "")
        
        # Stage-specific openers
        if stage == "Trial Active":
            points.append(f"Ask about their trial experience so far")
            points.append("Identify any issues to address before conversion")
            points.append("Present conversion offer/discount")
        elif stage == "Proposal Sent":
            points.append("Ask if they've had time to review the proposal")
            points.append("Address any questions or concerns")
            points.append("Create urgency — limited availability")
        elif stage == "Meeting Booked":
            points.append("Confirm meeting details and agenda")
            points.append("Prepare discovery questions")
        elif stage in ["Qualified", "Replied"]:
            points.append(f"Reference their previous interest")
            points.append(f"Share a relevant {industry} success story")
            points.append("Ask about their current pain points")
        
        # Add context from notes
        notes = deal.get("notes", "")
        if notes:
            # Extract key info from notes
            if "interested" in notes.lower():
                points.append("They expressed interest previously")
            if "objection" in notes.lower() or "concern" in notes.lower():
                points.append("Address their previous objection")
            if "budget" in notes.lower() or "cost" in notes.lower() or "price" in notes.lower():
                points.append("Be prepared to discuss pricing/value")
        
        # Add response context
        if outreach_history:
            last = outreach_history[0]
            response = last.get("response") or ""
            if "callback" in response.lower():
                points.insert(0, "They requested a callback!")
            elif "question" in response.lower():
                points.insert(0, "Answer their question first")
        
        return points[:5]  # Max 5 points
    
    def determine_urgency(self, score: float, days_since: int, 
                          stage: str, last_response: str) -> str:
        """Determine urgency level for a lead."""
        # Critical: hot leads aging, callbacks not returned
        if "callback" in last_response and days_since >= 1:
            return "critical"
        if stage == "Trial Active" and days_since >= 2:
            return "critical"
        if score >= 150 and days_since >= 1:
            return "critical"
        
        # High: good leads needing follow-up
        if score >= 100:
            return "high"
        if stage in ["Proposal Sent", "Meeting Booked"] and days_since >= 1:
            return "high"
        
        # Medium: standard follow-ups
        if score >= 50:
            return "medium"
        
        return "low"
    
    def get_prioritized_leads(self, limit: int = 10, 
                               tower: str = None,
                               include_contacted_today: bool = False) -> List[PrioritizedLead]:
        """
        Get prioritized list of leads to contact.
        
        Args:
            limit: Max number of leads to return
            tower: Filter by business tower
            include_contacted_today: Whether to include leads contacted today
            
        Returns:
            List of PrioritizedLead sorted by priority_score descending
        """
        conn = self.get_db()
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Get all active deals with phone numbers
        query = """
            SELECT d.id, d.company, d.contact_name, d.contact_phone, 
                   d.contact_email, d.industry, d.stage, d.notes,
                   d.proposal_amount, d.setup_fee, d.monthly_fee,
                   d.city, d.state, d.tower, d.updated_at
            FROM deals d
            WHERE d.stage NOT IN ('Closed Won', 'Closed Lost')
            AND (d.contact_phone IS NOT NULL AND d.contact_phone != '')
        """
        params = []
        
        if tower:
            query += " AND d.tower = ?"
            params.append(tower)
        
        if not include_contacted_today:
            query += """
                AND d.id NOT IN (
                    SELECT deal_id FROM outreach_log 
                    WHERE date(created_at) = ? AND channel IN ('Call', 'In-Person')
                )
            """
            params.append(today)
        
        query += " ORDER BY d.updated_at DESC"
        
        deals = conn.execute(query, params).fetchall()
        
        prioritized = []
        for deal_row in deals:
            deal = dict(deal_row)
            
            # Get outreach history
            history = conn.execute(
                """SELECT channel, message_summary, response, created_at 
                   FROM outreach_log 
                   WHERE deal_id = ? 
                   ORDER BY created_at DESC LIMIT 5""",
                (deal["id"],)
            ).fetchall()
            history = [dict(h) for h in history]
            
            # Calculate days since contact
            days_since = 999
            last_response = ""
            if history:
                try:
                    last_dt = datetime.fromisoformat(
                        history[0]["created_at"].replace("Z", "").split(".")[0]
                    )
                    days_since = (datetime.now() - last_dt).days
                except:
                    pass
                last_response = (history[0].get("response") or "").lower().replace(" ", "_")
            
            # Calculate scores
            priority_score = self.calculate_priority_score(deal, history)
            expected_value = self.calculate_expected_value(deal)
            decay_penalty, decay_rate = self.calculate_decay_score(
                days_since, deal["stage"], last_response
            )
            
            # Skip very low priority leads
            if priority_score < 10:
                continue
            
            # Generate talking points
            talking_points = self.generate_talking_points(deal, history)
            
            # Determine urgency
            urgency = self.determine_urgency(
                priority_score, days_since, deal["stage"], last_response
            )
            
            # Build reason string
            stage = deal["stage"]
            if urgency == "critical":
                reason = f"🔴 CRITICAL: {stage} lead cooling fast"
            elif urgency == "high":
                reason = f"🟠 HIGH: {stage} — follow up now"
            elif urgency == "medium":
                reason = f"🟡 MEDIUM: {stage} — good opportunity"
            else:
                reason = f"⚪ LOW: {stage}"
            
            if days_since < 999:
                reason += f" ({days_since}d ago)"
            
            lead = PrioritizedLead(
                deal_id=deal["id"],
                company=deal["company"],
                contact_name=deal.get("contact_name") or "Owner",
                contact_phone=deal["contact_phone"],
                contact_email=deal.get("contact_email") or "",
                industry=deal.get("industry") or "Other",
                stage=deal["stage"],
                expected_value=round(expected_value, 2),
                priority_score=priority_score,
                days_since_contact=days_since if days_since < 999 else -1,
                last_response=last_response,
                talking_points=talking_points,
                reason=reason,
                urgency=urgency,
                decay_rate=round(decay_rate, 2),
            )
            prioritized.append(lead)
        
        conn.close()
        
        # Sort by priority score descending
        prioritized.sort(key=lambda x: x.priority_score, reverse=True)
        
        return prioritized[:limit]
    
    def get_top_5(self) -> List[PrioritizedLead]:
        """Get the top 5 highest-priority leads for today."""
        return self.get_prioritized_leads(limit=5)
    
    def format_daily_list(self, leads: List[PrioritizedLead] = None) -> str:
        """Format the daily action list for display or Telegram."""
        if leads is None:
            leads = self.get_top_5()
        
        if not leads:
            return "✅ No high-priority follow-ups today.\nAll leads are contacted or no phone numbers available."
        
        lines = [
            f"📞 *TOP {len(leads)} FOLLOW-UPS*",
            f"_{datetime.now().strftime('%A, %B %d')}_ — Priority ranked\n"
        ]
        
        total_ev = sum(l.expected_value for l in leads)
        
        for i, lead in enumerate(leads, 1):
            urgency_emoji = {
                "critical": "🔴",
                "high": "🟠",
                "medium": "🟡",
                "low": "⚪"
            }.get(lead.urgency, "⚪")
            
            lines.append(f"{i}. {urgency_emoji} *{lead.company}*")
            lines.append(f"   📱 {lead.contact_phone}")
            lines.append(f"   {lead.contact_name} | {lead.industry}")
            lines.append(f"   Stage: {lead.stage} | EV: ${lead.expected_value:,.0f}")
            
            if lead.days_since_contact >= 0:
                lines.append(f"   Last contact: {lead.days_since_contact}d ago")
            
            if lead.talking_points:
                lines.append(f"   💬 {lead.talking_points[0]}")
            
            lines.append("")
        
        lines.append(f"─────────────────")
        lines.append(f"💰 Total EV: ${total_ev:,.0f}")
        lines.append(f"⏱️ Est. time: {len(leads) * 5} min")
        
        return "\n".join(lines)
    
    def learn_from_outcomes(self) -> Dict:
        """
        Analyze outcomes to update industry conversion rates.
        
        Looks at completed deals to calculate actual conversion rates by industry.
        Updates LEARNINGS_FILE with new rates.
        """
        conn = self.get_db()
        
        # Get conversion stats by industry
        stats = conn.execute("""
            SELECT 
                industry,
                COUNT(*) as total,
                SUM(CASE WHEN stage = 'Closed Won' THEN 1 ELSE 0 END) as won
            FROM deals
            WHERE stage IN ('Closed Won', 'Closed Lost')
            GROUP BY industry
            HAVING total >= 3
        """).fetchall()
        
        updated_rates = self.industry_rates.copy()
        learning_log = []
        
        for row in stats:
            industry = row["industry"]
            total = row["total"]
            won = row["won"]
            actual_rate = won / total if total > 0 else 0
            
            # Blend with existing rate (weighted average)
            old_rate = updated_rates.get(industry, 0.12)
            # More weight to actual data as sample size grows
            weight = min(total / 20, 0.8)  # Max 80% weight to actual data
            new_rate = (actual_rate * weight) + (old_rate * (1 - weight))
            
            if abs(new_rate - old_rate) > 0.01:  # Only log significant changes
                learning_log.append({
                    "industry": industry,
                    "old_rate": round(old_rate, 3),
                    "new_rate": round(new_rate, 3),
                    "sample_size": total,
                    "won": won
                })
            
            updated_rates[industry] = round(new_rate, 3)
        
        conn.close()
        
        # Save updated learnings
        learnings = {
            "industry_rates": updated_rates,
            "last_updated": datetime.now().isoformat(),
            "learning_log": learning_log
        }
        self._save_learnings(learnings)
        
        self.industry_rates = updated_rates
        
        return learnings
    
    def get_optimal_contact_windows(self) -> Dict[str, Dict]:
        """
        Analyze outreach_log to find optimal contact times by industry.
        
        Returns dict of industry -> {best_day, best_hour, response_rate}
        """
        conn = self.get_db()
        
        # This would require timestamp data we may not have
        # For now, return default recommendations
        defaults = {
            "Automotive": {"best_day": "Tuesday", "best_hour": "10am", "response_rate": 0.18},
            "HVAC": {"best_day": "Wednesday", "best_hour": "9am", "response_rate": 0.20},
            "Medical": {"best_day": "Monday", "best_hour": "2pm", "response_rate": 0.15},
            "Restaurant": {"best_day": "Tuesday", "best_hour": "3pm", "response_rate": 0.12},
            "Fitness": {"best_day": "Monday", "best_hour": "11am", "response_rate": 0.22},
            "Other": {"best_day": "Tuesday", "best_hour": "10am", "response_rate": 0.15},
        }
        
        conn.close()
        return defaults


def send_telegram(message: str) -> bool:
    """Send message to Telegram."""
    import urllib.request
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "5692454753")
    if not bot_token:
        print(f"[NO TELEGRAM] {message}")
        return False
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        data = json.dumps({
            "chat_id": chat_id, 
            "text": message[:4096], 
            "parse_mode": "Markdown"
        }).encode()
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=10)
        return True
    except Exception as e:
        print(f"Telegram error: {e}")
        return False


# =============================================================================
# Integration Functions for PA handle_next()
# =============================================================================

def get_highest_priority_lead() -> Optional[PrioritizedLead]:
    """Get the single highest-priority lead. Used by handle_next()."""
    prioritizer = FollowupPrioritizer()
    leads = prioritizer.get_prioritized_leads(limit=1)
    return leads[0] if leads else None


def get_daily_priorities_for_digest() -> str:
    """Get formatted priority list for morning digest."""
    prioritizer = FollowupPrioritizer()
    return prioritizer.format_daily_list()


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Follow-up Prioritization Engine")
    parser.add_argument("--all", action="store_true", help="Show all ranked leads")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--telegram", action="store_true", help="Send to Telegram")
    parser.add_argument("--learn", action="store_true", help="Update learnings from outcomes")
    parser.add_argument("--limit", type=int, default=5, help="Number of leads to show")
    parser.add_argument("--tower", type=str, help="Filter by tower")
    
    args = parser.parse_args()
    
    prioritizer = FollowupPrioritizer()
    
    if args.learn:
        print("Learning from outcomes...")
        learnings = prioritizer.learn_from_outcomes()
        print(f"Updated {len(learnings.get('learning_log', []))} industry rates")
        for entry in learnings.get("learning_log", []):
            print(f"  {entry['industry']}: {entry['old_rate']} → {entry['new_rate']} "
                  f"(n={entry['sample_size']}, won={entry['won']})")
        return
    
    limit = 50 if args.all else args.limit
    leads = prioritizer.get_prioritized_leads(limit=limit, tower=args.tower)
    
    if args.json:
        output = [lead.to_dict() for lead in leads]
        print(json.dumps(output, indent=2))
        return
    
    formatted = prioritizer.format_daily_list(leads)
    
    if args.telegram:
        if send_telegram(formatted):
            print("✅ Sent to Telegram")
        else:
            print("❌ Telegram send failed")
            print(formatted)
    else:
        print(formatted)


if __name__ == "__main__":
    main()
