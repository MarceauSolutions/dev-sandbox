#!/usr/bin/env python3
"""
Feedback Loop — Extracts learnings from Ralph runs and feeds them back.

After each Ralph run:
1. Parse progress.txt for patterns and gotchas
2. Extract Codebase Patterns section
3. Analyze what went well vs what needed retries
4. Update knowledge_base.json for future runs
5. Generate optimization suggestions for Clawdbot

This creates a continuous improvement cycle:
Ralph runs → learnings extracted → future PRDs improved → better Ralph output
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

RALPH_DIR = Path("/home/clawdbot/dev-sandbox/ralph")
PROGRESS_FILE = RALPH_DIR / "progress.txt"
KNOWLEDGE_BASE = RALPH_DIR / "pipeline" / "knowledge_base.json"


def load_knowledge_base() -> Dict:
    """Load or initialize the knowledge base."""
    if KNOWLEDGE_BASE.exists():
        with open(KNOWLEDGE_BASE) as f:
            return json.load(f)
    return {
        "patterns": [],
        "gotchas": [],
        "conventions": [],
        "run_history": [],
        "optimization_notes": [],
        "last_updated": None,
    }


def save_knowledge_base(kb: Dict):
    """Save the knowledge base."""
    kb["last_updated"] = datetime.utcnow().isoformat()
    KNOWLEDGE_BASE.parent.mkdir(parents=True, exist_ok=True)
    with open(KNOWLEDGE_BASE, "w") as f:
        json.dump(kb, f, indent=2)


def extract_codebase_patterns(progress_text: str) -> List[str]:
    """Extract the Codebase Patterns section from progress.txt."""
    patterns = []
    in_patterns_section = False
    
    for line in progress_text.split("\n"):
        if line.strip().startswith("## Codebase Patterns"):
            in_patterns_section = True
            continue
        if in_patterns_section:
            if line.startswith("## ") or line.startswith("---"):
                break
            if line.strip().startswith("- "):
                patterns.append(line.strip()[2:])
    
    return patterns


def extract_learnings(progress_text: str) -> Dict[str, List[str]]:
    """Extract learnings from iteration entries in progress.txt."""
    learnings = {"patterns": [], "gotchas": [], "discoveries": []}
    
    in_learnings = False
    
    for line in progress_text.split("\n"):
        stripped = line.strip()
        
        if "**Learnings" in stripped or "learnings for future" in stripped.lower():
            in_learnings = True
            continue
        
        if in_learnings:
            if stripped.startswith("---") or (stripped.startswith("## ") and "Learnings" not in stripped):
                in_learnings = False
                continue
            
            if stripped.startswith("- "):
                learning = stripped[2:]
                
                # Classify the learning
                if any(kw in learning.lower() for kw in ["gotcha", "don't forget", "careful", "watch out", "bug", "error"]):
                    learnings["gotchas"].append(learning)
                elif any(kw in learning.lower() for kw in ["pattern", "uses", "convention", "always", "standard"]):
                    learnings["patterns"].append(learning)
                else:
                    learnings["discoveries"].append(learning)
    
    return learnings


def analyze_iteration_efficiency(progress_text: str) -> Dict:
    """Analyze how efficient Ralph's iterations were."""
    iterations = progress_text.count("## 20")  # Rough count of iteration headers
    stories_completed = progress_text.count("passes: true") + progress_text.count("✅") + progress_text.count("COMPLETE")
    retries = progress_text.lower().count("retry") + progress_text.lower().count("re-attempt") + progress_text.lower().count("fixing")
    
    return {
        "estimated_iterations": iterations,
        "estimated_completions": stories_completed,
        "estimated_retries": retries,
        "efficiency": f"{stories_completed}/{iterations}" if iterations > 0 else "N/A",
    }


def extract_file_change_patterns(progress_text: str) -> List[str]:
    """Extract which files were commonly changed together."""
    files_mentioned = re.findall(r'[`"]([a-zA-Z0-9_/.-]+\.[a-zA-Z]+)[`"]', progress_text)
    
    # Count file mentions
    file_counts = {}
    for f in files_mentioned:
        file_counts[f] = file_counts.get(f, 0) + 1
    
    # Files changed more than once suggest coupling
    hot_files = [f"{f} ({count}x)" for f, count in sorted(file_counts.items(), key=lambda x: -x[1]) if count > 1]
    
    return hot_files[:10]  # Top 10


def generate_optimization_suggestions(kb: Dict, run_analysis: Dict) -> List[str]:
    """Generate suggestions for improving future runs based on accumulated data."""
    suggestions = []
    
    # Check for repeated gotchas
    gotcha_counts = {}
    for gotcha in kb.get("gotchas", []):
        key = gotcha[:50].lower()
        gotcha_counts[key] = gotcha_counts.get(key, 0) + 1
    
    repeated = [k for k, v in gotcha_counts.items() if v > 1]
    if repeated:
        suggestions.append(f"Recurring gotchas detected ({len(repeated)}x) — consider adding to PRD template")
    
    # Check iteration efficiency
    retries = run_analysis.get("estimated_retries", 0)
    if retries > 2:
        suggestions.append(f"High retry count ({retries}) — PRD acceptance criteria may need clarification")
    
    # Check knowledge base size
    total_learnings = len(kb.get("patterns", [])) + len(kb.get("gotchas", []))
    if total_learnings > 50:
        suggestions.append("Knowledge base growing large — consider pruning stale entries")
    
    return suggestions


def run_feedback_loop(
    prd_path: Optional[str] = None,
    progress_path: Optional[str] = None,
) -> Dict:
    """
    Run the full feedback loop after a Ralph completion.
    
    Returns a summary of extracted learnings and suggestions.
    """
    progress_file = Path(progress_path) if progress_path else PROGRESS_FILE
    
    if not progress_file.exists():
        return {"status": "no_progress_file", "learnings": {}}
    
    progress_text = progress_file.read_text()
    
    # Load knowledge base
    kb = load_knowledge_base()
    
    # Extract learnings
    codebase_patterns = extract_codebase_patterns(progress_text)
    learnings = extract_learnings(progress_text)
    efficiency = analyze_iteration_efficiency(progress_text)
    hot_files = extract_file_change_patterns(progress_text)
    
    # Update knowledge base (deduplicate)
    existing_patterns = set(kb["patterns"])
    for pattern in codebase_patterns + learnings["patterns"]:
        if pattern not in existing_patterns:
            kb["patterns"].append(pattern)
            existing_patterns.add(pattern)
    
    existing_gotchas = set(kb["gotchas"])
    for gotcha in learnings["gotchas"]:
        if gotcha not in existing_gotchas:
            kb["gotchas"].append(gotcha)
            existing_gotchas.add(gotcha)
    
    # Add run to history
    run_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "efficiency": efficiency,
        "new_patterns": len(codebase_patterns) + len(learnings["patterns"]),
        "new_gotchas": len(learnings["gotchas"]),
        "hot_files": hot_files[:5],
    }
    if prd_path:
        try:
            with open(prd_path) as f:
                prd = json.load(f)
            run_entry["project"] = prd.get("projectName", "Unknown")
        except Exception:
            pass
    
    kb["run_history"].append(run_entry)
    
    # Keep history manageable
    if len(kb["run_history"]) > 50:
        kb["run_history"] = kb["run_history"][-50:]
    if len(kb["patterns"]) > 100:
        kb["patterns"] = kb["patterns"][-100:]
    if len(kb["gotchas"]) > 50:
        kb["gotchas"] = kb["gotchas"][-50:]
    
    # Generate optimization suggestions
    suggestions = generate_optimization_suggestions(kb, efficiency)
    kb["optimization_notes"] = suggestions
    
    # Save
    save_knowledge_base(kb)
    
    return {
        "status": "success",
        "new_patterns": len(codebase_patterns) + len(learnings["patterns"]),
        "new_gotchas": len(learnings["gotchas"]),
        "efficiency": efficiency,
        "hot_files": hot_files,
        "suggestions": suggestions,
        "knowledge_base_size": {
            "patterns": len(kb["patterns"]),
            "gotchas": len(kb["gotchas"]),
            "runs": len(kb["run_history"]),
        },
    }


if __name__ == "__main__":
    import sys
    prd = sys.argv[1] if len(sys.argv) > 1 else None
    
    result = run_feedback_loop(prd_path=prd)
    print(json.dumps(result, indent=2))
