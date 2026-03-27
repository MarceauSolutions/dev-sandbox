#!/usr/bin/env python3
"""
Standardization Enforcer — Checks CLAUDE.md compliance on every run.

Verifies:
  1. Tower structure (src/, workflows/, VERSION, README.md, app.py, requirements.txt)
  2. Directives exist for all towers
  3. No nested src/src/
  4. No node_modules in repo
  5. No non-.py files in tower src/ roots (website contamination)
  6. No direct cross-tower imports (towers should use tower_protocol.py)
  7. execution/ contains only shared utilities (no tower-specific code)
  8. pipeline.db is accessible

Called by:
  - daily_loop.py (Stage 0, before acquisition stages)
  - unified_morning_digest.py (health check includes enforcer result)
  - Standalone: python execution/standardization_enforcer.py

Usage:
    python execution/standardization_enforcer.py          # Full check
    python execution/standardization_enforcer.py --json   # Machine-readable
    python execution/standardization_enforcer.py --fix    # Auto-fix safe violations
"""

import argparse
import json
import logging
import os
import urllib.request
from pathlib import Path
from typing import Any, Dict, List

REPO_ROOT = Path(__file__).resolve().parent.parent

logging.basicConfig(level=logging.INFO)

# Protected paths — NEVER delete or move these during cleanup
PROTECTED_PATHS = [
    # Client websites and deliverables
    "client-sites/",
    "client-sites/flamesofpassionentertainment.com/",
    "client-sites/gulf-coast-pressure-pros/",
    "client-sites/square-foot-shipping/",
    "websites/",
    "websites/marceausolutions.com/",
    # Main company website (also lives in ai-systems/src/ for deployment)
    "projects/ai-systems/src/index.html",
    "projects/ai-systems/src/CNAME",
    "projects/ai-systems/src/assets/",
    "projects/ai-systems/src/blog/",
    # Operations docs
    "docs/GO-LIVE-APRIL-6.md",
    "docs/THREE-AGENT-ARCHITECTURE.md",
    # Credentials (never commit, but never delete)
    ".env",
    "token.json",
    "credentials.json",
    # Pipeline data
    "projects/lead-generation/sales-pipeline/data/pipeline.db",
]
logger = logging.getLogger("enforcer")

TOWERS = ["ai-systems", "amazon-seller", "fitness-influencer",
          "lead-generation", "mcp-services", "personal-assistant"]


def check_tower_structure() -> List[str]:
    """Check each tower has required files per CLAUDE.md."""
    violations = []
    required = {
        "src": "directory",
        "workflows": "directory",
        "VERSION": "file",
        "README.md": "file",
        "requirements.txt": "file",
    }
    for tower in TOWERS:
        tower_dir = REPO_ROOT / "projects" / tower
        if not tower_dir.exists():
            violations.append(f"MISSING TOWER: projects/{tower}/ does not exist")
            continue
        for name, kind in required.items():
            path = tower_dir / name
            if kind == "directory" and not path.is_dir():
                violations.append(f"{tower}: missing {name}/")
            elif kind == "file" and not path.is_file():
                violations.append(f"{tower}: missing {name}")
        # Check entry point (app.py or main.py)
        has_entry = (tower_dir / "src" / "app.py").exists() or (tower_dir / "src" / "main.py").exists()
        if not has_entry:
            violations.append(f"{tower}: missing src/app.py or src/main.py entry point")
    return violations


def check_directives() -> List[str]:
    """Check directives exist for all towers."""
    violations = []
    for tower in TOWERS:
        path = REPO_ROOT / "directives" / f"{tower}.md"
        if not path.exists():
            violations.append(f"MISSING DIRECTIVE: directives/{tower}.md")
    return violations


def check_no_nested_src() -> List[str]:
    """Check for nested src/src/ directories (structural violation)."""
    violations = []
    for d in (REPO_ROOT / "projects").rglob("src/src"):
        if d.is_dir() and "__pycache__" not in str(d):
            violations.append(f"NESTED SRC: {d.relative_to(REPO_ROOT)}")
    return violations


def check_no_node_modules() -> List[str]:
    """Check for node_modules (should never be in repo)."""
    violations = []
    for d in (REPO_ROOT / "projects").rglob("node_modules"):
        if d.is_dir():
            violations.append(f"NODE_MODULES: {d.relative_to(REPO_ROOT)} (delete or .gitignore)")
    return violations


def check_no_web_contamination() -> List[str]:
    """Check tower src/ roots don't have HTML/CSS/JS/image files.

    Exception: ai-systems/src/ hosts the marceausolutions.com website
    (CNAME = marceausolutions.com). This is a known, protected deployment.
    """
    violations = []
    web_extensions = {".html", ".css", ".js", ".ico", ".png", ".jpg", ".svg", ".gif"}
    for tower in TOWERS:
        src_dir = REPO_ROOT / "projects" / tower / "src"
        if not src_dir.exists():
            continue
        # ai-systems hosts marceausolutions.com — website files are intentional
        if tower == "ai-systems":
            continue
        for f in src_dir.iterdir():
            if f.is_file() and f.suffix in web_extensions:
                violations.append(f"WEB FILE: {f.relative_to(REPO_ROOT)}")
    return violations


def check_cross_tower_imports() -> List[str]:
    """Check for direct imports between towers (should use tower_protocol).

    Catches both:
      1. from projects.other_tower.src import X
      2. sys.path.insert(...projects/other-tower/src...) + from X import Y
    """
    violations = []
    for tower in TOWERS:
        src_dir = REPO_ROOT / "projects" / tower / "src"
        if not src_dir.exists():
            continue
        for py_file in src_dir.glob("*.py"):
            try:
                content = py_file.read_text()
                for other_tower in TOWERS:
                    if other_tower == tower:
                        continue
                    other_mod = other_tower.replace("-", "_")
                    # Check 1: from projects.other_tower imports
                    if f"from projects.{other_mod}" in content or f"import projects.{other_mod}" in content:
                        violations.append(
                            f"CROSS-IMPORT: {py_file.relative_to(REPO_ROOT)} imports from {other_tower} "
                            f"(use execution/tower_protocol.py instead)"
                        )
                    # Check 2: sys.path manipulation to reach another tower
                    if f"projects/{other_tower}/src" in content or f"projects/{other_tower}\\/src" in content:
                        # Ignore comments
                        for line in content.split("\n"):
                            stripped = line.strip()
                            if f"projects/{other_tower}/src" in stripped and not stripped.startswith("#"):
                                violations.append(
                                    f"CROSS-PATH: {py_file.relative_to(REPO_ROOT)} adds {other_tower}/src to sys.path "
                                    f"(tower independence violation)"
                                )
                                break
            except Exception:
                pass
    return violations


def check_pipeline_db() -> List[str]:
    """Check pipeline.db is accessible."""
    violations = []
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "pipeline_db", REPO_ROOT / "execution" / "pipeline_db.py"
        )
        pdb = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(pdb)
        conn = pdb.get_db()
        cnt = conn.execute("SELECT COUNT(*) FROM deals").fetchone()[0]
        conn.close()
        if cnt == 0:
            violations.append("PIPELINE_DB: 0 deals — database may be empty or pointing to wrong file")
    except Exception as e:
        violations.append(f"PIPELINE_DB: not accessible — {e}")
    return violations


def check_execution_bloat() -> List[str]:
    """Check execution/ only has shared utilities, not tower-specific code."""
    violations = []
    exec_dir = REPO_ROOT / "execution"
    # Tower-specific keywords that shouldn't be in execution/
    tower_keywords = {
        "fitness": "fitness-influencer",
        "workout": "fitness-influencer",
        "coaching": "fitness-influencer",
        "amazon": "amazon-seller",
        "sp_api": "amazon-seller",
        "interview": "personal-assistant",
        "resume": "personal-assistant",
    }
    for py_file in exec_dir.glob("*.py"):
        name = py_file.stem.lower()
        for keyword, tower in tower_keywords.items():
            if keyword in name:
                violations.append(
                    f"EXEC BLOAT: {py_file.name} looks tower-specific ({tower}) — "
                    f"should be in projects/{tower}/src/"
                )
    return violations


def check_launchd_health() -> List[str]:
    """Check that critical launchd jobs are loaded."""
    violations = []
    import subprocess
    try:
        result = subprocess.run(["launchctl", "list"], capture_output=True, text=True, timeout=5)
        loaded = result.stdout
        critical_jobs = [
            "com.marceau.leadgen.daily-loop",
            "com.marceau.pa.morning-digest",
        ]
        for job in critical_jobs:
            if job not in loaded:
                violations.append(f"LAUNCHD: {job} not loaded — run install.sh")
    except Exception:
        pass  # Skip if launchctl not available (e.g., on EC2)
    return violations


def check_no_large_binaries() -> List[str]:
    """Check for large binary files that shouldn't be in the repo."""
    violations = []
    large_extensions = {".db", ".sqlite", ".zip", ".tar", ".gz", ".mp4", ".mov", ".wav"}
    for tower in TOWERS:
        src_dir = REPO_ROOT / "projects" / tower / "src"
        if not src_dir.exists():
            continue
        for f in src_dir.rglob("*"):
            if f.is_file() and f.suffix in large_extensions:
                size_mb = f.stat().st_size / (1024 * 1024)
                if size_mb > 5:
                    violations.append(
                        f"LARGE FILE: {f.relative_to(REPO_ROOT)} ({size_mb:.1f}MB) — "
                        f"should be in .gitignore or data/"
                    )
    return violations


def run_all_checks() -> Dict[str, Any]:
    """Run all standardization checks."""
    checks = {
        "tower_structure": check_tower_structure(),
        "directives": check_directives(),
        "nested_src": check_no_nested_src(),
        "node_modules": check_no_node_modules(),
        "web_contamination": check_no_web_contamination(),
        "cross_tower_imports": check_cross_tower_imports(),
        "pipeline_db": check_pipeline_db(),
        "execution_bloat": check_execution_bloat(),
        "launchd_health": check_launchd_health(),
        "large_binaries": check_no_large_binaries(),
    }
    all_violations = []
    for name, violations in checks.items():
        all_violations.extend(violations)

    return {
        "compliant": len(all_violations) == 0,
        "violation_count": len(all_violations),
        "violations": all_violations,
        "checks": {k: len(v) for k, v in checks.items()},
    }


def format_for_digest(result: Dict[str, Any]) -> str:
    """Format for inclusion in morning digest."""
    if result["compliant"]:
        return ""  # Don't add noise when compliant
    lines = [f"⚠️ *CLAUDE.md VIOLATIONS ({result['violation_count']})*"]
    for v in result["violations"][:5]:
        lines.append(f"  • {v}")
    if result["violation_count"] > 5:
        lines.append(f"  ... and {result['violation_count'] - 5} more")
    return "\n".join(lines)


def send_alert(result: Dict[str, Any]) -> bool:
    """Send Telegram alert if violations found."""
    if result["compliant"]:
        return False

    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "5692454753")
    if not bot_token:
        return False

    msg = (
        f"⚠️ *CLAUDE.md COMPLIANCE ALERT*\n\n"
        f"{result['violation_count']} violation(s) detected:\n"
    )
    for v in result["violations"][:5]:
        msg += f"  • {v}\n"
    if result["violation_count"] > 5:
        msg += f"\n... and {result['violation_count'] - 5} more\n"
    msg += "\nRun: `python execution/standardization_enforcer.py`"

    try:
        data = json.dumps({"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"}).encode()
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{bot_token}/sendMessage",
            data=data, headers={"Content-Type": "application/json"}, method="POST",
        )
        urllib.request.urlopen(req, timeout=10, context=__import__("ssl").create_default_context(cafile=__import__("certifi").where()))
        return True
    except Exception:
        return False


def main():
    parser = argparse.ArgumentParser(description="CLAUDE.md Standardization Enforcer")
    parser.add_argument("--json", action="store_true", help="JSON output")
    args = parser.parse_args()

    result = run_all_checks()

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        status = "COMPLIANT" if result["compliant"] else f"VIOLATIONS ({result['violation_count']})"
        print(f"\n{'='*50}")
        print(f"CLAUDE.md COMPLIANCE: {status}")
        print(f"{'='*50}\n")
        for check, count in result["checks"].items():
            icon = "✓" if count == 0 else "✗"
            print(f"  {icon} {check}: {count} violations")
        if result["violations"]:
            print(f"\nViolations:")
            for v in result["violations"]:
                print(f"  • {v}")
        print()


if __name__ == "__main__":
    main()
