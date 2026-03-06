#!/usr/bin/env python3
"""
health_check.py — Company on a Laptop: One-command system health check

Checks everything: EC2 services, n8n workflows, Clawdbot, disk, leads, revenue.

Usage:
    python scripts/health_check.py          # Full check
    python scripts/health_check.py --fast   # Skip SSH checks (local only)
"""

import os
import sys
import json
import subprocess
import argparse
import urllib.request
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

# Load .env — never hardcode secrets
try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
except ImportError:
    pass

EC2_HOST = os.getenv("EC2_HOST", "34.193.98.97")
EC2_KEY = os.path.expanduser(os.getenv("EC2_KEY_PATH", "~/.ssh/marceau-ec2-key.pem"))
N8N_API_KEY = os.getenv("N8N_API_KEY", "")

GREEN = "\033[32m"
RED = "\033[31m"
YELLOW = "\033[33m"
BOLD = "\033[1m"
RESET = "\033[0m"
GOLD = "\033[33m"

def ok(msg): return f"{GREEN}✓{RESET} {msg}"
def fail(msg): return f"{RED}✗{RESET} {msg}"
def warn(msg): return f"{YELLOW}⚠{RESET} {msg}"
def header(msg): return f"\n{BOLD}{GOLD}{'━' * 50}{RESET}\n{BOLD}  {msg}{RESET}\n{'━' * 50}"


def ssh(cmd, timeout=15):
    try:
        result = subprocess.run(
            ["ssh", "-i", EC2_KEY, "-o", "ConnectTimeout=8", "-o", "StrictHostKeyChecking=no",
             f"ec2-user@{EC2_HOST}", cmd],
            capture_output=True, text=True, timeout=timeout
        )
        return result.stdout.strip(), result.returncode == 0
    except Exception as e:
        return str(e), False


def n8n_api(path):
    try:
        req = urllib.request.Request(
            f"http://{EC2_HOST}:5678/api/v1/{path}",
            headers={"X-N8N-API-KEY": N8N_API_KEY}
        )
        resp = urllib.request.urlopen(req, timeout=8)
        return json.loads(resp.read())
    except Exception:
        return None


def check_ec2_services():
    print(header("EC2 SERVICES"))
    services = {
        "n8n": "Workflow automation",
        "clawdbot": "AI assistant (Telegram)",
        "mem0-api": "Shared agent memory",
        "fitai": "Fitness influencer platform",
        "voice-api": "Voice AI API",
    }
    out, success = ssh("systemctl is-active " + " ".join(services.keys()) + " 2>/dev/null")
    statuses = out.split("\n") if out else []

    for i, (svc, desc) in enumerate(services.items()):
        status = statuses[i].strip() if i < len(statuses) else "unknown"
        if status == "active":
            print(f"  {ok(svc)}: {desc}")
        else:
            print(f"  {fail(svc)}: {desc} [{status}]")


def check_disk_memory():
    print(header("EC2 RESOURCES"))
    out, _ = ssh("df -h / | tail -1 && free -m | grep Mem")
    if out:
        lines = out.split("\n")
        if lines:
            parts = lines[0].split()
            if len(parts) >= 5:
                used_pct = int(parts[4].replace("%", ""))
                color = RED if used_pct > 85 else YELLOW if used_pct > 75 else GREEN
                print(f"  Disk: {color}{parts[2]}/{parts[1]} ({parts[4]}){RESET}")
        if len(lines) > 1:
            mem = lines[1].split()
            if len(mem) >= 3:
                total, used = int(mem[1]), int(mem[2])
                pct = int(used / total * 100)
                color = RED if pct > 80 else YELLOW if pct > 65 else GREEN
                print(f"  Memory: {color}{used}M/{total}M ({pct}%){RESET}")

    out, _ = ssh("sudo journalctl --disk-usage 2>/dev/null | grep 'take up'")
    if out:
        print(f"  Journal: {out.strip()}")


def check_n8n():
    print(header("N8N WORKFLOWS"))
    data = n8n_api("workflows?limit=200")
    if not data:
        print(f"  {fail('n8n API unreachable')}")
        return

    workflows = data.get("data", [])
    active = [w for w in workflows if w.get("active")]
    inactive = [w for w in workflows if not w.get("active")]

    print(f"  {ok(f'{len(active)} active workflows')}  |  {len(inactive)} inactive")

    # Check key workflows
    key_workflows = {
        "1wS9VvXIt95BrR9V": "PT Payment Welcome",
        "aBxCj48nGQVLRRnq": "PT Monday Check-in",
        "5GXwor2hHuij614l": "WebDev Payment Welcome",
        "G14Mb6lpeFZVYGwa": "SMS Response Handler",
        "QhDtNagsZFUrKFsG": "n8n Health Check",
        "BsoplLFe1brLCBof": "GitHub → Telegram",
        "Ob7kiVvCnmDHAfNW": "Self-Annealing Error Handler",
    }
    wf_map = {w["id"]: w for w in workflows}
    print()
    for wf_id, name in key_workflows.items():
        wf = wf_map.get(wf_id)
        if not wf:
            print(f"  {fail(name)}: NOT FOUND")
        elif wf.get("active"):
            print(f"  {ok(name)}")
        else:
            print(f"  {warn(name)}: inactive")


def check_clawdbot():
    print(header("CLAWDBOT"))
    out, success = ssh("sudo -u clawdbot env PATH=/home/clawdbot/app/node_modules/.bin:/usr/local/bin:$PATH clawdbot sessions 2>/dev/null | grep 'agent:main:main'")
    if success and out:
        parts = out.split()
        tokens_col = next((p for p in parts if "/" in p and "k" in p), None)
        if tokens_col:
            used, total = tokens_col.split("/")
            used_k = float(used.replace("k", ""))
            total_k = float(total.replace("k", "").replace("(", ""))
            pct = int(used_k / total_k * 100)
            color = RED if pct > 80 else YELLOW if pct > 60 else GREEN
            print(f"  Context: {color}{tokens_col} ({pct}%){RESET}")
        else:
            print(f"  {ok('Session active, context fresh')}")
    else:
        print(f"  {warn('Could not read session info')}")

    out, _ = ssh("sudo journalctl -u clawdbot --since '24 hours ago' --no-pager 2>/dev/null | grep -c 'Main process exited'")
    crashes = int(out.strip()) if out.strip().isdigit() else 0
    if crashes == 0:
        print(f"  {ok('0 crashes in last 24h')}")
    else:
        print(f"  {warn(f'{crashes} crash(es) in last 24h')}")


def check_local_env():
    print(header("LOCAL ENVIRONMENT"))
    env_path = Path(__file__).parent.parent / ".env"
    required_keys = [
        "ANTHROPIC_API_KEY", "TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN",
        "STRIPE_SECRET_KEY", "OPENAI_API_KEY", "GOOGLE_SHEETS_SPREADSHEET_ID",
        "N8N_API_KEY",
    ]
    if env_path.exists():
        content = env_path.read_text()
        for key in required_keys:
            if key + "=" in content and f"{key}=\n" not in content:
                print(f"  {ok(key)}")
            else:
                print(f"  {warn(key)}: missing or empty")
    else:
        print(f"  {fail('.env not found')}")

    # Check git status
    try:
        result = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True,
                                cwd=str(Path(__file__).parent.parent))
        changed = len(result.stdout.strip().split("\n")) if result.stdout.strip() else 0
        if changed == 0:
            print(f"  {ok('Git: clean')}")
        else:
            print(f"  {warn(f'Git: {changed} uncommitted file(s)')}")
    except Exception:
        pass


def check_business_ops():
    print(header("BUSINESS OPERATIONS"))

    # PT Coaching
    print(f"  PT Coaching:")
    print(f"    Stripe: https://dashboard.stripe.com/customers")
    print(f"    Tracker: https://docs.google.com/spreadsheets/d/1ZkzOY9SxMcDrDtq69rDcQ0ZMd9Ss8YaE-qeJmS7FuBA")
    print(f"    Calendly: https://calendly.com/wmarceau/30min")

    # Web Dev
    print(f"  Web Dev:")
    print(f"    Client Tracker: https://docs.google.com/spreadsheets/d/1gWobdkQsa8XCr7xEOXTFJ3t45e2K54bfxQpYLkCqN7Q")

    # Client lead sheets
    print(f"  Lead Sheets:")
    print(f"    HVAC: https://docs.google.com/spreadsheets/d/1Lli3vWKErLR2eUo_623eJbyfohqhaqhKcWndss74eTM")
    print(f"    Square Foot: https://docs.google.com/spreadsheets/d/1Gk-y0G9x30zJnB7YDj1AYmcmaM_Z08pxkw1lodp_8i8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fast", action="store_true", help="Skip SSH checks")
    args = parser.parse_args()

    print(f"\n{BOLD}{GOLD}  MARCEAU SOLUTIONS — SYSTEM HEALTH{RESET}")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M')} | Company on a Laptop\n")

    if not args.fast:
        check_ec2_services()
        check_disk_memory()
        check_n8n()
        check_clawdbot()

    check_local_env()
    check_business_ops()

    print(f"\n{'━' * 50}\n")


if __name__ == "__main__":
    main()
