#!/usr/bin/env python3
"""
Ralph Auto-Invocation System - Automatically generates PRDs and launches Ralph.

Usage:
    python -m src.ralph_auto_invoke analyze "user request text"
    python -m src.ralph_auto_invoke generate-prd "user request" --output prd.json
"""

import argparse
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import subprocess
import sys

from .ralph_decision_engine import RalphDecisionEngine
from .docket import DocketManager


class RalphAutoInvoker:
    """Automatically generates PRDs and invokes Ralph when appropriate."""

    def __init__(self):
        self.decision_engine = RalphDecisionEngine()
        self.docket = DocketManager()

    def analyze_and_recommend(self, request_text: str) -> Dict[str, Any]:
        """
        Analyze a request and provide Ralph recommendation.

        Args:
            request_text: User's request

        Returns:
            Combined analysis and PRD preview
        """
        # Get decision from engine
        decision = self.decision_engine.analyze_request(request_text)

        # If Ralph recommended, generate PRD preview
        if decision['recommendation']['use_ralph']:
            prd_preview = self.generate_prd_structure(request_text, decision)
            decision['prd_preview'] = prd_preview

        return decision

    def generate_prd_structure(
        self,
        request_text: str,
        decision: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate a PRD structure from the request.

        This creates a template PRD that can be refined by Claude.

        Args:
            request_text: User's request
            decision: Decision engine output

        Returns:
            PRD structure ready for Ralph
        """
        estimated_stories = decision['analysis']['estimated_stories']
        agent_type = decision['recommendation']['agent_type']
        autonomous = decision['recommendation']['autonomous_mode']
        checkpoints = decision['recommendation']['checkpoints']

        # Break down request into story titles (Claude would refine these)
        stories = self._generate_story_templates(request_text, estimated_stories)

        # Build PRD
        prd = {
            "metadata": {
                "prd_name": f"Auto-generated: {request_text[:50]}...",
                "objective": request_text,
                "total_stories": estimated_stories,
                "completed_stories": 0,
                "autonomous_mode": autonomous,
                "checkpoint_stories": checkpoints,
                "generated_by": "ralph_auto_invoke",
                "generated_at": datetime.now().isoformat()
            },
            "stories": stories,
            "technical_notes": {
                "agent_type": agent_type,
                "estimated_time": decision['analysis']['estimated_time'],
                "decision_confidence": decision['confidence']
            }
        }

        return prd

    def _generate_story_templates(self, request_text: str, count: int) -> List[Dict[str, Any]]:
        """
        Generate story templates.

        In practice, Claude would refine these based on the request.
        This provides a starting structure.

        Args:
            request_text: User's request
            count: Number of stories to generate

        Returns:
            List of story dictionaries
        """
        stories = []

        # Generic story structure - Claude would fill in specifics
        for i in range(1, count + 1):
            story_id = f"{str(i).zfill(3)}"

            story = {
                "story_id": story_id,
                "title": f"Story {story_id}: [To be defined by Claude]",
                "description": f"Auto-generated placeholder for story {story_id} based on: {request_text}",
                "acceptance_criteria": [
                    "[Claude will define specific criteria]",
                    "[Based on analyzing the request]"
                ],
                "files_to_create": [],
                "files_to_modify": [],
                "passes": False
            }

            stories.append(story)

        return stories

    def add_to_docket(self, request_text: str, decision: Dict[str, Any]) -> str:
        """
        Add request to docket with Ralph decision attached.

        Args:
            request_text: User's request
            decision: Decision engine output

        Returns:
            request_id in docket
        """
        # Determine priority from complexity
        complexity = decision['analysis']['complexity']
        priority_map = {
            'simple': 'low',
            'medium': 'normal',
            'complex': 'high',
            'very_complex': 'urgent'
        }
        priority = priority_map.get(complexity, 'normal')

        # Create ralph_decision summary
        ralph_decision = {
            "use_ralph": decision['recommendation']['use_ralph'],
            "autonomous": decision['recommendation']['autonomous_mode'],
            "estimated_stories": decision['analysis']['estimated_stories'],
            "estimated_time": decision['analysis']['estimated_time'],
            "agent_type": decision['recommendation']['agent_type']
        }

        # Add to docket
        request_id = self.docket.add_request(
            description=request_text[:100],  # Truncate if too long
            priority=priority,
            user_message=request_text,
            ralph_decision=ralph_decision
        )

        return request_id

    def print_recommendation(self, decision: Dict[str, Any]):
        """Pretty print Ralph recommendation."""
        print("\n" + "="*70)
        print("RALPH AUTO-INVOCATION ANALYSIS")
        print("="*70)

        rec = decision['recommendation']

        if rec['use_ralph']:
            print("\n✅ RECOMMENDATION: Use Ralph")
            print(f"   Agent Type: {rec['agent_type']}")
            print(f"   Mode: {'Autonomous' if rec['autonomous_mode'] else 'Manual with checkpoints'}")
            print(f"   Estimated Stories: {decision['analysis']['estimated_stories']}")
            print(f"   Estimated Time: {decision['analysis']['estimated_time']}")

            if rec['checkpoints']:
                print(f"   Checkpoints at: Story {', '.join(map(str, rec['checkpoints']))}")

            print("\nREASONING:")
            for i, reason in enumerate(decision['reasoning'], 1):
                print(f"  {i}. {reason}")

            if 'prd_preview' in decision:
                print("\n📋 PRD PREVIEW GENERATED")
                print(f"   Total Stories: {decision['prd_preview']['metadata']['total_stories']}")

            print("\nNEXT STEPS:")
            print("  1. User confirms: 'Yes, use Ralph'")
            print("  2. Claude refines PRD stories")
            print("  3. Launch Ralph with refined PRD")

        else:
            print("\n❌ RECOMMENDATION: Handle manually (don't use Ralph)")
            print(f"   Reason: Too simple ({decision['analysis']['complexity']})")
            print(f"   Estimated Time: {decision['analysis']['estimated_time']}")

            print("\nREASONING:")
            for i, reason in enumerate(decision['reasoning'], 1):
                print(f"  {i}. {reason}")

        print("\n" + "="*70 + "\n")

    def save_prd(self, prd: Dict[str, Any], output_path: Path):
        """Save PRD to file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(prd, f, indent=2)
        print(f"✅ PRD saved to: {output_path}")


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Ralph auto-invocation system")
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze request and recommend')
    analyze_parser.add_argument('request', nargs='+', help='User request text')
    analyze_parser.add_argument('--add-to-docket', action='store_true', help='Add to docket')

    # Generate PRD command
    prd_parser = subparsers.add_parser('generate-prd', help='Generate PRD structure')
    prd_parser.add_argument('request', nargs='+', help='User request text')
    prd_parser.add_argument('--output', '-o', required=True, help='Output PRD file path')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    invoker = RalphAutoInvoker()

    if args.command == 'analyze':
        request_text = ' '.join(args.request)
        decision = invoker.analyze_and_recommend(request_text)
        invoker.print_recommendation(decision)

        if args.add_to_docket:
            request_id = invoker.add_to_docket(request_text, decision)
            print(f"✅ Added to docket: {request_id}\n")

    elif args.command == 'generate-prd':
        request_text = ' '.join(args.request)
        decision = invoker.analyze_and_recommend(request_text)

        if decision['recommendation']['use_ralph']:
            prd = decision['prd_preview']
            output_path = Path(args.output)
            invoker.save_prd(prd, output_path)

            print("\n⚠️  NOTE: This is an auto-generated template.")
            print("Claude should refine the story titles, descriptions, and criteria")
            print("before launching Ralph.\n")
        else:
            print("\n❌ Ralph not recommended for this request.")
            print("Handle manually instead.\n")


if __name__ == '__main__':
    main()
