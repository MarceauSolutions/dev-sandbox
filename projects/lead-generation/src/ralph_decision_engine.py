#!/usr/bin/env python3
"""
Ralph Decision Engine - Analyzes requests and determines when to use Ralph.

Usage:
    python -m src.ralph_decision_engine analyze "your request text"
    python -m src.ralph_decision_engine analyze "your request" --output decision.json
"""

import argparse
import json
import re
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime


class RalphDecisionEngine:
    """Intelligent decision engine for determining when to use Ralph."""

    def __init__(self):
        self.config_path = Path(__file__).parent.parent / "config" / "ralph_decision_rules.json"
        self.rules = self._load_rules()

    def _load_rules(self) -> Dict[str, Any]:
        """Load decision rules from config."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Decision rules not found: {self.config_path}")

        with open(self.config_path, 'r') as f:
            return json.load(f)

    def analyze_request(self, request_text: str) -> Dict[str, Any]:
        """
        Analyze a user request and determine if Ralph should be used.

        Args:
            request_text: The user's request

        Returns:
            Decision dictionary with recommendation
        """
        request_lower = request_text.lower()

        # Calculate scores
        use_ralph_score = self._calculate_use_ralph_score(request_lower)
        exclusion_score = self._calculate_exclusion_score(request_lower)
        final_score = max(0, use_ralph_score + exclusion_score)

        # Determine complexity
        complexity = self._determine_complexity(final_score)
        complexity_info = self.rules['decision_rules']['complexity_scoring'][complexity]

        # Estimate story count
        estimated_stories = self._estimate_story_count(request_text, complexity)

        # Determine agent type
        agent_type = self._determine_agent_type(request_lower)

        # Determine autonomous mode
        autonomous = self._should_use_autonomous(estimated_stories, request_lower)

        # Calculate checkpoints
        checkpoints = self._calculate_checkpoints(estimated_stories)

        # Make recommendation
        use_ralph = final_score >= 4.0 or estimated_stories >= 3

        # Build decision
        decision = {
            "timestamp": datetime.now().isoformat(),
            "request": request_text,
            "analysis": {
                "use_ralph_score": round(use_ralph_score, 2),
                "exclusion_score": round(exclusion_score, 2),
                "final_score": round(final_score, 2),
                "complexity": complexity,
                "estimated_stories": estimated_stories,
                "estimated_time": complexity_info["estimated_time"]
            },
            "recommendation": {
                "use_ralph": use_ralph,
                "agent_type": agent_type,
                "autonomous_mode": autonomous,
                "checkpoints": checkpoints
            },
            "reasoning": self._generate_reasoning(
                use_ralph,
                final_score,
                estimated_stories,
                complexity,
                request_lower
            ),
            "confidence": self._calculate_confidence(final_score, request_lower)
        }

        return decision

    def _calculate_use_ralph_score(self, request_lower: str) -> float:
        """Calculate score for using Ralph based on triggers."""
        score = 0.0
        triggers = self.rules['decision_rules']['use_ralph_triggers']

        for trigger in triggers:
            if trigger['trigger'] == 'file_count':
                # Count mentions of files/create/modify
                file_mentions = len(re.findall(r'\b(file|create|modify|add|update)\b', request_lower))
                if file_mentions >= trigger['threshold']:
                    score += trigger['weight'] * 10

            elif trigger['trigger'] == 'task_count':
                # Count numbered lists or "and" separators
                task_separators = request_lower.count(' and ') + request_lower.count(',')
                numbered = len(re.findall(r'\d+\)', request_lower))
                total_tasks = max(task_separators, numbered)
                if total_tasks >= trigger['threshold']:
                    score += trigger['weight'] * 10

            elif trigger['trigger'] == 'workflow_steps':
                # Count sequential indicators
                sequential = len(re.findall(r'\b(then|next|after|finally|first|second)\b', request_lower))
                if sequential >= trigger['threshold']:
                    score += trigger['weight'] * 10

            elif trigger['trigger'] == 'pattern_detection':
                # Check for pattern keywords
                for pattern in trigger['patterns']:
                    if pattern in request_lower:
                        score += trigger['weight'] * 10
                        break

            elif trigger['trigger'] == 'checkpoint_need':
                # Check for checkpoint indicators
                for indicator in trigger['indicators']:
                    if indicator in request_lower:
                        score += trigger['weight'] * 10
                        break

            elif trigger['trigger'] == 'explicit_request':
                # Check for explicit Ralph requests
                for phrase in trigger['phrases']:
                    if phrase in request_lower:
                        score += trigger['weight'] * 10
                        return 10.0  # Instant max score

        return min(score, 10.0)

    def _calculate_exclusion_score(self, request_lower: str) -> float:
        """Calculate negative score for exclusion triggers."""
        score = 0.0
        exclusions = self.rules['decision_rules']['dont_use_ralph_triggers']

        for exclusion in exclusions:
            for indicator in exclusion['indicators']:
                if indicator in request_lower:
                    score += exclusion['exclusion_score']
                    break

        return score

    def _determine_complexity(self, final_score: float) -> str:
        """Determine complexity level based on score."""
        scoring = self.rules['decision_rules']['complexity_scoring']

        for level, info in scoring.items():
            min_score, max_score = info['range']
            if min_score <= final_score <= max_score:
                return level

        # Default to very_complex if score > 10
        return 'very_complex'

    def _estimate_story_count(self, request_text: str, complexity: str) -> int:
        """Estimate number of stories needed."""
        complexity_info = self.rules['decision_rules']['complexity_scoring'][complexity]
        base_count = complexity_info['story_count']

        # If base_count is a string range like "2-3", take the upper bound
        if isinstance(base_count, str):
            if '-' in base_count:
                return int(base_count.split('-')[1])
            return int(base_count)

        return base_count

    def _determine_agent_type(self, request_lower: str) -> str:
        """Determine which type of Ralph agent to use."""
        agent_types = self.rules['decision_rules']['agent_type_selection']

        # Score each agent type
        scores = {}
        for agent_type, config in agent_types.items():
            score = sum(1 for keyword in config['keywords'] if keyword in request_lower)
            scores[agent_type] = score

        # Return highest scoring type, default to general
        if max(scores.values()) > 0:
            return max(scores, key=scores.get)
        return 'general'

    def _should_use_autonomous(self, estimated_stories: int, request_lower: str) -> bool:
        """Determine if autonomous mode should be used."""
        criteria = self.rules['decision_rules']['autonomous_mode_criteria']

        # Check for explicit checkpoint requests
        checkpoint_words = ['review', 'check', 'verify', 'validate']
        if any(word in request_lower for word in checkpoint_words):
            return False

        # Use autonomous if story count is manageable
        return estimated_stories <= 8

    def _calculate_checkpoints(self, estimated_stories: int) -> List[int]:
        """Calculate checkpoint story IDs."""
        if estimated_stories <= 3:
            return []

        checkpoints = []
        checkpoint_interval = 3

        for i in range(checkpoint_interval, estimated_stories, checkpoint_interval):
            checkpoints.append(i)

        return checkpoints

    def _generate_reasoning(
        self,
        use_ralph: bool,
        final_score: float,
        estimated_stories: int,
        complexity: str,
        request_lower: str
    ) -> List[str]:
        """Generate human-readable reasoning for the decision."""
        reasons = []

        if use_ralph:
            if 'ralph' in request_lower:
                reasons.append("User explicitly requested Ralph")
            if estimated_stories >= 5:
                reasons.append(f"{estimated_stories} stories estimated - multi-step workflow")
            if final_score >= 7:
                reasons.append(f"High complexity score ({final_score}/10)")
            if complexity in ['complex', 'very_complex']:
                reasons.append(f"Complexity level: {complexity}")

            # Pattern detection
            patterns = self.rules['decision_rules']['use_ralph_triggers'][3]['patterns']
            found_patterns = [p for p in patterns if p in request_lower]
            if found_patterns:
                reasons.append(f"Detected pattern keywords: {', '.join(found_patterns)}")
        else:
            if final_score < 4:
                reasons.append(f"Low complexity score ({final_score}/10)")
            if estimated_stories <= 2:
                reasons.append("Simple task (1-2 steps)")

            # Exclusion reasons
            exclusions = self.rules['decision_rules']['dont_use_ralph_triggers']
            for exclusion in exclusions:
                if any(ind in request_lower for ind in exclusion['indicators']):
                    reasons.append(f"Detected {exclusion['trigger']}: better handled directly")
                    break

        return reasons if reasons else ["Score-based recommendation"]

    def _calculate_confidence(self, final_score: float, request_lower: str) -> str:
        """Calculate confidence level in the recommendation."""
        # High confidence if score is very high or very low
        if final_score >= 8 or final_score <= 2:
            return "high"

        # High confidence if explicit Ralph request
        if 'ralph' in request_lower or 'autonomous' in request_lower:
            return "high"

        # Medium confidence for middle scores
        if 3 <= final_score <= 7:
            return "medium"

        return "low"

    def print_decision(self, decision: Dict[str, Any]):
        """Pretty print a decision for CLI output."""
        print("\n" + "="*60)
        print("RALPH DECISION ENGINE - ANALYSIS")
        print("="*60)

        print(f"\nREQUEST: {decision['request']}")

        print(f"\nANALYSIS:")
        analysis = decision['analysis']
        print(f"  Complexity Score: {analysis['final_score']}/10 ({analysis['complexity']})")
        print(f"  Estimated Stories: {analysis['estimated_stories']}")
        print(f"  Estimated Time: {analysis['estimated_time']}")

        print(f"\nRECOMMENDATION:")
        rec = decision['recommendation']
        print(f"  Use Ralph: {'YES' if rec['use_ralph'] else 'NO'}")
        if rec['use_ralph']:
            print(f"  Agent Type: {rec['agent_type']}")
            print(f"  Autonomous Mode: {'YES' if rec['autonomous_mode'] else 'NO (with checkpoints)'}")
            if rec['checkpoints']:
                print(f"  Checkpoints at stories: {rec['checkpoints']}")

        print(f"\nREASONING:")
        for i, reason in enumerate(decision['reasoning'], 1):
            print(f"  {i}. {reason}")

        print(f"\nCONFIDENCE: {decision['confidence'].upper()}")
        print("\n" + "="*60 + "\n")


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Analyze requests and determine when to use Ralph"
    )
    parser.add_argument(
        'request',
        nargs='+',
        help='The request text to analyze'
    )
    parser.add_argument(
        '--output',
        '-o',
        help='Output JSON file path (optional)'
    )
    parser.add_argument(
        '--json-only',
        action='store_true',
        help='Only output JSON, no pretty print'
    )

    args = parser.parse_args()
    request_text = ' '.join(args.request)

    # Analyze request
    engine = RalphDecisionEngine()
    decision = engine.analyze_request(request_text)

    # Output
    if args.json_only:
        print(json.dumps(decision, indent=2))
    else:
        engine.print_decision(decision)

    # Save to file if requested
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(decision, f, indent=2)
        print(f"Decision saved to: {output_path}")


if __name__ == '__main__':
    main()
