#!/usr/bin/env python3
"""
Weekly Lead List Generation System — Autonomous ICP-Scored Lead Discovery

Generates a fresh, deduplicated, ICP-tiered lead list on a configurable schedule
(default: weekly Monday 8am). Integrates with outcome_learner for dynamic 
frequency adjustment and learned preferences.

Features:
  - Weekly default cadence (configurable via outcome_learner preferences)
  - ICP tiering/scoring on ingest (Tier 1-3)
  - Deduplication against existing pipeline.db
  - Enrichment via Apollo (verified emails/phones)
  - Export to dated CSV AND pipeline.db "Prospect" stage
  - Activity logging for audit trail
  - Summary output for morning digest integration
  - Dynamic frequency hooks for outcome_learner self-improvement

Usage:
    python -m src.generate_new_lead_list generate --limit 100         # Weekly generation (default)
    python -m src.generate_new_lead_list generate --limit 50 --dry-run # Preview
    python -m src.generate_new_lead_list status                        # Show last generation stats
    python -m src.generate_new_lead_list should-run                    # Check if generation is due

Schedule (cron):
    # Weekly Monday 8am ET (12:00 UTC)
    0 12 * * 1 cd /home/clawdbot/dev-sandbox && python3 -m projects.lead_generation.src.generate_new_lead_list generate --limit 100

Integration:
    - Called by daily_loop.py on designated generation days
    - Writes summary to DIGEST_FILE for morning digest inclusion
    - Updates learned_preferences.json with generation outcomes
"""

import argparse
import csv
import json
import logging
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Setup paths
PROJECT_ROOT = Path(__file__).parent.parent
SRC_DIR = Path(__file__).parent
REPO_ROOT = PROJECT_ROOT.parent.parent

sys.path.insert(0, str(SRC_DIR))
sys.path.insert(0, str(REPO_ROOT))

try:
    from dotenv import load_dotenv
    load_dotenv(REPO_ROOT / ".env")
except ImportError:
    pass

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("lead_list_gen")

# Output paths
OUTPUT_DIR = PROJECT_ROOT / "output" / "weekly_lists"
STATE_FILE = PROJECT_ROOT / "logs" / "lead_generation_state.json"
DIGEST_FILE = PROJECT_ROOT / "logs" / "generation_digest.json"


# =============================================================================
# ICP SCORING CONFIGURATION
# =============================================================================

# Tier 1: Best fit (80-100 score)
# Tier 2: Good fit (50-79 score)
# Tier 3: Possible fit (20-49 score)
# Below 20: Discard

ICP_WEIGHTS = {
    # Industry fit (based on William's experience + outcome_learner adjustments)
    "industry": {
        "hvac": 30,
        "plumbing": 30,
        "electrical": 25,
        "med spa": 28,
        "medspa": 28,
        "dental": 25,
        "chiropractic": 25,
        "chiropractor": 25,
        "fitness": 20,
        "gym": 20,
        "roofing": 22,
        "pest control": 22,
        "landscaping": 20,
        "pool": 20,
        "auto repair": 18,
        "real estate": 15,
        "restaurant": 10,
        "retail": 8,
        "default": 5,
    },
    # Company size preference
    "employee_count": {
        "1-10": 25,    # Sweet spot for AI automation
        "11-50": 20,
        "51-200": 10,
        "201+": 5,
    },
    # Location preference (Naples focus)
    "location": {
        "naples": 25,
        "bonita springs": 20,
        "fort myers": 18,
        "cape coral": 15,
        "estero": 15,
        "marco island": 12,
        "immokalee": 10,
        "florida": 5,
        "default": 0,
    },
    # Contact quality
    "contact": {
        "verified_email": 10,
        "has_phone": 8,
        "has_owner_name": 7,
        "has_website": 5,
    }
}


def calculate_icp_score(lead: Dict[str, Any]) -> Tuple[int, str, Dict[str, int]]:
    """Calculate ICP score for a lead.
    
    Returns:
        (score: int, tier: str, breakdown: dict)
    """
    breakdown = {}
    score = 0
    
    # Industry scoring
    industry = (lead.get("industry") or lead.get("category") or "").lower()
    industry_score = ICP_WEIGHTS["industry"].get("default", 5)
    for ind_key, ind_val in ICP_WEIGHTS["industry"].items():
        if ind_key in industry:
            industry_score = max(industry_score, ind_val)
    score += industry_score
    breakdown["industry"] = industry_score
    
    # Employee count scoring
    emp_count = lead.get("employee_count", lead.get("num_employees", ""))
    emp_score = 10  # Default moderate score
    if emp_count:
        emp_str = str(emp_count).lower()
        if any(x in emp_str for x in ["1-10", "1 to 10", "micro", "solo"]):
            emp_score = ICP_WEIGHTS["employee_count"]["1-10"]
        elif any(x in emp_str for x in ["11-50", "11 to 50", "small"]):
            emp_score = ICP_WEIGHTS["employee_count"]["11-50"]
        elif any(x in emp_str for x in ["51-200", "medium"]):
            emp_score = ICP_WEIGHTS["employee_count"]["51-200"]
        elif any(x in emp_str for x in ["201", "large", "enterprise"]):
            emp_score = ICP_WEIGHTS["employee_count"]["201+"]
    score += emp_score
    breakdown["employee_count"] = emp_score
    
    # Location scoring
    location = (
        lead.get("city", "") + " " + 
        lead.get("state", "") + " " + 
        lead.get("location", "")
    ).lower()
    loc_score = ICP_WEIGHTS["location"].get("default", 0)
    for loc_key, loc_val in ICP_WEIGHTS["location"].items():
        if loc_key in location:
            loc_score = max(loc_score, loc_val)
    score += loc_score
    breakdown["location"] = loc_score
    
    # Contact quality scoring
    contact_score = 0
    if lead.get("email_status") == "verified" or lead.get("email_confidence", 0) >= 90:
        contact_score += ICP_WEIGHTS["contact"]["verified_email"]
    if lead.get("phone") or lead.get("contact_phone"):
        contact_score += ICP_WEIGHTS["contact"]["has_phone"]
    if lead.get("owner_name") or lead.get("contact_name"):
        contact_score += ICP_WEIGHTS["contact"]["has_owner_name"]
    if lead.get("website"):
        contact_score += ICP_WEIGHTS["contact"]["has_website"]
    score += contact_score
    breakdown["contact_quality"] = contact_score
    
    # Determine tier
    if score >= 80:
        tier = "Tier 1"
    elif score >= 50:
        tier = "Tier 2"
    elif score >= 20:
        tier = "Tier 3"
    else:
        tier = "Discard"
    
    return score, tier, breakdown


def apply_learned_preferences(leads: List[Dict], preferences: Dict) -> List[Dict]:
    """Apply learned preferences from outcome_learner to adjust scores.
    
    Boosts industries that convert well, deprioritizes those that don't.
    """
    # Get industry rankings from outcome_learner
    industry_rankings = {
        r["industry"].lower(): r["conversion_pct"] 
        for r in preferences.get("industry_rankings", [])
    }
    deprioritized = [i.lower() for i in preferences.get("deprioritized_industries", [])]
    
    for lead in leads:
        industry = (lead.get("industry") or "").lower()
        original_score = lead.get("icp_score", 50)
        
        # Boost based on conversion data
        for ind_key, conv_pct in industry_rankings.items():
            if ind_key in industry:
                # +10 points for >50% conversion, +5 for >25%
                if conv_pct > 50:
                    lead["icp_score"] = original_score + 10
                    lead["_score_reason"] = f"+10 (learned: {ind_key} {conv_pct}% conv)"
                elif conv_pct > 25:
                    lead["icp_score"] = original_score + 5
                    lead["_score_reason"] = f"+5 (learned: {ind_key} {conv_pct}% conv)"
                break
        
        # Penalize deprioritized industries
        for dep_ind in deprioritized:
            if dep_ind in industry:
                lead["icp_score"] = max(0, original_score - 15)
                lead["_score_reason"] = f"-15 (learned: {dep_ind} not converting)"
                break
    
    return leads


# =============================================================================
# DISCOVERY SOURCES
# =============================================================================

def discover_from_apollo(limit: int = 100, filters: Dict = None) -> List[Dict]:
    """Discover leads from Apollo API.
    
    Uses ICP-aligned search filters.
    """
    leads = []
    try:
        from .apollo import Apollo, PeopleSearchFilters, Seniority, EmployeeRange, EmailStatus
        
        apollo = Apollo()
        
        # Default ICP filters
        default_filters = PeopleSearchFilters(
            person_titles=["owner", "founder", "ceo", "president", "general manager"],
            person_seniorities=[Seniority.OWNER, Seniority.FOUNDER, Seniority.C_SUITE],
            person_locations=["Naples, FL", "Fort Myers, FL", "Bonita Springs, FL"],
            organization_num_employees_ranges=[EmployeeRange.MICRO, EmployeeRange.SMALL],
            contact_email_status=[EmailStatus.VERIFIED, EmailStatus.GUESSED],
            has_phone=True,
        )
        
        # Target industries for Southwest Florida market
        target_industries = [
            "HVAC", "Plumbing", "Electrical Contractors",
            "Medical Spa", "Dental", "Chiropractic",
            "Roofing", "Pest Control", "Landscaping", "Pool Service",
            "Auto Repair"
        ]
        
        for industry in target_industries:
            if len(leads) >= limit:
                break
            
            try:
                results = apollo.search_people(
                    q_keywords=industry,
                    filters=default_filters,
                    per_page=min(25, limit - len(leads))
                )
                
                for person in results.get("people", []):
                    org = person.get("organization", {})
                    lead = {
                        "company": org.get("name", ""),
                        "contact_name": person.get("name", ""),
                        "contact_email": person.get("email", ""),
                        "email_status": person.get("email_status", ""),
                        "contact_phone": person.get("phone_numbers", [{}])[0].get("number") if person.get("phone_numbers") else None,
                        "industry": org.get("industry", industry),
                        "city": person.get("city", "Naples"),
                        "state": person.get("state", "FL"),
                        "website": org.get("website_url", ""),
                        "employee_count": org.get("estimated_num_employees", ""),
                        "lead_source": "apollo",
                        "discovered_at": datetime.now().isoformat(),
                    }
                    leads.append(lead)
                    
            except Exception as e:
                logger.warning(f"Apollo search for {industry} failed: {e}")
                continue
        
        logger.info(f"Apollo: Discovered {len(leads)} leads")
        
    except ImportError:
        logger.warning("Apollo module not available — skipping Apollo discovery")
    except Exception as e:
        logger.error(f"Apollo discovery failed: {e}")
    
    return leads


def discover_from_google_places(limit: int = 50) -> List[Dict]:
    """Discover leads from Google Places API."""
    leads = []
    try:
        from .google_places import GooglePlacesClient
        
        client = GooglePlacesClient()
        
        # Target search queries for ICP
        queries = [
            "HVAC company Naples FL",
            "plumber Naples FL",
            "electrician Naples FL",
            "med spa Naples FL",
            "dentist Naples FL",
            "chiropractor Naples FL",
            "roofing contractor Fort Myers FL",
            "pest control Bonita Springs FL",
        ]
        
        for query in queries:
            if len(leads) >= limit:
                break
            
            try:
                results = client.search_businesses(query, max_results=10)
                for place in results:
                    lead = {
                        "company": place.get("name", ""),
                        "contact_phone": place.get("phone", ""),
                        "industry": query.split()[0],  # First word is usually the industry
                        "city": place.get("city", "Naples"),
                        "state": "FL",
                        "website": place.get("website", ""),
                        "lead_source": "google_places",
                        "review_count": place.get("review_count", 0),
                        "rating": place.get("rating", 0),
                        "discovered_at": datetime.now().isoformat(),
                    }
                    leads.append(lead)
            except Exception as e:
                logger.warning(f"Google Places search for '{query}' failed: {e}")
        
        logger.info(f"Google Places: Discovered {len(leads)} leads")
        
    except ImportError:
        logger.warning("Google Places module not available — skipping")
    except Exception as e:
        logger.error(f"Google Places discovery failed: {e}")
    
    return leads


def discover_from_existing_leads(limit: int = 50) -> List[Dict]:
    """Load existing leads that haven't been processed yet."""
    leads = []
    try:
        from .models import LeadCollection
        
        collection = LeadCollection(str(PROJECT_ROOT / "output"))
        collection.load_json()
        
        for lead_id, lead in list(collection.leads.items())[:limit]:
            lead_dict = {
                "company": lead.business_name,
                "contact_name": lead.owner_name,
                "contact_email": lead.email,
                "contact_phone": lead.phone,
                "industry": lead.category,
                "city": lead.city or "Naples",
                "state": lead.state or "FL",
                "website": lead.website,
                "lead_source": "existing_leads",
                "discovered_at": datetime.now().isoformat(),
            }
            leads.append(lead_dict)
        
        logger.info(f"Existing leads: Loaded {len(leads)} leads")
        
    except Exception as e:
        logger.warning(f"Existing leads load failed: {e}")
    
    return leads


# =============================================================================
# DEDUPLICATION
# =============================================================================

def get_existing_companies(conn) -> set:
    """Get set of existing company names (lowercased) for deduplication."""
    rows = conn.execute(
        "SELECT LOWER(company) FROM deals WHERE company IS NOT NULL"
    ).fetchall()
    return {r[0] for r in rows}


def get_existing_phones(conn) -> set:
    """Get set of existing phone numbers for deduplication."""
    rows = conn.execute(
        "SELECT contact_phone FROM deals WHERE contact_phone IS NOT NULL"
    ).fetchall()
    # Normalize phones to last 10 digits
    phones = set()
    for r in rows:
        phone = r[0].replace("-", "").replace(" ", "").replace("(", "").replace(")", "")
        if len(phone) >= 10:
            phones.add(phone[-10:])
    return phones


def get_existing_emails(conn) -> set:
    """Get set of existing email addresses for deduplication."""
    rows = conn.execute(
        "SELECT LOWER(contact_email) FROM deals WHERE contact_email IS NOT NULL"
    ).fetchall()
    return {r[0] for r in rows}


def deduplicate_leads(leads: List[Dict], conn) -> Tuple[List[Dict], int]:
    """Remove leads that already exist in pipeline.db.
    
    Returns:
        (deduplicated_leads, count_removed)
    """
    existing_companies = get_existing_companies(conn)
    existing_phones = get_existing_phones(conn)
    existing_emails = get_existing_emails(conn)
    
    deduplicated = []
    removed = 0
    
    for lead in leads:
        company_lower = (lead.get("company") or "").lower().strip()
        email_lower = (lead.get("contact_email") or "").lower().strip()
        phone = (lead.get("contact_phone") or "").replace("-", "").replace(" ", "")
        phone_norm = phone[-10:] if len(phone) >= 10 else phone
        
        is_duplicate = False
        
        # Check company name
        if company_lower and company_lower in existing_companies:
            is_duplicate = True
        
        # Check email
        if email_lower and email_lower in existing_emails:
            is_duplicate = True
        
        # Check phone
        if phone_norm and phone_norm in existing_phones:
            is_duplicate = True
        
        if is_duplicate:
            removed += 1
        else:
            deduplicated.append(lead)
            # Add to existing sets to catch duplicates within the batch
            if company_lower:
                existing_companies.add(company_lower)
            if email_lower:
                existing_emails.add(email_lower)
            if phone_norm:
                existing_phones.add(phone_norm)
    
    logger.info(f"Deduplication: {removed} duplicates removed, {len(deduplicated)} unique leads")
    return deduplicated, removed


# =============================================================================
# ENRICHMENT
# =============================================================================

def enrich_leads(leads: List[Dict], dry_run: bool = False) -> List[Dict]:
    """Enrich leads with additional contact data via Apollo."""
    if dry_run:
        logger.info("Enrichment skipped (dry run)")
        return leads
    
    enriched = []
    try:
        from .apollo import Apollo
        apollo = Apollo()
        
        for lead in leads:
            # Skip if already has verified contact
            if lead.get("email_status") == "verified" and lead.get("contact_phone"):
                enriched.append(lead)
                continue
            
            # Try to enrich
            try:
                if lead.get("contact_email"):
                    person = apollo.enrich_person(email=lead["contact_email"])
                    if person:
                        lead["contact_name"] = lead.get("contact_name") or person.get("name")
                        lead["contact_phone"] = lead.get("contact_phone") or (
                            person.get("phone_numbers", [{}])[0].get("number")
                            if person.get("phone_numbers") else None
                        )
                        lead["email_status"] = person.get("email_status", lead.get("email_status"))
                        lead["enriched"] = True
            except Exception as e:
                logger.debug(f"Enrichment failed for {lead.get('company')}: {e}")
            
            enriched.append(lead)
        
        logger.info(f"Enrichment: {sum(1 for l in enriched if l.get('enriched'))} leads enriched")
        
    except ImportError:
        logger.warning("Apollo not available — skipping enrichment")
        enriched = leads
    except Exception as e:
        logger.error(f"Enrichment failed: {e}")
        enriched = leads
    
    return enriched


# =============================================================================
# PIPELINE INTEGRATION
# =============================================================================

def import_to_pipeline(leads: List[Dict], conn, dry_run: bool = False) -> int:
    """Import scored leads into pipeline.db.
    
    Returns count of leads imported.
    """
    if dry_run:
        logger.info(f"Would import {len(leads)} leads (dry run)")
        return 0
    
    imported = 0
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "pipeline_db", REPO_ROOT / "execution" / "pipeline_db.py"
        )
        pdb = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(pdb)
        
        for lead in leads:
            try:
                deal_id = pdb.create_deal(
                    conn,
                    company=lead["company"],
                    tower="digital-ai-services",
                    contact_name=lead.get("contact_name"),
                    contact_phone=lead.get("contact_phone"),
                    contact_email=lead.get("contact_email"),
                    industry=lead.get("industry", "Other"),
                    city=lead.get("city", "Naples"),
                    state=lead.get("state", "FL"),
                    website=lead.get("website"),
                    lead_source=lead.get("lead_source", "weekly_generation"),
                    stage="Prospect",
                    lead_score=lead.get("icp_score", 0),
                    tier=1 if lead.get("tier") == "Tier 1" else (2 if lead.get("tier") == "Tier 2" else 3),
                    notes=f"ICP Score: {lead.get('icp_score', 0)} ({lead.get('tier', 'N/A')})",
                )
                
                pdb.log_activity(
                    conn, deal_id, "lead_imported",
                    f"Weekly generation import - {lead.get('tier', 'N/A')} - Score {lead.get('icp_score', 0)}"
                )
                imported += 1
                
            except Exception as e:
                logger.error(f"Failed to import {lead.get('company')}: {e}")
        
        conn.commit()
        logger.info(f"Pipeline import: {imported} leads imported")
        
    except Exception as e:
        logger.error(f"Pipeline import failed: {e}")
    
    return imported


def export_to_csv(leads: List[Dict], output_path: Path) -> bool:
    """Export leads to dated CSV file."""
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        fieldnames = [
            "company", "contact_name", "contact_email", "contact_phone",
            "industry", "city", "state", "website", "employee_count",
            "lead_source", "icp_score", "tier", "discovered_at"
        ]
        
        with open(output_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(leads)
        
        logger.info(f"Exported {len(leads)} leads to {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"CSV export failed: {e}")
        return False


# =============================================================================
# STATE MANAGEMENT
# =============================================================================

def load_state() -> Dict:
    """Load generation state from disk."""
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "last_generation": None,
        "total_generated": 0,
        "frequency_days": 7,
        "runs": []
    }


def save_state(state: Dict):
    """Save generation state to disk."""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def should_run_generation() -> Tuple[bool, str]:
    """Check if it's time to run lead generation.
    
    Considers:
    - Last generation timestamp
    - Day of week (prefer Monday)
    - outcome_learner frequency preference
    
    Returns:
        (should_run: bool, reason: str)
    """
    state = load_state()
    last_gen = state.get("last_generation")
    freq_days = state.get("frequency_days", 7)
    
    # Load learned preferences for dynamic frequency
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "outcome_learner", 
            REPO_ROOT / "projects" / "personal-assistant" / "src" / "outcome_learner.py"
        )
        ol = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(ol)
        prefs = ol.load_preferences()
        
        # If we have good conversion data, consider more frequent generation
        if prefs.get("total_outcomes", 0) >= 10:
            best_rate = prefs.get("best_channel_rate", 0)
            if best_rate > 60:
                freq_days = 5  # More frequent if high conversion
            elif best_rate < 20:
                freq_days = 10  # Less frequent if low conversion
                
    except Exception:
        pass
    
    if not last_gen:
        return True, "First generation (no previous run)"
    
    try:
        last_dt = datetime.fromisoformat(last_gen)
        days_since = (datetime.now() - last_dt).days
        
        if days_since >= freq_days:
            return True, f"{days_since} days since last generation (threshold: {freq_days})"
        else:
            return False, f"Only {days_since} days since last generation (threshold: {freq_days})"
            
    except (ValueError, TypeError):
        return True, "Invalid last generation timestamp"


def save_digest(summary: Dict):
    """Save generation summary for morning digest integration."""
    DIGEST_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(DIGEST_FILE, "w") as f:
        json.dump(summary, f, indent=2)
    logger.info(f"Digest saved: {DIGEST_FILE}")


def get_digest_summary() -> str:
    """Get formatted summary for morning digest."""
    if not DIGEST_FILE.exists():
        return ""
    
    try:
        with open(DIGEST_FILE) as f:
            summary = json.load(f)
        
        lines = [
            f"📋 LEAD GENERATION ({summary.get('date', 'N/A')})",
            f"  Generated: {summary.get('total_generated', 0)} new leads",
            f"  Tier 1: {summary.get('tier_1', 0)} | Tier 2: {summary.get('tier_2', 0)} | Tier 3: {summary.get('tier_3', 0)}",
            f"  Duplicates removed: {summary.get('duplicates_removed', 0)}",
            f"  Imported to pipeline: {summary.get('imported', 0)}",
        ]
        
        return "\n".join(lines)
        
    except Exception:
        return ""


# =============================================================================
# MAIN GENERATION FUNCTION
# =============================================================================

def generate_lead_list(
    limit: int = 100,
    dry_run: bool = False,
    force: bool = False
) -> Dict[str, Any]:
    """Generate a fresh, ICP-scored lead list.
    
    Args:
        limit: Maximum leads to generate
        dry_run: Preview only, don't import
        force: Run even if not scheduled
        
    Returns:
        Summary dict with generation statistics
    """
    logger.info(f"\n{'='*60}")
    logger.info(f"WEEKLY LEAD LIST GENERATION")
    logger.info(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    logger.info(f"Limit: {limit} leads")
    logger.info(f"{'='*60}\n")
    
    # Check if we should run
    if not force:
        should_run, reason = should_run_generation()
        if not should_run:
            logger.info(f"Generation skipped: {reason}")
            return {"status": "skipped", "reason": reason}
        logger.info(f"Running generation: {reason}")
    
    summary = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "timestamp": datetime.now().isoformat(),
        "dry_run": dry_run,
        "status": "running",
    }
    
    # Load learned preferences
    preferences = {}
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "outcome_learner",
            REPO_ROOT / "projects" / "personal-assistant" / "src" / "outcome_learner.py"
        )
        ol = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(ol)
        preferences = ol.load_preferences()
        logger.info(f"Loaded preferences: {preferences.get('total_outcomes', 0)} outcomes learned")
    except Exception as e:
        logger.warning(f"Could not load preferences: {e}")
    
    # Get pipeline connection
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "pipeline_db", REPO_ROOT / "execution" / "pipeline_db.py"
        )
        pdb = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(pdb)
        conn = pdb.get_db()
    except Exception as e:
        logger.error(f"Failed to connect to pipeline.db: {e}")
        return {"status": "error", "error": str(e)}
    
    # Step 1: Discover leads from multiple sources
    logger.info("\n▶ Step 1: Discovery")
    all_leads = []
    
    # Priority: Apollo (best contact data)
    apollo_leads = discover_from_apollo(limit=limit // 2)
    all_leads.extend(apollo_leads)
    
    # Supplement with Google Places
    places_leads = discover_from_google_places(limit=limit // 3)
    all_leads.extend(places_leads)
    
    # Fill remainder with existing leads
    if len(all_leads) < limit:
        existing_leads = discover_from_existing_leads(limit=limit - len(all_leads))
        all_leads.extend(existing_leads)
    
    summary["raw_discovered"] = len(all_leads)
    logger.info(f"Total discovered: {len(all_leads)} leads")
    
    if not all_leads:
        logger.warning("No leads discovered — aborting")
        return {"status": "error", "error": "No leads discovered"}
    
    # Step 2: Deduplicate
    logger.info("\n▶ Step 2: Deduplication")
    unique_leads, dups_removed = deduplicate_leads(all_leads, conn)
    summary["duplicates_removed"] = dups_removed
    
    # Step 3: Score and tier
    logger.info("\n▶ Step 3: ICP Scoring")
    scored_leads = []
    tier_counts = {"Tier 1": 0, "Tier 2": 0, "Tier 3": 0, "Discard": 0}
    
    for lead in unique_leads:
        score, tier, breakdown = calculate_icp_score(lead)
        lead["icp_score"] = score
        lead["tier"] = tier
        lead["score_breakdown"] = breakdown
        tier_counts[tier] += 1
        
        if tier != "Discard":
            scored_leads.append(lead)
    
    logger.info(f"Scoring complete: {tier_counts}")
    summary["tier_1"] = tier_counts["Tier 1"]
    summary["tier_2"] = tier_counts["Tier 2"]
    summary["tier_3"] = tier_counts["Tier 3"]
    summary["discarded"] = tier_counts["Discard"]
    
    # Apply learned preferences
    if preferences:
        scored_leads = apply_learned_preferences(scored_leads, preferences)
    
    # Sort by score (highest first)
    scored_leads.sort(key=lambda x: x.get("icp_score", 0), reverse=True)
    
    # Cap at limit
    scored_leads = scored_leads[:limit]
    summary["total_generated"] = len(scored_leads)
    
    # Step 4: Enrich
    logger.info("\n▶ Step 4: Enrichment")
    enriched_leads = enrich_leads(scored_leads, dry_run=dry_run)
    summary["enriched"] = sum(1 for l in enriched_leads if l.get("enriched"))
    
    # Step 5: Export to CSV
    logger.info("\n▶ Step 5: CSV Export")
    csv_path = OUTPUT_DIR / f"leads_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
    export_to_csv(enriched_leads, csv_path)
    summary["csv_path"] = str(csv_path)
    
    # Step 6: Import to pipeline
    logger.info("\n▶ Step 6: Pipeline Import")
    imported = import_to_pipeline(enriched_leads, conn, dry_run=dry_run)
    summary["imported"] = imported
    
    conn.close()
    
    # Update state
    if not dry_run:
        state = load_state()
        state["last_generation"] = datetime.now().isoformat()
        state["total_generated"] = state.get("total_generated", 0) + len(enriched_leads)
        state["runs"].append({
            "date": summary["date"],
            "generated": len(enriched_leads),
            "imported": imported,
        })
        # Keep last 30 runs
        state["runs"] = state["runs"][-30:]
        save_state(state)
    
    # Save digest for morning summary
    summary["status"] = "completed"
    save_digest(summary)
    
    # Log completion
    logger.info(f"\n{'='*60}")
    logger.info("GENERATION COMPLETE")
    logger.info(f"  Generated: {len(enriched_leads)} leads")
    logger.info(f"  Tier 1: {tier_counts['Tier 1']} | Tier 2: {tier_counts['Tier 2']} | Tier 3: {tier_counts['Tier 3']}")
    logger.info(f"  Imported to pipeline: {imported}")
    logger.info(f"  CSV: {csv_path}")
    logger.info(f"{'='*60}\n")
    
    return summary


def show_status():
    """Show status of lead generation system."""
    state = load_state()
    should_run, reason = should_run_generation()
    
    print("\n📊 Lead Generation Status\n")
    print(f"Last generation: {state.get('last_generation', 'Never')}")
    print(f"Total generated: {state.get('total_generated', 0)}")
    print(f"Frequency: Every {state.get('frequency_days', 7)} days")
    print(f"Should run now: {'Yes' if should_run else 'No'} — {reason}")
    
    if state.get("runs"):
        print("\nRecent runs:")
        for run in state["runs"][-5:]:
            print(f"  {run['date']}: {run['generated']} generated, {run['imported']} imported")
    
    # Check digest
    digest = get_digest_summary()
    if digest:
        print(f"\nLast digest:\n{digest}")


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="Weekly Lead List Generation")
    sub = parser.add_subparsers(dest="command")
    
    gen = sub.add_parser("generate", help="Generate new lead list")
    gen.add_argument("--limit", type=int, default=100, help="Max leads to generate")
    gen.add_argument("--dry-run", action="store_true", help="Preview only")
    gen.add_argument("--force", action="store_true", help="Run even if not scheduled")
    
    sub.add_parser("status", help="Show generation status")
    sub.add_parser("should-run", help="Check if generation should run")
    sub.add_parser("digest", help="Show digest summary")
    
    args = parser.parse_args()
    
    if args.command == "generate":
        result = generate_lead_list(
            limit=args.limit,
            dry_run=args.dry_run,
            force=args.force
        )
        print(json.dumps(result, indent=2))
        
    elif args.command == "status":
        show_status()
        
    elif args.command == "should-run":
        should_run, reason = should_run_generation()
        print(f"Should run: {should_run}")
        print(f"Reason: {reason}")
        
    elif args.command == "digest":
        digest = get_digest_summary()
        print(digest if digest else "No digest available")
        
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
