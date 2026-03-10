"""
Viral Optimizer — Analyze weaknesses and auto-map to pipeline fixes.

Pre-edit: Run viral_detector + hook_analyzer + retention_predictor on raw upload.
Post-edit: Re-score, show improvement delta.
Maps each weakness to concrete pipeline step recommendations.
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# ── Data Classes ──────────────────────────────────────────────────────────────

@dataclass
class Weakness:
    """A detected weakness with a recommended fix."""
    category: str        # hook, retention, energy, captions, pacing, visual
    severity: str        # critical, high, medium, low
    description: str     # Human-readable description
    metric_name: str     # Which metric is weak
    metric_value: float  # Current value
    metric_target: float # Target value
    fix_step: str        # Pipeline step that addresses this
    fix_params: Dict     # Parameters to pass to the fix step
    impact_estimate: str # Expected improvement description


@dataclass
class OptimizationPlan:
    """A set of recommended pipeline adjustments."""
    weaknesses: List[Weakness] = field(default_factory=list)
    recommended_steps: List[Dict] = field(default_factory=list)
    priority_order: List[str] = field(default_factory=list)

    @property
    def critical_count(self) -> int:
        return sum(1 for w in self.weaknesses if w.severity == "critical")

    @property
    def high_count(self) -> int:
        return sum(1 for w in self.weaknesses if w.severity == "high")


@dataclass
class ViralReport:
    """Complete viral optimization report with before/after."""
    video_path: str

    # Before scores
    viral_score_before: float = 0.0
    hook_score_before: float = 0.0
    hook_grade_before: str = "F"
    retention_score_before: float = 0.0
    retention_grade_before: str = "F"

    # After scores (populated after re-analysis)
    viral_score_after: Optional[float] = None
    hook_score_after: Optional[float] = None
    hook_grade_after: Optional[str] = None
    retention_score_after: Optional[float] = None
    retention_grade_after: Optional[str] = None

    # Optimization
    plan: Optional[OptimizationPlan] = None
    weaknesses_found: int = 0
    fixes_applied: int = 0

    # Retention cliffs
    cliff_count: int = 0
    cliff_timestamps: List[float] = field(default_factory=list)

    # Timing
    analysis_time: float = 0.0

    @property
    def viral_improvement(self) -> Optional[float]:
        if self.viral_score_after is not None:
            return self.viral_score_after - self.viral_score_before
        return None

    @property
    def hook_improvement(self) -> Optional[float]:
        if self.hook_score_after is not None:
            return self.hook_score_after - self.hook_score_before
        return None

    @property
    def retention_improvement(self) -> Optional[float]:
        if self.retention_score_after is not None:
            return self.retention_score_after - self.retention_score_before
        return None

    def to_dict(self) -> Dict:
        return {
            "viral_score": {
                "before": round(self.viral_score_before, 1),
                "after": round(self.viral_score_after, 1) if self.viral_score_after else None,
                "delta": round(self.viral_improvement, 1) if self.viral_improvement else None,
            },
            "hook_score": {
                "before": round(self.hook_score_before, 1),
                "after": round(self.hook_score_after, 1) if self.hook_score_after else None,
                "grade_before": self.hook_grade_before,
                "grade_after": self.hook_grade_after,
                "delta": round(self.hook_improvement, 1) if self.hook_improvement else None,
            },
            "retention_score": {
                "before": round(self.retention_score_before, 1),
                "after": round(self.retention_score_after, 1) if self.retention_score_after else None,
                "grade_before": self.retention_grade_before,
                "grade_after": self.retention_grade_after,
                "delta": round(self.retention_improvement, 1) if self.retention_improvement else None,
            },
            "weaknesses": [
                {
                    "category": w.category,
                    "severity": w.severity,
                    "description": w.description,
                    "fix": w.fix_step,
                    "impact": w.impact_estimate,
                }
                for w in (self.plan.weaknesses if self.plan else [])
            ],
            "cliff_timestamps": self.cliff_timestamps,
            "analysis_time": round(self.analysis_time, 1),
        }


# ── Weakness Detection ────────────────────────────────────────────────────────

def _detect_hook_weaknesses(hook_result: Any) -> List[Weakness]:
    """Map hook analysis weaknesses to pipeline fixes."""
    weaknesses = []

    if not hook_result or not hasattr(hook_result, "score"):
        return weaknesses

    score = hook_result.score

    # Low overall hook score
    if score.total < 50:
        weaknesses.append(Weakness(
            category="hook",
            severity="critical" if score.total < 30 else "high",
            description=f"Hook score is {score.total:.0f}/100 — viewers will scroll past",
            metric_name="hook_total",
            metric_value=score.total,
            metric_target=65.0,
            fix_step="remotion_composite",
            fix_params={"include_intro": True, "text_bomb_texts": ["WATCH THIS"]},
            impact_estimate="+15-25 hook score with attention-grabbing text bomb in first 3s",
        ))

    # Low action score (boring opening)
    if hasattr(score, "action") and score.action < 0.4:
        weaknesses.append(Weakness(
            category="hook",
            severity="high",
            description="Opening lacks immediate action or movement",
            metric_name="hook_action",
            metric_value=score.action,
            metric_target=0.6,
            fix_step="punch_zoom",
            fix_params={"zoom_level": 1.4, "max_zooms_per_minute": 10},
            impact_estimate="Punch zoom in first 3s creates immediate visual energy",
        ))

    # Low curiosity (no question/tease)
    if hasattr(score, "curiosity") and score.curiosity < 0.3:
        weaknesses.append(Weakness(
            category="hook",
            severity="medium",
            description="No curiosity gap — viewer has no reason to keep watching",
            metric_name="hook_curiosity",
            metric_value=score.curiosity,
            metric_target=0.5,
            fix_step="remotion_composite",
            fix_params={"text_bomb_texts": ["YOU'RE DOING IT WRONG"]},
            impact_estimate="Text bomb creates curiosity gap to retain viewers",
        ))

    # Low audio impact
    if hasattr(score, "audio_impact") and score.audio_impact < 0.3:
        weaknesses.append(Weakness(
            category="hook",
            severity="medium",
            description="Hook audio lacks punch — no impact sound or energy",
            metric_name="hook_audio",
            metric_value=score.audio_impact,
            metric_target=0.5,
            fix_step="sfx",
            fix_params={"sfx_on_cuts": True, "sfx_type": "impact", "volume": 0.35},
            impact_estimate="Impact SFX in first 2s grabs audio attention",
        ))

    return weaknesses


def _detect_retention_weaknesses(retention_result: Any) -> List[Weakness]:
    """Map retention prediction weaknesses to pipeline fixes."""
    weaknesses = []

    if not retention_result:
        return weaknesses

    # Low overall retention
    score = getattr(retention_result, "overall_score", 0)
    if score < 50:
        weaknesses.append(Weakness(
            category="retention",
            severity="critical" if score < 30 else "high",
            description=f"Predicted retention is {score:.0f}/100 — most viewers drop off",
            metric_name="retention_overall",
            metric_value=score,
            metric_target=60.0,
            fix_step="jumpcut",
            fix_params={"aggressive": True, "silence_thresh": -35, "min_silence_dur": 0.15},
            impact_estimate="Aggressive jump cuts remove all dead air, keeping pace up",
        ))

    # Retention cliffs (specific drop-off points)
    cliffs = getattr(retention_result, "cliffs", [])
    for cliff in cliffs:
        ts = getattr(cliff, "timestamp", 0)
        drop = getattr(cliff, "drop_percent", 0)
        cause = getattr(cliff, "cause", "unknown")

        if drop >= 15:
            severity = "critical" if drop >= 25 else "high"

            # Map cause to fix
            if "silence" in cause.lower() or "pause" in cause.lower():
                fix_step = "jumpcut"
                fix_params = {"aggressive": True}
                impact = f"Remove silence at {ts:.1f}s to prevent {drop:.0f}% drop"
            elif "repetit" in cause.lower() or "boring" in cause.lower():
                fix_step = "transition_effects"
                fix_params = {"insert_at": [ts]}
                impact = f"Add transition at {ts:.1f}s to re-engage viewers"
            else:
                fix_step = "punch_zoom"
                fix_params = {"custom_timestamps": [ts]}
                impact = f"Punch zoom at {ts:.1f}s to recapture attention"

            weaknesses.append(Weakness(
                category="retention",
                severity=severity,
                description=f"Retention cliff at {ts:.1f}s — {drop:.0f}% viewer drop-off ({cause})",
                metric_name="retention_cliff",
                metric_value=drop,
                metric_target=10.0,
                fix_step=fix_step,
                fix_params=fix_params,
                impact_estimate=impact,
            ))

    # Low final retention
    final = getattr(retention_result, "final_retention", 0)
    if final < 30:
        weaknesses.append(Weakness(
            category="retention",
            severity="high",
            description=f"Only {final:.0f}% of viewers reach the end",
            metric_name="retention_final",
            metric_value=final,
            metric_target=40.0,
            fix_step="captions",
            fix_params={"style": "bold", "word_highlight": True, "max_words_per_line": 4},
            impact_estimate="Bold word-by-word captions keep viewers reading along",
        ))

    return weaknesses


def _detect_viral_weaknesses(viral_result: Any) -> List[Weakness]:
    """Map viral detection weaknesses to pipeline fixes."""
    weaknesses = []

    if not viral_result:
        return weaknesses

    avg = getattr(viral_result, "avg_score", 0)
    if avg < 40:
        weaknesses.append(Weakness(
            category="energy",
            severity="high" if avg < 25 else "medium",
            description=f"Low viral potential ({avg:.0f}/100) — content lacks energy moments",
            metric_name="viral_avg",
            metric_value=avg,
            metric_target=50.0,
            fix_step="punch_zoom",
            fix_params={"zoom_level": 1.35, "max_zooms_per_minute": 8},
            impact_estimate="Punch zooms on key moments create energy bursts",
        ))

    # No captions weakness (always recommend for viral)
    pct = getattr(viral_result, "viral_percentage", 0)
    if pct < 20:
        weaknesses.append(Weakness(
            category="visual",
            severity="medium",
            description="Less than 20% of video has high-energy moments",
            metric_name="viral_percentage",
            metric_value=pct,
            metric_target=30.0,
            fix_step="sfx",
            fix_params={"sfx_on_cuts": True, "sfx_type": "whoosh"},
            impact_estimate="Sound effects at cuts amplify perceived energy",
        ))

    return weaknesses


# ── Optimization Plan Builder ─────────────────────────────────────────────────

def build_optimization_plan(
    weaknesses: List[Weakness],
) -> OptimizationPlan:
    """
    Build an ordered optimization plan from detected weaknesses.

    Deduplicates fix steps, prioritizes by severity, and orders
    steps logically for the pipeline.
    """
    # Priority: critical → high → medium → low
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    sorted_weaknesses = sorted(
        weaknesses,
        key=lambda w: severity_order.get(w.severity, 3),
    )

    # Deduplicate steps (keep highest-severity params for each step)
    seen_steps = {}
    for w in sorted_weaknesses:
        if w.fix_step not in seen_steps:
            seen_steps[w.fix_step] = {
                "name": w.fix_step,
                "module": w.fix_step,
                "params": dict(w.fix_params),
                "reason": w.description,
                "severity": w.severity,
            }

    # Order steps in logical pipeline sequence
    step_order = [
        "jumpcut", "punch_zoom", "captions", "sfx",
        "remotion_composite", "transition_effects", "color_grade",
        "reframe", "export",
    ]
    ordered_steps = []
    ordered_names = []
    for step_name in step_order:
        if step_name in seen_steps:
            ordered_steps.append(seen_steps[step_name])
            ordered_names.append(step_name)

    # Add any remaining steps not in the standard order
    for step_name, step_data in seen_steps.items():
        if step_name not in ordered_names:
            ordered_steps.append(step_data)
            ordered_names.append(step_name)

    return OptimizationPlan(
        weaknesses=sorted_weaknesses,
        recommended_steps=ordered_steps,
        priority_order=ordered_names,
    )


# ── Main Analysis ─────────────────────────────────────────────────────────────

async def analyze_and_optimize(
    video_path: str,
    analysis: Optional[Any] = None,
    transcription: Optional[Dict] = None,
    platform: str = "tiktok",
) -> ViralReport:
    """
    Run all three analyzers and build an optimization plan.

    This is the pre-edit analysis that tells the pipeline what to fix.

    Args:
        video_path: Raw video to analyze
        analysis: Pre-computed video analysis (optional)
        transcription: Pre-computed transcription (optional)
        platform: Target platform

    Returns:
        ViralReport with scores, weaknesses, and optimization plan
    """
    start = time.time()
    report = ViralReport(video_path=video_path)

    # Import analyzers
    try:
        from backend.viral_detector import detect_viral_moments, ViralConfig
        from backend.hook_analyzer import analyze_hook, HookConfig
        from backend.retention_predictor import predict_retention, RetentionConfig
    except ImportError:
        from viral_detector import detect_viral_moments, ViralConfig
        from hook_analyzer import analyze_hook, HookConfig
        from retention_predictor import predict_retention, RetentionConfig

    # Run all three in parallel
    viral_task = detect_viral_moments(
        video_path,
        transcription_result=transcription,
        video_analysis=analysis,
    )
    hook_task = analyze_hook(
        video_path,
        transcription_result=transcription,
        config=HookConfig(platform=platform, generate_variants=True),
    )
    retention_task = predict_retention(
        video_path,
        transcription_result=transcription,
        video_analysis=analysis,
        config=RetentionConfig(platform=platform),
    )

    # Gather results (continue on individual failures)
    viral_result = None
    hook_result = None
    retention_result = None

    results = await asyncio.gather(viral_task, hook_task, retention_task, return_exceptions=True)

    if not isinstance(results[0], Exception):
        viral_result = results[0]
        report.viral_score_before = getattr(viral_result, "avg_score", 0)
    else:
        logger.warning(f"Viral detection failed: {results[0]}")

    if not isinstance(results[1], Exception):
        hook_result = results[1]
        score = getattr(hook_result, "score", None)
        report.hook_score_before = score.total if score else 0
        report.hook_grade_before = getattr(hook_result, "grade", "F")
    else:
        logger.warning(f"Hook analysis failed: {results[1]}")

    if not isinstance(results[2], Exception):
        retention_result = results[2]
        report.retention_score_before = getattr(retention_result, "overall_score", 0)
        report.retention_grade_before = getattr(retention_result, "grade", "F")
        cliffs = getattr(retention_result, "cliffs", [])
        report.cliff_count = len(cliffs)
        report.cliff_timestamps = [getattr(c, "timestamp", 0) for c in cliffs]
    else:
        logger.warning(f"Retention prediction failed: {results[2]}")

    # Detect weaknesses from all results
    all_weaknesses = []
    all_weaknesses.extend(_detect_hook_weaknesses(hook_result))
    all_weaknesses.extend(_detect_retention_weaknesses(retention_result))
    all_weaknesses.extend(_detect_viral_weaknesses(viral_result))

    # Build optimization plan
    report.plan = build_optimization_plan(all_weaknesses)
    report.weaknesses_found = len(all_weaknesses)
    report.analysis_time = time.time() - start

    logger.info(
        f"Viral optimization analysis complete in {report.analysis_time:.1f}s: "
        f"viral={report.viral_score_before:.0f}, hook={report.hook_score_before:.0f} ({report.hook_grade_before}), "
        f"retention={report.retention_score_before:.0f} ({report.retention_grade_before}), "
        f"weaknesses={report.weaknesses_found} ({report.plan.critical_count} critical)"
    )

    return report


async def rescore_after_edit(
    video_path: str,
    report: ViralReport,
    analysis: Optional[Any] = None,
    transcription: Optional[Dict] = None,
    platform: str = "tiktok",
) -> ViralReport:
    """
    Re-run analysis on the edited video and compute improvement deltas.

    Args:
        video_path: Edited video to re-analyze
        report: The original pre-edit report to update
        analysis: Pre-computed video analysis (optional)
        transcription: Pre-computed transcription (optional)
        platform: Target platform

    Returns:
        Updated ViralReport with after scores and deltas
    """
    try:
        from backend.viral_detector import detect_viral_moments
        from backend.hook_analyzer import analyze_hook, HookConfig
        from backend.retention_predictor import predict_retention, RetentionConfig
    except ImportError:
        from viral_detector import detect_viral_moments
        from hook_analyzer import analyze_hook, HookConfig
        from retention_predictor import predict_retention, RetentionConfig

    results = await asyncio.gather(
        detect_viral_moments(video_path, transcription_result=transcription, video_analysis=analysis),
        analyze_hook(video_path, transcription_result=transcription, config=HookConfig(platform=platform)),
        predict_retention(video_path, transcription_result=transcription, video_analysis=analysis,
                          config=RetentionConfig(platform=platform)),
        return_exceptions=True,
    )

    if not isinstance(results[0], Exception):
        report.viral_score_after = getattr(results[0], "avg_score", 0)
    if not isinstance(results[1], Exception):
        score = getattr(results[1], "score", None)
        report.hook_score_after = score.total if score else 0
        report.hook_grade_after = getattr(results[1], "grade", "F")
    if not isinstance(results[2], Exception):
        report.retention_score_after = getattr(results[2], "overall_score", 0)
        report.retention_grade_after = getattr(results[2], "grade", "F")

    logger.info(
        f"Re-score complete: viral {report.viral_score_before:.0f}→{report.viral_score_after or 0:.0f} "
        f"({'+' if (report.viral_improvement or 0) >= 0 else ''}{report.viral_improvement or 0:.0f}), "
        f"hook {report.hook_score_before:.0f}→{report.hook_score_after or 0:.0f}, "
        f"retention {report.retention_score_before:.0f}→{report.retention_score_after or 0:.0f}"
    )

    return report


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Viral Optimizer — Analyze and recommend fixes")
    parser.add_argument("video", help="Input video path")
    parser.add_argument("--platform", default="tiktok", choices=["tiktok", "youtube_shorts", "instagram_reels", "youtube"])
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    report = asyncio.run(analyze_and_optimize(args.video, platform=args.platform))

    print(f"\n{'='*60}")
    print(f"  VIRAL OPTIMIZATION REPORT")
    print(f"{'='*60}")
    print(f"  Viral Score:     {report.viral_score_before:.0f}/100")
    print(f"  Hook Score:      {report.hook_score_before:.0f}/100 (Grade: {report.hook_grade_before})")
    print(f"  Retention Score: {report.retention_score_before:.0f}/100 (Grade: {report.retention_grade_before})")
    print(f"  Retention Cliffs: {report.cliff_count}")
    print(f"\n  Weaknesses Found: {report.weaknesses_found}")

    if report.plan:
        for w in report.plan.weaknesses:
            icon = {"critical": "!!!", "high": "!!", "medium": "!", "low": "."}
            print(f"  [{icon.get(w.severity, '?')}] {w.description}")
            print(f"      Fix: {w.fix_step} → {w.impact_estimate}")

        print(f"\n  Recommended Pipeline Steps:")
        for s in report.plan.recommended_steps:
            print(f"    → {s['name']}: {s['reason']}")
    print(f"\n  Analysis Time: {report.analysis_time:.1f}s")
