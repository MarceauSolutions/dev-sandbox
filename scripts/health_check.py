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
from datetime import datetime, timezone
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
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "5692454753")

GREEN = "\033[32m"
RED = "\033[31m"
YELLOW = "\033[33m"
BOLD = "\033[1m"
RESET = "\033[0m"
GOLD = "\033[33m"

FAILURES = []

def ok(msg): return f"{GREEN}✓{RESET} {msg}"
def fail(msg):
    FAILURES.append(msg)
    return f"{RED}✗{RESET} {msg}"
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

    # Check n8n restart count in last 24h (unexpected restarts = instability)
    out, _ = ssh("sudo journalctl -u n8n --since '24 hours ago' --no-pager 2>/dev/null | grep -c 'Started n8n.service'")
    n8n_restarts = int(out.strip()) if out.strip().isdigit() else 0
    if n8n_restarts <= 1:
        print(f"  {ok('n8n stable')}: {n8n_restarts} restart(s) in 24h")
    elif n8n_restarts <= 3:
        print(f"  {warn('n8n restarted')}: {n8n_restarts} restart(s) in 24h")
    else:
        print(f"  {fail('n8n unstable')}: {n8n_restarts} restart(s) in 24h")


def check_disk_memory():
    print(header("EC2 RESOURCES"))
    out, _ = ssh("df -h / | tail -1 && free -m | grep Mem")
    if out:
        lines = out.split("\n")
        if lines:
            parts = lines[0].split()
            if len(parts) >= 5:
                used_pct = int(parts[4].replace("%", ""))
                label = f"Disk: {parts[2]}/{parts[1]} ({parts[4]})"
                if used_pct > 85:
                    print(f"  {fail(label)}")
                else:
                    color = YELLOW if used_pct > 75 else GREEN
                    print(f"  {color}{label}{RESET}")
        if len(lines) > 1:
            mem = lines[1].split()
            if len(mem) >= 3:
                total, used = int(mem[1]), int(mem[2])
                pct = int(used / total * 100)
                label = f"Memory: {used}M/{total}M ({pct}%)"
                if pct > 80:
                    print(f"  {fail(label)}")
                else:
                    color = YELLOW if pct > 65 else GREEN
                    print(f"  {color}{label}{RESET}")

    # CPU load average (1min)
    out, _ = ssh("uptime | awk -F'load average:' '{print $2}' | awk '{print $1}'")
    if out:
        load = out.strip().rstrip(",")
        try:
            load_f = float(load)
            label = f"CPU load: {load:.2f}"
            if load_f > 2.0:
                print(f"  {fail(label)}")
            elif load_f > 1.0:
                print(f"  {YELLOW}{label}{RESET}")
            else:
                print(f"  {GREEN}{label}{RESET}")
        except ValueError:
            pass

    out, _ = ssh("sudo journalctl --disk-usage 2>/dev/null | grep 'take up'")
    if out:
        print(f"  Journal: {out.strip()}")


def check_domains():
    """Check that external-facing domains are reachable."""
    print(header("EXTERNAL DOMAINS"))
    domains = {
        "n8n.marceausolutions.com": "n8n automation",
        "api.marceausolutions.com": "Python bridge API",
        "fitai.marceausolutions.com": "Fitness influencer platform",
        "marceausolutions.com": "Marceau Solutions website",
        "swfloridacomfort.com": "HVAC client website",
        "www.boabfit.com": "BoabFit client website",
    }
    import ssl
    for domain, desc in domains.items():
        try:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            url = f"https://{domain}"
            req = urllib.request.Request(url, headers={"User-Agent": "HealthCheck/1.0"})
            with urllib.request.urlopen(req, timeout=10, context=ctx) as r:
                code = r.status
                if code < 500:
                    print(f"  {ok(domain)}: {desc} [{code}]")
                else:
                    print(f"  {fail(domain)}: {desc} [HTTP {code}]")
        except Exception as e:
            err = str(e)[:60]
            print(f"  {fail(domain)}: {desc} [{err}]")


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

    # Check key workflows — infrastructure + revenue-critical business workflows
    key_workflows = {
        # Infrastructure
        "Ob7kiVvCnmDHAfNW": "Self-Annealing Error Handler",
        "QhDtNagsZFUrKFsG": "n8n Health Check",
        "BsoplLFe1brLCBof": "GitHub → Telegram",
        "Hz05R5SeJGb4VNCl": "Daily Operations Digest",
        # PT Coaching
        "1wS9VvXIt95BrR9V": "PT Payment Welcome",
        "aBxCj48nGQVLRRnq": "PT Monday Check-in",
        "uKjqRexDIheaDJJH": "PT Cancellation Exit",
        "89XxmBQMEej15nak": "Fitness SMS Outreach",
        # Lead capture
        "hgInaJCLffLFBX1G": "Lead Magnet Capture",
        "WHFIE3Ej7Y3SCtHk": "Website Lead Capture",
        # Web Dev
        "5GXwor2hHuij614l": "WebDev Payment Welcome",
        "N8HIFsZdE5Go7Lky": "WebDev Monthly Checkin",
        # Stripe
        "QMWkhAb8SWMSImc4": "Stripe Payment Failed",
        "unF3M3IfnGPqV0xU": "Stripe Invoice Paid (Renewals)",
        # SMS
        "G14Mb6lpeFZVYGwa": "SMS Response Handler",
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
                print(f"  {fail(key)}: missing or empty")
    else:
        print(f"  {fail('.env not found')}")

    # Check Twilio balance (SMS fails silently when account runs low)
    twilio_sid = os.getenv("TWILIO_ACCOUNT_SID", "")
    twilio_token = os.getenv("TWILIO_AUTH_TOKEN", "")
    if twilio_sid and twilio_token:
        try:
            import base64, ssl as _ssl
            creds = base64.b64encode(f"{twilio_sid}:{twilio_token}".encode()).decode()
            ctx = _ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = _ssl.CERT_NONE
            req = urllib.request.Request(
                f"https://api.twilio.com/2010-04-01/Accounts/{twilio_sid}/Balance.json",
                headers={"Authorization": f"Basic {creds}"}
            )
            resp = urllib.request.urlopen(req, timeout=8, context=ctx)
            bal = json.loads(resp.read())
            balance = float(bal.get("balance", 0))
            if balance < 5:
                print(f"  {fail(f'Twilio balance: ${balance:.2f} — CRITICAL, SMS will fail')}")
            elif balance < 10:
                print(f"  {warn(f'Twilio balance: ${balance:.2f} — low, top up soon')}")
            else:
                print(f"  {ok(f'Twilio balance: ${balance:.2f}')}")
        except Exception:
            print(f"  {warn('Twilio balance: check failed')}")

    # Check git status (uncommitted + unpushed)
    try:
        repo = str(Path(__file__).parent.parent)
        result = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, cwd=repo)
        changed = len(result.stdout.strip().split("\n")) if result.stdout.strip() else 0

        ahead = subprocess.run(
            ["git", "rev-list", "--count", "@{u}..HEAD"],
            capture_output=True, text=True, cwd=repo
        )
        unpushed = int(ahead.stdout.strip()) if ahead.returncode == 0 and ahead.stdout.strip().isdigit() else 0

        if changed == 0 and unpushed == 0:
            print(f"  {ok('Git: clean, fully pushed')}")
        else:
            parts = []
            if changed:
                parts.append(f"{changed} uncommitted")
            if unpushed:
                parts.append(f"{unpushed} unpushed commit(s)")
            print(f"  {warn('Git: ' + ', '.join(parts))}")
    except Exception:
        pass


def check_stripe_webhooks():
    """Verify all expected Stripe webhooks are registered and enabled."""
    print(header("STRIPE WEBHOOKS"))
    stripe_key = os.getenv("STRIPE_SECRET_KEY", "")
    if not stripe_key:
        print(f"  {warn('STRIPE_SECRET_KEY not set — skipping')}")
        return

    expected = {
        "stripe-payment-welcome": "checkout.session.completed",
        "stripe-webdev-payment": "checkout.session.completed",
        "stripe-cancellation": "customer.subscription.deleted",
        "stripe-digital-delivery": "checkout.session.completed",
        "stripe-payment-failed": "invoice.payment_failed",
        "stripe-invoice-paid": "invoice.paid",
    }

    try:
        req = urllib.request.Request(
            "https://api.stripe.com/v1/webhook_endpoints?limit=20",
            headers={"Authorization": f"Bearer {stripe_key}"}
        )
        import ssl
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        resp = urllib.request.urlopen(req, timeout=10, context=ctx)
        data = json.loads(resp.read())
        endpoints = data.get("data", [])

        registered = {}
        for ep in endpoints:
            url = ep.get("url", "")
            status = ep.get("status", "")
            events = ep.get("enabled_events", [])
            for path_key in expected:
                if path_key in url:
                    registered[path_key] = {"status": status, "events": events}

        all_ok = True
        for path_key, expected_event in expected.items():
            info = registered.get(path_key)
            if not info:
                print(f"  {fail(path_key)}: NOT REGISTERED in Stripe")
                all_ok = False
            elif info["status"] != "enabled":
                print(f"  {warn(path_key)}: registered but status={info['status']}")
                all_ok = False
            else:
                print(f"  {ok(path_key)}: enabled")

        if all_ok:
            print(f"  {ok(f'All {len(expected)} webhooks registered and enabled')}")
    except Exception as e:
        print(f"  {warn(f'Stripe API check failed: {str(e)[:60]}')}")


def check_recent_executions():
    print(header("RECENT ACTIVITY"))

    # Build workflow ID → name map for error display
    wf_data = n8n_api("workflows?limit=200")
    wf_names = {}
    if wf_data:
        wf_names = {w["id"]: w["name"] for w in wf_data.get("data", [])}

    # Check for recent workflow errors across all workflows (last 24h)
    # Note: n8n is configured to prune successful executions — only errors are stored
    data = n8n_api("executions?status=error&limit=100")
    if not data:
        print(f"  {warn('n8n execution API unreachable')}")
        return

    errors = data.get("data", [])
    cutoff = datetime.now(timezone.utc).timestamp() - 86400
    recent_errors = []
    for e in errors:
        started = e.get("startedAt", "")
        if started:
            try:
                dt = datetime.fromisoformat(started.replace("Z", "+00:00"))
                if dt.timestamp() > cutoff:
                    wf_id = e.get("workflowId", "")
                    recent_errors.append(wf_names.get(wf_id, wf_id))
            except Exception:
                pass

    if recent_errors:
        # Group by workflow name with counts
        counts = {}
        for name in recent_errors:
            counts[name] = counts.get(name, 0) + 1
        summary = ", ".join(f"{n} ×{c}" if c > 1 else n for n, c in counts.items())
        print(f"  {fail(f'{len(recent_errors)} workflow error(s) in last 24h')}: {summary}")
    else:
        print(f"  {ok('0 workflow errors in last 24h')}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fast", action="store_true", help="Skip SSH checks")
    args = parser.parse_args()

    print(f"\n{BOLD}{GOLD}  MARCEAU SOLUTIONS — SYSTEM HEALTH{RESET}")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M')} | Company on a Laptop\n")

    if not args.fast:
        check_ec2_services()
        check_disk_memory()
        check_domains()
        check_n8n()
        check_clawdbot()
        check_stripe_webhooks()

    check_local_env()

    if not args.fast:
        check_recent_executions()

    # Summary + exit code (don't call fail() here — it would mutate FAILURES)
    print(f"\n{'━' * 50}")
    if FAILURES:
        print(f"  {RED}✗{RESET} {len(FAILURES)} critical failure(s): {', '.join(FAILURES[:3])}")
        print(f"{'━' * 50}\n")
        _send_telegram_alert(FAILURES)
        sys.exit(1)
    else:
        print(f"  {ok('All systems healthy')}")
        print(f"{'━' * 50}\n")


def _send_telegram_alert(failures):
    """Send Telegram alert when health check finds critical failures."""
    import ssl
    token = TELEGRAM_BOT_TOKEN or os.getenv("TELEGRAM_BOT_TOKEN", "")
    if not token:
        return  # No token configured, skip silently
    msg = f"⚠️ Health Check Alert — {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
    msg += "\n".join(f"• {f}" for f in failures[:5])
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{token}/sendMessage",
            data=json.dumps({"chat_id": TELEGRAM_CHAT_ID, "text": msg}).encode(),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        urllib.request.urlopen(req, timeout=5, context=ctx)
    except Exception:
        pass  # Never let alerting break the health check


if __name__ == "__main__":
    main()
