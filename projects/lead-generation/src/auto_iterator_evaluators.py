#!/usr/bin/env python3
"""
auto_iterator_evaluators.py — Domain-Specific Evaluators for AutoIterator

Each evaluator knows how to:
1. Collect baseline metrics from existing data sources
2. Deploy a variant into the live system
3. Collect variant metrics after the measurement window
4. Compute a composite score from raw metrics
5. Revert a failed variant

Evaluators consume data from existing systems (outreach_optimizer, ab_testing,
coaching_analytics, Gmail API, GA4) — they do NOT create new data pipelines.

WHAT: Pluggable evaluation functions for autonomous optimization
WHY:  Separates "what to measure" from "how to optimize" — each domain has
      different metrics, latencies, and deployment mechanisms
INPUT: Experiment objects from AutoIterator
OUTPUT: ExperimentMetrics with composite scores
COST: FREE (reads existing data) + ~$0.005 per LLM-as-judge evaluation
"""

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from auto_iterator import (
    Evaluator,
    Experiment,
    ExperimentMetrics,
)


# ── SMS Outreach Evaluator ──


class SMSOutreachEvaluator:
    """
    Evaluates SMS outreach template performance.

    Metrics: response_rate, hot_lead_rate, opt_out_rate
    Data source: sms_campaigns.json via outreach_optimizer.py
    Latency: 3-7 days for meaningful sample
    Deployment: Adds variant to template rotation in outreach_optimizer

    Composite score = (response_rate * 0.4) + (hot_lead_rate * 0.3) - (opt_out_rate * 0.3)
    """

    domain = "sms_outreach"
    metrics_window_hours = 168  # 7 days

    WEIGHTS = {
        "response_rate": 0.4,
        "hot_lead_rate": 0.3,
        "opt_out_rate": -0.3,  # Negative — lower is better
    }

    # Default to lead-scraper output where real campaign data lives
    DEFAULT_CAMPAIGNS_DIR = Path(__file__).parent.parent / "projects" / "shared" / "lead-scraper" / "output"

    def __init__(self, campaigns_dir: str = ""):
        self.campaigns_dir = Path(campaigns_dir) if campaigns_dir else self.DEFAULT_CAMPAIGNS_DIR
        self.campaigns_file = self.campaigns_dir / "sms_campaigns.json"

    def _load_campaigns(self) -> list[dict]:
        if not self.campaigns_file.exists():
            return []
        with open(self.campaigns_file) as f:
            data = json.load(f)
        return data.get("records", [])

    def _template_metrics(self, template_name: str) -> dict:
        """Calculate metrics for a specific template from campaign records."""
        records = self._load_campaigns()
        matching = [r for r in records if r.get("template_used") == template_name]
        total = len(matching)
        if total == 0:
            return {"total_sent": 0, "response_rate": 0, "hot_lead_rate": 0, "opt_out_rate": 0}

        responses = len([r for r in matching if r.get("status") == "responded"])
        hot_leads = len([r for r in matching if r.get("response_category") == "hot_lead"])
        opt_outs = len([r for r in matching if r.get("status") == "opted_out"])

        return {
            "total_sent": total,
            "responses": responses,
            "hot_leads": hot_leads,
            "opt_outs": opt_outs,
            "response_rate": responses / total,
            "hot_lead_rate": hot_leads / total,
            "opt_out_rate": opt_outs / total,
        }

    def compute_composite_score(self, metrics: dict) -> float:
        score = 0.0
        for metric, weight in self.WEIGHTS.items():
            score += metrics.get(metric, 0) * weight
        return max(score, 0)  # Floor at 0

    def collect_baseline_metrics(self, baseline_text: str) -> ExperimentMetrics:
        """Collect current performance across all active templates as baseline."""
        records = self._load_campaigns()
        total = len(records) if records else 1
        responses = len([r for r in records if r.get("status") == "responded"])
        hot_leads = len([r for r in records if r.get("response_category") == "hot_lead"])
        opt_outs = len([r for r in records if r.get("status") == "opted_out"])

        raw = {
            "total_sent": total,
            "response_rate": responses / max(total, 1),
            "hot_lead_rate": hot_leads / max(total, 1),
            "opt_out_rate": opt_outs / max(total, 1),
        }
        return ExperimentMetrics(
            raw=raw,
            composite_score=self.compute_composite_score(raw),
            sample_size=total,
            collection_window_hours=self.metrics_window_hours,
        )

    def collect_variant_metrics(self, experiment: Experiment) -> ExperimentMetrics:
        """Collect metrics for the deployed variant template."""
        template_name = experiment.variant.metadata.get("deployed_template_name", "")
        if not template_name:
            template_name = f"auto_{experiment.experiment_id}"

        raw = self._template_metrics(template_name)
        return ExperimentMetrics(
            raw=raw,
            composite_score=self.compute_composite_score(raw),
            sample_size=raw.get("total_sent", 0),
            collection_window_hours=self.metrics_window_hours,
        )

    def is_ready_for_evaluation(self, experiment: Experiment) -> bool:
        """Ready when: metrics window elapsed AND minimum 30 sends."""
        if not experiment.deployed_at:
            return False
        deployed = datetime.fromisoformat(experiment.deployed_at)
        window = timedelta(hours=self.metrics_window_hours)
        if datetime.utcnow() < deployed + window:
            return False

        template_name = experiment.variant.metadata.get("deployed_template_name", "")
        if template_name:
            metrics = self._template_metrics(template_name)
            return metrics.get("total_sent", 0) >= 30
        return True

    def deploy_variant(self, experiment: Experiment) -> bool:
        """
        Add the variant text as a new template in the outreach system.
        In practice, this writes to a staging file that the outreach optimizer picks up.
        """
        template_name = f"auto_{experiment.experiment_id}"
        experiment.variant.metadata["deployed_template_name"] = template_name

        staging_file = self.campaigns_dir / "auto_iterator_staged_templates.json"
        staged = {}
        if staging_file.exists():
            with open(staging_file) as f:
                staged = json.load(f)

        staged[template_name] = {
            "text": experiment.variant.variant_text,
            "hypothesis": experiment.variant.hypothesis,
            "experiment_id": experiment.experiment_id,
            "deployed_at": datetime.utcnow().isoformat(),
            "active": True,
        }

        with open(staging_file, "w") as f:
            json.dump(staged, f, indent=2)

        return True

    def revert_variant(self, experiment: Experiment) -> bool:
        """Remove the variant template from rotation."""
        template_name = experiment.variant.metadata.get("deployed_template_name", "")
        if not template_name:
            return True

        staging_file = self.campaigns_dir / "auto_iterator_staged_templates.json"
        if staging_file.exists():
            with open(staging_file) as f:
                staged = json.load(f)
            if template_name in staged:
                staged[template_name]["active"] = False
                with open(staging_file, "w") as f:
                    json.dump(staged, f, indent=2)

        return True


# ── Content Quality Evaluator (LLM-as-Judge) ──


class ContentQualityEvaluator:
    """
    Evaluates content generation prompts using LLM-as-judge.

    This is the closest to Karpathy's original pattern — instant evaluation,
    no async metrics. Perfect for overnight batch runs.

    The target artifact is a PROMPT (not the content itself). We generate
    sample outputs from both baseline and variant prompts, then have Claude
    judge which produces better content.

    Metrics: quality_score, brand_voice_score, engagement_score, accuracy_score
    Data source: LLM evaluation (instant)
    Latency: ~5 seconds per evaluation
    Deployment: Updates prompt template file

    Composite score = mean of 4 quality dimensions (0-10 scale, normalized to 0-1)
    """

    domain = "content_quality"
    metrics_window_hours = 0  # Instant evaluation

    QUALITY_DIMENSIONS = [
        "accuracy",       # Is the information correct and evidence-based?
        "engagement",     # Would the target audience find this compelling?
        "brand_voice",    # Does it match Marceau Solutions tone (professional, direct, no fluff)?
        "actionability",  # Can the reader take immediate action from this?
    ]

    def __init__(self, content_type: str = "workout_plan"):
        """
        Args:
            content_type: What kind of content the prompt generates.
                         Used for judge context. E.g., "workout_plan",
                         "nutrition_guide", "social_post", "email_copy"
        """
        self.content_type = content_type
        self._model = "claude-sonnet-4-20250514"

    def _generate_sample(self, prompt_text: str) -> str:
        """Generate a sample output from a prompt."""
        from anthropic import Anthropic

        client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        response = client.messages.create(
            model=self._model,
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt_text}],
        )
        return response.content[0].text

    def _judge(self, content_a: str, content_b: str) -> dict:
        """Have Claude judge two content samples across quality dimensions."""
        from anthropic import Anthropic

        client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

        dimensions_text = "\n".join(
            f"- **{d}**: Score 0-10" for d in self.QUALITY_DIMENSIONS
        )

        response = client.messages.create(
            model=self._model,
            max_tokens=500,
            messages=[
                {
                    "role": "user",
                    "content": f"""You are a content quality judge for {self.content_type} content.
Score each piece on these dimensions (0-10):
{dimensions_text}

## Content A
{content_a[:1500]}

## Content B
{content_b[:1500]}

Respond in this exact JSON format (no markdown):
{{
    "content_a_scores": {{"accuracy": N, "engagement": N, "brand_voice": N, "actionability": N}},
    "content_b_scores": {{"accuracy": N, "engagement": N, "brand_voice": N, "actionability": N}},
    "explanation": "Brief explanation of scoring"
}}""",
                }
            ],
        )

        try:
            return json.loads(response.content[0].text)
        except json.JSONDecodeError:
            return {
                "content_a_scores": {d: 5 for d in self.QUALITY_DIMENSIONS},
                "content_b_scores": {d: 5 for d in self.QUALITY_DIMENSIONS},
                "explanation": "Failed to parse judge response",
            }

    def compute_composite_score(self, metrics: dict) -> float:
        """Average across all quality dimensions, normalized to 0-1."""
        scores = [metrics.get(d, 5) for d in self.QUALITY_DIMENSIONS]
        return sum(scores) / (len(scores) * 10)  # Normalize 0-10 to 0-1

    def collect_baseline_metrics(self, baseline_text: str) -> ExperimentMetrics:
        """Generate samples from baseline prompt and self-evaluate."""
        samples = [self._generate_sample(baseline_text) for _ in range(2)]

        # Judge each sample
        all_scores = {d: [] for d in self.QUALITY_DIMENSIONS}
        for sample in samples:
            judge_result = self._judge(sample, sample)
            for d in self.QUALITY_DIMENSIONS:
                all_scores[d].append(judge_result["content_a_scores"].get(d, 5))

        raw = {d: sum(scores) / len(scores) for d, scores in all_scores.items()}
        return ExperimentMetrics(
            raw=raw,
            composite_score=self.compute_composite_score(raw),
            sample_size=len(samples),
        )

    def collect_variant_metrics(self, experiment: Experiment) -> ExperimentMetrics:
        """Generate samples from variant prompt and evaluate against baseline samples."""
        baseline_sample = self._generate_sample(experiment.variant.baseline_text)
        variant_sample = self._generate_sample(experiment.variant.variant_text)

        judge_result = self._judge(baseline_sample, variant_sample)

        # Use content_b_scores since variant is B
        raw = judge_result.get("content_b_scores", {d: 5 for d in self.QUALITY_DIMENSIONS})
        return ExperimentMetrics(
            raw=raw,
            composite_score=self.compute_composite_score(raw),
            sample_size=1,
        )

    def is_ready_for_evaluation(self, experiment: Experiment) -> bool:
        return True  # Always ready — instant evaluation

    def deploy_variant(self, experiment: Experiment) -> bool:
        return True  # No actual deployment for prompt optimization

    def revert_variant(self, experiment: Experiment) -> bool:
        return True  # No actual revert needed


# ── Email Subject Line Evaluator ──


class EmailSubjectEvaluator:
    """
    Evaluates email subject line performance.

    Metrics: open_rate, click_rate, reply_rate, unsubscribe_rate
    Data source: Gmail API (future), currently LLM-as-judge for initial bootstrap
    Latency: 24-48 hours for real metrics, instant for LLM judge
    Deployment: Updates n8n nurture workflow templates

    Composite score = (open_rate * 0.4) + (reply_rate * 0.35) - (unsubscribe_rate * 0.25)
    """

    domain = "email_subject"
    metrics_window_hours = 48

    WEIGHTS = {
        "open_rate": 0.4,
        "reply_rate": 0.35,
        "unsubscribe_rate": -0.25,
    }

    def compute_composite_score(self, metrics: dict) -> float:
        score = 0.0
        for metric, weight in self.WEIGHTS.items():
            score += metrics.get(metric, 0) * weight
        return max(score, 0)

    def collect_baseline_metrics(self, baseline_text: str) -> ExperimentMetrics:
        """Bootstrap with LLM-predicted metrics until real data pipeline exists."""
        predicted = self._predict_metrics(baseline_text)
        return ExperimentMetrics(
            raw=predicted,
            composite_score=self.compute_composite_score(predicted),
            sample_size=0,
        )

    def collect_variant_metrics(self, experiment: Experiment) -> ExperimentMetrics:
        predicted = self._predict_metrics(experiment.variant.variant_text)
        return ExperimentMetrics(
            raw=predicted,
            composite_score=self.compute_composite_score(predicted),
            sample_size=0,
        )

    def _predict_metrics(self, subject_line: str) -> dict:
        """Use LLM to predict email metrics. Bootstrap until real data exists."""
        from anthropic import Anthropic

        client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=200,
            messages=[
                {
                    "role": "user",
                    "content": f"""Predict email performance metrics for this subject line in a B2B
fitness/digital services context. Be realistic based on industry benchmarks.

Subject: "{subject_line}"

Respond in JSON only:
{{"open_rate": 0.XX, "reply_rate": 0.XX, "unsubscribe_rate": 0.XX}}""",
                }
            ],
        )
        try:
            return json.loads(response.content[0].text)
        except json.JSONDecodeError:
            return {"open_rate": 0.20, "reply_rate": 0.02, "unsubscribe_rate": 0.01}

    def is_ready_for_evaluation(self, experiment: Experiment) -> bool:
        return True  # Using LLM predictions for bootstrap

    def deploy_variant(self, experiment: Experiment) -> bool:
        return True

    def revert_variant(self, experiment: Experiment) -> bool:
        return True


# ── Evaluator Registry ──


EVALUATORS: dict[str, type] = {
    "sms_outreach": SMSOutreachEvaluator,
    "content_quality": ContentQualityEvaluator,
    "email_subject": EmailSubjectEvaluator,
}

# Deferred registration — classes defined below the registry
def _register_deferred():
    EVALUATORS["nurture_email"] = NurtureEmailEvaluator
    EVALUATORS["website_cta"] = WebsiteCTAEvaluator


def get_evaluator(domain: str, **kwargs) -> Evaluator:
    """Get an evaluator instance by domain name."""
    cls = EVALUATORS.get(domain)
    if not cls:
        raise ValueError(f"Unknown domain: {domain}. Available: {list(EVALUATORS.keys())}")
    return cls(**kwargs)


# ── Nurture Email Sequence Evaluator ──


class NurtureEmailEvaluator:
    """
    Evaluates email nurture sequence templates.
    LLM-as-judge bootstrap → real Gmail API metrics when MailAssist is wired.
    Composite = (open * 0.3) + (reply * 0.4) - (unsub * 0.2) + (conversion * 0.1)
    """

    domain = "nurture_email"
    metrics_window_hours = 0

    WEIGHTS = {"open_rate": 0.3, "reply_rate": 0.4, "unsubscribe_rate": -0.2, "conversion_rate": 0.1}

    def __init__(self, sequence_position: str = "day1_checkin"):
        self.sequence_position = sequence_position
        self._model = "claude-sonnet-4-20250514"

    def compute_composite_score(self, metrics: dict) -> float:
        return max(sum(metrics.get(m, 0) * w for m, w in self.WEIGHTS.items()), 0)

    def _predict_metrics(self, email_text: str) -> dict:
        from anthropic import Anthropic
        client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        response = client.messages.create(
            model=self._model, max_tokens=300,
            messages=[{"role": "user", "content": f"""Predict B2B lead nurture email performance.
Context: {self.sequence_position} in multi-touch sequence for Naples FL local businesses.
Email: "{email_text[:500]}"
Benchmarks: 15-25% open, 1-5% reply, <0.5% unsub.
JSON only: {{"open_rate": 0.XX, "reply_rate": 0.XX, "unsubscribe_rate": 0.XX, "conversion_rate": 0.XX}}"""}],
        )
        try:
            return json.loads(response.content[0].text)
        except json.JSONDecodeError:
            return {"open_rate": 0.18, "reply_rate": 0.02, "unsubscribe_rate": 0.005, "conversion_rate": 0.01}

    def collect_baseline_metrics(self, baseline_text: str) -> ExperimentMetrics:
        p = self._predict_metrics(baseline_text)
        return ExperimentMetrics(raw=p, composite_score=self.compute_composite_score(p), sample_size=0)

    def collect_variant_metrics(self, experiment: Experiment) -> ExperimentMetrics:
        p = self._predict_metrics(experiment.variant.variant_text)
        return ExperimentMetrics(raw=p, composite_score=self.compute_composite_score(p), sample_size=0)

    def is_ready_for_evaluation(self, experiment: Experiment) -> bool:
        return True

    def deploy_variant(self, experiment: Experiment) -> bool:
        return True

    def revert_variant(self, experiment: Experiment) -> bool:
        return True


# ── Website CTA Evaluator ──


class WebsiteCTAEvaluator:
    """
    Evaluates website CTA copy via LLM-as-judge.
    Path to GA4 real metrics when Measurement ID is activated.
    Composite = mean of clarity/urgency/relevance/value_prop (0-10 → 0-1)
    """

    domain = "website_cta"
    metrics_window_hours = 0

    CTA_DIMENSIONS = ["clarity", "urgency", "relevance", "value_prop"]

    def __init__(self, page_context: str = "homepage"):
        self.page_context = page_context
        self._model = "claude-sonnet-4-20250514"

    def _judge_cta(self, cta_a: str, cta_b: str) -> dict:
        from anthropic import Anthropic
        client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        dims = ", ".join(self.CTA_DIMENSIONS)
        response = client.messages.create(
            model=self._model, max_tokens=500,
            messages=[{"role": "user", "content": f"""CRO expert: evaluate CTAs for {self.page_context} page
(Marceau Solutions, Naples FL). Score 0-10 on: {dims}
CTA A: "{cta_a}"
CTA B: "{cta_b}"
JSON only: {{"cta_a_scores": {{"clarity": N, "urgency": N, "relevance": N, "value_prop": N}},
"cta_b_scores": {{"clarity": N, "urgency": N, "relevance": N, "value_prop": N}},
"predicted_click_improvement_pct": N, "explanation": "brief"}}"""}],
        )
        try:
            return json.loads(response.content[0].text)
        except json.JSONDecodeError:
            return {"cta_a_scores": {d: 5 for d in self.CTA_DIMENSIONS},
                    "cta_b_scores": {d: 5 for d in self.CTA_DIMENSIONS},
                    "predicted_click_improvement_pct": 0}

    def compute_composite_score(self, metrics: dict) -> float:
        scores = [metrics.get(d, 5) for d in self.CTA_DIMENSIONS]
        return sum(scores) / (len(scores) * 10)

    def collect_baseline_metrics(self, baseline_text: str) -> ExperimentMetrics:
        r = self._judge_cta(baseline_text, baseline_text)
        raw = r.get("cta_a_scores", {d: 5 for d in self.CTA_DIMENSIONS})
        return ExperimentMetrics(raw=raw, composite_score=self.compute_composite_score(raw), sample_size=1)

    def collect_variant_metrics(self, experiment: Experiment) -> ExperimentMetrics:
        r = self._judge_cta(experiment.variant.baseline_text, experiment.variant.variant_text)
        raw = r.get("cta_b_scores", {d: 5 for d in self.CTA_DIMENSIONS})
        raw["predicted_click_improvement_pct"] = r.get("predicted_click_improvement_pct", 0)
        return ExperimentMetrics(raw=raw, composite_score=self.compute_composite_score(raw), sample_size=1)

    def is_ready_for_evaluation(self, experiment: Experiment) -> bool:
        return True

    def deploy_variant(self, experiment: Experiment) -> bool:
        return True

    def revert_variant(self, experiment: Experiment) -> bool:
        return True


_register_deferred()
