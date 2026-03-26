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
# Structured failure records for self-healing consumption
FAILURE_RECORDS = []

def ok(msg): return f"{GREEN}✓{RESET} {msg}"
def fail(msg, category=None, service=None, detail=None):
    FAILURES.append(msg)
    FAILURE_RECORDS.append({
        "message": msg,
        "category": category or _infer_category(msg),
        "service": service,
        "detail": detail,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    return f"{RED}✗{RESET} {msg}"
def warn(msg): return f"{YELLOW}⚠{RESET} {msg}"

def _infer_category(msg):
    """Best-effort category inference from failure message text."""
    msg_lower = msg.lower()
    if any(s in msg_lower for s in ["clawdbot", "mem0", "n8n", "fitai", "voice-api", "ai-phone"]):
        return "service_down"
    if "memory" in msg_lower:
        return "high_memory"
    if "disk" in msg_lower:
        return "high_disk"
    if "google token" in msg_lower:
        return "google_token_expired"
    if "twilio" in msg_lower and "webhook" in msg_lower:
        return "twilio_webhook_missing"
    if "twilio" in msg_lower and "balance" in msg_lower:
        return "twilio_balance_low"
    if "telegram" in msg_lower and "cred" in msg_lower:
        return "telegram_cred_stale"
    if "symlink" in msg_lower:
        return "n8n_symlink_missing"
    if "sync" in msg_lower:
        return "repo_out_of_sync"
    if "unstable" in msg_lower:
        return "service_unstable"
    if "workflow" in msg_lower and "failing" in msg_lower:
        return "n8n_workflow_failing"
    if "soul.md" in msg_lower:
        return "soul_md_issue"
    if "anthropic" in msg_lower or "elevenlabs" in msg_lower:
        return "api_key_invalid"
    return "unknown"
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
            print(f"  {fail(svc, category='service_down', service=svc, detail=status)}: {desc} [{status}]")

    # Check n8n restart count in last 24h (unexpected restarts = instability)
    out, _ = ssh("sudo journalctl -u n8n --since '24 hours ago' --no-pager 2>/dev/null | grep -c 'Started n8n.service'")
    n8n_restarts = int(out.strip()) if out.strip().isdigit() else 0
    if n8n_restarts <= 1:
        print(f"  {ok('n8n stable')}: {n8n_restarts} restart(s) in 24h")
    elif n8n_restarts <= 6:
        print(f"  {warn('n8n restarted')}: {n8n_restarts} restart(s) in 24h")
    else:
        print(f"  {fail('n8n unstable', category='service_unstable', service='n8n', detail=str(n8n_restarts))}: {n8n_restarts} restart(s) in 24h")


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
                    print(f"  {fail(label, category='high_disk', detail=str(used_pct))}")
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
                    print(f"  {fail(label, category='high_memory', detail=str(pct))}")
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


def check_credential_lifecycle():
    """Validate live credentials — not just existence, actual API calls."""
    print(header("CREDENTIAL LIFECYCLE"))
    import ssl

    def ssl_ctx():
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return ctx

    # Google token — live validation via Gmail getProfile
    token_path = ROOT / "token.json"
    if token_path.exists():
        try:
            import subprocess as sp
            result = sp.run(
                [sys.executable, str(ROOT / "scripts" / "validate_google_token.py")],
                capture_output=True, text=True, timeout=15, cwd=str(ROOT)
            )
            out = result.stdout.strip()
            if out in ("VALID", "REFRESHED"):
                status = "valid" if out == "VALID" else "refreshed"
                print(f"  {ok(f'Google token: {status}')}")
            elif out == "NO_REFRESH":
                print(f"  {fail('Google token: expired, no refresh token', category='google_token_expired', detail='no_refresh_token')}")
            elif out == "NO_TOKEN":
                print(f"  {fail('Google token.json not found', category='google_token_expired')}")
            elif out.startswith("ERROR:"):
                err = out[6:]
                if "invalid_grant" in err.lower():
                    print(f"  {fail('Google token: refresh revoked — needs re-auth', category='google_token_expired', detail='invalid_grant')}")
                else:
                    print(f"  {fail(f'Google token: INVALID — {err[:80]}', category='google_token_expired', detail=err[:80])}")
            else:
                err = result.stderr.strip()[:80] if result.stderr else "unknown"
                print(f"  {fail(f'Google token: INVALID — {err}', category='google_token_expired', detail=err)}")
        except Exception as e:
            print(f"  {warn(f'Google token: check failed ({str(e)[:40]})')}")
    else:
        print(f"  {fail('Google token.json not found')}")

    # Twilio — verify webhook URLs on all owned numbers
    twilio_sid = os.getenv("TWILIO_ACCOUNT_SID", "")
    twilio_token = os.getenv("TWILIO_AUTH_TOKEN", "")
    if twilio_sid and twilio_token:
        try:
            import base64
            creds = base64.b64encode(f"{twilio_sid}:{twilio_token}".encode()).decode()
            req = urllib.request.Request(
                f"https://api.twilio.com/2010-04-01/Accounts/{twilio_sid}/IncomingPhoneNumbers.json",
                headers={"Authorization": f"Basic {creds}"}
            )
            resp = urllib.request.urlopen(req, timeout=10, context=ssl_ctx())
            data = json.loads(resp.read())
            numbers = data.get("incoming_phone_numbers", [])
            for num in numbers:
                phone = num.get("phone_number", "unknown")
                sms_url = num.get("sms_url", "")
                friendly = num.get("friendly_name", phone)
                if sms_url:
                    print(f"  {ok(f'Twilio {friendly}: SMS webhook set')}")
                else:
                    print(f"  {fail(f'Twilio {friendly}: NO SMS webhook — inbound texts silently dropped', category='twilio_webhook_missing', service='twilio', detail=phone)}")
        except Exception as e:
            print(f"  {warn(f'Twilio number check failed: {str(e)[:40]}')}")


def check_ec2_stability():
    """Check EC2 service stability indicators beyond basic is-active."""
    print(header("EC2 STABILITY"))

    # Clawdbot restart count (separate from n8n which is already checked)
    out, _ = ssh("sudo journalctl -u clawdbot --since '24 hours ago' --no-pager 2>/dev/null | grep -c 'Started clawdbot'")
    cb_restarts = int(out.strip()) if out.strip().isdigit() else 0
    if cb_restarts <= 1:
        print(f"  {ok(f'Clawdbot stable: {cb_restarts} restart(s) in 24h')}")
    elif cb_restarts <= 3:
        print(f"  {warn(f'Clawdbot restarted {cb_restarts}x in 24h')}")
    else:
        print(f"  {fail(f'Clawdbot unstable: {cb_restarts} restarts in 24h', category='service_unstable', service='clawdbot', detail=str(cb_restarts))}")

    # n8n symlink check (prevents crash-loop on restart)
    out, success = ssh("sudo test -L /home/ec2-user/.local/bin/n8n && echo exists || echo missing")
    if "exists" in (out or ""):
        print(f"  {ok('n8n symlink: ~/.local/bin/n8n exists')}")
    else:
        print(f"  {fail('n8n symlink MISSING — will crash-loop on restart', category='n8n_symlink_missing', service='n8n')}")

    # SOUL.md version check
    out, _ = ssh("sudo grep 'Version' /home/clawdbot/clawd/SOUL.md 2>/dev/null | head -1")
    if out:
        version = out.strip()
        if "2.1.0" in version:
            print(f"  {ok(f'SOUL.md: {version}')}")
        else:
            print(f"  {warn(f'SOUL.md version drift: {version} (expected 2.1.0)')}")
    else:
        print(f"  {fail('SOUL.md not readable')}")

    # Check ARCHITECTURE-DECISIONS.md exists and is recent
    out, _ = ssh("sudo -u clawdbot bash -c 'cd /home/clawdbot/dev-sandbox && test -f docs/ARCHITECTURE-DECISIONS.md && echo exists'")
    if "exists" in (out or ""):
        print(f"  {ok('ARCHITECTURE-DECISIONS.md: present on EC2')}")
    else:
        print(f"  {fail('ARCHITECTURE-DECISIONS.md MISSING on EC2 — Clawdbot has no quality rules')}")

    # journald size
    out, _ = ssh("sudo journalctl --disk-usage 2>/dev/null | grep -oP '[\\d.]+[MG]'")
    if out:
        size_str = out.strip()
        try:
            if "G" in size_str:
                size_mb = float(size_str.replace("G", "")) * 1024
            else:
                size_mb = float(size_str.replace("M", ""))
            if size_mb > 450:
                print(f"  {warn(f'journald: {size_str} (cap is 500M)')}")
            else:
                print(f"  {ok(f'journald: {size_str}')}")
        except ValueError:
            print(f"  Journal: {size_str}")


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


def check_ai_apis():
    """Validate critical AI API keys are working (not just present)."""
    print(header("AI API STATUS"))
    import ssl

    def ssl_ctx():
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return ctx

    # Anthropic — GET /v1/models (no token cost)
    anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not anthropic_key:
        print(f"  {fail('Anthropic: key missing')}")
    else:
        try:
            req = urllib.request.Request(
                "https://api.anthropic.com/v1/models",
                headers={"x-api-key": anthropic_key, "anthropic-version": "2023-06-01"}
            )
            resp = urllib.request.urlopen(req, timeout=8, context=ssl_ctx())
            print(f"  {ok('Anthropic: key valid')}")
        except urllib.error.HTTPError as e:
            if e.code == 401:
                print(f"  {fail('Anthropic: invalid key (401)')}")
            elif e.code == 429:
                print(f"  {warn('Anthropic: rate limited (429)')}")
            else:
                print(f"  {warn(f'Anthropic: HTTP {e.code}')}")
        except Exception as e:
            print(f"  {warn(f'Anthropic: check failed ({str(e)[:40]})')}")

    # ElevenLabs — GET /v1/user/subscription (character quota)
    el_key = os.getenv("ELEVENLABS_API_KEY", "")
    if not el_key:
        print(f"  {warn('ElevenLabs: key missing')}")
    else:
        try:
            req = urllib.request.Request(
                "https://api.elevenlabs.io/v1/user/subscription",
                headers={"xi-api-key": el_key}
            )
            resp = urllib.request.urlopen(req, timeout=8, context=ssl_ctx())
            data = json.loads(resp.read())
            used = data.get("character_count", 0)
            limit = data.get("character_limit", 0)
            pct = (used / limit * 100) if limit > 0 else 0
            if pct > 95:
                print(f"  {fail(f'ElevenLabs: {used:,}/{limit:,} chars ({pct:.0f}% — EXHAUSTED)')}")
            elif pct > 80:
                print(f"  {warn(f'ElevenLabs: {used:,}/{limit:,} chars ({pct:.0f}% — low)')}")
            else:
                print(f"  {ok(f'ElevenLabs: {used:,}/{limit:,} chars ({pct:.0f}% used)')}")
        except urllib.error.HTTPError as e:
            if e.code == 401:
                print(f"  {fail('ElevenLabs: invalid key (401)')}")
            else:
                print(f"  {warn(f'ElevenLabs: HTTP {e.code}')}")
        except Exception as e:
            print(f"  {warn(f'ElevenLabs: check failed ({str(e)[:40]})')}")

    # Telegram bot token — critical for GitHub→Telegram and all alerts
    tg_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    if not tg_token:
        print(f"  {fail('Telegram: TELEGRAM_BOT_TOKEN not set')}")
    else:
        try:
            req = urllib.request.Request(
                f"https://api.telegram.org/bot{tg_token}/getMe"
            )
            resp = urllib.request.urlopen(req, timeout=8, context=ssl_ctx())
            data = json.loads(resp.read())
            if data.get("ok"):
                bot_name = data.get("result", {}).get("username", "unknown")
                # Also check GitHub→Telegram most recent execution succeeded
                last_exec_ok = True
                try:
                    tg_execs = n8n_api("executions?workflowId=BsoplLFe1brLCBof&limit=1")
                    if tg_execs and tg_execs.get("data"):
                        last_status = tg_execs["data"][0].get("status", "")
                        if last_status == "error":
                            last_exec_ok = False
                except Exception:
                    pass
                if not last_exec_ok:
                    print(f"  {fail(f'Telegram: bot valid (@{bot_name}) but n8n cred stale — last GitHub→Telegram failed. Run: python scripts/health_check.py --repatch-telegram')}")
                else:
                    print(f"  {ok(f'Telegram: bot valid (@{bot_name})')}")
            else:
                print(f"  {fail(f'Telegram: bot API returned ok=false')}")
        except urllib.error.HTTPError as e:
            print(f"  {fail(f'Telegram: invalid bot token (HTTP {e.code})')}")
        except Exception as e:
            print(f"  {warn(f'Telegram: check failed ({str(e)[:40]})')}")


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

    # Build workflow ID → name map for error display (all workflows for names)
    wf_data_all = n8n_api("workflows?limit=200")
    wf_names = {}
    if wf_data_all:
        wf_names = {w["id"]: w["name"] for w in wf_data_all.get("data", [])}
    # Active workflows only (for filtering — inactive errors are expected/intentional)
    wf_data = n8n_api("workflows?active=true&limit=200")

    # Check for recent workflow errors across all workflows (last 24h)
    # Note: n8n is configured to prune successful executions — only errors are stored
    data = n8n_api("executions?status=error&limit=100")
    if not data:
        print(f"  {warn('n8n execution API unreachable')}")
        return

    errors = data.get("data", [])
    cutoff = datetime.now(timezone.utc).timestamp() - 86400
    # Find workflows that errored in last 24h
    errored_wf_ids = set()
    for e in errors:
        started = e.get("startedAt", "")
        if started:
            try:
                dt = datetime.fromisoformat(started.replace("Z", "+00:00"))
                if dt.timestamp() > cutoff:
                    wf_id = e.get("workflowId", "")
                    if wf_id:
                        errored_wf_ids.add(wf_id)
            except Exception:
                pass

    # For each erroring workflow, check if the LATEST execution is still an error
    # and whether the workflow is currently active
    active_wf_ids = {w["id"] for w in wf_data.get("data", [])} if wf_data else set()
    still_failing = []      # active workflow, latest exec is error
    stale_failures = []     # active workflow, latest exec is error but old (>6h ago)
    cutoff_6h = datetime.now(timezone.utc).timestamp() - 21600
    for wf_id in errored_wf_ids:
        if wf_id not in active_wf_ids:
            continue  # Skip inactive workflows — expected state
        latest = n8n_api(f"executions?workflowId={wf_id}&limit=1")
        if latest and latest.get("data"):
            last_ex = latest["data"][0]
            last_status = last_ex.get("status", "")
            started = last_ex.get("startedAt", "")
            if last_status == "error":
                # Check if this is a recent error (in last 6h) or stale
                is_recent = False
                if started:
                    try:
                        dt = datetime.fromisoformat(started.replace("Z", "+00:00"))
                        is_recent = dt.timestamp() > cutoff_6h
                    except Exception:
                        pass
                name = wf_names.get(wf_id, wf_id)
                if is_recent:
                    still_failing.append(name)
                else:
                    stale_failures.append(name)

    if still_failing:
        summary = ", ".join(still_failing)
        print(f"  {fail(f'{len(still_failing)} workflow(s) actively failing')}: {summary}")
    else:
        print(f"  {ok('No active workflow failures')}")
    if stale_failures:
        summary = ", ".join(stale_failures)
        print(f"  {warn(f'{len(stale_failures)} workflow(s) failed last run, not yet re-verified')}: {summary}")


def check_workflow_health():
    """Run n8n workflow validator to catch silent configuration issues."""
    print(header("N8N WORKFLOW VALIDATION"))
    try:
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "n8n_workflow_validator.py"), "--json"],
            capture_output=True, text=True, timeout=60, cwd=str(ROOT)
        )
        if result.returncode != 0 and not result.stdout.strip():
            print(f"  {warn('Validator failed to run')}")
            return

        data = json.loads(result.stdout)
        if "error" in data:
            print(f"  {warn(data['error'])}")
            return

        total = len(data.get("issues", []))
        critical = data.get("critical", 0)
        high = data.get("high", 0)
        checked = data.get("workflows_checked", 0)

        if total == 0:
            print(f"  {ok(f'{checked} workflows scanned — all healthy')}")
        else:
            if critical > 0:
                print(f"  {fail(f'{critical} critical issue(s) in {checked} workflows', category='n8n_config_issues', detail=str(critical))}")
            if high > 0:
                print(f"  {warn(f'{high} high-severity issue(s)')}")
            # Show first 3 issues
            for issue in data["issues"][:3]:
                sev = "✗" if issue["severity"] == "critical" else "⚠"
                print(f"    {sev} {issue['workflow']}: {issue['check']} on {issue['node']}")
            if total > 3:
                print(f"    ... and {total - 3} more. Run: python scripts/n8n_workflow_validator.py --fix-report")
    except Exception as e:
        print(f"  {warn(f'Validator error: {str(e)[:50]}')}")


def check_pipeline_health():
    """Check sales pipeline for business process failures — orphaned leads, stalled sequences."""
    print(header("SALES PIPELINE HEALTH"))
    import sqlite3

    db_path = ROOT / "projects" / "shared" / "sales-pipeline" / "data" / "pipeline.db"
    if not db_path.exists():
        print(f"  {warn('pipeline.db not found — skipping')}")
        return

    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row

        # 1. Orphaned leads: emailed but no follow-up date set
        orphaned = conn.execute("""
            SELECT COUNT(DISTINCT d.id) FROM deals d
            JOIN outreach_log o ON o.deal_id = d.id AND o.channel = 'Email'
            WHERE d.stage NOT IN ('Closed Won', 'Closed Lost')
            AND (d.next_action_date IS NULL OR d.next_action_date = '')
        """).fetchone()[0]

        if orphaned > 0:
            print(f"  {fail(f'{orphaned} leads emailed but NOT in follow-up sequence', category='orphaned_leads', detail=str(orphaned))}")
        else:
            print(f"  {ok('All emailed leads have follow-up dates')}")

        # 2. Overdue follow-ups: next_action_date in the past, not acted on
        overdue = conn.execute("""
            SELECT COUNT(*) FROM deals
            WHERE next_action_date < date('now', '-2 days')
            AND next_action_date IS NOT NULL AND next_action_date != ''
            AND stage NOT IN ('Closed Won', 'Closed Lost')
        """).fetchone()[0]

        if overdue > 10:
            print(f"  {fail(f'{overdue} follow-ups overdue by 2+ days', category='overdue_followups', detail=str(overdue))}")
        elif overdue > 0:
            print(f"  {warn(f'{overdue} follow-up(s) overdue by 2+ days')}")
        else:
            print(f"  {ok('No overdue follow-ups')}")

        # 3. Stalled deals: deals with outreach but no activity in 7+ days
        stalled = conn.execute("""
            SELECT COUNT(DISTINCT d.id) FROM deals d
            JOIN outreach_log o ON o.deal_id = d.id
            WHERE d.stage NOT IN ('Closed Won', 'Closed Lost')
            AND d.stage != 'New'
            GROUP BY d.id
            HAVING MAX(o.created_at) < date('now', '-7 days')
        """).fetchall()

        stalled_count = len(stalled)
        if stalled_count > 20:
            print(f"  {fail(f'{stalled_count} deals stalled (no activity in 7+ days)', category='stalled_deals', detail=str(stalled_count))}")
        elif stalled_count > 0:
            print(f"  {warn(f'{stalled_count} deal(s) with no activity in 7+ days')}")
        else:
            print(f"  {ok('No stalled deals')}")

        # 4. Pipeline summary (informational)
        total_active = conn.execute("""
            SELECT COUNT(*) FROM deals WHERE stage NOT IN ('Closed Won', 'Closed Lost')
        """).fetchone()[0]
        due_today = conn.execute("""
            SELECT COUNT(*) FROM deals
            WHERE next_action_date <= date('now')
            AND next_action_date IS NOT NULL AND next_action_date != ''
            AND stage NOT IN ('Closed Won', 'Closed Lost')
        """).fetchone()[0]
        print(f"  Pipeline: {total_active} active deals, {due_today} due today")

        conn.close()
    except Exception as e:
        print(f"  {warn(f'Pipeline check failed: {str(e)[:60]}')}")


def check_repo_sync():
    """Check that Local, GitHub, and EC2 repos are in sync."""
    print(header("REPOSITORY SYNC"))

    # Local commit
    try:
        local = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True, text=True, timeout=5, cwd=str(ROOT)
        )
        local_commit = local.stdout.strip()[:7]
    except Exception:
        print(f"  {fail('Cannot read local git repo')}")
        return

    # Fetch GitHub
    try:
        subprocess.run(
            ["git", "fetch", "origin", "main"],
            capture_output=True, text=True, timeout=15, cwd=str(ROOT)
        )
        gh = subprocess.run(
            ["git", "rev-parse", "origin/main"],
            capture_output=True, text=True, timeout=5, cwd=str(ROOT)
        )
        github_commit = gh.stdout.strip()[:7]
    except Exception:
        print(f"  {warn('Cannot fetch from GitHub')}")
        github_commit = "unknown"

    # EC2 commit
    ec2_out, ec2_ok = ssh("sudo -u clawdbot bash -c 'cd /home/clawdbot/dev-sandbox && git rev-parse HEAD'")
    ec2_commit = ec2_out.strip()[:7] if ec2_ok else "unknown"

    print(f"  Local:  {local_commit}")
    print(f"  GitHub: {github_commit}")
    print(f"  EC2:    {ec2_commit}")

    # Check local vs GitHub
    if local_commit != github_commit:
        ahead = subprocess.run(
            ["git", "rev-list", "--count", "origin/main..HEAD"],
            capture_output=True, text=True, timeout=5, cwd=str(ROOT)
        )
        behind = subprocess.run(
            ["git", "rev-list", "--count", "HEAD..origin/main"],
            capture_output=True, text=True, timeout=5, cwd=str(ROOT)
        )
        a = ahead.stdout.strip()
        b = behind.stdout.strip()
        print(f"  {fail(f'Local ↔ GitHub out of sync ({a} ahead, {b} behind)', category='repo_out_of_sync', detail=f'local: {a} ahead, {b} behind')}")
    else:
        print(f"  {ok('Local ↔ GitHub in sync')}")

    # Check EC2 vs GitHub
    if ec2_commit == "unknown":
        print(f"  {warn('Cannot verify EC2 sync (SSH failed)')}")
    elif ec2_commit != github_commit:
        print(f"  {fail(f'EC2 ↔ GitHub out of sync (EC2={ec2_commit}, GitHub={github_commit})', category='ec2_repo_out_of_sync', detail=f'ec2={ec2_commit}, github={github_commit}')}")
    else:
        print(f"  {ok('EC2 ↔ GitHub in sync')}")

    # Check sync agent exists on EC2
    agent_out, agent_ok = ssh("sudo -u clawdbot test -x /home/clawdbot/scripts/sync-agent.sh && echo exists")
    if agent_ok and "exists" in agent_out:
        print(f"  {ok('EC2 sync-agent.sh deployed')}")
    else:
        print(f"  {fail('EC2 sync-agent.sh missing or not executable')}")

    # Check cron is set
    cron_out, cron_ok = ssh("sudo -u clawdbot crontab -l 2>/dev/null")
    if cron_ok and "sync-agent.sh" in cron_out:
        print(f"  {ok('EC2 auto-sync cron active')}")
    else:
        print(f"  {fail('EC2 auto-sync cron not configured')}")


def repatch_telegram():
    """Re-patch the Clawdbot Telegram credential in n8n with the token from .env."""
    import ssl
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    if not token:
        print("TELEGRAM_BOT_TOKEN not in .env")
        return False

    n8n_url = os.getenv("N8N_URL", "https://n8n.marceausolutions.com")
    payload = json.dumps({
        "name": "Clawdbot Telegram",
        "type": "telegramApi",
        "data": {"accessToken": token}
    }).encode()

    req = urllib.request.Request(
        f"{n8n_url}/api/v1/credentials/RlAwU3xzcX4hifgj",
        data=payload,
        headers={"X-N8N-API-KEY": N8N_API_KEY, "Content-Type": "application/json"},
        method="PATCH"
    )
    try:
        resp = urllib.request.urlopen(req, timeout=10, context=ctx)
        result = json.loads(resp.read())
        print(f"✓ Telegram cred re-patched: {result.get('name')}")
        # Bounce GitHub→Telegram workflow
        for action in ["deactivate", "activate"]:
            req2 = urllib.request.Request(
                f"{n8n_url}/api/v1/workflows/BsoplLFe1brLCBof/{action}",
                data=b"{}",
                headers={"X-N8N-API-KEY": N8N_API_KEY, "Content-Type": "application/json"},
                method="POST"
            )
            urllib.request.urlopen(req2, timeout=10, context=ctx)
        print("✓ GitHub→Telegram workflow bounced")
        return True
    except Exception as e:
        print(f"✗ Re-patch failed: {e}")
        return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fast", action="store_true", help="Skip SSH checks")
    parser.add_argument("--json", action="store_true", help="Output structured JSON failures (for self-heal)")
    parser.add_argument("--repatch-telegram", action="store_true", help="Re-patch stale Telegram cred in n8n")
    args = parser.parse_args()

    if args.repatch_telegram:
        repatch_telegram()
        return

    print(f"\n{BOLD}{GOLD}  MARCEAU SOLUTIONS — SYSTEM HEALTH{RESET}")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M')} | Company on a Laptop\n")

    if not args.fast:
        check_ec2_services()
        check_disk_memory()
        check_ec2_stability()
        check_domains()
        check_n8n()
        check_clawdbot()
        check_repo_sync()
        check_ai_apis()
        check_stripe_webhooks()
        check_credential_lifecycle()
        check_pipeline_health()

    check_local_env()

    if not args.fast:
        check_recent_executions()
        check_workflow_health()

    # Summary + exit code (don't call fail() here — it would mutate FAILURES)
    if args.json:
        # Structured output for self_heal.py consumption
        print(json.dumps({
            "failures": FAILURE_RECORDS,
            "failure_count": len(FAILURES),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }))
        sys.exit(1 if FAILURES else 0)
        return

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
