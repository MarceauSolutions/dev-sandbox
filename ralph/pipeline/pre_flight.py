#!/usr/bin/env python3
"""
PRD Quality Gate — Validates PRD quality before triggering Ralph.

Quality checks:
1. Every story has specific, testable acceptance criteria
2. Stories have clear dependency ordering
3. Architecture/tech stack is documented
4. Coding standards are specified
5. Total scope is reasonable (not too many stories per run)

Returns a quality score (0-100) and blocks execution below threshold.
"""

import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

QUALITY_THRESHOLD = 70  # Minimum score to proceed


def validate_prd(prd_path: str) -> Tuple[int, List[str], List[str]]:
    """
    Validate PRD quality.
    
    Returns:
        (score, issues, suggestions) — score 0-100, list of blocking issues, list of suggestions
    """
    with open(prd_path) as f:
        prd = json.load(f)
    
    score = 100
    issues = []
    suggestions = []
    
    # --- Required Fields ---
    required_fields = ["projectName", "branchName", "description", "stories"]
    for field in required_fields:
        if field not in prd or not prd[field]:
            issues.append(f"Missing required field: {field}")
            score -= 15
    
    # --- Story Quality ---
    stories = prd.get("stories", [])
    
    if not stories:
        issues.append("PRD has no stories")
        return 0, issues, suggestions
    
    if len(stories) > 15:
        suggestions.append(f"PRD has {len(stories)} stories — consider splitting into phases (optimal: 5-10)")
        score -= 5
    
    for story in stories:
        story_id = story.get("id", "unknown")
        
        # Check for acceptance criteria
        criteria = story.get("acceptanceCriteria", [])
        if not criteria:
            issues.append(f"{story_id}: No acceptance criteria defined")
            score -= 10
        elif len(criteria) < 2:
            suggestions.append(f"{story_id}: Only {len(criteria)} acceptance criterion — consider adding more specificity")
            score -= 3
        
        # Check criteria quality — flag vague criteria
        vague_words = ["should work", "looks good", "properly", "correctly", "appropriate", "reasonable"]
        for criterion in criteria:
            for vague in vague_words:
                if vague in criterion.lower():
                    suggestions.append(f"{story_id}: Vague criterion detected ('{vague}') — make testable: '{criterion[:60]}...'")
                    score -= 2
                    break
        
        # Check for description
        if not story.get("description") or len(story.get("description", "")) < 20:
            suggestions.append(f"{story_id}: Story description is too brief — Ralph needs context")
            score -= 3
        
        # Check for title
        if not story.get("title"):
            issues.append(f"{story_id}: Missing title")
            score -= 5
    
    # --- Architecture Context ---
    has_architecture = any(key in prd for key in ["architecture", "techStack", "tech_stack", "codingStandards"])
    if not has_architecture:
        suggestions.append("PRD lacks architecture/techStack field — Ralph will make assumptions")
        score -= 10
    
    # --- Dependency Ordering ---
    has_dependencies = any("dependencies" in story or "dependsOn" in story for story in stories)
    if len(stories) > 3 and not has_dependencies:
        suggestions.append("Stories have no dependency ordering — Ralph may build in wrong order")
        score -= 5
    
    # --- Quality Standards ---
    has_quality = any(key in prd for key in ["qualityChecks", "quality_checks", "testingStrategy"])
    if not has_quality:
        suggestions.append("PRD lacks qualityChecks field — Ralph won't know what checks to run")
        score -= 5
    
    # Clamp score
    score = max(0, min(100, score))
    
    return score, issues, suggestions


def enhance_prd(prd_path: str) -> Dict:
    """
    Auto-enhance a PRD by adding missing quality fields with sensible defaults.
    Returns the enhanced PRD dict.
    """
    with open(prd_path) as f:
        prd = json.load(f)
    
    enhanced = False
    
    # Add tech stack if missing
    if "techStack" not in prd:
        prd["techStack"] = {
            "note": "AUTO-ADDED: Please specify your tech stack",
            "language": "",
            "framework": "",
            "database": "",
            "testing": ""
        }
        enhanced = True
    
    # Add quality checks if missing
    if "qualityChecks" not in prd:
        prd["qualityChecks"] = [
            "syntax_check",
            "lint",
            "type_check",
            "unit_tests"
        ]
        enhanced = True
    
    # Add coding standards if missing
    if "codingStandards" not in prd:
        prd["codingStandards"] = {
            "note": "AUTO-ADDED: Please specify coding standards",
            "style": "Follow existing codebase conventions",
            "documentation": "Docstrings on all public functions",
            "errorHandling": "Graceful error handling with logging",
            "testing": "Unit tests for business logic"
        }
        enhanced = True
    
    # Ensure all stories have acceptance criteria
    for story in prd.get("stories", []):
        if not story.get("acceptanceCriteria"):
            story["acceptanceCriteria"] = [
                f"AUTO-ADDED: Define specific, testable criteria for '{story.get('title', 'this story')}'"
            ]
            enhanced = True
    
    if enhanced:
        # Save enhanced version (backup original first)
        backup_path = prd_path + ".backup"
        with open(prd_path) as f:
            original = f.read()
        with open(backup_path, "w") as f:
            f.write(original)
        
        with open(prd_path, "w") as f:
            json.dump(prd, f, indent=2)
    
    return prd


def run_preflight(prd_path: str, auto_enhance: bool = True) -> bool:
    """
    Run pre-flight checks. Returns True if Ralph should proceed.
    """
    print(f"🔍 Pre-flight check: {prd_path}")
    print("=" * 60)
    
    score, issues, suggestions = validate_prd(prd_path)
    
    # Report
    print(f"\n📊 Quality Score: {score}/100 (threshold: {QUALITY_THRESHOLD})")
    
    if issues:
        print(f"\n❌ Blocking Issues ({len(issues)}):")
        for issue in issues:
            print(f"  • {issue}")
    
    if suggestions:
        print(f"\n⚠️ Suggestions ({len(suggestions)}):")
        for suggestion in suggestions:
            print(f"  • {suggestion}")
    
    if score < QUALITY_THRESHOLD:
        print(f"\n🚫 PRD quality too low ({score} < {QUALITY_THRESHOLD})")
        
        if auto_enhance:
            print("\n🔧 Auto-enhancing PRD...")
            enhance_prd(prd_path)
            
            # Re-validate
            new_score, new_issues, _ = validate_prd(prd_path)
            print(f"📊 Enhanced score: {new_score}/100")
            
            if new_score >= QUALITY_THRESHOLD:
                print("✅ PRD enhanced to acceptable quality")
                return True
            else:
                print("❌ Still below threshold — manual review needed")
                return False
        return False
    
    print("\n✅ PRD passes pre-flight checks")
    return True


if __name__ == "__main__":
    prd_file = sys.argv[1] if len(sys.argv) > 1 else "/home/clawdbot/dev-sandbox/ralph/prd.json"
    success = run_preflight(prd_file)
    sys.exit(0 if success else 1)
