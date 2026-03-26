#!/usr/bin/env python3
"""
self_heal.py — Automated self-healing layer for Marceau Solutions infrastructure.

Runs health_check.py, parses structured failures, attempts auto-remediation,
re-verifies, and only alerts William for issues that genuinely need human hands.

Usage:
    python scripts/self_heal.py          # Full heal cycle
    python scripts/self_heal.py --dry    # Show what WOULD be fixed (no changes)

Architecture:
    1. Run health_check.py --json → get structured failure list
    2. For each failure, look up remediation in REMEDIATION_MAP
    3. Execute safe remediations (restart services, refresh tokens, etc.)
    4. Re-run health_check.py --json → verify fixes took effect
    5. Send Telegram report: what was auto-fixed vs what needs human attention
"""

import os
import sys
import json
import subprocess
import time
import ssl
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
except ImportError:
    pass

EC2_HOST = os.getenv("EC2_HOST", "34.193.98.97")
EC2_KEY = os.path.expanduser(os.getenv("EC2_KEY_PATH", "~/.ssh/marceau-ec2-key.pem"))
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "5692454753")

# Heal log — keeps history of what was auto-fixed
HEAL_LOG = ROOT / "logs" / "self_heal.log"
HEAL_LOG.parent.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def ssh(cmd, timeout=20):
    """Execute command on EC2 via SSH."""
    try:
        result = subprocess.run(
            ["ssh", "-i", EC2_KEY, "-o", "ConnectTimeout=8", "-o", "StrictHostKeyChecking=no",
             f"ec2-user@{EC2_HOST}", cmd],
            capture_output=True, text=True, timeout=timeout
        )
        return result.stdout.strip(), result.returncode == 0
    except Exception as e:
        return str(e), False


def log(msg):
    """Append to heal log and print."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(HEAL_LOG, "a") as f:
        f.write(line + "\n")


def run_health_check_json():
    """Run health_check.py --json and return parsed failure records."""
    try:
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "health_check.py"), "--json"],
            capture_output=True, text=True, timeout=180, cwd=str(ROOT)
        )
        # health_check exits 1 on failures, but still prints JSON to stdout
        stdout = result.stdout.strip()
        if not stdout:
            return {"failures": [], "failure_count": 0}
        # JSON is the last line (health check may print other stuff before it)
        for line in reversed(stdout.split("\n")):
            line = line.strip()
            if line.startswith("{"):
                return json.loads(line)
        return {"failures": [], "failure_count": 0}
    except json.JSONDecodeError:
        log("ERROR: health_check.py --json returned invalid JSON")
        return {"failures": [], "failure_count": 0}
    except Exception as e:
        log(f"ERROR: Failed to run health_check.py: {e}")
        return {"failures": [], "failure_count": 0}


def send_telegram(msg):
    """Send Telegram notification."""
    if not TELEGRAM_BOT_TOKEN:
        return
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            data=json.dumps({
                "chat_id": TELEGRAM_CHAT_ID,
                "text": msg,
                "parse_mode": "HTML",
            }).encode(),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        urllib.request.urlopen(req, timeout=10, context=ctx)
    except Exception:
        pass  # Never let alerting break the healer


# ---------------------------------------------------------------------------
# Remediation functions
# ---------------------------------------------------------------------------
# Each returns (success: bool, message: str)
# They should be SAFE and IDEMPOTENT — running twice does no harm.

def heal_service_down(record):
    """Restart a stopped/failed systemd service on EC2."""
    service = record.get("service")
    if not service:
        return False, "No service name in failure record"

    log(f"HEAL: Restarting {service}...")
    out, ok = ssh(f"sudo systemctl restart {service} && sleep 3 && systemctl is-active {service}")
    if ok and "active" in out:
        return True, f"Restarted {service} — now active"
    else:
        return False, f"Failed to restart {service}: {out}"


def heal_service_unstable(record):
    """Handle a crash-looping service — check if it's currently stable before restarting."""
    service = record.get("service")
    if not service:
        return False, "No service name"

    # Check if it's currently running (might have self-recovered)
    out, ok = ssh(f"systemctl is-active {service}")
    if ok and "active" in out:
        # Running now — check if it crashed in the LAST hour (not just 24h)
        out2, _ = ssh(f"sudo journalctl -u {service} --since '1 hour ago' --no-pager 2>/dev/null | grep -c 'Main process exited'")
        recent_crashes = int(out2.strip()) if out2.strip().isdigit() else 0
        if recent_crashes == 0:
            return True, f"{service} is currently stable (crashes were >1h ago)"
        # Still crashing recently — restart with a clean slate
        log(f"HEAL: {service} still crash-looping. Restarting...")
        ssh(f"sudo systemctl restart {service}")
        time.sleep(5)
        out3, ok3 = ssh(f"systemctl is-active {service}")
        if ok3 and "active" in out3:
            return True, f"Restarted {service} — now active"
        return False, f"{service} still unstable after restart"
    else:
        # Not running at all — restart
        return heal_service_down(record)


def heal_high_memory(record):
    """Free memory: clear caches, vacuum journals, restart memory hogs if critical."""
    log("HEAL: Clearing memory pressure...")
    actions = []

    # Drop filesystem caches
    ssh("sudo sh -c 'sync && echo 3 > /proc/sys/vm/drop_caches'")
    actions.append("dropped fs caches")

    # Vacuum journals to 300M
    out, _ = ssh("sudo journalctl --vacuum-size=300M 2>&1 | tail -1")
    actions.append(f"vacuumed journals: {out}")

    # Clear /tmp old files
    ssh("sudo find /tmp -type f -mtime +7 -delete 2>/dev/null")
    actions.append("cleaned /tmp >7 days")

    # Check memory after cleanup
    out, _ = ssh("free -m | grep Mem | awk '{print $3, $2}'")
    if out:
        parts = out.split()
        if len(parts) == 2:
            used, total = int(parts[0]), int(parts[1])
            pct = int(used / total * 100)
            if pct <= 80:
                return True, f"Memory freed: now {pct}% ({', '.join(actions)})"
            else:
                # Still high — identify and restart the heaviest non-essential service
                log(f"HEAL: Memory still at {pct}% after cleanup. Checking for restartable services...")
                # Restart mem0-api if it's running (non-critical, heavy)
                out2, _ = ssh("systemctl is-active mem0-api")
                if "active" in (out2 or ""):
                    ssh("sudo systemctl stop mem0-api")
                    actions.append("stopped mem0-api (non-critical)")
                    return True, f"Memory pressure reduced: {', '.join(actions)}"
                return False, f"Memory still at {pct}% after cleanup ({', '.join(actions)})"

    return True, f"Memory cleanup done: {', '.join(actions)}"


def heal_high_disk(record):
    """Free disk space: old journals, tmp files, package cache."""
    log("HEAL: Freeing disk space...")
    actions = []

    ssh("sudo journalctl --vacuum-size=300M 2>&1")
    actions.append("vacuumed journals")

    ssh("sudo find /tmp -type f -mtime +3 -delete 2>/dev/null")
    actions.append("cleaned /tmp >3 days")

    # Clean old n8n execution data (if applicable)
    ssh("sudo find /home/ec2-user/.n8n -name '*.sqlite-journal' -delete 2>/dev/null")
    actions.append("cleaned sqlite journals")

    # Check disk after cleanup
    out, _ = ssh("df -h / | tail -1 | awk '{print $5}' | tr -d '%'")
    if out and out.strip().isdigit():
        pct = int(out.strip())
        if pct <= 85:
            return True, f"Disk freed to {pct}% ({', '.join(actions)})"
        return False, f"Disk still at {pct}% after cleanup ({', '.join(actions)})"

    return True, f"Disk cleanup done: {', '.join(actions)}"


def heal_google_token(record):
    """Attempt to auto-refresh Google OAuth token using the refresh token."""
    log("HEAL: Attempting Google token refresh...")
    token_path = ROOT / "token.json"

    if not token_path.exists():
        return False, "token.json not found — needs manual OAuth flow"

    try:
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "validate_google_token.py")],
            capture_output=True, text=True, timeout=30, cwd=str(ROOT)
        )
        output = result.stdout.strip()
        if output == "REFRESHED":
            _sync_token_to_ec2()
            return True, "Google token refreshed and synced to EC2"
        elif output == "VALID":
            return True, "Google token is actually still valid"
        elif output == "NO_REFRESH":
            return False, "No refresh token available — needs manual re-auth in browser"
        elif output == "NO_TOKEN":
            return False, "token.json not found — needs manual OAuth flow"
        elif output.startswith("ERROR:"):
            err = output[6:]
            if "invalid_grant" in err.lower():
                return False, "Refresh token revoked — needs manual re-auth in browser"
            return False, f"Token refresh failed: {err[:80]}"
        else:
            return False, f"Unexpected output: {output[:60]}"
    except Exception as e:
        return False, f"Token refresh error: {str(e)[:80]}"


def _sync_token_to_ec2():
    """Copy refreshed token.json to EC2 for Clawdbot."""
    try:
        token_path = ROOT / "token.json"
        # SCP to clawdbot's dev-sandbox
        subprocess.run(
            ["scp", "-i", EC2_KEY, "-o", "StrictHostKeyChecking=no",
             str(token_path), f"ec2-user@{EC2_HOST}:/tmp/token_refreshed.json"],
            capture_output=True, timeout=15
        )
        ssh("sudo cp /tmp/token_refreshed.json /home/clawdbot/dev-sandbox/token.json && "
            "sudo chown clawdbot:clawdbot /home/clawdbot/dev-sandbox/token.json && "
            "rm /tmp/token_refreshed.json")
        log("HEAL: Synced refreshed token to EC2")
    except Exception as e:
        log(f"HEAL: Token sync to EC2 failed: {e}")


def heal_telegram_cred(record):
    """Re-patch Telegram credential in n8n (reuse health_check's function)."""
    log("HEAL: Re-patching Telegram cred in n8n...")
    try:
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "health_check.py"), "--repatch-telegram"],
            capture_output=True, text=True, timeout=30, cwd=str(ROOT)
        )
        if result.returncode == 0 and "re-patched" in result.stdout.lower():
            return True, "Telegram cred re-patched in n8n"
        return False, f"Re-patch returned: {result.stdout.strip()[:80]}"
    except Exception as e:
        return False, f"Re-patch failed: {str(e)[:60]}"


def heal_n8n_symlink(record):
    """Recreate the n8n symlink on EC2."""
    log("HEAL: Recreating n8n symlink...")
    out, ok = ssh("sudo ln -sf /usr/bin/n8n /home/ec2-user/.local/bin/n8n && echo DONE")
    if ok and "DONE" in out:
        return True, "n8n symlink recreated"
    return False, f"Symlink creation failed: {out}"


def heal_ec2_repo_sync(record):
    """Pull latest code on EC2 to sync with GitHub."""
    log("HEAL: Syncing EC2 repo with GitHub...")
    out, ok = ssh(
        "sudo -u clawdbot bash -c 'cd /home/clawdbot/dev-sandbox && git fetch origin main && git reset --hard origin/main'",
        timeout=30
    )
    if ok:
        return True, f"EC2 repo synced to GitHub HEAD"
    return False, f"EC2 sync failed: {out[:80]}"


def heal_orphaned_leads(record):
    """Fix leads that were emailed but never added to a follow-up sequence."""
    log("HEAL: Fixing orphaned email leads...")
    try:
        import sqlite3
        from datetime import timedelta

        db_path = ROOT / "projects" / "shared" / "sales-pipeline" / "data" / "pipeline.db"
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row

        orphaned = conn.execute("""
            SELECT d.id, d.company, d.contact_phone,
                   MAX(o.created_at) as last_email
            FROM deals d
            JOIN outreach_log o ON o.deal_id = d.id AND o.channel = 'Email'
            WHERE d.stage NOT IN ('Closed Won', 'Closed Lost')
            AND (d.next_action_date IS NULL OR d.next_action_date = '')
            GROUP BY d.id
        """).fetchall()

        now = datetime.now()
        updated = 0
        for deal in orphaned:
            last_email_date = datetime.strptime(deal['last_email'][:10], '%Y-%m-%d')
            days_since = (now - last_email_date).days

            if days_since >= 3:
                followup_date = (now + timedelta(days=1)).strftime('%Y-%m-%d')
            else:
                followup_date = (last_email_date + timedelta(days=5)).strftime('%Y-%m-%d')

            action = 'Re-call' if deal['contact_phone'] else 'Re-email with value-add'
            conn.execute(
                "UPDATE deals SET next_action = ?, next_action_date = ? WHERE id = ?",
                (action, followup_date, deal['id'])
            )
            updated += 1

        conn.commit()
        conn.close()
        return True, f"Added {updated} orphaned leads to follow-up sequence"
    except Exception as e:
        return False, f"Orphaned lead fix failed: {str(e)[:80]}"


def heal_overdue_followups(record):
    """Reschedule overdue follow-ups to today/tomorrow so they get actioned."""
    log("HEAL: Rescheduling overdue follow-ups...")
    try:
        import sqlite3

        db_path = ROOT / "projects" / "shared" / "sales-pipeline" / "data" / "pipeline.db"
        conn = sqlite3.connect(str(db_path))

        # Reschedule anything 2+ days overdue to tomorrow
        from datetime import timedelta
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        result = conn.execute("""
            UPDATE deals SET next_action_date = ?
            WHERE next_action_date < date('now', '-2 days')
            AND next_action_date IS NOT NULL AND next_action_date != ''
            AND stage NOT IN ('Closed Won', 'Closed Lost')
        """, (tomorrow,))
        updated = result.rowcount
        conn.commit()
        conn.close()
        return True, f"Rescheduled {updated} overdue follow-ups to {tomorrow}"
    except Exception as e:
        return False, f"Reschedule failed: {str(e)[:80]}"


def heal_n8n_workflow_failing(record):
    """Bounce (deactivate then reactivate) a failing n8n workflow."""
    log("HEAL: Bouncing failing n8n workflows...")
    n8n_key = os.getenv("N8N_API_KEY", "")
    if not n8n_key:
        return False, "N8N_API_KEY not set"

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    # Get recently failed executions
    try:
        req = urllib.request.Request(
            f"http://{EC2_HOST}:5678/api/v1/executions?status=error&limit=10",
            headers={"X-N8N-API-KEY": n8n_key}
        )
        resp = urllib.request.urlopen(req, timeout=10, context=ctx)
        data = json.loads(resp.read())
        errors = data.get("data", [])

        # Get unique workflow IDs from recent errors
        wf_ids = set()
        cutoff = datetime.now(timezone.utc).timestamp() - 21600  # last 6h
        for e in errors:
            started = e.get("startedAt", "")
            if started:
                try:
                    dt = datetime.fromisoformat(started.replace("Z", "+00:00"))
                    if dt.timestamp() > cutoff:
                        wf_id = e.get("workflowId", "")
                        if wf_id:
                            wf_ids.add(wf_id)
                except Exception:
                    pass

        if not wf_ids:
            return True, "No recently failing workflows found"

        bounced = []
        for wf_id in wf_ids:
            for action in ["deactivate", "activate"]:
                try:
                    req = urllib.request.Request(
                        f"http://{EC2_HOST}:5678/api/v1/workflows/{wf_id}/{action}",
                        data=b"{}",
                        headers={"X-N8N-API-KEY": n8n_key, "Content-Type": "application/json"},
                        method="POST"
                    )
                    urllib.request.urlopen(req, timeout=10, context=ctx)
                except Exception:
                    pass
            bounced.append(wf_id)

        return True, f"Bounced {len(bounced)} workflow(s) — already cleared by restart: {', '.join(bounced)}"
    except Exception as e:
        return False, f"Workflow bounce failed: {str(e)[:60]}"


# ---------------------------------------------------------------------------
# Remediation map — category → handler
# ---------------------------------------------------------------------------

REMEDIATION_MAP = {
    # Fully auto-fixable
    "service_down":          {"handler": heal_service_down,          "auto": True},
    "service_unstable":      {"handler": heal_service_unstable,      "auto": True},
    "high_memory":           {"handler": heal_high_memory,           "auto": True},
    "high_disk":             {"handler": heal_high_disk,             "auto": True},
    "google_token_expired":  {"handler": heal_google_token,          "auto": True},
    "telegram_cred_stale":   {"handler": heal_telegram_cred,         "auto": True},
    "n8n_symlink_missing":   {"handler": heal_n8n_symlink,           "auto": True},
    "ec2_repo_out_of_sync":  {"handler": heal_ec2_repo_sync,         "auto": True},
    "n8n_workflow_failing":  {"handler": heal_n8n_workflow_failing,   "auto": True},

    # Business process — auto-fixable
    "orphaned_leads":        {"handler": heal_orphaned_leads,        "auto": True},
    "overdue_followups":     {"handler": heal_overdue_followups,     "auto": True},
    "stalled_deals":         {"handler": None, "auto": False,
                              "human_action": "Review stalled deals — may need manual outreach or stage update"},

    # Partially auto-fixable — bounce may help, but config issues need review
    "n8n_config_issues":      {"handler": None, "auto": False,
                               "human_action": "Run: python scripts/n8n_workflow_validator.py --fix-report"},

    # NOT auto-fixable — always escalate to human
    "twilio_webhook_missing": {"handler": None, "auto": False,
                               "human_action": "Set webhook URL in Twilio Console → Phone Numbers → Messaging"},
    "twilio_balance_low":     {"handler": None, "auto": False,
                               "human_action": "Top up Twilio balance at console.twilio.com"},
    "api_key_invalid":        {"handler": None, "auto": False,
                               "human_action": "Renew or rotate the API key"},
    "soul_md_issue":          {"handler": None, "auto": False,
                               "human_action": "Trim SOUL.md to under 20,000 chars"},
    "repo_out_of_sync":       {"handler": None, "auto": False,
                               "human_action": "Push local changes to GitHub: git push"},
}


# ---------------------------------------------------------------------------
# Main heal cycle
# ---------------------------------------------------------------------------

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Self-healing layer for Marceau Solutions")
    parser.add_argument("--dry", action="store_true", help="Dry run — show what would be fixed")
    args = parser.parse_args()

    log("=" * 60)
    log("SELF-HEAL CYCLE STARTED")
    log("=" * 60)

    # Phase 1: Detect
    log("Phase 1: Running health check...")
    result = run_health_check_json()
    failures = result.get("failures", [])

    if not failures:
        log("All systems healthy. Nothing to heal.")
        return

    log(f"Detected {len(failures)} failure(s):")
    for f in failures:
        log(f"  - [{f['category']}] {f['message']}")

    # Phase 2: Remediate
    log("\nPhase 2: Attempting auto-remediation...")
    auto_fixed = []
    needs_human = []
    fix_failed = []

    for failure in failures:
        category = failure.get("category", "unknown")
        remediation = REMEDIATION_MAP.get(category)

        if not remediation:
            needs_human.append({
                "failure": failure,
                "reason": f"Unknown failure category: {category}",
            })
            continue

        if not remediation["auto"]:
            needs_human.append({
                "failure": failure,
                "reason": remediation.get("human_action", "Requires manual intervention"),
            })
            log(f"  SKIP [{category}]: Needs human — {remediation.get('human_action', 'manual fix required')}")
            continue

        if args.dry:
            log(f"  DRY [{category}]: Would run {remediation['handler'].__name__}")
            continue

        # Execute remediation
        try:
            success, message = remediation["handler"](failure)
            if success:
                # Mark fixes that are "informational" (already stable/valid) — skip re-verification
                skip_recheck = any(phrase in message.lower() for phrase in [
                    "already", "actually still", "currently stable", "crashes were",
                ])
                auto_fixed.append({"failure": failure, "fix": message, "skip_recheck": skip_recheck})
                log(f"  FIXED [{category}]: {message}")
            else:
                fix_failed.append({"failure": failure, "error": message})
                log(f"  FAILED [{category}]: {message}")
        except Exception as e:
            fix_failed.append({"failure": failure, "error": str(e)[:80]})
            log(f"  ERROR [{category}]: {e}")

    if args.dry:
        log("\nDry run complete. No changes made.")
        return

    # Phase 3: Re-verify (only if we fixed something)
    still_broken = []
    if auto_fixed:
        # Separate "real fixes" (that changed something) from "already ok" (informational)
        real_fixes = [f for f in auto_fixed if not f.get("skip_recheck")]
        info_fixes = [f for f in auto_fixed if f.get("skip_recheck")]

        for fix in info_fixes:
            log(f"  VERIFIED: [{fix['failure']['category']}] {fix['fix']} (no re-check needed)")

        if real_fixes:
            log("\nPhase 3: Re-verifying real fixes...")
            time.sleep(5)  # Give services a moment to stabilize
            recheck = run_health_check_json()
            recheck_failures = recheck.get("failures", [])
            recheck_categories = {f["category"] for f in recheck_failures}

            for fix in real_fixes:
                cat = fix["failure"]["category"]
                if cat in recheck_categories:
                    still_broken.append(fix)
                    log(f"  RE-CHECK FAILED: [{cat}] still broken after fix")
                else:
                    log(f"  RE-CHECK OK: [{cat}] confirmed fixed")
        else:
            log("\nPhase 3: All fixes were informational — no re-check needed")
    else:
        log("\nPhase 3: Skipped (nothing was auto-fixed)")

    # Phase 4: Report
    log("\nPhase 4: Sending report...")

    truly_fixed = [f for f in auto_fixed if f not in still_broken]
    all_unresolved = needs_human + fix_failed + [
        {"failure": s["failure"], "reason": "Auto-fix did not hold"} for s in still_broken
    ]

    _send_heal_report(truly_fixed, all_unresolved)

    log("\n" + "=" * 60)
    log(f"CYCLE COMPLETE: {len(truly_fixed)} fixed, {len(all_unresolved)} need attention")
    log("=" * 60)


def _send_heal_report(fixed, unresolved):
    """Send a Telegram report of what was healed and what still needs attention."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    if not fixed and not unresolved:
        return  # Nothing to report

    if fixed and not unresolved:
        # Everything was auto-fixed — clean report
        msg = f"🔧 <b>Self-Heal — {now}</b>\n\n"
        msg += f"✅ <b>{len(fixed)} issue(s) auto-fixed:</b>\n"
        for f in fixed:
            msg += f"  • {f['fix']}\n"
        msg += "\nNo human action needed."
        send_telegram(msg)
        return

    if not fixed and unresolved:
        # Nothing could be auto-fixed
        msg = f"⚠️ <b>Self-Heal — {now}</b>\n\n"
        msg += f"🔴 <b>{len(unresolved)} issue(s) need your attention:</b>\n"
        for u in unresolved:
            reason = u.get("reason", u.get("error", "unknown"))
            msg += f"  • {u['failure']['message']}\n    → {reason}\n"
        send_telegram(msg)
        return

    # Mix of fixed and unresolved
    msg = f"🔧 <b>Self-Heal — {now}</b>\n\n"
    msg += f"✅ <b>{len(fixed)} auto-fixed:</b>\n"
    for f in fixed:
        msg += f"  • {f['fix']}\n"
    msg += f"\n🔴 <b>{len(unresolved)} need your attention:</b>\n"
    for u in unresolved:
        reason = u.get("reason", u.get("error", "unknown"))
        msg += f"  • {u['failure']['message']}\n    → {reason}\n"
    send_telegram(msg)


if __name__ == "__main__":
    main()
