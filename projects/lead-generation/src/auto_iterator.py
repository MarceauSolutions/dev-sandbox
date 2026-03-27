#!/usr/bin/env python3
"""
auto_iterator.py — Autonomous Optimization Engine

WHAT: Generalized framework for autonomous business optimization, adapted from
      Karpathy's AutoResearch pattern. An LLM proposes variants of business
      artifacts (SMS copy, email subjects, website copy), deploys them, measures
      results, and keeps improvements — all without human intervention.
WHY:  Turns manual A/B testing into a continuous improvement loop. Instead of
      William designing each test, the system proposes, tests, and learns 24/7.
INPUT: Strategy documents (markdown), domain evaluators, existing campaign data
OUTPUT: Optimized templates, experiment logs, weekly PDF reports
COST: ~$0.01-0.05 per experiment (Claude API)

QUICK USAGE:
  # Propose a new SMS variant
  python execution/auto_iterator.py propose --domain sms_outreach

  # Evaluate all in-flight experiments
  python execution/auto_iterator.py evaluate --all-domains

  # Generate status report
  python execution/auto_iterator.py status

  # Run overnight batch (content quality domain — instant LLM eval)
  python execution/auto_iterator.py batch --domain content_quality --iterations 50

DEPENDENCIES: anthropic, python-dotenv
API_KEYS: ANTHROPIC_API_KEY
"""

import json
import os
import sys
import hashlib
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Protocol, runtime_checkable

from dotenv import load_dotenv

load_dotenv()

# ── Constants ──

ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT / "data" / "auto_iterator"
EXPERIMENTS_DIR = DATA_DIR / "experiments"
STRATEGIES_DIR = DATA_DIR / "strategies"
REPORTS_DIR = DATA_DIR / "reports"

for d in [DATA_DIR, EXPERIMENTS_DIR, STRATEGIES_DIR, REPORTS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

MODEL = "claude-sonnet-4-20250514"


# ── Data Models ──


@dataclass
class Variant:
    """A proposed modification to a business artifact."""
    variant_id: str
    domain: str
    variant_text: str
    baseline_text: str
    hypothesis: str
    proposed_by: str = "claude-sonnet-4-20250514"
    proposed_at: str = ""
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        if not self.proposed_at:
            self.proposed_at = datetime.utcnow().isoformat()
        if not self.variant_id:
            h = hashlib.sha256(
                f"{self.domain}:{self.variant_text}:{self.proposed_at}".encode()
            ).hexdigest()[:12]
            self.variant_id = f"{self.domain}_{datetime.utcnow().strftime('%Y%m%d')}_{h}"


@dataclass
class ExperimentMetrics:
    """Metrics collected for an experiment."""
    raw: dict = field(default_factory=dict)
    composite_score: float = 0.0
    sample_size: int = 0
    collection_window_hours: int = 0
    collected_at: str = ""

    def __post_init__(self):
        if not self.collected_at and self.raw:
            self.collected_at = datetime.utcnow().isoformat()


@dataclass
class Experiment:
    """A single optimization experiment tracking proposal through evaluation."""
    experiment_id: str
    domain: str
    variant: Variant
    baseline_metrics: ExperimentMetrics = field(default_factory=ExperimentMetrics)
    variant_metrics: ExperimentMetrics = field(default_factory=ExperimentMetrics)
    status: str = "proposed"  # proposed → approved → deployed → collecting → evaluated → kept/reverted
    approved_at: str = ""
    deployed_at: str = ""
    evaluated_at: str = ""
    result: str = ""  # "kept" | "reverted" | "inconclusive"
    learnings: str = ""
    approval_required: bool = True
    metrics_window_hours: int = 168  # 7 days default

    def to_dict(self) -> dict:
        d = asdict(self)
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "Experiment":
        variant_data = data.pop("variant", {})
        baseline_data = data.pop("baseline_metrics", {})
        variant_metrics_data = data.pop("variant_metrics", {})
        return cls(
            variant=Variant(**variant_data),
            baseline_metrics=ExperimentMetrics(**baseline_data),
            variant_metrics=ExperimentMetrics(**variant_metrics_data),
            **data,
        )


# ── Evaluator Protocol ──


@runtime_checkable
class Evaluator(Protocol):
    """Interface for domain-specific evaluators."""

    domain: str
    metrics_window_hours: int

    def collect_baseline_metrics(self, baseline_text: str) -> ExperimentMetrics:
        """Collect metrics for the current baseline."""
        ...

    def collect_variant_metrics(self, experiment: Experiment) -> ExperimentMetrics:
        """Collect metrics for a deployed variant."""
        ...

    def compute_composite_score(self, metrics: dict) -> float:
        """Compute a single composite score from raw metrics dict."""
        ...

    def is_ready_for_evaluation(self, experiment: Experiment) -> bool:
        """Check if enough data has been collected to evaluate."""
        ...

    def deploy_variant(self, experiment: Experiment) -> bool:
        """Deploy a variant to the live system. Returns True on success."""
        ...

    def revert_variant(self, experiment: Experiment) -> bool:
        """Revert a variant back to baseline. Returns True on success."""
        ...


# ── Experiment Store ──


class ExperimentStore:
    """JSON-based experiment persistence. One file per domain."""

    def __init__(self):
        self._cache: dict[str, list[Experiment]] = {}

    def _file_path(self, domain: str) -> Path:
        return EXPERIMENTS_DIR / f"{domain}_experiments.json"

    def load_domain(self, domain: str) -> list[Experiment]:
        if domain in self._cache:
            return self._cache[domain]
        path = self._file_path(domain)
        if not path.exists():
            self._cache[domain] = []
            return []
        with open(path) as f:
            data = json.load(f)
        experiments = [Experiment.from_dict(e) for e in data.get("experiments", [])]
        self._cache[domain] = experiments
        return experiments

    def save_domain(self, domain: str):
        experiments = self._cache.get(domain, [])
        path = self._file_path(domain)
        data = {
            "domain": domain,
            "updated_at": datetime.utcnow().isoformat(),
            "total_experiments": len(experiments),
            "experiments": [e.to_dict() for e in experiments],
        }
        with open(path, "w") as f:
            json.dump(data, f, indent=2, default=str)

    def add_experiment(self, experiment: Experiment):
        domain = experiment.domain
        if domain not in self._cache:
            self.load_domain(domain)
        self._cache[domain].append(experiment)
        self.save_domain(domain)

    def get_experiment(self, domain: str, experiment_id: str) -> Experiment | None:
        experiments = self.load_domain(domain)
        for e in experiments:
            if e.experiment_id == experiment_id:
                return e
        return None

    def update_experiment(self, experiment: Experiment):
        domain = experiment.domain
        experiments = self.load_domain(domain)
        for i, e in enumerate(experiments):
            if e.experiment_id == experiment.experiment_id:
                experiments[i] = experiment
                break
        self.save_domain(domain)

    def get_by_status(self, domain: str, status: str) -> list[Experiment]:
        return [e for e in self.load_domain(domain) if e.status == status]

    def get_learnings(self, domain: str, limit: int = 20) -> list[dict]:
        """Get recent learnings for strategy context."""
        experiments = self.load_domain(domain)
        completed = [e for e in experiments if e.result in ("kept", "reverted")]
        completed.sort(key=lambda e: e.evaluated_at, reverse=True)
        return [
            {
                "hypothesis": e.variant.hypothesis,
                "result": e.result,
                "learnings": e.learnings,
                "baseline_score": e.baseline_metrics.composite_score,
                "variant_score": e.variant_metrics.composite_score,
                "date": e.evaluated_at[:10],
            }
            for e in completed[:limit]
        ]

    def get_stats(self, domain: str) -> dict:
        experiments = self.load_domain(domain)
        return {
            "total": len(experiments),
            "proposed": len([e for e in experiments if e.status == "proposed"]),
            "approved": len([e for e in experiments if e.status == "approved"]),
            "deployed": len([e for e in experiments if e.status == "deployed"]),
            "collecting": len([e for e in experiments if e.status == "collecting"]),
            "kept": len([e for e in experiments if e.result == "kept"]),
            "reverted": len([e for e in experiments if e.result == "reverted"]),
            "inconclusive": len([e for e in experiments if e.result == "inconclusive"]),
        }


# ── Core Engine ──


class AutoIterator:
    """
    Autonomous optimization engine.

    The core loop:
    1. Read strategy document + experiment history
    2. LLM proposes a new variant with a hypothesis
    3. Variant is staged for approval (high-risk) or auto-deployed (low-risk)
    4. Metrics are collected over a configurable window
    5. Evaluator scores variant vs baseline
    6. If better: keep variant as new baseline, log learnings
    7. If worse: revert to baseline, log what didn't work
    8. Strategy document evolves with accumulated learnings
    """

    def __init__(self, evaluator: Evaluator):
        self.evaluator = evaluator
        self.domain = evaluator.domain
        self.store = ExperimentStore()
        self.strategy_path = STRATEGIES_DIR / f"{self.domain}_strategy.md"

    def _load_strategy(self) -> str:
        """Load the domain strategy document."""
        if self.strategy_path.exists():
            return self.strategy_path.read_text()
        return f"# {self.domain} Optimization Strategy\n\nNo strategy document found. Create one at {self.strategy_path}"

    def _build_proposal_prompt(self, current_baseline: str) -> str:
        """Build the prompt for the LLM to propose a new variant."""
        strategy = self._load_strategy()
        learnings = self.store.get_learnings(self.domain, limit=15)
        stats = self.store.get_stats(self.domain)

        learnings_text = ""
        if learnings:
            learnings_text = "\n## Past Experiment Results\n"
            for l in learnings:
                emoji = "+" if l["result"] == "kept" else "-"
                learnings_text += (
                    f"\n[{emoji}] {l['hypothesis']}\n"
                    f"   Result: {l['result']} (baseline={l['baseline_score']:.3f}, "
                    f"variant={l['variant_score']:.3f})\n"
                    f"   Learning: {l['learnings']}\n"
                )

        return f"""You are an autonomous optimization agent for the domain: {self.domain}.

## Strategy Document
{strategy}

## Current Baseline
```
{current_baseline}
```

## Optimization History
Total experiments: {stats['total']} | Kept: {stats['kept']} | Reverted: {stats['reverted']}
{learnings_text}

## Your Task
Propose ONE new variant that is likely to outperform the current baseline.

Consider:
1. What has worked in past experiments (if any)
2. What has NOT worked (avoid repeating failed approaches)
3. The strategy document constraints and brand voice
4. A specific, testable hypothesis about WHY this variant should perform better

Respond in this exact JSON format (no markdown, just raw JSON):
{{
    "variant_text": "The full text of your proposed variant",
    "hypothesis": "A specific, testable hypothesis about why this will outperform the baseline",
    "reasoning": "Your detailed reasoning based on the strategy and past learnings"
}}"""

    def propose(self, current_baseline: str) -> Experiment:
        """Use the LLM to propose a new variant."""
        from anthropic import Anthropic

        client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

        prompt = self._build_proposal_prompt(current_baseline)
        response = client.messages.create(
            model=MODEL,
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}],
        )

        try:
            result = json.loads(response.content[0].text)
        except json.JSONDecodeError:
            raise ValueError(f"LLM returned invalid JSON: {response.content[0].text[:200]}")

        variant = Variant(
            variant_id="",
            domain=self.domain,
            variant_text=result["variant_text"],
            baseline_text=current_baseline,
            hypothesis=result["hypothesis"],
            metadata={"reasoning": result.get("reasoning", "")},
        )

        experiment = Experiment(
            experiment_id=variant.variant_id,
            domain=self.domain,
            variant=variant,
            status="proposed",
            approval_required=self.evaluator.metrics_window_hours > 0,
            metrics_window_hours=self.evaluator.metrics_window_hours,
        )

        self.store.add_experiment(experiment)
        return experiment

    def approve(self, experiment_id: str) -> Experiment:
        """Approve a proposed variant for deployment."""
        exp = self.store.get_experiment(self.domain, experiment_id)
        if not exp:
            raise ValueError(f"Experiment {experiment_id} not found")
        if exp.status != "proposed":
            raise ValueError(f"Experiment is {exp.status}, not proposed")

        exp.status = "approved"
        exp.approved_at = datetime.utcnow().isoformat()
        self.store.update_experiment(exp)
        return exp

    def deploy(self, experiment_id: str) -> Experiment:
        """Deploy an approved variant to the live system."""
        exp = self.store.get_experiment(self.domain, experiment_id)
        if not exp:
            raise ValueError(f"Experiment {experiment_id} not found")
        if exp.status not in ("approved", "proposed"):
            raise ValueError(f"Experiment is {exp.status}, cannot deploy")

        # Collect baseline metrics before deploying variant
        exp.baseline_metrics = self.evaluator.collect_baseline_metrics(
            exp.variant.baseline_text
        )

        # Deploy the variant
        success = self.evaluator.deploy_variant(exp)
        if not success:
            raise RuntimeError(f"Failed to deploy variant for {experiment_id}")

        exp.status = "deployed"
        exp.deployed_at = datetime.utcnow().isoformat()
        self.store.update_experiment(exp)
        return exp

    def evaluate(self, experiment_id: str) -> Experiment:
        """Evaluate a deployed variant against its baseline."""
        exp = self.store.get_experiment(self.domain, experiment_id)
        if not exp:
            raise ValueError(f"Experiment {experiment_id} not found")
        if exp.status not in ("deployed", "collecting"):
            raise ValueError(f"Experiment is {exp.status}, cannot evaluate")

        # Check if ready
        if not self.evaluator.is_ready_for_evaluation(exp):
            exp.status = "collecting"
            self.store.update_experiment(exp)
            return exp

        # Collect variant metrics
        exp.variant_metrics = self.evaluator.collect_variant_metrics(exp)

        # Compare
        baseline_score = exp.baseline_metrics.composite_score
        variant_score = exp.variant_metrics.composite_score

        if variant_score > baseline_score:
            exp.result = "kept"
            exp.learnings = self._generate_learnings(exp, "kept")
        elif variant_score < baseline_score:
            exp.result = "reverted"
            exp.learnings = self._generate_learnings(exp, "reverted")
            self.evaluator.revert_variant(exp)
        else:
            exp.result = "inconclusive"
            exp.learnings = "No significant difference between variant and baseline."
            self.evaluator.revert_variant(exp)

        exp.status = "evaluated"
        exp.evaluated_at = datetime.utcnow().isoformat()
        self.store.update_experiment(exp)
        return exp

    def evaluate_all_pending(self) -> list[Experiment]:
        """Evaluate all deployed/collecting experiments that are ready."""
        results = []
        for exp in self.store.get_by_status(self.domain, "deployed"):
            result = self.evaluate(exp.experiment_id)
            results.append(result)
        for exp in self.store.get_by_status(self.domain, "collecting"):
            result = self.evaluate(exp.experiment_id)
            results.append(result)
        return results

    def run_batch(self, baseline: str, iterations: int = 10) -> list[Experiment]:
        """
        Run multiple propose-evaluate cycles for instant-evaluation domains.
        This is the closest to Karpathy's original loop — used for content quality
        where LLM-as-judge provides instant feedback.
        """
        results = []
        current_best = baseline

        for i in range(iterations):
            try:
                # Propose
                exp = self.propose(current_best)

                # For instant-eval domains, skip approval and deploy directly
                exp.status = "approved"
                exp.approved_at = datetime.utcnow().isoformat()

                # Collect baseline metrics
                exp.baseline_metrics = self.evaluator.collect_baseline_metrics(current_best)

                # Deploy and collect variant metrics
                self.evaluator.deploy_variant(exp)
                exp.status = "deployed"
                exp.deployed_at = datetime.utcnow().isoformat()

                exp.variant_metrics = self.evaluator.collect_variant_metrics(exp)

                # Evaluate
                baseline_score = exp.baseline_metrics.composite_score
                variant_score = exp.variant_metrics.composite_score

                if variant_score > baseline_score:
                    exp.result = "kept"
                    exp.learnings = self._generate_learnings(exp, "kept")
                    current_best = exp.variant.variant_text
                else:
                    exp.result = "reverted"
                    exp.learnings = self._generate_learnings(exp, "reverted")
                    self.evaluator.revert_variant(exp)

                exp.status = "evaluated"
                exp.evaluated_at = datetime.utcnow().isoformat()
                self.store.update_experiment(exp)
                results.append(exp)

                print(
                    f"  [{i+1}/{iterations}] {exp.result.upper()} "
                    f"(baseline={baseline_score:.4f}, variant={variant_score:.4f}) "
                    f"— {exp.variant.hypothesis[:60]}..."
                )

            except Exception as e:
                print(f"  [{i+1}/{iterations}] ERROR: {e}")
                continue

        return results

    def _generate_learnings(self, exp: Experiment, result: str) -> str:
        """Use LLM to generate concise learnings from an experiment."""
        from anthropic import Anthropic

        client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

        response = client.messages.create(
            model=MODEL,
            max_tokens=200,
            messages=[
                {
                    "role": "user",
                    "content": f"""Summarize the key learning from this experiment in 1-2 sentences.

Domain: {exp.domain}
Hypothesis: {exp.variant.hypothesis}
Result: {result}
Baseline score: {exp.baseline_metrics.composite_score:.4f}
Variant score: {exp.variant_metrics.composite_score:.4f}
Baseline text: {exp.variant.baseline_text[:200]}
Variant text: {exp.variant.variant_text[:200]}

Write a concise, actionable learning. Start with what worked or didn't work and why.""",
                }
            ],
        )
        return response.content[0].text.strip()

    def status_report(self) -> dict:
        """Generate a status report for this domain."""
        stats = self.store.get_stats(self.domain)
        recent_learnings = self.store.get_learnings(self.domain, limit=5)

        # Calculate cumulative improvement
        experiments = self.store.load_domain(self.domain)
        kept = [e for e in experiments if e.result == "kept"]
        if kept:
            first_baseline = kept[0].baseline_metrics.composite_score if kept else 0
            last_variant = kept[-1].variant_metrics.composite_score if kept else 0
            improvement = (
                ((last_variant - first_baseline) / first_baseline * 100)
                if first_baseline > 0
                else 0
            )
        else:
            improvement = 0

        return {
            "domain": self.domain,
            "stats": stats,
            "cumulative_improvement_pct": round(improvement, 1),
            "recent_learnings": recent_learnings,
            "active_experiments": [
                {
                    "id": e.experiment_id,
                    "status": e.status,
                    "hypothesis": e.variant.hypothesis,
                    "deployed_at": e.deployed_at,
                }
                for e in experiments
                if e.status in ("proposed", "approved", "deployed", "collecting")
            ],
        }


# ── CLI ──

def main():
    import argparse

    parser = argparse.ArgumentParser(description="AutoIterator — Autonomous Optimization Engine")
    subparsers = parser.add_subparsers(dest="command")

    # Status
    status_parser = subparsers.add_parser("status", help="Show optimization status")
    status_parser.add_argument("--domain", "-d", default=None, help="Specific domain")

    # Propose
    propose_parser = subparsers.add_parser("propose", help="Propose a new variant")
    propose_parser.add_argument("--domain", "-d", required=True)
    propose_parser.add_argument("--baseline", "-b", help="Current baseline text")

    # Approve
    approve_parser = subparsers.add_parser("approve", help="Approve a proposed variant")
    approve_parser.add_argument("--domain", "-d", required=True)
    approve_parser.add_argument("--experiment-id", "-e", required=True)

    # Evaluate
    eval_parser = subparsers.add_parser("evaluate", help="Evaluate experiments")
    eval_parser.add_argument("--domain", "-d", default=None)
    eval_parser.add_argument("--all-domains", action="store_true")

    # Batch
    batch_parser = subparsers.add_parser("batch", help="Run batch iterations (instant-eval domains)")
    batch_parser.add_argument("--domain", "-d", required=True)
    batch_parser.add_argument("--iterations", "-n", type=int, default=10)
    batch_parser.add_argument("--baseline", "-b", help="Starting baseline text")

    args = parser.parse_args()

    if args.command == "status":
        store = ExperimentStore()
        if args.domain:
            domains = [args.domain]
        else:
            domains = [f.stem.replace("_experiments", "") for f in EXPERIMENTS_DIR.glob("*_experiments.json")]
        if not domains:
            print("No experiments found yet. Run 'propose' to start.")
            return
        for domain in domains:
            stats = store.get_stats(domain)
            print(f"\n{'='*50}")
            print(f"Domain: {domain}")
            print(f"  Total: {stats['total']} | Kept: {stats['kept']} | Reverted: {stats['reverted']}")
            print(f"  Active: proposed={stats['proposed']} approved={stats['approved']} deployed={stats['deployed']}")
            learnings = store.get_learnings(domain, limit=3)
            if learnings:
                print(f"  Recent learnings:")
                for l in learnings:
                    emoji = "+" if l["result"] == "kept" else "-"
                    print(f"    [{emoji}] {l['hypothesis'][:70]}")

    elif args.command in ("propose", "approve", "evaluate", "batch"):
        from execution.auto_iterator_evaluators import get_evaluator, EVALUATORS

        if args.command == "propose":
            evaluator = get_evaluator(args.domain)
            iterator = AutoIterator(evaluator)
            baseline = args.baseline or "No baseline provided — use strategy document defaults."
            exp = iterator.propose(baseline)
            print(f"Proposed: {exp.experiment_id}")
            print(f"Hypothesis: {exp.variant.hypothesis}")
            print(f"Variant: {exp.variant.variant_text[:300]}")
            if exp.approval_required:
                print(f"\nRequires approval. Run: python execution/auto_iterator.py approve -d {args.domain} -e {exp.experiment_id}")

        elif args.command == "approve":
            evaluator = get_evaluator(args.domain)
            iterator = AutoIterator(evaluator)
            exp = iterator.approve(args.experiment_id)
            print(f"Approved: {exp.experiment_id}")
            print(f"Run: python execution/auto_iterator.py evaluate -d {args.domain}")

        elif args.command == "evaluate":
            if args.all_domains:
                domains = list(EVALUATORS.keys())
            elif args.domain:
                domains = [args.domain]
            else:
                print("Specify --domain or --all-domains")
                return

            for domain in domains:
                evaluator = get_evaluator(domain)
                iterator = AutoIterator(evaluator)
                results = iterator.evaluate_all_pending()
                if results:
                    print(f"\n{domain}: evaluated {len(results)} experiments")
                    for r in results:
                        print(f"  {r.result.upper()}: {r.variant.hypothesis[:60]}")
                else:
                    print(f"\n{domain}: no experiments ready for evaluation")

        elif args.command == "batch":
            evaluator = get_evaluator(args.domain)
            if evaluator.metrics_window_hours > 0:
                print(f"WARNING: {args.domain} has a {evaluator.metrics_window_hours}h metrics window.")
                print("Batch mode is designed for instant-eval domains (content_quality).")
                print("Proceeding anyway with LLM-predicted metrics...")

            iterator = AutoIterator(evaluator)
            baseline = args.baseline or "No baseline provided — use strategy document defaults."
            print(f"Running {args.iterations} iterations for {args.domain}...")
            results = iterator.run_batch(baseline, iterations=args.iterations)
            kept = [r for r in results if r.result == "kept"]
            print(f"\nDone: {len(kept)}/{len(results)} variants kept")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
