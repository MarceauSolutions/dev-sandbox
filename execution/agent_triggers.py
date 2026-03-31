#!/usr/bin/env python3
"""
Agent Consultation Triggers — Automatic multi-agent consultation for key decisions.

Integrates multi_agent_llm.py across all towers by defining:
1. When to automatically consult another agent
2. Which agents to consult for which decision types
3. How to integrate consultation into existing workflows

Trigger Categories:
  STRATEGIC  — Business direction, pricing, market focus
  TECHNICAL  — Architecture, tool selection, implementation approach
  CREATIVE   — Content, messaging, campaign ideas
  RISK       — Potential issues, edge cases, safety checks

Usage:
    from execution.agent_triggers import should_consult, auto_consult
    
    # Check if consultation needed
    if should_consult(decision_type="pricing", value_at_stake=5000):
        result = auto_consult("What price should we charge for X?", decision_type="pricing")
    
    # Or use decorator
    @consult_before_action("strategic")
    def change_pricing_strategy(new_price):
        ...
"""

import functools
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

REPO_ROOT = Path(__file__).parent.parent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("agent_triggers")


# =============================================================================
# TRIGGER RULES
# =============================================================================

CONSULTATION_TRIGGERS = {
    # Strategic decisions - always consult Grok
    "strategic": {
        "consult_agents": ["grok"],
        "primary_agent": "claude",
        "thresholds": {
            "always": True,  # Always consult for strategic
        },
        "examples": [
            "pricing changes",
            "new market entry",
            "pivot decisions",
            "client acquisition strategy",
            "resource allocation"
        ]
    },
    
    # Technical decisions - consult Claude and optionally GPT-4
    "technical": {
        "consult_agents": ["grok"],
        "primary_agent": "claude",
        "thresholds": {
            "lines_of_code": 500,  # If change > 500 lines
            "files_affected": 5,   # If > 5 files changed
            "new_dependency": True,  # If adding new dependency
        },
        "examples": [
            "architecture decisions",
            "framework selection",
            "database schema changes",
            "API design"
        ]
    },
    
    # Creative decisions - brainstorm with multiple
    "creative": {
        "consult_agents": ["grok", "gpt4"],
        "primary_agent": "claude",
        "thresholds": {
            "audience_size": 100,  # If reaching > 100 people
        },
        "examples": [
            "email copy",
            "ad campaigns",
            "content strategy",
            "brand messaging"
        ]
    },
    
    # Risk decisions - validate with multiple
    "risk": {
        "consult_agents": ["grok", "claude"],
        "primary_agent": "claude",
        "thresholds": {
            "money_involved": 1000,  # If > $1000 at stake
            "data_affected": 100,    # If > 100 records affected
            "irreversible": True,    # If action can't be undone
        },
        "examples": [
            "data migrations",
            "production deployments",
            "client communications",
            "contract decisions"
        ]
    },
    
    # Outreach decisions
    "outreach": {
        "consult_agents": ["grok"],
        "primary_agent": "claude",
        "thresholds": {
            "lead_count": 20,  # If outreach to > 20 leads
            "new_template": True,  # If using new template
        },
        "examples": [
            "email sequence changes",
            "SMS campaigns",
            "call scripts"
        ]
    }
}


# Tower-specific triggers
TOWER_TRIGGERS = {
    "lead-generation": {
        "triggers": ["strategic", "outreach", "risk"],
        "auto_consult_on": [
            "new_campaign_launch",
            "pricing_change",
            "template_change",
            "batch_outreach_50+"
        ]
    },
    "ai-systems": {
        "triggers": ["technical", "risk"],
        "auto_consult_on": [
            "schema_change",
            "new_integration",
            "production_deploy"
        ]
    },
    "fitness-influencer": {
        "triggers": ["creative", "outreach"],
        "auto_consult_on": [
            "content_strategy",
            "influencer_outreach"
        ]
    },
    "personal-assistant": {
        "triggers": ["strategic", "risk"],
        "auto_consult_on": [
            "workflow_change",
            "automation_setup"
        ]
    }
}


# =============================================================================
# CONSULTATION LOGIC
# =============================================================================

def should_consult(
    decision_type: str,
    value_at_stake: int = 0,
    lines_changed: int = 0,
    records_affected: int = 0,
    is_irreversible: bool = False,
    force: bool = False
) -> bool:
    """
    Determine if we should consult another agent before proceeding.
    
    Returns True if consultation is recommended.
    """
    if force:
        return True
    
    trigger = CONSULTATION_TRIGGERS.get(decision_type)
    if not trigger:
        return False
    
    thresholds = trigger.get("thresholds", {})
    
    # Check each threshold
    if thresholds.get("always"):
        return True
    
    if value_at_stake > 0 and thresholds.get("money_involved", float('inf')) <= value_at_stake:
        return True
    
    if lines_changed > 0 and thresholds.get("lines_of_code", float('inf')) <= lines_changed:
        return True
    
    if records_affected > 0 and thresholds.get("data_affected", float('inf')) <= records_affected:
        return True
    
    if is_irreversible and thresholds.get("irreversible"):
        return True
    
    return False


def auto_consult(
    question: str,
    decision_type: str = "strategic",
    context: Dict = None,
    tower: str = None
) -> Dict[str, Any]:
    """
    Automatically consult the appropriate agents for a decision.
    
    Returns consultation result with conclusion.
    """
    from execution.multi_agent_llm import AgentCouncil, ConsultationType
    
    trigger = CONSULTATION_TRIGGERS.get(decision_type, CONSULTATION_TRIGGERS["strategic"])
    
    # Map decision type to consultation type
    type_mapping = {
        "strategic": ConsultationType.STRATEGIC,
        "technical": ConsultationType.TECHNICAL,
        "creative": ConsultationType.CREATIVE,
        "risk": ConsultationType.VALIDATION,
        "outreach": ConsultationType.STRATEGIC
    }
    
    consultation_type = type_mapping.get(decision_type, ConsultationType.STRATEGIC)
    
    # Add tower context
    full_context = context or {}
    if tower:
        full_context["tower"] = tower
    
    council = AgentCouncil()
    
    # Use first consult agent
    consult_agent = trigger["consult_agents"][0]
    primary_agent = trigger["primary_agent"]
    
    logger.info(f"Auto-consulting {consult_agent} on: {question[:50]}...")
    
    result = council.consult(
        question=question,
        primary_agent=primary_agent,
        consult_agent=consult_agent,
        context=full_context,
        consultation_type=consultation_type
    )
    
    # Log for tracking
    _log_auto_consultation(decision_type, question, result)
    
    return result


def _log_auto_consultation(decision_type: str, question: str, result: Dict):
    """Log auto-consultation for tracking."""
    log_file = REPO_ROOT / "data" / "auto_consultations.jsonl"
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    entry = {
        "timestamp": datetime.now().isoformat(),
        "decision_type": decision_type,
        "question": question[:200],
        "agents_used": result.get("agents_used", []),
        "conclusion": result.get("conclusion", "")[:500],
        "tokens": result.get("total_tokens", 0)
    }
    
    with open(log_file, "a") as f:
        f.write(json.dumps(entry) + "\n")


# =============================================================================
# DECORATOR FOR AUTOMATIC CONSULTATION
# =============================================================================

def consult_before_action(
    decision_type: str,
    question_template: str = None,
    force: bool = False
):
    """
    Decorator that triggers agent consultation before executing a function.
    
    Usage:
        @consult_before_action("strategic", "Should we proceed with {action}?")
        def launch_campaign(campaign_name):
            ...
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Build question
            if question_template:
                question = question_template.format(**kwargs, args=args)
            else:
                question = f"Should we proceed with {func.__name__}?"
            
            # Check if consultation needed
            if should_consult(decision_type, force=force):
                result = auto_consult(question, decision_type)
                
                # Log the consultation
                logger.info(f"Consultation before {func.__name__}: {result['conclusion'][:100]}...")
                
                # Could add logic here to abort based on consultation
                # For now, just log and proceed
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


# =============================================================================
# TOWER INTEGRATION HELPERS
# =============================================================================

def get_tower_triggers(tower: str) -> Dict:
    """Get trigger configuration for a specific tower."""
    return TOWER_TRIGGERS.get(tower, {
        "triggers": ["strategic"],
        "auto_consult_on": []
    })


def check_tower_trigger(tower: str, action: str) -> bool:
    """Check if an action in a tower should trigger consultation."""
    tower_config = get_tower_triggers(tower)
    return action in tower_config.get("auto_consult_on", [])


# =============================================================================
# QUICK HELPERS FOR TOWER CODE
# =============================================================================

def consult_grok(question: str, context: Dict = None) -> str:
    """Quick helper to consult Grok on a question."""
    result = auto_consult(question, "strategic", context)
    return result.get("conclusion", "")


def consult_on_pricing(
    service: str,
    options: List[str],
    market: str = "Naples FL",
    context: Dict = None
) -> str:
    """Consult multiple agents on pricing decision."""
    from execution.multi_agent_llm import AgentCouncil
    
    council = AgentCouncil()
    result = council.decide(
        question=f"What's the best pricing for {service} in {market}?",
        options=options,
        context=context or {}
    )
    return result.get("decision", "")


def consult_on_outreach(
    target: str,
    channels: List[str] = None,
    context: Dict = None
) -> str:
    """Consult on best outreach approach."""
    channels = channels or ["email", "phone", "SMS", "in-person"]
    
    question = f"What's the best outreach approach for {target}? Options: {', '.join(channels)}"
    result = auto_consult(question, "outreach", context)
    return result.get("conclusion", "")


def review_before_send(content: str, content_type: str = "email") -> Dict:
    """Have Grok review content before sending."""
    from execution.multi_agent_llm import AgentCouncil
    
    council = AgentCouncil()
    result = council.review(
        work=content,
        work_type=content_type,
        reviewer_agent="grok"
    )
    return {
        "approved": result.get("approved", False),
        "feedback": result.get("feedback", "")
    }


# =============================================================================
# CLI
# =============================================================================

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Agent Consultation Triggers")
    subparsers = parser.add_subparsers(dest="command")
    
    # Check command
    check_p = subparsers.add_parser("check", help="Check if consultation needed")
    check_p.add_argument("--type", required=True, choices=list(CONSULTATION_TRIGGERS.keys()))
    check_p.add_argument("--value", type=int, default=0)
    check_p.add_argument("--lines", type=int, default=0)
    
    # Consult command
    consult_p = subparsers.add_parser("consult", help="Run auto consultation")
    consult_p.add_argument("question", help="Question to consult on")
    consult_p.add_argument("--type", default="strategic")
    consult_p.add_argument("--tower", help="Tower context")
    
    # Triggers command
    subparsers.add_parser("triggers", help="Show all triggers")
    
    args = parser.parse_args()
    
    if args.command == "check":
        needed = should_consult(
            args.type,
            value_at_stake=args.value,
            lines_changed=args.lines
        )
        print(f"Consultation needed: {'Yes' if needed else 'No'}")
    
    elif args.command == "consult":
        result = auto_consult(args.question, args.type, tower=args.tower)
        print(f"\n✅ Conclusion:\n{result['conclusion']}")
    
    elif args.command == "triggers":
        print("\n📋 Consultation Triggers:\n")
        for dtype, config in CONSULTATION_TRIGGERS.items():
            print(f"  {dtype.upper()}")
            print(f"    Consult: {', '.join(config['consult_agents'])}")
            print(f"    Examples: {', '.join(config['examples'][:3])}")
            print()


if __name__ == "__main__":
    main()
