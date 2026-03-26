#!/usr/bin/env python3
"""
Weekly Outreach Monitor - Track Week 1 performance

Usage:
    python -m src.weekly_monitor daily-check
    python -m src.weekly_monitor week-summary
    python -m src.weekly_monitor high-value-leads --limit 20
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict
from collections import defaultdict

class WeeklyMonitor:
    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.history_file = self.output_dir / "outreach_history.json"
        self.log_file = self.output_dir / "outreach.log"
        
    def load_history(self) -> Dict:
        """Load outreach history."""
        if not self.history_file.exists():
            return {"campaigns": []}
        
        with open(self.history_file) as f:
            return json.load(f)
    
    def daily_check(self):
        """Quick daily check of outreach activity."""
        print("\n" + "="*60)
        print("DAILY OUTREACH CHECK")
        print("="*60)
        print(f"Date: {datetime.now().strftime('%Y-%m-%d %I:%M %p')}\n")
        
        # Load history
        history = self.load_history()
        campaigns = history.get("campaigns", [])
        
        # Today's campaigns
        today = datetime.now().date().isoformat()
        today_campaigns = [c for c in campaigns if c.get("sent_at", "").startswith(today)]
        
        if not today_campaigns:
            print("⚠️  No outreach sent today yet")
            print(f"   Next scheduled: Check crontab (6 AM daily-run)")
            return
        
        # Stats by business
        by_business = defaultdict(lambda: {"emails": 0, "sms": 0})
        
        for campaign in today_campaigns:
            business = campaign.get("business_id", "unknown")
            type_ = campaign.get("type", "unknown")
            stats = campaign.get("stats", {})
            
            if type_ == "email":
                by_business[business]["emails"] += stats.get("emails_sent", 0)
            elif type_ == "sms":
                by_business[business]["sms"] += stats.get("messages_sent", 0)
        
        # Display
        for business, stats in by_business.items():
            print(f"📊 {business}:")
            print(f"   Emails sent: {stats['emails']}")
            print(f"   SMS sent: {stats['sms']}")
            print()
        
        # Check for errors in log
        if self.log_file.exists():
            with open(self.log_file) as f:
                lines = f.readlines()[-50:]  # Last 50 lines
            
            errors = [l for l in lines if "ERROR" in l or "WARNING" in l]
            if errors:
                print("⚠️  Recent warnings/errors:")
                for error in errors[-5:]:  # Last 5 errors
                    print(f"   {error.strip()}")
            else:
                print("✅ No errors in recent logs")
        
        print()
    
    def week_summary(self):
        """Weekly summary of outreach performance."""
        print("\n" + "="*60)
        print("WEEK 1 OUTREACH SUMMARY")
        print("="*60)
        
        # Load history
        history = self.load_history()
        campaigns = history.get("campaigns", [])
        
        # Week 1 campaigns (last 7 days)
        week_ago = (datetime.now() - timedelta(days=7)).isoformat()
        week_campaigns = [c for c in campaigns if c.get("sent_at", "") >= week_ago]
        
        if not week_campaigns:
            print("No campaigns in the last 7 days")
            return
        
        # Aggregate stats
        stats = {
            "marceau-solutions": {"emails": 0, "sms": 0, "days": set()},
            "swflorida-hvac": {"emails": 0, "sms": 0, "days": set()}
        }
        
        for campaign in week_campaigns:
            business = campaign.get("business_id", "unknown")
            type_ = campaign.get("type", "unknown")
            sent_at = campaign.get("sent_at", "")
            day = sent_at.split("T")[0] if "T" in sent_at else sent_at[:10]
            
            if business in stats:
                stats[business]["days"].add(day)
                
                c_stats = campaign.get("stats", {})
                if type_ == "email":
                    stats[business]["emails"] += c_stats.get("emails_sent", 0)
                elif type_ == "sms":
                    stats[business]["sms"] += c_stats.get("messages_sent", 0)
        
        # Display
        print("\nMarceau Solutions (AI Automation)")
        print(f"  Days active: {len(stats['marceau-solutions']['days'])}/7")
        print(f"  Emails sent: {stats['marceau-solutions']['emails']} (target: 140/week)")
        print(f"  SMS sent: {stats['marceau-solutions']['sms']} (target: 70/week)")
        
        print("\nSW Florida Comfort HVAC")
        print(f"  Days active: {len(stats['swflorida-hvac']['days'])}/7")
        print(f"  Emails sent: {stats['swflorida-hvac']['emails']} (target: 105/week)")
        print(f"  SMS sent: {stats['swflorida-hvac']['sms']} (target: 70/week)")
        
        print("\n" + "="*60)
        print("EXPECTED RESPONSES (based on 2-5% rate)")
        print("="*60)
        
        total_sent = (stats['marceau-solutions']['emails'] + 
                     stats['marceau-solutions']['sms'] +
                     stats['swflorida-hvac']['emails'] + 
                     stats['swflorida-hvac']['sms'])
        
        expected_low = int(total_sent * 0.02)
        expected_high = int(total_sent * 0.05)
        
        print(f"\nTotal outreach: {total_sent}")
        print(f"Expected replies: {expected_low}-{expected_high}")
        print(f"\n✅ Check SMS replies daily")
        print(f"✅ Check email inbox for responses")
        print()
    
    def high_value_leads(self, limit: int = 20):
        """Identify high-value leads for manual email collection."""
        from .scraper import LeadDatabase
        
        db = LeadDatabase()
        
        print("\n" + "="*60)
        print("HIGH-VALUE LEADS FOR MANUAL EMAIL COLLECTION")
        print("="*60)
        print(f"Finding top {limit} restaurants/gyms with websites\n")
        
        # Filter criteria:
        # 1. Has website (can find contact info)
        # 2. No email yet
        # 3. Good reviews OR high-traffic location
        # 4. Restaurant or gym
        
        candidates = []
        for lead in db.leads.values():
            if not lead.website:
                continue
            if lead.email:
                continue
            if lead.category not in ["restaurant", "gym"]:
                continue
            
            # Score based on:
            # - Review count (more reviews = more popular)
            # - Rating (higher = better quality)
            # - Pain points (no_website = easier sell)
            
            score = 0
            
            # Review count (0-10 points)
            if hasattr(lead, 'review_count') and lead.review_count:
                score += min(10, lead.review_count / 10)
            
            # Rating (0-5 points)
            if hasattr(lead, 'rating') and lead.rating:
                score += lead.rating
            
            # Pain points (bonus points)
            if "no_website" in lead.pain_points:
                score += 5  # Easy sell
            if "low_reviews" in lead.pain_points:
                score += 2  # Needs help with online presence
            
            candidates.append({
                "lead": lead,
                "score": score
            })
        
        # Sort by score
        candidates.sort(key=lambda x: x["score"], reverse=True)
        
        # Display top N
        print(f"Found {len(candidates)} leads with websites\n")
        print("Top candidates for manual outreach:\n")
        
        for i, candidate in enumerate(candidates[:limit], 1):
            lead = candidate["lead"]
            score = candidate["score"]
            
            print(f"{i}. {lead.name}")
            print(f"   Category: {lead.category}")
            print(f"   Website: {lead.website}")
            if hasattr(lead, 'rating') and lead.rating:
                print(f"   Rating: {lead.rating:.1f} stars")
            if hasattr(lead, 'review_count') and lead.review_count:
                print(f"   Reviews: {lead.review_count}")
            print(f"   Pain points: {', '.join(lead.pain_points)}")
            print(f"   Score: {score:.1f}")
            print(f"   📧 TODO: Find owner email via website contact page or LinkedIn")
            print()
        
        # Export to CSV for easier manual work
        csv_file = self.output_dir / "high_value_leads_manual_email.csv"
        with open(csv_file, 'w') as f:
            f.write("Name,Category,Website,Phone,Pain Points,Score\n")
            for candidate in candidates[:limit]:
                lead = candidate["lead"]
                f.write(f'"{lead.name}","{lead.category}","{lead.website}","{lead.phone}","{",".join(lead.pain_points)}",{candidate["score"]:.1f}\n')
        
        print(f"✅ Exported to: {csv_file}")
        print(f"\nNext steps:")
        print(f"1. Visit each website's contact page")
        print(f"2. Find owner on LinkedIn (search: '[Business Name] owner Naples')")
        print(f"3. Add emails to leads.json manually")
        print(f"4. Re-run outreach scheduler to send emails")
        print()

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Monitor weekly outreach performance")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Daily check
    subparsers.add_parser("daily-check", help="Quick daily outreach check")
    
    # Week summary
    subparsers.add_parser("week-summary", help="Weekly performance summary")
    
    # High-value leads
    high_value_parser = subparsers.add_parser("high-value-leads", help="Find leads for manual email collection")
    high_value_parser.add_argument("--limit", "-l", type=int, default=20, help="Number of leads to show")
    
    args = parser.parse_args()
    
    monitor = WeeklyMonitor()
    
    if args.command == "daily-check":
        monitor.daily_check()
    elif args.command == "week-summary":
        monitor.week_summary()
    elif args.command == "high-value-leads":
        monitor.high_value_leads(limit=args.limit)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
