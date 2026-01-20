#!/usr/bin/env python3
"""
Ralph Meta-PRD Generator - Ralph creates PRDs for improving itself.

This is the ultimate meta-circular design: Ralph can analyze its own code,
identify improvements, generate PRDs, and execute them (with user approval).

Usage:
    python -m src.ralph_meta_prd_generator analyze-system docket
    python -m src.ralph_meta_prd_generator analyze-system ralph_decision_engine
    python -m src.ralph_meta_prd_generator improve "Make the docket system faster"
"""

import argparse
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import ast
import re

from .ralph_auto_invoke import RalphAutoInvoker


class RalphMetaPRDGenerator:
    """Ralph generates PRDs to improve its own systems."""

    def __init__(self):
        self.auto_invoker = RalphAutoInvoker()
        self.src_path = Path(__file__).parent

    def analyze_system(self, system_name: str) -> Dict[str, Any]:
        """
        Analyze a Ralph system and identify improvement opportunities.

        Args:
            system_name: Name of the system to analyze (docket, ralph_decision_engine, etc)

        Returns:
            Analysis report with improvement suggestions
        """
        # Map system names to files
        system_files = {
            'docket': self.src_path / 'docket.py',
            'ralph_decision_engine': self.src_path / 'ralph_decision_engine.py',
            'ralph_auto_invoke': self.src_path / 'ralph_auto_invoke.py',
            'ralph_meta': self.src_path / 'ralph_meta_prd_generator.py'
        }

        if system_name not in system_files:
            raise ValueError(f"Unknown system: {system_name}. Choose from: {list(system_files.keys())}")

        file_path = system_files[system_name]

        if not file_path.exists():
            raise FileNotFoundError(f"System file not found: {file_path}")

        # Read and analyze code
        with open(file_path, 'r') as f:
            code = f.read()

        # Basic code analysis
        analysis = {
            "system_name": system_name,
            "file_path": str(file_path),
            "analyzed_at": datetime.now().isoformat(),
            "metrics": self._calculate_metrics(code),
            "improvement_opportunities": self._identify_improvements(code, system_name),
            "complexity_score": self._calculate_complexity(code)
        }

        return analysis

    def _calculate_metrics(self, code: str) -> Dict[str, Any]:
        """Calculate code metrics."""
        lines = code.split('\n')
        code_lines = [l for l in lines if l.strip() and not l.strip().startswith('#')]

        return {
            "total_lines": len(lines),
            "code_lines": len(code_lines),
            "comment_lines": len([l for l in lines if l.strip().startswith('#')]),
            "blank_lines": len([l for l in lines if not l.strip()]),
            "functions": len(re.findall(r'^\s*def ', code, re.MULTILINE)),
            "classes": len(re.findall(r'^\s*class ', code, re.MULTILINE))
        }

    def _calculate_complexity(self, code: str) -> int:
        """Calculate rough complexity score (1-10)."""
        # Simple heuristic based on code characteristics
        score = 0

        # Long files are more complex
        lines = len(code.split('\n'))
        if lines > 500:
            score += 3
        elif lines > 200:
            score += 2
        elif lines > 100:
            score += 1

        # Many functions = more complex
        functions = len(re.findall(r'^\s*def ', code, re.MULTILINE))
        if functions > 20:
            score += 3
        elif functions > 10:
            score += 2
        elif functions > 5:
            score += 1

        # Nested loops and conditionals
        nesting = len(re.findall(r'for .* in .*:', code)) + len(re.findall(r'if .*:', code))
        if nesting > 20:
            score += 3
        elif nesting > 10:
            score += 2

        # TODO/FIXME comments indicate incomplete areas
        todos = len(re.findall(r'TODO|FIXME', code, re.IGNORECASE))
        if todos > 5:
            score += 2
        elif todos > 2:
            score += 1

        return min(score, 10)

    def _identify_improvements(self, code: str, system_name: str) -> List[Dict[str, str]]:
        """Identify specific improvement opportunities."""
        improvements = []

        # Check for common improvement patterns
        if len(code.split('\n')) > 300:
            improvements.append({
                "type": "refactor",
                "priority": "medium",
                "description": "File is large (>300 lines). Consider splitting into modules.",
                "estimated_stories": 2
            })

        if 'TODO' in code or 'FIXME' in code:
            todo_count = len(re.findall(r'TODO|FIXME', code, re.IGNORECASE))
            improvements.append({
                "type": "feature",
                "priority": "low",
                "description": f"Complete {todo_count} TODO/FIXME items",
                "estimated_stories": min(todo_count, 3)
            })

        if system_name == 'docket':
            # Docket-specific improvements
            if 'test' not in code.lower():
                improvements.append({
                    "type": "testing",
                    "priority": "high",
                    "description": "Add comprehensive unit tests for docket operations",
                    "estimated_stories": 3
                })

            if 'export' not in code.lower():
                improvements.append({
                    "type": "feature",
                    "priority": "low",
                    "description": "Add export functionality (JSON, CSV, Markdown)",
                    "estimated_stories": 2
                })

        elif system_name == 'ralph_decision_engine':
            # Decision engine improvements
            if 'machine learning' not in code.lower():
                improvements.append({
                    "type": "enhancement",
                    "priority": "low",
                    "description": "Add ML-based scoring based on historical accuracy",
                    "estimated_stories": 4
                })

        # Generic improvements
        if not re.search(r'logging', code):
            improvements.append({
                "type": "observability",
                "priority": "medium",
                "description": "Add structured logging for debugging",
                "estimated_stories": 1
            })

        return improvements

    def generate_improvement_prd(
        self,
        system_name: str,
        improvement_request: str
    ) -> Dict[str, Any]:
        """
        Generate a PRD for improving a Ralph system.

        Args:
            system_name: System to improve
            improvement_request: User's improvement request

        Returns:
            Complete PRD ready for Ralph execution
        """
        # Analyze current system
        analysis = self.analyze_system(system_name)

        # Filter relevant improvements based on request
        relevant_improvements = self._filter_improvements(
            analysis['improvement_opportunities'],
            improvement_request
        )

        # Generate stories from improvements
        stories = []
        for i, improvement in enumerate(relevant_improvements, 1):
            story_id = f"{str(i).zfill(3)}"

            story = {
                "story_id": story_id,
                "title": f"Story {story_id}: {improvement['type'].title()} - {improvement['description'][:50]}",
                "description": improvement['description'],
                "acceptance_criteria": [
                    f"{improvement['type'].title()} complete",
                    "Tests added and passing",
                    "Documentation updated"
                ],
                "files_to_modify": [f"src/{system_name}.py"],
                "priority": improvement['priority'],
                "passes": False
            }
            stories.append(story)

        # Calculate checkpoints
        total_stories = len(stories)
        checkpoints = [3 * i for i in range(1, (total_stories // 3) + 1)]

        # Build PRD
        prd = {
            "metadata": {
                "prd_name": f"Ralph Self-Improvement: {system_name}",
                "objective": f"Improve {system_name} based on: {improvement_request}",
                "total_stories": total_stories,
                "completed_stories": 0,
                "autonomous_mode": total_stories <= 5,
                "checkpoint_stories": checkpoints,
                "generated_by": "ralph_meta_prd_generator",
                "generated_at": datetime.now().isoformat(),
                "target_system": system_name
            },
            "system_analysis": {
                "current_metrics": analysis['metrics'],
                "complexity_score": analysis['complexity_score'],
                "improvement_count": len(relevant_improvements)
            },
            "stories": stories,
            "safety_notes": [
                "⚠️  SELF-MODIFICATION: This PRD modifies Ralph's own code",
                "User approval required before execution",
                "Backup current code before applying changes",
                "Test thoroughly before committing"
            ]
        }

        return prd

    def _filter_improvements(
        self,
        improvements: List[Dict[str, str]],
        request: str
    ) -> List[Dict[str, str]]:
        """Filter improvements relevant to the request."""
        request_lower = request.lower()

        # If request mentions specific types, filter by type
        if 'test' in request_lower:
            return [imp for imp in improvements if imp['type'] == 'testing']
        elif 'refactor' in request_lower:
            return [imp for imp in improvements if imp['type'] == 'refactor']
        elif 'feature' in request_lower or 'add' in request_lower:
            return [imp for imp in improvements if imp['type'] in ['feature', 'enhancement']]

        # Otherwise, prioritize by priority
        priority_order = {'high': 0, 'medium': 1, 'low': 2}
        sorted_improvements = sorted(improvements, key=lambda x: priority_order.get(x['priority'], 3))

        # Return top 5 or all if fewer
        return sorted_improvements[:5]

    def print_analysis(self, analysis: Dict[str, Any]):
        """Pretty print system analysis."""
        print("\n" + "="*70)
        print(f"RALPH META-ANALYSIS: {analysis['system_name'].upper()}")
        print("="*70)

        print("\nCODE METRICS:")
        metrics = analysis['metrics']
        print(f"  Total Lines: {metrics['total_lines']}")
        print(f"  Code Lines: {metrics['code_lines']}")
        print(f"  Functions: {metrics['functions']}")
        print(f"  Classes: {metrics['classes']}")

        print(f"\nCOMPLEXITY SCORE: {analysis['complexity_score']}/10")

        print("\nIMPROVEMENT OPPORTUNITIES:")
        for i, improvement in enumerate(analysis['improvement_opportunities'], 1):
            priority_emoji = {'high': '🔥', 'medium': '⚡', 'low': '📋'}
            emoji = priority_emoji.get(improvement['priority'], '•')
            print(f"\n{i}. {emoji} [{improvement['type'].upper()}] {improvement['description']}")
            print(f"   Priority: {improvement['priority']}")
            print(f"   Estimated Stories: {improvement.get('estimated_stories', '?')}")

        print("\n" + "="*70 + "\n")

    def print_prd_summary(self, prd: Dict[str, Any]):
        """Pretty print PRD summary for user approval."""
        print("\n" + "="*70)
        print("🤖 RALPH SELF-IMPROVEMENT PLAN")
        print("="*70)

        meta = prd['metadata']
        print(f"\nTARGET: {meta['target_system']}")
        print(f"OBJECTIVE: {meta['objective']}")
        print(f"TOTAL STORIES: {meta['total_stories']}")
        print(f"MODE: {'Autonomous' if meta['autonomous_mode'] else 'Manual with checkpoints'}")

        if meta['checkpoint_stories']:
            print(f"CHECKPOINTS: Story {', '.join(map(str, meta['checkpoint_stories']))}")

        print("\nSTORIES:")
        for story in prd['stories']:
            print(f"\n  {story['story_id']}. {story['title']}")
            print(f"      {story['description']}")

        print("\n⚠️  SAFETY NOTES:")
        for note in prd['safety_notes']:
            print(f"  - {note}")

        print("\n" + "="*70)
        print("APPROVAL REQUIRED: Do you approve this self-improvement plan?")
        print("="*70 + "\n")


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Ralph meta-PRD generator")
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Analyze system command
    analyze_parser = subparsers.add_parser('analyze-system', help='Analyze a Ralph system')
    analyze_parser.add_argument(
        'system',
        choices=['docket', 'ralph_decision_engine', 'ralph_auto_invoke', 'ralph_meta'],
        help='System to analyze'
    )

    # Improve command
    improve_parser = subparsers.add_parser('improve', help='Generate improvement PRD')
    improve_parser.add_argument(
        'system',
        choices=['docket', 'ralph_decision_engine', 'ralph_auto_invoke', 'ralph_meta'],
        help='System to improve'
    )
    improve_parser.add_argument('request', nargs='+', help='Improvement request')
    improve_parser.add_argument('--output', '-o', help='Output PRD file path')
    improve_parser.add_argument('--auto-approve', action='store_true', help='Skip approval prompt')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    generator = RalphMetaPRDGenerator()

    if args.command == 'analyze-system':
        analysis = generator.analyze_system(args.system)
        generator.print_analysis(analysis)

    elif args.command == 'improve':
        request_text = ' '.join(args.request)
        prd = generator.generate_improvement_prd(args.system, request_text)
        generator.print_prd_summary(prd)

        if not args.auto_approve:
            approval = input("\nApprove? (yes/no): ").strip().lower()
            if approval not in ['yes', 'y']:
                print("❌ Improvement plan rejected. No changes made.")
                return

        # Save PRD
        if args.output:
            output_path = Path(args.output)
        else:
            output_path = Path(f"ralph/ralph-self-improvement-{args.system}-{datetime.now().strftime('%Y%m%d')}.json")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(prd, f, indent=2)

        print(f"\n✅ PRD saved to: {output_path}")
        print("\nNEXT STEPS:")
        print(f"  1. Review the PRD in {output_path}")
        print("  2. Launch Ralph with this PRD")
        print("  3. Ralph will execute self-improvements autonomously")
        print("  4. Review changes and test before committing\n")


if __name__ == '__main__':
    main()
