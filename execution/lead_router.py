#!/usr/bin/env python3
"""
Lead Router — Intelligent multi-tower lead routing with learning layer.

Scores incoming leads for fit with each tower and recommends optimal assignment.
Learns from conversion outcomes to improve routing over time.

TOWERS:
  - digital-ai-services   AI automation (missed call text-back, chatbots)
  - digital-web-dev       Website builds and redesigns
  - fitness-coaching      1:1 PT coaching ($197/mo)
  - fitness-influencer    Brand partnership deals for influencer clients

SCORING FACTORS:
  1. Industry match (30%) - Direct industry → tower mapping
  2. Keyword match (20%) - Pain points, notes contain tower keywords
  3. Company size fit (15%) - Employee count, revenue in tower's sweet spot
  4. Budget signals (15%) - Proposal amount fits tower's pricing
  5. Pain point match (10%) - Specific pain points align with tower solutions
  6. Lead source bonus (10%) - Referrals/inbound score higher

LEARNING LAYER:
  - Tracks which lead characteristics → conversions by tower
  - Adjusts routing scores based on historical outcomes
  - Feeds successful patterns back to routing rules

Usage:
    from execution.lead_router import LeadRouter, score_lead, route_new_leads
    
    # Score a single lead
    scores = score_lead(deal_dict)
    # Returns: {'digital-ai-services': 85, 'digital-web-dev': 42, ...}
    
    # Auto-route all unrouted leads
    route_new_leads()
    
    # Learn from outcomes
    update_learning_from_conversions()
"""

import json
import logging
import re
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"
RULES_FILE = DATA_DIR / "routing_rules.json"
LEARNING_FILE = DATA_DIR / "routing_learning.json"

# Lazy import to avoid circular
_pipeline_db = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("lead_router")


def _get_pipeline_db():
    """Lazy import pipeline_db to avoid circular imports."""
    global _pipeline_db
    if _pipeline_db is None:
        import sys
        sys.path.insert(0, str(REPO_ROOT / "execution"))
        import pipeline_db
        _pipeline_db = pipeline_db
    return _pipeline_db


def load_routing_rules() -> Dict:
    """Load routing rules from JSON config."""
    if RULES_FILE.exists():
        with open(RULES_FILE) as f:
            return json.load(f)
    logger.warning("No routing_rules.json found, using defaults")
    return _get_default_rules()


def load_learning_data() -> Dict:
    """Load historical learning data."""
    if LEARNING_FILE.exists():
        with open(LEARNING_FILE) as f:
            return json.load(f)
    return {
        "industry_conversions": {},
        "keyword_conversions": {},
        "score_adjustments": {},
        "last_updated": None
    }


def save_learning_data(data: Dict):
    """Save learning data to disk."""
    data["last_updated"] = datetime.now().isoformat()
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(LEARNING_FILE, "w") as f:
        json.dump(data, f, indent=2)


def _get_default_rules() -> Dict:
    """Fallback routing rules if config not found."""
    return {
        "towers": {
            "digital-ai-services": {"base_score": 50, "ideal_industries": []},
            "digital-web-dev": {"base_score": 40, "ideal_industries": []},
            "fitness-coaching": {"base_score": 30, "ideal_industries": []},
            "fitness-influencer": {"base_score": 20, "ideal_industries": []},
        },
        "industry_mappings": {},
        "scoring_weights": {
            "industry_match": 30,
            "keyword_match": 20,
            "company_size_fit": 15,
            "budget_signals": 15,
            "pain_point_match": 10,
            "lead_source_bonus": 10
        },
        "lead_source_bonuses": {},
        "override_rules": []
    }


class LeadRouter:
    """
    Intelligent lead router that scores and assigns leads to towers.
    """
    
    def __init__(self, rules: Optional[Dict] = None):
        self.rules = rules or load_routing_rules()
        self.learning = load_learning_data()
        self.towers = list(self.rules.get("towers", {}).keys())
    
    def score_lead(self, lead: Dict) -> Dict[str, int]:
        """
        Score a lead for each tower.
        
        Args:
            lead: Deal dictionary with keys like industry, pain_points, 
                  lead_source, proposal_amount, notes, etc.
        
        Returns:
            Dict mapping tower_id → score (0-100)
        """
        scores = {}
        weights = self.rules.get("scoring_weights", {})
        
        for tower_id, tower_config in self.rules.get("towers", {}).items():
            score = tower_config.get("base_score", 40)
            
            # 1. Industry match
            score += self._score_industry_match(lead, tower_id, tower_config, weights)
            
            # 2. Keyword match (pain points, notes)
            score += self._score_keyword_match(lead, tower_id, tower_config, weights)
            
            # 3. Company size fit
            score += self._score_company_fit(lead, tower_config, weights)
            
            # 4. Budget signals
            score += self._score_budget_fit(lead, tower_id, tower_config, weights)
            
            # 5. Pain point specific match
            score += self._score_pain_points(lead, tower_id, weights)
            
            # 6. Lead source bonus
            score += self._score_lead_source(lead, weights)
            
            # 7. Learning adjustments
            score += self._apply_learning_adjustments(lead, tower_id)
            
            # Clamp to 0-100
            scores[tower_id] = max(0, min(100, int(score)))
        
        # Apply override rules (can force or boost specific towers)
        scores = self._apply_override_rules(lead, scores)
        
        return scores
    
    def _score_industry_match(self, lead: Dict, tower_id: str, 
                              tower_config: Dict, weights: Dict) -> int:
        """Score based on industry → tower mapping."""
        industry = (lead.get("industry") or "").strip()
        if not industry:
            return 0
        
        max_weight = weights.get("industry_match", 30)
        
        # Check direct mapping
        mappings = self.rules.get("industry_mappings", {})
        if industry in mappings:
            mapping = mappings[industry]
            if mapping.get("primary") == tower_id:
                return max_weight
            elif mapping.get("secondary") == tower_id:
                return max_weight // 2
        
        # Check if in ideal_industries list
        ideal = tower_config.get("ideal_industries", [])
        if industry in ideal:
            return max_weight
        
        # Fuzzy match
        industry_lower = industry.lower()
        for ideal_ind in ideal:
            if ideal_ind.lower() in industry_lower or industry_lower in ideal_ind.lower():
                return max_weight * 0.7
        
        return 0
    
    def _score_keyword_match(self, lead: Dict, tower_id: str,
                             tower_config: Dict, weights: Dict) -> int:
        """Score based on keywords in pain_points, notes, etc."""
        max_weight = weights.get("keyword_match", 20)
        
        # Combine all text fields
        text_fields = [
            lead.get("pain_points", ""),
            lead.get("notes", ""),
            lead.get("next_action", ""),
            lead.get("company", "")
        ]
        combined_text = " ".join(str(f) for f in text_fields if f).lower()
        
        if not combined_text:
            return 0
        
        keywords = tower_config.get("keywords", [])
        if not keywords:
            return 0
        
        matches = sum(1 for kw in keywords if kw.lower() in combined_text)
        if matches == 0:
            return 0
        
        # Score based on match ratio
        match_ratio = min(matches / len(keywords), 1.0)
        return int(max_weight * match_ratio)
    
    def _score_company_fit(self, lead: Dict, tower_config: Dict, 
                           weights: Dict) -> int:
        """Score based on company size/revenue fit."""
        max_weight = weights.get("company_size_fit", 15)
        size_config = tower_config.get("company_size_fit", {})
        
        if not size_config:
            return max_weight // 2  # Neutral if no config
        
        # We don't always have company size data, give partial credit
        # In future: integrate with Apollo/Clearbit for company data
        return max_weight // 3
    
    def _score_budget_fit(self, lead: Dict, tower_id: str,
                          tower_config: Dict, weights: Dict) -> int:
        """Score based on budget/proposal amount alignment."""
        max_weight = weights.get("budget_signals", 15)
        budget_config = tower_config.get("budget_signals", {})
        
        if not budget_config:
            return 0
        
        # Check proposal_amount or monthly_fee
        amount = lead.get("proposal_amount") or lead.get("monthly_fee") or 0
        
        if amount == 0:
            return 0
        
        # Check against tower's ideal range
        ideal_monthly = budget_config.get("ideal_monthly") or budget_config.get("ideal_project", 0)
        min_val = budget_config.get("min_monthly") or budget_config.get("min_project", 0)
        high_val = budget_config.get("high_value") or budget_config.get("ideal_deal", 0)
        
        if amount >= ideal_monthly:
            return max_weight
        elif amount >= min_val:
            return int(max_weight * 0.7)
        
        return 0
    
    def _score_pain_points(self, lead: Dict, tower_id: str, weights: Dict) -> int:
        """Score specific pain point alignment."""
        max_weight = weights.get("pain_point_match", 10)
        pain_points = lead.get("pain_points") or ""
        
        if not pain_points:
            return 0
        
        pain_lower = pain_points.lower()
        
        # Tower-specific pain point indicators
        indicators = {
            "digital-ai-services": ["missed call", "after hours", "leads", "booking", "text back", "chatbot"],
            "digital-web-dev": ["website", "redesign", "seo", "online", "landing page", "mobile"],
            "fitness-coaching": ["weight", "strength", "muscle", "training", "workout", "nutrition"],
            "fitness-influencer": ["brand", "sponsor", "partnership", "content", "social media"]
        }
        
        tower_indicators = indicators.get(tower_id, [])
        matches = sum(1 for ind in tower_indicators if ind in pain_lower)
        
        if matches > 0:
            return min(max_weight, matches * 5)
        
        return 0
    
    def _score_lead_source(self, lead: Dict, weights: Dict) -> int:
        """Bonus score based on lead source quality."""
        max_weight = weights.get("lead_source_bonus", 10)
        source = (lead.get("lead_source") or "").lower()
        
        bonuses = self.rules.get("lead_source_bonuses", {})
        
        for source_key, bonus in bonuses.items():
            if source_key.lower() in source:
                return min(bonus, max_weight)
        
        return 0
    
    def _apply_learning_adjustments(self, lead: Dict, tower_id: str) -> int:
        """Apply learned adjustments based on historical conversions."""
        adjustments = self.learning.get("score_adjustments", {})
        industry = lead.get("industry", "Other")
        
        # Check for industry-specific adjustment
        key = f"{industry}:{tower_id}"
        if key in adjustments:
            return adjustments[key]
        
        return 0
    
    def _apply_override_rules(self, lead: Dict, scores: Dict[str, int]) -> Dict[str, int]:
        """Apply override rules that can force or boost specific towers."""
        override_rules = self.rules.get("override_rules", [])
        
        # Sort by priority (highest first)
        override_rules = sorted(override_rules, key=lambda r: r.get("priority", 0), reverse=True)
        
        for rule in override_rules:
            if self._rule_matches(lead, rule.get("condition", {})):
                action = rule.get("action", {})
                
                if "force_tower" in action:
                    # Force this tower to 100, others to 0
                    forced = action["force_tower"]
                    return {t: (100 if t == forced else 0) for t in scores}
                
                if "boost_tower" in action:
                    tower = action["boost_tower"]
                    boost = action.get("boost_amount", 20)
                    if tower in scores:
                        scores[tower] = min(100, scores[tower] + boost)
        
        return scores
    
    def _rule_matches(self, lead: Dict, condition: Dict) -> bool:
        """Check if a lead matches an override rule condition."""
        if not condition:
            return False
        
        # Check industry_contains
        if "industry_contains" in condition:
            industry = (lead.get("industry") or "").lower()
            if not any(kw.lower() in industry for kw in condition["industry_contains"]):
                return False
        
        # Check pain_points_contain
        if "pain_points_contain" in condition:
            pain = (lead.get("pain_points") or "").lower()
            notes = (lead.get("notes") or "").lower()
            combined = pain + " " + notes
            if not any(kw.lower() in combined for kw in condition["pain_points_contain"]):
                return False
        
        # Check lead_source
        if "lead_source" in condition:
            source = (lead.get("lead_source") or "").lower()
            if condition["lead_source"].lower() not in source:
                return False
        
        return True
    
    def get_recommendation(self, lead: Dict) -> Tuple[str, Dict[str, int]]:
        """
        Get the recommended tower for a lead.
        
        Returns:
            Tuple of (recommended_tower_id, all_scores)
        """
        scores = self.score_lead(lead)
        
        # Find highest scoring tower
        if not scores:
            return "digital-ai-services", {}
        
        recommended = max(scores, key=scores.get)
        return recommended, scores
    
    def get_ranked_towers(self, lead: Dict) -> List[Tuple[str, int]]:
        """
        Get towers ranked by score for a lead.
        
        Returns:
            List of (tower_id, score) tuples, sorted by score descending
        """
        scores = self.score_lead(lead)
        return sorted(scores.items(), key=lambda x: x[1], reverse=True)


# ── Convenience Functions ─────────────────────────────────────────────────────

def score_lead(lead: Dict) -> Dict[str, int]:
    """Score a single lead for all towers."""
    router = LeadRouter()
    return router.score_lead(lead)


def recommend_tower(lead: Dict) -> Tuple[str, Dict[str, int]]:
    """Get recommended tower for a lead."""
    router = LeadRouter()
    return router.get_recommendation(lead)


def route_new_leads(dry_run: bool = False) -> Dict:
    """
    Route all unrouted leads (where tower is still default and recommended_tower is null).
    
    Returns:
        Summary of routing actions taken
    """
    pdb = _get_pipeline_db()
    conn = pdb.get_db()
    
    # Add recommended_tower column if not exists
    _ensure_recommended_tower_column(conn)
    
    # Find leads that haven't been routed
    leads = conn.execute("""
        SELECT * FROM deals 
        WHERE recommended_tower IS NULL 
        AND tower = 'digital-ai-services'
        AND stage NOT IN ('Closed Won', 'Closed Lost')
        ORDER BY created_at DESC
        LIMIT 100
    """).fetchall()
    
    router = LeadRouter()
    results = {"routed": 0, "skipped": 0, "errors": 0, "details": []}
    
    for lead in leads:
        lead_dict = dict(lead)
        
        try:
            recommended, scores = router.get_recommendation(lead_dict)
            
            detail = {
                "deal_id": lead_dict["id"],
                "company": lead_dict.get("company"),
                "industry": lead_dict.get("industry"),
                "recommended": recommended,
                "scores": scores
            }
            
            if dry_run:
                logger.info(f"[DRY RUN] Would route {lead_dict.get('company')} → {recommended}")
                results["details"].append(detail)
                results["routed"] += 1
                continue
            
            # Update the deal with recommendation
            conn.execute("""
                UPDATE deals 
                SET recommended_tower = ?, updated_at = datetime('now')
                WHERE id = ?
            """, (recommended, lead_dict["id"]))
            
            results["routed"] += 1
            results["details"].append(detail)
            
        except Exception as e:
            logger.error(f"Error routing deal {lead_dict.get('id')}: {e}")
            results["errors"] += 1
    
    conn.commit()
    conn.close()
    
    return results


def _ensure_recommended_tower_column(conn: sqlite3.Connection):
    """Add recommended_tower column if it doesn't exist."""
    try:
        conn.execute("ALTER TABLE deals ADD COLUMN recommended_tower TEXT")
        conn.commit()
        logger.info("Added recommended_tower column to deals table")
    except sqlite3.OperationalError:
        pass  # Column already exists


# ── Learning Layer ───────────────────────────────────────────────────────────

def update_learning_from_conversions():
    """
    Analyze closed deals and update learning data.
    Track which lead characteristics → conversions by tower.
    """
    pdb = _get_pipeline_db()
    conn = pdb.get_db()
    learning = load_learning_data()
    
    # Get recent conversions (last 90 days)
    config = load_routing_rules().get("learning_config", {})
    decay_days = config.get("recency_decay_days", 90)
    
    closed_deals = conn.execute("""
        SELECT * FROM deals 
        WHERE stage IN ('Closed Won', 'Closed Lost')
        AND updated_at > datetime('now', ?)
    """, (f'-{decay_days} days',)).fetchall()
    
    # Count conversions by industry + tower
    industry_conversions = {}
    
    for deal in closed_deals:
        d = dict(deal)
        industry = d.get("industry", "Other")
        tower = d.get("tower", "digital-ai-services")
        key = f"{industry}:{tower}"
        
        if key not in industry_conversions:
            industry_conversions[key] = {"won": 0, "lost": 0}
        
        if d["stage"] == "Closed Won":
            industry_conversions[key]["won"] += 1
        else:
            industry_conversions[key]["lost"] += 1
    
    # Calculate score adjustments based on conversion rates
    score_adjustments = {}
    min_samples = config.get("min_samples_for_adjustment", 10)
    max_adjustment = config.get("max_score_adjustment", 15)
    
    for key, counts in industry_conversions.items():
        total = counts["won"] + counts["lost"]
        if total < min_samples:
            continue
        
        win_rate = counts["won"] / total
        
        # If win rate > 60%, boost this industry:tower combo
        if win_rate > 0.6:
            adjustment = int((win_rate - 0.5) * max_adjustment * 2)
            score_adjustments[key] = min(adjustment, max_adjustment)
        # If win rate < 40%, penalize
        elif win_rate < 0.4:
            adjustment = int((0.5 - win_rate) * max_adjustment * -2)
            score_adjustments[key] = max(adjustment, -max_adjustment)
    
    # Update learning data
    learning["industry_conversions"] = industry_conversions
    learning["score_adjustments"] = score_adjustments
    save_learning_data(learning)
    
    conn.close()
    
    logger.info(f"Learning updated: {len(score_adjustments)} adjustments from {len(closed_deals)} deals")
    return learning


def get_routing_analytics() -> Dict:
    """
    Get analytics on routing performance.
    """
    pdb = _get_pipeline_db()
    conn = pdb.get_db()
    
    analytics = {
        "total_deals": 0,
        "routed_deals": 0,
        "tower_distribution": {},
        "industry_distribution": {},
        "conversion_by_tower": {}
    }
    
    # Total deals
    analytics["total_deals"] = conn.execute(
        "SELECT COUNT(*) FROM deals"
    ).fetchone()[0]
    
    # Routed deals
    analytics["routed_deals"] = conn.execute(
        "SELECT COUNT(*) FROM deals WHERE recommended_tower IS NOT NULL"
    ).fetchone()[0]
    
    # Distribution by tower
    rows = conn.execute("""
        SELECT tower, COUNT(*) as count 
        FROM deals 
        GROUP BY tower
    """).fetchall()
    analytics["tower_distribution"] = {r["tower"]: r["count"] for r in rows}
    
    # Distribution by industry
    rows = conn.execute("""
        SELECT industry, COUNT(*) as count 
        FROM deals 
        GROUP BY industry
        ORDER BY count DESC
        LIMIT 15
    """).fetchall()
    analytics["industry_distribution"] = {r["industry"]: r["count"] for r in rows}
    
    # Conversion by tower
    rows = conn.execute("""
        SELECT tower, 
               SUM(CASE WHEN stage = 'Closed Won' THEN 1 ELSE 0 END) as won,
               SUM(CASE WHEN stage = 'Closed Lost' THEN 1 ELSE 0 END) as lost
        FROM deals
        WHERE stage IN ('Closed Won', 'Closed Lost')
        GROUP BY tower
    """).fetchall()
    
    for row in rows:
        total = row["won"] + row["lost"]
        analytics["conversion_by_tower"][row["tower"]] = {
            "won": row["won"],
            "lost": row["lost"],
            "win_rate": round(row["won"] / total * 100, 1) if total > 0 else 0
        }
    
    conn.close()
    return analytics


# ── Integration Functions ─────────────────────────────────────────────────────

def auto_assign_on_import(deal_id: int) -> Optional[str]:
    """
    Auto-assign a recommended tower when a new deal is imported.
    Called by pipeline_db.create_deal() or lead import scripts.
    
    Returns:
        The recommended tower ID, or None if already assigned
    """
    pdb = _get_pipeline_db()
    conn = pdb.get_db()
    _ensure_recommended_tower_column(conn)
    
    deal = conn.execute("SELECT * FROM deals WHERE id = ?", (deal_id,)).fetchone()
    if not deal:
        return None
    
    lead_dict = dict(deal)
    
    # Skip if already has a recommendation
    if lead_dict.get("recommended_tower"):
        return lead_dict["recommended_tower"]
    
    router = LeadRouter()
    recommended, scores = router.get_recommendation(lead_dict)
    
    # Update deal
    conn.execute("""
        UPDATE deals 
        SET recommended_tower = ?, updated_at = datetime('now')
        WHERE id = ?
    """, (recommended, deal_id))
    conn.commit()
    conn.close()
    
    logger.info(f"Auto-routed deal {deal_id} ({lead_dict.get('company')}) → {recommended}")
    return recommended


def backfill_routing():
    """
    Backfill recommended_tower for all existing deals that don't have one.
    """
    return route_new_leads(dry_run=False)


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Lead Routing System")
    parser.add_argument("command", choices=["route", "backfill", "learn", "analytics", "test"],
                        help="Command to run")
    parser.add_argument("--dry-run", action="store_true", help="Preview without changes")
    parser.add_argument("--deal-id", type=int, help="Test specific deal ID")
    args = parser.parse_args()
    
    if args.command == "route":
        results = route_new_leads(dry_run=args.dry_run)
        print(f"✅ Routed {results['routed']} leads")
        if results.get("details"):
            for d in results["details"][:10]:
                print(f"  • {d['company']} ({d['industry']}) → {d['recommended']}")
    
    elif args.command == "backfill":
        results = backfill_routing()
        print(f"✅ Backfilled {results['routed']} leads")
    
    elif args.command == "learn":
        learning = update_learning_from_conversions()
        print(f"✅ Learning updated: {len(learning.get('score_adjustments', {}))} adjustments")
    
    elif args.command == "analytics":
        analytics = get_routing_analytics()
        print("\n📊 Routing Analytics:")
        print(f"  Total deals: {analytics['total_deals']}")
        print(f"  Routed deals: {analytics['routed_deals']}")
        print("\n  Tower Distribution:")
        for tower, count in analytics.get("tower_distribution", {}).items():
            print(f"    {tower}: {count}")
        print("\n  Conversion by Tower:")
        for tower, data in analytics.get("conversion_by_tower", {}).items():
            print(f"    {tower}: {data['won']} won / {data['lost']} lost ({data['win_rate']}%)")
    
    elif args.command == "test":
        pdb = _get_pipeline_db()
        conn = pdb.get_db()
        
        if args.deal_id:
            deal = conn.execute("SELECT * FROM deals WHERE id = ?", (args.deal_id,)).fetchone()
            if deal:
                router = LeadRouter()
                recommended, scores = router.get_recommendation(dict(deal))
                print(f"\n🎯 Deal #{args.deal_id}: {deal['company']}")
                print(f"   Industry: {deal['industry']}")
                print(f"   Recommended: {recommended}")
                print(f"   All scores: {scores}")
        else:
            # Test with sample deals
            deals = conn.execute("""
                SELECT * FROM deals 
                WHERE stage NOT IN ('Closed Won', 'Closed Lost')
                LIMIT 5
            """).fetchall()
            
            router = LeadRouter()
            print("\n🎯 Sample Lead Routing:")
            for deal in deals:
                d = dict(deal)
                recommended, scores = router.get_recommendation(d)
                top_score = scores.get(recommended, 0)
                print(f"  • {d['company'][:30]:30} | {d['industry'][:20]:20} → {recommended} ({top_score})")
        
        conn.close()
