#!/usr/bin/env python3
"""
auto_iterator_learner.py — Cross-Domain Learning Engine + Mem0 Integration

WHAT: Extracts patterns from experiments across ALL domains and persists insights
      to Mem0 so all three agents (Claude Code, Clawdbot, Ralph) can access them.
WHY:  A pattern that works in SMS ("question openers get 2x replies") likely
      transfers to email, website CTAs, and content. This engine finds those
      cross-domain patterns and makes them available system-wide.
INPUT: Experiment history from all domains
OUTPUT: Cross-domain insights stored in Mem0 + strategy document updates
COST: ~$0.02 per analysis cycle (Claude API) + FREE Mem0 storage

QUICK USAGE:
  python execution/auto_iterator_learner.py analyze
  python execution/auto_iterator_learner.py sync-mem0
  python execution/auto_iterator_learner.py update-strategies
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from execution.auto_iterator import ExperimentStore, STRATEGIES_DIR, EXPERIMENTS_DIR
from execution.auto_iterator_evaluators import EVALUATORS

MODEL = "claude-sonnet-4-20250514"


class CrossDomainLearner:
    """
    Analyzes experiment results across all domains to find transferable patterns.

    The core insight: what works in one domain often works in another.
    - "Question openers" work in SMS AND email
    - "Specificity" works in CTAs AND social proof
    - "Breakup/scarcity" works in SMS follow-ups AND email sequences

    This engine:
    1. Collects all learnings across domains
    2. Uses Claude to identify cross-domain patterns
    3. Stores insights in Mem0 for all agents
    4. Updates domain strategy documents with new cross-domain insights
    """

    def __init__(self):
        self.store = ExperimentStore()

    def collect_all_learnings(self) -> dict[str, list[dict]]:
        """Collect learnings from all domains."""
        all_learnings = {}
        for domain in EVALUATORS:
            learnings = self.store.get_learnings(domain, limit=30)
            if learnings:
                all_learnings[domain] = learnings
        return all_learnings

    def analyze_cross_domain_patterns(self) -> dict:
        """
        Use Claude to identify patterns that transfer across domains.

        Returns dict with:
          - patterns: list of cross-domain patterns found
          - recommendations: per-domain recommendations based on other domains
          - meta_learnings: high-level insights about what works
        """
        from anthropic import Anthropic

        all_learnings = self.collect_all_learnings()
        if not all_learnings:
            return {"patterns": [], "recommendations": {}, "meta_learnings": []}

        # Build context
        learnings_text = ""
        for domain, learnings in all_learnings.items():
            learnings_text += f"\n## Domain: {domain}\n"
            for l in learnings:
                emoji = "+" if l["result"] == "kept" else "-"
                learnings_text += (
                    f"[{emoji}] {l['hypothesis']}\n"
                    f"   Scores: baseline={l['baseline_score']:.3f}, variant={l['variant_score']:.3f}\n"
                    f"   Learning: {l['learnings']}\n\n"
                )

        client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        response = client.messages.create(
            model=MODEL,
            max_tokens=2000,
            messages=[
                {
                    "role": "user",
                    "content": f"""You are analyzing optimization experiment results across multiple business domains
for Marceau Solutions (digital services + fitness coaching, Naples FL).

Your goal: identify CROSS-DOMAIN PATTERNS — insights from one domain that likely transfer to others.

{learnings_text}

Analyze these results and respond in JSON:
{{
    "patterns": [
        {{
            "pattern": "Description of the cross-domain pattern",
            "evidence_domains": ["domain1", "domain2"],
            "confidence": "high/medium/low",
            "transfer_to": ["domain3", "domain4"],
            "action": "Specific recommendation for applying this pattern"
        }}
    ],
    "recommendations": {{
        "domain_name": ["Specific recommendation based on other domains' learnings"]
    }},
    "meta_learnings": [
        "High-level insight about what consistently works across all domains"
    ]
}}""",
                }
            ],
        )

        try:
            return json.loads(response.content[0].text)
        except json.JSONDecodeError:
            return {"patterns": [], "recommendations": {}, "meta_learnings": []}

    def sync_to_mem0(self, analysis: dict) -> int:
        """
        Store cross-domain insights in Mem0 for all three agents.

        Returns number of memories stored.
        """
        try:
            from execution.mem0_client import Mem0Client
        except ImportError:
            print("[WARN] Mem0 client not available — storing locally only")
            return self._store_locally(analysis)

        try:
            client = Mem0Client(agent_id="auto-iterator")
        except Exception as e:
            print(f"[WARN] Mem0 connection failed: {e} — storing locally")
            return self._store_locally(analysis)

        stored = 0

        # Store patterns
        for pattern in analysis.get("patterns", []):
            try:
                client.add(
                    content=f"Cross-domain pattern: {pattern['pattern']}. "
                    f"Evidence from: {', '.join(pattern.get('evidence_domains', []))}. "
                    f"Action: {pattern.get('action', 'N/A')}",
                    metadata={
                        "category": "optimization_pattern",
                        "confidence": pattern.get("confidence", "medium"),
                        "source": "auto_iterator_learner",
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                )
                stored += 1
            except Exception as e:
                print(f"[WARN] Failed to store pattern in Mem0: {e}")

        # Store meta-learnings
        for learning in analysis.get("meta_learnings", []):
            try:
                client.add(
                    content=f"AutoIterator meta-learning: {learning}",
                    metadata={
                        "category": "meta_learning",
                        "source": "auto_iterator_learner",
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                )
                stored += 1
            except Exception as e:
                print(f"[WARN] Failed to store meta-learning: {e}")

        return stored

    def _store_locally(self, analysis: dict) -> int:
        """Fallback: store analysis as local JSON when Mem0 is unavailable."""
        output_dir = ROOT / "data" / "auto_iterator" / "reports"
        output_dir.mkdir(parents=True, exist_ok=True)

        output_file = output_dir / f"cross_domain_analysis_{datetime.utcnow().strftime('%Y%m%d')}.json"
        with open(output_file, "w") as f:
            json.dump(
                {
                    "analyzed_at": datetime.utcnow().isoformat(),
                    "analysis": analysis,
                },
                f,
                indent=2,
            )

        return len(analysis.get("patterns", [])) + len(analysis.get("meta_learnings", []))

    def update_strategy_documents(self, analysis: dict) -> list[str]:
        """
        Append cross-domain recommendations to each domain's strategy document.

        Returns list of updated strategy file paths.
        """
        updated = []
        recommendations = analysis.get("recommendations", {})

        for domain, recs in recommendations.items():
            strategy_path = STRATEGIES_DIR / f"{domain}_strategy.md"
            if not strategy_path.exists():
                continue

            # Read existing content
            content = strategy_path.read_text()

            # Check if cross-domain section already exists
            marker = "## Cross-Domain Insights"
            if marker in content:
                # Replace existing section
                parts = content.split(marker)
                # Find next ## header after the marker
                rest = parts[1]
                next_section = rest.find("\n## ")
                if next_section > 0:
                    rest = rest[next_section:]
                else:
                    rest = ""
                content = parts[0]
            else:
                content = content.rstrip() + "\n\n"
                rest = ""

            # Build new cross-domain section
            section = f"{marker}\n\n"
            section += f"*Auto-generated on {datetime.utcnow().strftime('%Y-%m-%d')} by CrossDomainLearner*\n\n"
            for rec in recs:
                section += f"- {rec}\n"

            # Add relevant patterns
            for pattern in analysis.get("patterns", []):
                if domain in pattern.get("transfer_to", []) or domain in pattern.get("evidence_domains", []):
                    section += f"- Pattern [{pattern.get('confidence', '?')}]: {pattern['pattern']}\n"

            content += section + rest
            strategy_path.write_text(content)
            updated.append(str(strategy_path))

        return updated

    def run_full_analysis(self) -> dict:
        """Run the complete cross-domain learning pipeline."""
        print("Collecting learnings from all domains...")
        all_learnings = self.collect_all_learnings()
        total_learnings = sum(len(v) for v in all_learnings.values())

        if total_learnings == 0:
            print("No experiment data yet. Run some experiments first.")
            return {}

        print(f"Found {total_learnings} learnings across {len(all_learnings)} domains.")

        print("Analyzing cross-domain patterns...")
        analysis = self.analyze_cross_domain_patterns()

        patterns_count = len(analysis.get("patterns", []))
        print(f"Found {patterns_count} cross-domain patterns.")

        print("Syncing to Mem0...")
        stored = self.sync_to_mem0(analysis)
        print(f"Stored {stored} insights.")

        print("Updating strategy documents...")
        updated = self.update_strategy_documents(analysis)
        print(f"Updated {len(updated)} strategy documents.")

        return {
            "total_learnings_analyzed": total_learnings,
            "patterns_found": patterns_count,
            "mem0_stored": stored,
            "strategies_updated": updated,
            "analysis": analysis,
        }


# ── CLI ──


def main():
    import argparse

    parser = argparse.ArgumentParser(description="AutoIterator Cross-Domain Learner")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("analyze", help="Run full cross-domain analysis")
    subparsers.add_parser("sync-mem0", help="Sync latest analysis to Mem0")
    subparsers.add_parser("update-strategies", help="Update strategy docs with cross-domain insights")

    args = parser.parse_args()

    learner = CrossDomainLearner()

    if args.command == "analyze":
        result = learner.run_full_analysis()
        if result:
            print(f"\nDone. Patterns: {result['patterns_found']}, "
                  f"Mem0: {result['mem0_stored']}, "
                  f"Strategies: {len(result['strategies_updated'])}")
    elif args.command == "sync-mem0":
        # Load latest local analysis and sync
        reports_dir = ROOT / "data" / "auto_iterator" / "reports"
        latest = sorted(reports_dir.glob("cross_domain_analysis_*.json"), reverse=True)
        if latest:
            with open(latest[0]) as f:
                data = json.load(f)
            stored = learner.sync_to_mem0(data.get("analysis", {}))
            print(f"Synced {stored} insights to Mem0.")
        else:
            print("No analysis found. Run 'analyze' first.")
    elif args.command == "update-strategies":
        analysis = learner.analyze_cross_domain_patterns()
        updated = learner.update_strategy_documents(analysis)
        print(f"Updated {len(updated)} strategy documents.")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
