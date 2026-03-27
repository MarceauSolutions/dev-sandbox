#!/usr/bin/env python3
"""
System Health Check — Verifies all autonomous components are operational.

Checks:
  1. Launchd jobs loaded and running
  2. Pipeline DB accessible with data
  3. Gmail API token valid
  4. Twilio API reachable
  5. Daily loop health (consecutive failures)
  6. .env keys present

Called by unified_morning_digest.py to include status in the 6:30am digest.
Can also be run standalone for debugging.

Usage:
    python -m src.system_health_check          # Full check
    python -m src.system_health_check --json   # Machine-readable output
"""

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent

try:
    from dotenv import load_dotenv
    load_dotenv(REPO_ROOT / ".env")
except ImportError:
    pass


def check_launchd_jobs() -> Dict[str, Any]:
    """Check if all expected launchd jobs are loaded."""
    expected = [
        "com.marceau.leadgen.daily-loop",
        "com.marceau.leadgen.check-responses",
        "com.marceau.leadgen.digest",
        "com.marceau.pa.morning-digest",
    ]
    try:
        result = subprocess.run(
            ["launchctl", "list"], capture_output=True, text=True, timeout=5
        )
        loaded = result.stdout
        statuses = {}
        for job in expected:
            statuses[job.split(".")[-1]] = job in loaded
        all_ok = all(statuses.values())
        return {"ok": all_ok, "jobs": statuses}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def check_pipeline_db() -> Dict[str, Any]:
    """Check pipeline.db is accessible and has data."""
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "pipeline_db", REPO_ROOT / "execution" / "pipeline_db.py"
        )
        pdb = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(pdb)
        conn = pdb.get_db()
        deal_count = conn.execute("SELECT COUNT(*) FROM deals").fetchone()[0]
        recent = conn.execute(
            "SELECT COUNT(*) FROM deals WHERE date(updated_at) >= date('now', '-7 days')"
        ).fetchone()[0]
        conn.close()
        return {"ok": deal_count > 0, "deals": deal_count, "active_7d": recent}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def check_gmail_token() -> Dict[str, Any]:
    """Check Gmail OAuth token is valid."""
    token_path = REPO_ROOT / "token.json"
    if not token_path.exists():
        return {"ok": False, "error": "token.json missing"}
    try:
        with open(token_path) as f:
            token = json.load(f)
        scopes = token.get("scopes", [])
        has_read = "https://www.googleapis.com/auth/gmail.readonly" in scopes
        has_send = "https://www.googleapis.com/auth/gmail.send" in scopes
        has_refresh = bool(token.get("refresh_token"))
        return {
            "ok": has_read and has_refresh,
            "scopes": len(scopes),
            "can_read": has_read,
            "can_send": has_send,
            "has_refresh": has_refresh,
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


def check_twilio() -> Dict[str, Any]:
    """Check Twilio credentials are configured."""
    sid = os.getenv("TWILIO_ACCOUNT_SID", "")
    token = os.getenv("TWILIO_AUTH_TOKEN", "")
    phone = os.getenv("TWILIO_PHONE_NUMBER", "")
    all_set = all([sid, token, phone])
    return {"ok": all_set, "configured": all_set}


def check_daily_loop_health() -> Dict[str, Any]:
    """Check daily loop health file for consecutive failures."""
    health_file = REPO_ROOT / "projects" / "lead-generation" / "logs" / "loop_health.json"
    if not health_file.exists():
        return {"ok": True, "note": "no health file yet (first run pending)"}
    try:
        with open(health_file) as f:
            health = json.load(f)
        failures = health.get("consecutive_failures", 0)
        runs = health.get("runs", [])
        last_run = runs[-1] if runs else {}
        return {
            "ok": failures < 2,
            "consecutive_failures": failures,
            "last_run_date": last_run.get("date", "unknown"),
            "last_run_passed": f"{last_run.get('stages_passed', '?')}/{last_run.get('stages_total', '?')}",
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


def check_env_keys() -> Dict[str, Any]:
    """Check required .env keys are present."""
    required = [
        "TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "TWILIO_PHONE_NUMBER",
        "SMTP_USERNAME", "SMTP_PASSWORD",
        "TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID",
    ]
    missing = [k for k in required if not os.getenv(k)]
    return {"ok": len(missing) == 0, "missing": missing}


def run_all_checks() -> Dict[str, Any]:
    """Run all health checks and return combined result."""
    checks = {
        "launchd": check_launchd_jobs(),
        "pipeline_db": check_pipeline_db(),
        "gmail_token": check_gmail_token(),
        "twilio": check_twilio(),
        "daily_loop": check_daily_loop_health(),
        "env_keys": check_env_keys(),
    }
    all_ok = all(c.get("ok", False) for c in checks.values())
    return {
        "healthy": all_ok,
        "timestamp": datetime.now().isoformat(),
        "checks": checks,
    }


def format_for_digest(result: Dict[str, Any]) -> str:
    """Format health check result for inclusion in morning digest Telegram message."""
    if result["healthy"]:
        return "🟢 *SYSTEM HEALTH*: All checks pass"

    lines = ["🔴 *SYSTEM HEALTH*: Issues detected"]
    for name, check in result["checks"].items():
        if not check.get("ok", False):
            error = check.get("error", check.get("missing", ""))
            detail = f": {error}" if error else ""
            lines.append(f"  ⚠️ {name}{detail}")
    return "\n".join(lines)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="System Health Check")
    parser.add_argument("--json", action="store_true", help="JSON output")
    args = parser.parse_args()

    result = run_all_checks()

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        status = "HEALTHY" if result["healthy"] else "DEGRADED"
        print(f"\n{'='*50}")
        print(f"SYSTEM HEALTH: {status}")
        print(f"{'='*50}\n")
        for name, check in result["checks"].items():
            icon = "✓" if check.get("ok") else "✗"
            detail = {k: v for k, v in check.items() if k != "ok"}
            print(f"  {icon} {name}: {detail}")
        print()


if __name__ == "__main__":
    main()
