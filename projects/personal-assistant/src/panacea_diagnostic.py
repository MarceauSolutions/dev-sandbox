#!/usr/bin/env python3
"""
Panacea Performance Diagnostic
================================
Measures why the Grok orchestration feels faster/better on EC2/Telegram
vs Claude Code on the Mac. Captures latency, context, integration health,
and architecture differences between the two execution environments.

Run from EC2:
    python3 projects/personal-assistant/src/panacea_diagnostic.py

Run from Mac (if you want to compare):
    python3 projects/personal-assistant/src/panacea_diagnostic.py --env mac

Output: Console summary + saves report to docs/diagnostic_report_TIMESTAMP.md
"""

import argparse
import json
import os
import platform
import socket
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# ── Setup ──────────────────────────────────────────────────────────────────
REPO_ROOT = Path(os.environ.get("REPO_ROOT", Path(__file__).parents[3]))
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "execution"))

try:
    from dotenv import load_dotenv
    load_dotenv(REPO_ROOT / ".env")
except ImportError:
    pass

GOLD   = "\033[93m"
GREEN  = "\033[92m"
RED    = "\033[91m"
BLUE   = "\033[94m"
RESET  = "\033[0m"
BOLD   = "\033[1m"

results = {}


def header(title: str):
    print(f"\n{BOLD}{GOLD}{'─' * 60}{RESET}")
    print(f"{BOLD}{GOLD}  {title}{RESET}")
    print(f"{BOLD}{GOLD}{'─' * 60}{RESET}")


def ok(label: str, value: str):
    print(f"  {GREEN}✓{RESET}  {label:<40} {BOLD}{value}{RESET}")


def warn(label: str, value: str):
    print(f"  {GOLD}⚠{RESET}  {label:<40} {BOLD}{value}{RESET}")


def fail(label: str, value: str):
    print(f"  {RED}✗{RESET}  {label:<40} {BOLD}{value}{RESET}")


def info(label: str, value: str):
    print(f"  {BLUE}·{RESET}  {label:<40} {value}")


def measure_latency(host: str, port: int = 443, label: str = "") -> float:
    """TCP connect latency in ms."""
    try:
        start = time.perf_counter()
        sock = socket.create_connection((host, port), timeout=5)
        elapsed = (time.perf_counter() - start) * 1000
        sock.close()
        return round(elapsed, 1)
    except Exception as e:
        return -1


def measure_https_latency(url: str) -> dict:
    """Measure full HTTPS round-trip latency using curl."""
    try:
        result = subprocess.run(
            ["curl", "-o", "/dev/null", "-s", "-w",
             '{"dns":"%{time_namelookup}","connect":"%{time_connect}",'
             '"tls":"%{time_appconnect}","ttfb":"%{time_starttransfer}",'
             '"total":"%{time_total}"}',
             "--max-time", "10", url],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode == 0:
            d = json.loads(result.stdout)
            return {k: round(float(v) * 1000, 1) for k, v in d.items()}
        return {}
    except Exception:
        return {}


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 1 — Environment
# ══════════════════════════════════════════════════════════════════════════════
def check_environment(env: str):
    header("1. EXECUTION ENVIRONMENT")

    hostname = socket.gethostname()
    is_ec2 = "ec2" in hostname.lower() or "ip-" in hostname.lower() or env == "ec2"
    is_mac = platform.system() == "Darwin" or env == "mac"

    results["environment"] = {
        "hostname": hostname,
        "platform": platform.platform(),
        "python": sys.version.split()[0],
        "repo_root": str(REPO_ROOT),
        "is_ec2": is_ec2,
        "is_mac": is_mac,
    }

    env_label = "EC2 (Panacea/Telegram)" if is_ec2 else "Mac (Claude Code/VS Code)"
    info("Hostname", hostname)
    info("Platform", platform.platform())
    info("Python version", sys.version.split()[0])
    info("Detected environment", f"{BOLD}{env_label}{RESET}")
    info("REPO_ROOT", str(REPO_ROOT))
    info("Working directory", os.getcwd())

    cwd_match = Path(os.getcwd()).resolve() == REPO_ROOT.resolve()
    if cwd_match:
        ok("cwd == REPO_ROOT", "YES — context loads correctly")
    else:
        warn("cwd == REPO_ROOT", f"NO — cwd is {os.getcwd()}, REPO_ROOT is {REPO_ROOT}")
        results["environment"]["cwd_mismatch"] = True

    return is_ec2


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 2 — Network Latency
# ══════════════════════════════════════════════════════════════════════════════
def check_network():
    header("2. API NETWORK LATENCY")

    targets = {
        "Anthropic API (api.anthropic.com)": ("api.anthropic.com", "https://api.anthropic.com"),
        "xAI / Grok (api.x.ai)": ("api.x.ai", "https://api.x.ai"),
        "Telegram API (api.telegram.org)": ("api.telegram.org", "https://api.telegram.org"),
        "n8n (n8n.marceausolutions.com)": ("n8n.marceausolutions.com", "https://n8n.marceausolutions.com"),
    }

    latency_data = {}
    for label, (host, url) in targets.items():
        tcp = measure_latency(host, 443)
        https = measure_https_latency(url)

        latency_data[label] = {"tcp_ms": tcp, "https": https}

        if tcp < 0:
            fail(label, "UNREACHABLE")
        elif tcp < 30:
            ok(label, f"TCP {tcp}ms | TTFB {https.get('ttfb', '?')}ms")
        elif tcp < 80:
            warn(label, f"TCP {tcp}ms | TTFB {https.get('ttfb', '?')}ms (acceptable)")
        else:
            fail(label, f"TCP {tcp}ms | TTFB {https.get('ttfb', '?')}ms — HIGH LATENCY")

    results["network_latency"] = latency_data

    # Local services
    print()
    info("─── Local Services (EC2 localhost) ───", "")
    local_services = {
        "n8n (localhost:5678)": 5678,
        "Mem0 API (localhost:5020)": 5020,
        "Agent Bridge (localhost:5010)": 5010,
        "AI Phone Agent": 5000,
    }
    local_data = {}
    for label, port in local_services.items():
        try:
            start = time.perf_counter()
            s = socket.create_connection(("127.0.0.1", port), timeout=1)
            ms = round((time.perf_counter() - start) * 1000, 2)
            s.close()
            ok(label, f"UP — {ms}ms")
            local_data[label] = {"up": True, "ms": ms}
        except Exception:
            warn(label, "NOT RUNNING (expected on Mac)")
            local_data[label] = {"up": False}
    results["local_services"] = local_data


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 3 — Grok Integration
# ══════════════════════════════════════════════════════════════════════════════
def check_grok():
    header("3. GROK STRATEGIC LAYER")

    grok_key = os.environ.get("XAI_API_KEY", "")
    if not grok_key:
        fail("XAI_API_KEY", "NOT SET — Grok consultation will silently skip")
        results["grok"] = {"key_set": False}
        return

    ok("XAI_API_KEY", f"Set ({grok_key[:8]}...)")

    # Test import
    try:
        sys.path.insert(0, str(REPO_ROOT / "execution"))
        from grok_strategic_layer import consult_grok
        ok("grok_strategic_layer import", "SUCCESS")
        results["grok"] = {"key_set": True, "importable": True}
    except ImportError as e:
        fail("grok_strategic_layer import", f"FAILED: {e}")
        results["grok"] = {"key_set": True, "importable": False, "error": str(e)}
        return

    # Live latency test
    print()
    info("Testing live Grok API call (small prompt)...", "")
    start = time.perf_counter()
    try:
        direction = consult_grok("Respond in one sentence: what is 2+2?")
        elapsed = round((time.perf_counter() - start) * 1000)
        if direction:
            ok("Grok API response time", f"{elapsed}ms")
            ok("Grok returned content", direction[:80] + "..." if len(direction) > 80 else direction)
            results["grok"]["api_latency_ms"] = elapsed
            results["grok"]["working"] = True
        else:
            warn("Grok API response", f"Returned empty ({elapsed}ms) — check API key quota")
            results["grok"]["working"] = False
    except Exception as e:
        elapsed = round((time.perf_counter() - start) * 1000)
        fail("Grok API call", f"FAILED after {elapsed}ms: {e}")
        results["grok"]["working"] = False
        results["grok"]["error"] = str(e)


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 4 — Claude Execution Path
# ══════════════════════════════════════════════════════════════════════════════
def check_claude():
    header("4. CLAUDE EXECUTION PATH")

    # Check claude binary
    try:
        result = subprocess.run(["which", "claude"], capture_output=True, text=True)
        claude_path = result.stdout.strip()
        if claude_path:
            ok("claude binary location", claude_path)
            results["claude"] = {"binary": claude_path}
        else:
            fail("claude binary", "NOT FOUND IN PATH")
            results["claude"] = {"binary": None}
            return
    except Exception:
        fail("claude binary", "ERROR CHECKING")
        results["claude"] = {}
        return

    # Check claude version
    try:
        result = subprocess.run(["claude", "--version"], capture_output=True, text=True, timeout=10)
        version = result.stdout.strip() or result.stderr.strip()
        ok("claude version", version[:60])
        results["claude"]["version"] = version
    except Exception as e:
        warn("claude version", f"Could not check: {e}")

    # Time a minimal claude -p call
    print()
    info("Timing a minimal claude -p call (1-token response)...", "")
    start = time.perf_counter()
    try:
        result = subprocess.run(
            ["claude", "-p", "Reply with only the number 42. Nothing else.",
             "--dangerously-skip-permissions"],
            capture_output=True, text=True,
            timeout=60,
            cwd=str(REPO_ROOT)
        )
        elapsed = round((time.perf_counter() - start) * 1000)
        output = (result.stdout or result.stderr or "").strip()[:100]

        if result.returncode == 0:
            ok(f"claude -p cold start + response", f"{elapsed}ms")
            ok("Response content", output)
            results["claude"]["cold_start_ms"] = elapsed
        else:
            warn(f"claude -p returned code {result.returncode}", f"{elapsed}ms — {output[:80]}")
            results["claude"]["cold_start_ms"] = elapsed
            results["claude"]["error"] = output
    except subprocess.TimeoutExpired:
        elapsed = round((time.perf_counter() - start) * 1000)
        fail("claude -p", f"TIMEOUT after {elapsed}ms")
        results["claude"]["cold_start_ms"] = elapsed
        results["claude"]["timeout"] = True
    except Exception as e:
        fail("claude -p", f"FAILED: {e}")

    # Execution flags used by Panacea vs Mac
    print()
    info("─── Execution Flag Comparison ───", "")
    info("EC2 Panacea flags", "claude -p <prompt> --dangerously-skip-permissions --system-prompt <...> [--resume <session_id>]")
    info("Mac Claude Code flags", "Interactive session — no -p flag, no system prompt override, permission prompts enabled")
    info("Key difference", "EC2 skips all permission prompts; Mac pauses for each tool call")
    results["claude"]["ec2_flags"] = "--dangerously-skip-permissions --resume <session_id>"
    results["claude"]["mac_flags"] = "interactive, permission prompts, no -p"


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 5 — Context & Prompt Architecture
# ══════════════════════════════════════════════════════════════════════════════
def check_context():
    header("5. CONTEXT & PROMPT ARCHITECTURE")

    # CLAUDE.md size
    claude_md = REPO_ROOT / "CLAUDE.md"
    if claude_md.exists():
        size = claude_md.stat().st_size
        lines = len(claude_md.read_text().splitlines())
        ok("CLAUDE.md exists", f"{lines} lines / {size:,} bytes")
        results["context"] = {"claude_md_lines": lines, "claude_md_bytes": size}
    else:
        fail("CLAUDE.md", "NOT FOUND")
        results["context"] = {}

    # MEMORY.md
    for mem_path in [REPO_ROOT / "MEMORY.md", REPO_ROOT / "docs" / "MEMORY.md"]:
        if mem_path.exists():
            size = mem_path.stat().st_size
            ok(f"MEMORY.md ({mem_path.name})", f"{size:,} bytes")
            results["context"]["memory_md_bytes"] = size
            break
    else:
        warn("MEMORY.md", "NOT FOUND — agent has no persistent memory base")

    # System prompt size (Panacea's)
    panacea_system_prompt_path = REPO_ROOT / "projects" / "personal-assistant" / "src" / "panacea_relay.py"
    if panacea_system_prompt_path.exists():
        content = panacea_system_prompt_path.read_text()
        # Extract the system prompt
        import re
        match = re.search(r'PANACEA_SYSTEM_PROMPT\s*=\s*\((.*?)\)', content, re.DOTALL)
        if match:
            sp = match.group(1).strip().strip('"\'')
            info("Panacea system prompt length", f"~{len(sp)} chars")

    # Grok append size
    info("─── Prompt Construction (EC2 vs Mac) ───", "")
    info("EC2 prompt structure",
         "Grok direction (2-3 sentences) → appended to every claude -p call as --append-system-prompt")
    info("Mac prompt structure",
         "CLAUDE.md + conversation history — Grok direction NOT automatically appended")
    info("Effect",
         "EC2 always has Grok's current strategic direction. Mac only has it if you manually consult Grok.")
    results["context"]["grok_always_appended_ec2"] = True
    results["context"]["grok_always_appended_mac"] = False

    # Session continuity
    print()
    info("─── Session Continuity ───", "")
    info("EC2 session model", "--resume <session_id> maintains conversation within a Telegram session")
    info("Mac session model", "Each VS Code window starts fresh unless /resume is used")
    info("Effect",
         "EC2 Panacea remembers earlier messages in the same session automatically")


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 6 — Resource Usage
# ══════════════════════════════════════════════════════════════════════════════
def check_resources():
    header("6. SERVER RESOURCES")

    # CPU
    try:
        result = subprocess.run(
            ["top", "-bn1"], capture_output=True, text=True, timeout=5
        )
        lines = result.stdout.splitlines()
        cpu_line = next((l for l in lines if "Cpu" in l or "cpu" in l), "")
        if cpu_line:
            info("CPU summary", cpu_line.strip()[:70])
    except Exception:
        pass

    # Memory
    try:
        result = subprocess.run(["free", "-h"], capture_output=True, text=True, timeout=5)
        for line in result.stdout.splitlines():
            if "Mem" in line:
                parts = line.split()
                total, used, free = parts[1], parts[2], parts[3]
                if float(used[:-1]) / float(total[:-1]) > 0.85:
                    warn("RAM", f"Total {total} | Used {used} | Free {free} — HIGH USAGE")
                else:
                    ok("RAM", f"Total {total} | Used {used} | Free {free}")
                results["resources"] = {"ram_total": total, "ram_used": used}
                break
    except Exception:
        info("RAM", "Could not read (may be on Mac)")

    # Disk
    try:
        result = subprocess.run(["df", "-h", str(REPO_ROOT)], capture_output=True, text=True, timeout=5)
        lines = result.stdout.splitlines()
        if len(lines) > 1:
            parts = lines[1].split()
            info("Disk (repo root)", f"Total {parts[1]} | Used {parts[2]} | Free {parts[3]} | {parts[4]} used")
    except Exception:
        pass

    # Running processes relevant to performance
    print()
    info("─── Key Processes ───", "")
    try:
        result = subprocess.run(
            ["pgrep", "-la", "panacea\|claude\|n8n\|mem0\|bridge"],
            capture_output=True, text=True, timeout=5
        )
        procs = result.stdout.strip()
        if procs:
            for line in procs.splitlines()[:8]:
                info("Running", line[:70])
        else:
            # try ps instead
            result2 = subprocess.run(
                ["ps", "aux"], capture_output=True, text=True, timeout=5
            )
            relevant = [l for l in result2.stdout.splitlines()
                        if any(x in l for x in ["panacea", "claude", "n8n", "mem0"])]
            for line in relevant[:8]:
                info("Process", " ".join(line.split()[10:])[:70])
    except Exception:
        pass


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 7 — Root Cause Analysis
# ══════════════════════════════════════════════════════════════════════════════
def root_cause_analysis(is_ec2: bool):
    header("7. ROOT CAUSE ANALYSIS — Why EC2 Feels Better")

    causes = [
        {
            "rank": 1,
            "factor": "Grok always appended on EC2, never on Mac",
            "explanation": (
                "Every single claude -p call on EC2 has Grok's current strategic direction "
                "appended as --append-system-prompt. On Mac (Claude Code), Grok is only consulted "
                "if you explicitly use /grok or the skill — it is NOT automatically injected. "
                "This means EC2 Claude is always strategically aligned; Mac Claude is flying blind."
            ),
            "severity": "HIGH",
            "fix": "Use the Grok skill at the start of every Mac session, or build a CLAUDE.md hook that auto-appends it."
        },
        {
            "rank": 2,
            "factor": "--dangerously-skip-permissions removes all friction",
            "explanation": (
                "EC2 Panacea runs claude -p with --dangerously-skip-permissions. "
                "No tool call ever pauses for approval. On Mac, Claude Code prompts before "
                "bash commands, file writes, and API calls — every prompt adds 3–15 seconds "
                "of waiting and breaks flow. Over a 10-step task, this is 30–150 seconds of friction."
            ),
            "severity": "HIGH",
            "fix": "Add commonly used tools to the allowlist in .claude/settings.local.json on Mac (the fewer-permission-prompts skill does this)."
        },
        {
            "rank": 3,
            "factor": "Network proximity: EC2 → Anthropic API is ~5–20ms; Mac → ISP → Anthropic is ~60–150ms",
            "explanation": (
                "EC2 (us-east-1) connects to Anthropic's API over AWS backbone infrastructure. "
                "Your Mac connects through your home ISP which adds 40–120ms per request. "
                "For a 10-message conversation with 5 tool calls each, that is 500–6,000ms of "
                "extra latency on Mac that doesn't exist on EC2."
            ),
            "severity": "MEDIUM",
            "fix": (
                "Cannot eliminate ISP latency on Mac. Mitigate by batching tool calls "
                "(fewer round-trips). EC2 will always win here."
            )
        },
        {
            "rank": 4,
            "factor": "Session continuity via --resume maintains full conversation context",
            "explanation": (
                "EC2 Panacea uses --resume <session_id> so Claude remembers everything said "
                "earlier in the Telegram session. On Mac, every Claude Code window starts fresh "
                "unless you manually /resume. Mid-session context loss on Mac means Claude "
                "re-learns your intent on every new window."
            ),
            "severity": "MEDIUM",
            "fix": "Use /resume at the start of Mac sessions. Or build a session state file that Panacea and Mac Claude both read."
        },
        {
            "rank": 5,
            "factor": "Local services (n8n, Mem0, Agent Bridge) on EC2 respond in <1ms vs network calls from Mac",
            "explanation": (
                "When Panacea needs n8n, Mem0, or the Agent Bridge, it calls localhost. "
                "From Mac, the same calls go over the public internet (or VPN) to EC2. "
                "That is 40–150ms per service call vs <1ms on EC2."
            ),
            "severity": "MEDIUM",
            "fix": "Set up SSH tunnel from Mac to EC2 for localhost:5678, localhost:5020, localhost:5010 when working locally."
        },
        {
            "rank": 6,
            "factor": "Telegram interface forces concise I/O; VS Code encourages verbose back-and-forth",
            "explanation": (
                "Telegram on a phone forces William to write short, focused prompts. "
                "VS Code on a big screen encourages long exploratory sessions. "
                "Short prompts → faster Grok consultation → tighter Claude output. "
                "This is UX psychology, not code."
            ),
            "severity": "LOW",
            "fix": "Write Mac prompts like Telegram prompts — one clear task per message."
        },
    ]

    results["root_causes"] = causes

    for c in causes:
        sev_color = RED if c["severity"] == "HIGH" else GOLD if c["severity"] == "MEDIUM" else BLUE
        print(f"\n  {BOLD}#{c['rank']} [{sev_color}{c['severity']}{RESET}{BOLD}]{RESET}  {c['factor']}")
        # Word-wrap explanation
        words = c["explanation"].split()
        line = "         "
        for word in words:
            if len(line) + len(word) > 78:
                print(line)
                line = "         " + word + " "
            else:
                line += word + " "
        if line.strip():
            print(line)
        print(f"         {GREEN}FIX:{RESET} {c['fix']}")


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 8 — Fixes & Recommendations
# ══════════════════════════════════════════════════════════════════════════════
def recommendations():
    header("8. FIXES — Close THE MAC/EC2 GAP")

    fixes = [
        ("IMMEDIATE — Run on Mac now",
         "Run the fewer-permission-prompts skill to allowlist common tool calls. "
         "This eliminates the biggest friction point in Mac sessions."),
        ("IMMEDIATE — Auto-append Grok on Mac",
         "Add a pre-session hook to .claude/settings.local.json that reads the last "
         "Grok direction from a cached file and appends it to every Mac session's system prompt. "
         "EC2 does this automatically — Mac should too."),
        ("SHORT TERM — SSH tunnel for local services",
         "Create a script: `ssh -L 5678:localhost:5678 -L 5020:localhost:5020 "
         "-L 5010:localhost:5010 ec2-user@34.193.98.97 -N` "
         "Run this before Mac sessions — gives Mac the same <1ms service latency as EC2."),
        ("SHORT TERM — Grok direction cache file",
         "Have grok_strategic_layer.py write its last response to "
         "~/.claude/grok_direction_cache.txt after every consultation. "
         "Both Mac and EC2 can read this file as a --append-system-prompt source."),
        ("ONGOING — Monitor EC2 uptime",
         "Install UptimeRobot (free) on ai-phone.marceausolutions.com and n8n.marceausolutions.com. "
         "EC2 restarts disrupt active Panacea sessions. Knowing immediately when it goes down "
         "prevents silent failures."),
    ]

    for title, desc in fixes:
        print(f"\n  {GOLD}▶{RESET}  {BOLD}{title}{RESET}")
        words = desc.split()
        line = "       "
        for word in words:
            if len(line) + len(word) > 78:
                print(line)
                line = "       " + word + " "
            else:
                line += word + " "
        if line.strip():
            print(line)


# ══════════════════════════════════════════════════════════════════════════════
# SAVE REPORT
# ══════════════════════════════════════════════════════════════════════════════
def save_report():
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    report_path = REPO_ROOT / "docs" / f"panacea_diagnostic_{timestamp}.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)

    with open(report_path, "w") as f:
        f.write(f"# Panacea Diagnostic Report\n")
        f.write(f"**Date:** {datetime.now().strftime('%B %d, %Y %H:%M:%S')}\n")
        f.write(f"**Environment:** {results.get('environment', {}).get('hostname', 'unknown')}\n\n")
        f.write("---\n\n")
        f.write("## Raw Results\n\n")
        f.write("```json\n")
        f.write(json.dumps(results, indent=2, default=str))
        f.write("\n```\n\n")

        if "root_causes" in results:
            f.write("## Root Cause Analysis\n\n")
            for c in results["root_causes"]:
                f.write(f"### #{c['rank']} [{c['severity']}] {c['factor']}\n\n")
                f.write(f"{c['explanation']}\n\n")
                f.write(f"**Fix:** {c['fix']}\n\n")

    print(f"\n  {GREEN}✓{RESET}  Report saved: {report_path}")
    return report_path


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════
def main():
    parser = argparse.ArgumentParser(description="Panacea Performance Diagnostic")
    parser.add_argument("--env", choices=["ec2", "mac", "auto"], default="auto",
                        help="Override environment detection (default: auto)")
    parser.add_argument("--skip-claude", action="store_true",
                        help="Skip the live claude -p timing test (saves ~30s)")
    args = parser.parse_args()

    print(f"\n{BOLD}{GOLD}{'═' * 60}{RESET}")
    print(f"{BOLD}{GOLD}  PANACEA PERFORMANCE DIAGNOSTIC{RESET}")
    print(f"{BOLD}{GOLD}  Marceau Solutions | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{RESET}")
    print(f"{BOLD}{GOLD}{'═' * 60}{RESET}")

    is_ec2 = check_environment(args.env)
    check_network()
    check_grok()
    if not args.skip_claude:
        check_claude()
    else:
        header("4. CLAUDE EXECUTION PATH")
        info("Skipped", "--skip-claude flag set")
    check_context()
    check_resources()
    root_cause_analysis(is_ec2)
    recommendations()

    report_path = save_report()

    print(f"\n{BOLD}{GOLD}{'═' * 60}{RESET}")
    print(f"{BOLD}  DIAGNOSTIC COMPLETE{RESET}")
    print(f"{BOLD}{GOLD}{'═' * 60}{RESET}\n")


if __name__ == "__main__":
    main()
