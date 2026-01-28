#!/usr/bin/env python3
"""
Pipeline Orchestrator — Coordinates the full Clawdbot ↔ Ralph workflow.

Flow:
1. PRE-FLIGHT  → Validate PRD quality, auto-enhance if needed
2. CONTEXT     → Build enhanced prompt with project-specific context
3. EXECUTE     → Trigger Ralph with enhanced prompt
4. MONITOR     → Track progress during execution
5. REVIEW      → Post-completion quality check
6. FEEDBACK    → Extract learnings, update knowledge base
7. NOTIFY      → Report results (only if quality passes)

Usage:
    python3 orchestrator.py <prd_path> [project_dir] [max_iterations]
"""

import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from pre_flight import run_preflight, validate_prd
from prompt_builder import build_enhanced_prompt, save_enhanced_prompt
from post_review import run_post_review, generate_review_report
from feedback_loop import run_feedback_loop

RALPH_DIR = Path("/home/clawdbot/dev-sandbox/ralph")
RALPH_SCRIPT = Path("/home/clawdbot/scripts/ralph-ec2.sh")
PIPELINE_LOG = RALPH_DIR / "pipeline" / "pipeline_runs.json"


def log_pipeline_event(run_id: str, event: str, data: Dict = None):
    """Append an event to the pipeline log."""
    log_path = PIPELINE_LOG
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    logs = []
    if log_path.exists():
        try:
            with open(log_path) as f:
                logs = json.load(f)
        except Exception:
            logs = []
    
    logs.append({
        "run_id": run_id,
        "event": event,
        "timestamp": datetime.utcnow().isoformat(),
        "data": data or {},
    })
    
    # Keep last 200 events
    if len(logs) > 200:
        logs = logs[-200:]
    
    with open(log_path, "w") as f:
        json.dump(logs, f, indent=2)


def run_pipeline(
    prd_path: str,
    project_dir: Optional[str] = None,
    max_iterations: int = 10,
    clawdbot_context: Optional[str] = None,
    dry_run: bool = False,
) -> Dict:
    """
    Run the full optimized pipeline.
    
    Returns:
        Result dict with status, scores, and reports.
    """
    run_id = f"pipeline-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"
    result = {
        "run_id": run_id,
        "status": "started",
        "prd_path": prd_path,
        "project_dir": project_dir,
        "stages": {},
    }
    
    print(f"\n{'='*60}")
    print(f"  🚀 Ralph Pipeline — Run {run_id}")
    print(f"{'='*60}\n")
    
    # ═══════════════════════════════════════════
    # Stage 1: PRE-FLIGHT
    # ═══════════════════════════════════════════
    print("📋 Stage 1: Pre-Flight Check")
    print("-" * 40)
    log_pipeline_event(run_id, "preflight_start")
    
    preflight_passed = run_preflight(prd_path, auto_enhance=True)
    score, issues, suggestions = validate_prd(prd_path)
    
    result["stages"]["preflight"] = {
        "passed": preflight_passed,
        "score": score,
        "issues": issues,
        "suggestions": suggestions,
    }
    
    log_pipeline_event(run_id, "preflight_complete", {"passed": preflight_passed, "score": score})
    
    if not preflight_passed:
        result["status"] = "blocked_preflight"
        print("\n🚫 Pipeline blocked — PRD quality insufficient")
        return result
    
    # ═══════════════════════════════════════════
    # Stage 2: BUILD ENHANCED PROMPT
    # ═══════════════════════════════════════════
    print(f"\n📝 Stage 2: Building Enhanced Prompt")
    print("-" * 40)
    log_pipeline_event(run_id, "prompt_build_start")
    
    enhanced_prompt_path = save_enhanced_prompt(
        prd_path,
        project_dir=project_dir,
        clawdbot_context=clawdbot_context,
    )
    
    # Read and count context
    with open(enhanced_prompt_path) as f:
        prompt_content = f.read()
    
    base_lines = len(Path(RALPH_DIR / "prompt.md").read_text().split("\n"))
    enhanced_lines = len(prompt_content.split("\n"))
    context_added = enhanced_lines - base_lines
    
    result["stages"]["prompt"] = {
        "path": enhanced_prompt_path,
        "base_lines": base_lines,
        "enhanced_lines": enhanced_lines,
        "context_lines_added": context_added,
    }
    
    print(f"  Base prompt: {base_lines} lines")
    print(f"  Enhanced prompt: {enhanced_lines} lines (+{context_added} context)")
    
    log_pipeline_event(run_id, "prompt_build_complete", {"context_added": context_added})
    
    if dry_run:
        result["status"] = "dry_run_complete"
        print("\n🏁 Dry run complete — skipping execution")
        return result
    
    # ═══════════════════════════════════════════
    # Stage 3: EXECUTE RALPH
    # ═══════════════════════════════════════════
    print(f"\n🤖 Stage 3: Executing Ralph ({max_iterations} max iterations)")
    print("-" * 40)
    log_pipeline_event(run_id, "execution_start", {"max_iterations": max_iterations})
    
    start_time = time.time()
    
    try:
        # Use enhanced prompt by updating ralph's prompt temporarily
        original_prompt = RALPH_DIR / "prompt.md"
        backup_prompt = RALPH_DIR / "prompt.md.original"
        
        # Backup original, replace with enhanced
        if original_prompt.exists():
            backup_prompt.write_text(original_prompt.read_text())
        original_prompt.write_text(prompt_content)
        
        # Run Ralph
        exec_result = subprocess.run(
            [str(RALPH_SCRIPT), str(max_iterations)],
            cwd="/home/clawdbot/dev-sandbox",
            capture_output=True,
            text=True,
            timeout=3600,  # 1 hour
            env={**dict(__import__("os").environ), "HOME": "/home/clawdbot"},
        )
        
        # Restore original prompt
        if backup_prompt.exists():
            original_prompt.write_text(backup_prompt.read_text())
            backup_prompt.unlink()
        
        elapsed = time.time() - start_time
        
        result["stages"]["execution"] = {
            "return_code": exec_result.returncode,
            "elapsed_seconds": round(elapsed),
            "output_tail": exec_result.stdout[-1000:] if exec_result.stdout else "",
            "succeeded": exec_result.returncode == 0,
        }
        
        log_pipeline_event(run_id, "execution_complete", {
            "return_code": exec_result.returncode,
            "elapsed": round(elapsed),
        })
        
        print(f"  Completed in {round(elapsed)}s (exit code: {exec_result.returncode})")
        
    except subprocess.TimeoutExpired:
        result["stages"]["execution"] = {"succeeded": False, "error": "timeout"}
        result["status"] = "execution_timeout"
        log_pipeline_event(run_id, "execution_timeout")
        print("  ❌ Execution timed out (1 hour limit)")
        return result
    except Exception as e:
        result["stages"]["execution"] = {"succeeded": False, "error": str(e)}
        result["status"] = "execution_error"
        log_pipeline_event(run_id, "execution_error", {"error": str(e)})
        print(f"  ❌ Execution error: {e}")
        return result
    
    # ═══════════════════════════════════════════
    # Stage 4: POST-COMPLETION REVIEW
    # ═══════════════════════════════════════════
    print(f"\n🔍 Stage 4: Post-Completion Review")
    print("-" * 40)
    log_pipeline_event(run_id, "review_start")
    
    review_dir = project_dir or "/home/clawdbot/dev-sandbox"
    review_result = run_post_review(prd_path, review_dir)
    report = generate_review_report(review_result)
    
    result["stages"]["review"] = {
        "score": review_result.score,
        "passed": review_result.passed,
        "summary": review_result.summary,
        "checks": review_result.checks,
        "report": report,
    }
    
    print(report)
    log_pipeline_event(run_id, "review_complete", {
        "score": review_result.score,
        "passed": review_result.passed,
    })
    
    # ═══════════════════════════════════════════
    # Stage 5: FEEDBACK LOOP
    # ═══════════════════════════════════════════
    print(f"\n🔄 Stage 5: Feedback Loop")
    print("-" * 40)
    log_pipeline_event(run_id, "feedback_start")
    
    feedback = run_feedback_loop(prd_path=prd_path)
    
    result["stages"]["feedback"] = feedback
    
    print(f"  New patterns: {feedback.get('new_patterns', 0)}")
    print(f"  New gotchas: {feedback.get('new_gotchas', 0)}")
    print(f"  Knowledge base: {feedback.get('knowledge_base_size', {})}")
    
    if feedback.get("suggestions"):
        print("  Optimization suggestions:")
        for suggestion in feedback["suggestions"]:
            print(f"    → {suggestion}")
    
    log_pipeline_event(run_id, "feedback_complete", feedback)
    
    # ═══════════════════════════════════════════
    # Final Status
    # ═══════════════════════════════════════════
    if review_result.passed:
        result["status"] = "success"
        print(f"\n✅ Pipeline complete — Quality: {review_result.score}/100")
    else:
        result["status"] = "review_failed"
        print(f"\n⚠️ Pipeline complete but review failed — Quality: {review_result.score}/100")
        print("  Manual review recommended before delivery.")
    
    log_pipeline_event(run_id, "pipeline_complete", {"status": result["status"]})
    
    # Save full result
    result_path = RALPH_DIR / "pipeline" / f"{run_id}.json"
    with open(result_path, "w") as f:
        json.dump(result, f, indent=2)
    
    return result


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: orchestrator.py <prd_path> [project_dir] [max_iterations]")
        sys.exit(1)
    
    prd = sys.argv[1]
    project = sys.argv[2] if len(sys.argv) > 2 else None
    iters = int(sys.argv[3]) if len(sys.argv) > 3 else 10
    
    result = run_pipeline(prd, project_dir=project, max_iterations=iters)
    
    print(f"\n{'='*60}")
    print(f"  Pipeline Result: {result['status'].upper()}")
    print(f"{'='*60}")
