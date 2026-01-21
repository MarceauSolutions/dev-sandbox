"""
Iterative search refinement to improve lead quality.

Filters out unwanted titles (sales reps, assistants, etc.) and refines searches
to find decision makers.
"""

from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


def filter_people_by_excluded_titles(
    people: List[Dict[str, Any]],
    excluded_titles: List[str]
) -> List[Dict[str, Any]]:
    """
    Filter out people with unwanted job titles.

    Args:
        people: List of people from Apollo search
        excluded_titles: List of title keywords to exclude (case-insensitive)

    Returns:
        Filtered list of people
    """
    filtered = []

    for person in people:
        title = person.get("title", "").lower()

        # Check if any excluded term appears in title
        is_excluded = False
        for excluded in excluded_titles:
            if excluded.lower() in title:
                is_excluded = True
                logger.debug(f"Excluding: {person.get('name')} - {title}")
                break

        if not is_excluded:
            filtered.append(person)

    return filtered


def score_lead_quality(person: Dict[str, Any]) -> float:
    """
    Score a lead based on title, company info, and contact availability.

    Args:
        person: Person data from Apollo

    Returns:
        Quality score (0.0 - 1.0)
    """
    score = 0.0

    # Title scoring (40 points)
    title = person.get("title", "").lower()
    if any(keyword in title for keyword in ["owner", "ceo", "founder", "president"]):
        score += 0.4
    elif any(keyword in title for keyword in ["director", "vp", "vice president", "manager"]):
        score += 0.3
    elif "head of" in title or "chief" in title:
        score += 0.35
    else:
        score += 0.1

    # Contact info availability (30 points)
    has_email = bool(person.get("email"))
    has_phone = bool(person.get("phone_numbers"))

    if has_email and has_phone:
        score += 0.3
    elif has_email or has_phone:
        score += 0.15

    # Company info (20 points)
    org = person.get("organization") or {}
    has_website = bool(org.get("website_url"))
    has_industry = bool(org.get("industry"))

    if has_website:
        score += 0.1
    if has_industry:
        score += 0.1

    # LinkedIn presence (10 points)
    has_linkedin = bool(person.get("linkedin_url"))
    if has_linkedin:
        score += 0.1

    return min(score, 1.0)


def validate_search_results(
    people: List[Dict[str, Any]],
    excluded_titles: List[str],
    min_quality_score: float = 0.5
) -> Dict[str, Any]:
    """
    Validate search results and determine if refinement is needed.

    Args:
        people: List of people from search
        excluded_titles: Titles to exclude
        min_quality_score: Minimum acceptable quality score

    Returns:
        Dict with validation results and recommendations
    """
    if not people:
        return {
            "valid": False,
            "reason": "No results found",
            "needs_refinement": True,
            "recommendation": "Try broader search criteria"
        }

    # Filter by excluded titles
    filtered = filter_people_by_excluded_titles(people, excluded_titles)

    # Score each lead
    scored_leads = []
    for person in filtered:
        quality_score = score_lead_quality(person)
        scored_leads.append({
            "person": person,
            "quality_score": quality_score
        })

    # Sort by quality
    scored_leads.sort(key=lambda x: x["quality_score"], reverse=True)

    # Calculate metrics
    total_count = len(people)
    filtered_count = len(filtered)
    high_quality_count = sum(1 for lead in scored_leads if lead["quality_score"] >= min_quality_score)

    exclusion_rate = (total_count - filtered_count) / total_count if total_count > 0 else 0
    quality_rate = high_quality_count / filtered_count if filtered_count > 0 else 0

    # Determine if refinement is needed
    needs_refinement = False
    reason = "Results look good"

    if exclusion_rate > 0.5:
        needs_refinement = True
        reason = f"High exclusion rate: {exclusion_rate:.0%} of results filtered out"
    elif quality_rate < 0.3:
        needs_refinement = True
        reason = f"Low quality rate: only {quality_rate:.0%} meet quality threshold"

    return {
        "valid": not needs_refinement,
        "reason": reason,
        "needs_refinement": needs_refinement,
        "metrics": {
            "total_results": total_count,
            "after_filtering": filtered_count,
            "high_quality": high_quality_count,
            "exclusion_rate": exclusion_rate,
            "quality_rate": quality_rate
        },
        "scored_leads": scored_leads,
        "recommendation": _get_refinement_recommendation(exclusion_rate, quality_rate)
    }


def _get_refinement_recommendation(exclusion_rate: float, quality_rate: float) -> str:
    """Generate recommendation for search refinement."""
    if exclusion_rate > 0.7:
        return "Too many unwanted titles - strengthen title filters"
    elif exclusion_rate > 0.5:
        return "Moderate exclusion rate - consider adding more specific titles"
    elif quality_rate < 0.2:
        return "Very low quality - try different search criteria or location"
    elif quality_rate < 0.3:
        return "Low quality - consider narrowing to decision-maker titles only"
    else:
        return "Results acceptable - proceed with enrichment"


def refine_search_params(
    original_params: Dict[str, Any],
    validation_result: Dict[str, Any],
    iteration: int
) -> Optional[Dict[str, Any]]:
    """
    Refine search parameters based on validation results.

    Args:
        original_params: Original search parameters
        validation_result: Results from validate_search_results()
        iteration: Current iteration number (1-based)

    Returns:
        Refined parameters or None if max iterations reached
    """
    if iteration >= 3:
        logger.warning("Max refinement iterations reached")
        return None

    refined = original_params.copy()

    exclusion_rate = validation_result["metrics"]["exclusion_rate"]
    quality_rate = validation_result["metrics"]["quality_rate"]

    # Iteration 1: Strengthen title filters
    if iteration == 1 and exclusion_rate > 0.5:
        # Use only top decision-maker titles
        refined["person_titles"] = ["Owner", "CEO", "Founder", "President"]
        logger.info("Refinement iteration 1: Using top decision-maker titles only")

    # Iteration 2: Further narrow to owners/founders
    elif iteration == 2 and (exclusion_rate > 0.5 or quality_rate < 0.3):
        refined["person_titles"] = ["Owner", "Founder"]
        logger.info("Refinement iteration 2: Narrowing to owners and founders only")

    # Iteration 3 would be handled by returning None above

    return refined


def select_top_leads_for_enrichment(
    scored_leads: List[Dict[str, Any]],
    top_percent: float = 0.2,
    min_leads: int = 10,
    max_leads: int = 50
) -> List[Dict[str, Any]]:
    """
    Select top-quality leads for enrichment.

    Args:
        scored_leads: List of scored lead dicts (from validate_search_results)
        top_percent: Top percentage to select (default 20%)
        min_leads: Minimum number of leads to return
        max_leads: Maximum number of leads to return

    Returns:
        List of people (not scored dicts, just the person data)
    """
    if not scored_leads:
        return []

    # Calculate how many to select
    count = max(
        min_leads,
        min(
            max_leads,
            int(len(scored_leads) * top_percent)
        )
    )

    # Return top N
    top_scored = scored_leads[:count]
    return [lead["person"] for lead in top_scored]
