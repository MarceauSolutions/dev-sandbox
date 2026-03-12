#!/usr/bin/env python3
"""
launch.py — Interactive Product Launch Runner

Run from dev-sandbox root:
    python scripts/launch.py

No flags, no file paths to remember. Picks up where you left off.
"""

import os
import sys
import json
import subprocess
import time
from pathlib import Path
from datetime import datetime, timedelta

ROOT = Path(__file__).resolve().parent.parent

# ─── Colors ──────────────────────────────────────────────────────────────────
CLEAR  = "\033[2J\033[H"
BOLD   = "\033[1m"
DIM    = "\033[2m"
GOLD   = "\033[38;2;201;150;60m"
GREEN  = "\033[32m"
RED    = "\033[31m"
YELLOW = "\033[33m"
CYAN   = "\033[36m"
RESET  = "\033[0m"

# ─── Product Registry ────────────────────────────────────────────────────────
# Each product has a launch_manager.py and a state file.
# Add new products here as they get launch systems built.

def discover_products():
    """Auto-discover any project with a launch/launch_manager.py."""
    products = []
    for manager in sorted(ROOT.glob("projects/**/launch/launch_manager.py")):
        project_dir = manager.parent.parent
        state_file = manager.parent / "launch_state.json"
        state = {}
        if state_file.exists():
            try:
                with open(state_file) as f:
                    state = json.load(f)
            except Exception:
                pass
        products.append({
            "name": project_dir.name,
            "dir": project_dir,
            "manager": manager,
            "state": state,
            "phase": state.get("phase", "preflight"),
        })
    return products


PHASE_LABELS = {
    "preflight":          (DIM,    "Not started"),
    "organic_validation": (CYAN,   "Validating — organic window running"),
    "gate_passed":        (GREEN,  "Gate passed — ready for paid ads"),
    "paid_ads":           (YELLOW, "Paid ads running"),
    "scaling":            (GOLD,   "Scaling"),
    "killed":             (RED,    "No-go / paused"),
}

PIPELINE_STEPS = [
    {
        "phase":       "preflight",
        "label":       "Pre-Launch Check",
        "description": "Verify landing page, automation workflows, and data collection are all live.",
        "command":     "preflight",
        "next_phase":  "organic_validation",
    },
    {
        "phase":       "organic_validation",
        "label":       "Organic Validation",
        "description": "Start the 48h content window. Posts to Reddit, Twitter, Instagram, TikTok, HN.",
        "command":     "validate",
        "next_phase":  "organic_validation",
    },
    {
        "phase":       "organic_validation",
        "label":       "Live Monitor",
        "description": "Watch signups in real time. Get a text when you hit 25, 50, 100.",
        "command":     "watch",
        "background":  True,
        "next_phase":  "organic_validation",
    },
    {
        "phase":       "organic_validation",
        "label":       "Validation Gate",
        "description": "Evaluate results after 48h. Get a scored GO / PIVOT / NO-GO decision.",
        "command":     "gate",
        "next_phase":  "gate_passed",
    },
    {
        "phase":       "gate_passed",
        "label":       "Launch Report",
        "description": "Generate a branded PDF with all metrics, sources, and next actions.",
        "command":     "report",
        "next_phase":  "gate_passed",
    },
]

ANYTIME_STEPS = [
    {"label": "Status",         "description": "Current phase, signups, UTM breakdown",  "command": "status"},
    {"label": "Iterate Copy",   "description": "Get 5 new A/B copy variants to test",    "command": "iterate"},
    {"label": "Feedback",       "description": "Surface SMS drip replies as market signal", "command": "feedback"},
    {"label": "Mark Post Done", "description": "Mark a content post as completed",        "command": "_mark"},
    {"label": "Report",         "description": "Generate branded PDF launch report",      "command": "report"},
]

# ─── Helpers ─────────────────────────────────────────────────────────────────

def header(subtitle=""):
    print(CLEAR, end="")
    print(f"{GOLD}{BOLD}")
    print("  ╔══════════════════════════════════════════╗")
    print("  ║       PRODUCT LAUNCH MANAGER             ║")
    if subtitle:
        padded = subtitle[:42].center(42)
        print(f"  ║  {DIM}{padded}{RESET}{GOLD}{BOLD}  ║")
    print("  ╚══════════════════════════════════════════╝")
    print(f"{RESET}")


def run_manager(product, command, extra_args=None, interactive=False):
    """Run a launch_manager command and stream output."""
    cmd = [sys.executable, str(product["manager"]), command]
    if interactive and command == "validate":
        cmd.append("--interactive")
    if extra_args:
        cmd.extend(extra_args)
    print(f"\n  {DIM}Running: {' '.join(cmd[2:])}{RESET}\n")
    result = subprocess.run(cmd, cwd=str(ROOT))
    return result.returncode == 0


def prompt(message, options=None):
    """Print a prompt and return input. Shows options if provided."""
    if options:
        opts = "  /  ".join(f"{GOLD}{k}{RESET} {DIM}{v}{RESET}" for k, v in options.items())
        print(f"  {opts}")
    print(f"  {GOLD}›{RESET} ", end="")
    try:
        return input().strip()
    except (KeyboardInterrupt, EOFError):
        return "q"


def get_validation_hours(state):
    if not state.get("validation_started"):
        return None, None
    started = datetime.fromisoformat(state["validation_started"])
    elapsed = (datetime.now() - started).total_seconds() / 3600
    remaining = max(0, 48 - elapsed)
    return elapsed, remaining


def reload_state(product):
    state_file = product["manager"].parent / "launch_state.json"
    if state_file.exists():
        try:
            with open(state_file) as f:
                product["state"] = json.load(f)
                product["phase"] = product["state"].get("phase", "preflight")
        except Exception:
            pass


# ─── Screens ─────────────────────────────────────────────────────────────────

def screen_product_select():
    """Show all products and let user pick one."""
    while True:
        products = discover_products()
        header("Select a Product")

        if not products:
            print(f"  {RED}No products with launch systems found.{RESET}")
            print(f"  {DIM}Add a launch/launch_manager.py to a project to register it here.{RESET}\n")
            return None

        print(f"  {BOLD}Your Products{RESET}\n")
        for i, p in enumerate(products):
            phase = p["phase"]
            p_color, p_label = PHASE_LABELS.get(phase, (DIM, phase))

            # Signups
            signups = p["state"].get("gate_signups", "")
            signup_str = f"  {DIM}{signups} signups{RESET}" if signups else ""

            # Time remaining
            elapsed, remaining = get_validation_hours(p["state"])
            time_str = ""
            if remaining is not None and remaining > 0:
                time_str = f"  {DIM}{remaining:.0f}h left{RESET}"
            elif remaining == 0:
                time_str = f"  {YELLOW}window closed → gate{RESET}"

            print(f"    {GOLD}{i + 1}{RESET}  {BOLD}{p['name']}{RESET}")
            print(f"       {p_color}{p_label}{RESET}{signup_str}{time_str}")

        print(f"\n    {DIM}q  Quit{RESET}\n")
        choice = prompt("Pick a product")

        if choice.lower() == "q":
            return None
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(products):
                return products[idx]
        except ValueError:
            pass


def screen_product_dashboard(product):
    """Main dashboard for a selected product. Shows phase and next action."""
    while True:
        reload_state(product)
        phase = product["phase"]
        state = product["state"]

        header(product["name"].replace("-", " ").title())

        # Phase banner
        p_color, p_label = PHASE_LABELS.get(phase, (DIM, phase))
        print(f"  {BOLD}Phase:{RESET}  {p_color}{p_label}{RESET}")

        # Validation window
        elapsed, remaining = get_validation_hours(state)
        if elapsed is not None:
            pct = min(int(elapsed / 48 * 20), 20)
            bar = "█" * pct + "░" * (20 - pct)
            print(f"  {BOLD}Window:{RESET} {GOLD}{bar}{RESET}  {elapsed:.1f}h / 48h", end="")
            if remaining and remaining > 0:
                print(f"  {DIM}({remaining:.0f}h left){RESET}")
            else:
                print(f"  {YELLOW}  CLOSED{RESET}")

        # Posts progress
        posts_done = len(state.get("posts_completed", {}))
        if posts_done > 0:
            print(f"  {BOLD}Posts:{RESET}   {posts_done}/10 completed")

        # Gate decision
        if state.get("gate_decision"):
            gd = state["gate_decision"]
            gd_color = {
                "GO": GREEN, "PIVOT": YELLOW, "NO-GO": RED
            }.get(gd, RESET)
            at = state.get("gate_decided_at", "")[:10]
            sigs = state.get("gate_signups", 0)
            print(f"  {BOLD}Gate:{RESET}    {gd_color}{BOLD}{gd}{RESET}  {DIM}({at}, {sigs} signups){RESET}")

        print()

        # ── Recommended next step ──
        next_step = _get_next_step(phase, state)
        if next_step:
            print(f"  {GOLD}{BOLD}Recommended Next Step{RESET}")
            print(f"  {BOLD}{next_step['label']}{RESET}")
            print(f"  {DIM}{next_step['description']}{RESET}\n")

        # ── Menu ──
        print(f"  {BOLD}What do you want to do?{RESET}\n")

        options = {}
        if next_step:
            options["1"] = f"→ {next_step['label']} (recommended)"

        options["2"] = "Status & metrics"
        options["3"] = "Iterate copy variants"
        options["4"] = "Mark a post as done"
        options["5"] = "Feedback / SMS replies"
        options["6"] = "Generate report PDF"
        options["7"] = "Generate image + post content (next ready platform)"
        options["8"] = "Open Web Dashboard (full SaaS view)"
        options["b"] = "Back to products"
        options["q"] = "Quit"

        for k, v in options.items():
            color = GOLD if k == "1" else (DIM if k in ("b", "q") else "")
            rst = RESET if color else ""
            print(f"    {color}{k}{rst}  {v}")

        print()
        choice = prompt("Choose")

        if choice == "1" and next_step:
            _run_step(product, next_step)
        elif choice == "2":
            run_manager(product, "status")
            _pause()
        elif choice == "3":
            run_manager(product, "iterate")
            _pause()
        elif choice == "4":
            _mark_post(product)
        elif choice == "5":
            run_manager(product, "feedback")
            _pause()
        elif choice == "6":
            run_manager(product, "report")
            _pause()
        elif choice == "7":
            _post_content(product)
        elif choice == "8":
            _open_web_dashboard(product)
        elif choice.lower() == "b":
            return
        elif choice.lower() == "q":
            _exit()


def _get_next_step(phase, state):
    """Return the most logical next step for the current phase."""
    # If validation window is closed and gate not run yet
    if phase == "organic_validation":
        _, remaining = get_validation_hours(state)
        if remaining is not None and remaining <= 0 and not state.get("gate_decision"):
            return {
                "label":       "Validation Gate",
                "description": "48h window is closed. Evaluate your results now.",
                "command":     "gate",
            }
        # If posts remain and window is open
        posts_done = len(state.get("posts_completed", {}))
        if posts_done < 10:
            return {
                "label":       "Post Content",
                "description": f"{posts_done}/10 posts done. Open your posting schedule.",
                "command":     "validate",
            }

    # Default pipeline steps
    for step in PIPELINE_STEPS:
        if step["phase"] == phase:
            return step

    if phase == "gate_passed":
        return {
            "label":       "Generate Report",
            "description": "Document your validated results in a branded PDF.",
            "command":     "report",
        }

    return None


def _run_step(product, step):
    """Run a pipeline step, handling special cases."""
    command = step.get("command")

    if command == "_mark":
        _mark_post(product)
        return

    if step.get("background"):
        print(f"\n  {CYAN}This runs in the background — open a new terminal tab and run:{RESET}")
        print(f"\n  {BOLD}python scripts/launch.py watch {product['name']}{RESET}")
        print(f"\n  {DIM}Or run directly:{RESET}")
        print(f"  python {product['manager']} watch\n")
        _pause()
        return

    run_manager(product, command, interactive=True)

    # After showing the posting schedule, immediately offer to mark a post done
    if command == "validate":
        print(f"\n  {GOLD}Did you complete a post while reading the schedule?{RESET}")
        print(f"  {DIM}y  Mark it now    Enter  Back to menu{RESET}")
        print(f"  {GOLD}›{RESET} ", end="")
        try:
            answer = input().strip().lower()
        except (KeyboardInterrupt, EOFError):
            answer = ""
        if answer == "y":
            _mark_post(product)
            return
    else:
        _pause()


def _mark_post(product):
    """Interactive post-marking flow."""
    state = product["state"]
    posts_done = state.get("posts_completed", {})

    POSTING_SCHEDULE = [
        {"order": 1,  "platform": "Reddit r/nosurf",           "key": "reddit_nosurf"},
        {"order": 2,  "platform": "Twitter/X thread",           "key": "twitter"},
        {"order": 3,  "platform": "Reddit r/productivity",      "key": "reddit_productivity"},
        {"order": 4,  "platform": "Instagram Reel",             "key": "instagram"},
        {"order": 5,  "platform": "Reddit r/digitalminimalism", "key": "reddit_dm"},
        {"order": 6,  "platform": "TikTok",                     "key": "tiktok"},
        {"order": 7,  "platform": "Reddit r/dumbphones",        "key": "reddit_dumbphones"},
        {"order": 8,  "platform": "Hacker News Show HN",        "key": "hackernews"},
        {"order": 9,  "platform": "Reddit r/getdisciplined",    "key": "reddit_getdisciplined"},
        {"order": 10, "platform": "Reddit comments (hunt)",     "key": "reddit_comments"},
    ]

    pending = [p for p in POSTING_SCHEDULE if p["key"] not in posts_done]

    print(f"\n  {BOLD}Which post did you complete?{RESET}\n")
    for i, p in enumerate(pending):
        print(f"    {GOLD}{i + 1}{RESET}  {p['platform']}")

    if not pending:
        print(f"  {GREEN}All posts completed!{RESET}")
        _pause()
        return

    print()
    choice = prompt("Pick a number (or Enter to cancel)")
    if not choice:
        return
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(pending):
            key = pending[idx]["key"]
            run_manager(product, "validate", ["--mark", key], interactive=True)
            _pause()
    except ValueError:
        pass


def _post_content(product):
    """Run the content pipeline for the next ready platform, then offer to mark it done."""
    pipeline_script = product["manager"].parent / "content_pipeline.py"
    if not pipeline_script.exists():
        print(f"\n  {RED}content_pipeline.py not found for this product.{RESET}\n")
        _pause()
        return

    # Ask which platform to post (default: auto next ready)
    reload_state(product)
    state = product["state"]
    posts_done = set(state.get("posts_completed", {}).keys())

    POSTING_SCHEDULE = [
        {"order": 1,  "key": "reddit_nosurf",       "platform": "Reddit r/nosurf"},
        {"order": 2,  "key": "twitter",              "platform": "Twitter/X thread"},
        {"order": 3,  "key": "reddit_productivity",  "platform": "Reddit r/productivity"},
        {"order": 4,  "key": "instagram",            "platform": "Instagram Reel"},
        {"order": 5,  "key": "reddit_dm",            "platform": "Reddit r/digitalminimalism"},
        {"order": 6,  "key": "tiktok",               "platform": "TikTok"},
        {"order": 7,  "key": "reddit_dumbphones",    "platform": "Reddit r/dumbphones"},
        {"order": 8,  "key": "hackernews",           "platform": "Hacker News Show HN"},
        {"order": 9,  "key": "reddit_getdisciplined","platform": "Reddit r/getdisciplined"},
        {"order": 10, "key": "reddit_comments",      "platform": "Reddit comments (hunt)"},
    ]
    pending = [p for p in POSTING_SCHEDULE if p["key"] not in posts_done]

    if not pending:
        print(f"\n  {GREEN}All posts completed!{RESET}\n")
        _pause()
        return

    print(f"\n  {BOLD}Which platform do you want to post to?{RESET}\n")
    for i, p in enumerate(pending):
        print(f"    {GOLD}{i + 1}{RESET}  {p['platform']}")

    print(f"\n  {DIM}Enter  Auto-select next ready{RESET}")
    print(f"  {GOLD}›{RESET} ", end="")
    try:
        choice = input().strip()
    except (KeyboardInterrupt, EOFError):
        return

    if choice:
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(pending):
                key = pending[idx]["key"]
            else:
                return
        except ValueError:
            return
    else:
        key = pending[0]["key"]

    # Run content pipeline
    cmd = [sys.executable, str(pipeline_script), "post", key]
    print(f"\n  {DIM}Running content pipeline for {key}...{RESET}\n")
    subprocess.run(cmd, cwd=str(ROOT))

    # Offer to mark it done
    print(f"\n  {GOLD}Did you complete the post? Mark it as done?{RESET}")
    print(f"  {DIM}y  Mark done    Enter  Skip{RESET}")
    print(f"  {GOLD}›{RESET} ", end="")
    try:
        answer = input().strip().lower()
    except (KeyboardInterrupt, EOFError):
        answer = ""
    if answer == "y":
        run_manager(product, "validate", ["--mark", key], interactive=True)

    _pause()


def _open_web_dashboard(product):
    """Start the LaunchPad Flask server and open the browser."""
    import webbrowser
    app_path = ROOT / "projects" / "marceau-solutions" / "labs" / "launch-platform" / "src" / "app.py"
    if not app_path.exists():
        print(f"\n  {RED}LaunchPad web app not found at:{RESET}")
        print(f"  {DIM}{app_path}{RESET}\n")
        _pause()
        return

    port = 8765
    url  = f"http://127.0.0.1:{port}"
    print(f"\n  {GOLD}{BOLD}Starting LaunchPad web dashboard...{RESET}")
    print(f"  {DIM}URL: {url}{RESET}\n")
    print(f"  {DIM}Press Ctrl+C in this terminal to stop the server.{RESET}\n")

    # Open browser after brief delay (server needs a moment to start)
    import threading
    def open_browser():
        time.sleep(1.5)
        webbrowser.open(url)

    t = threading.Thread(target=open_browser, daemon=True)
    t.start()

    try:
        subprocess.run(
            [sys.executable, str(app_path), "--product", product["name"], "--port", str(port)],
            cwd=str(ROOT)
        )
    except KeyboardInterrupt:
        print(f"\n  {DIM}Web dashboard stopped.{RESET}\n")


def _pause():
    print(f"\n  {DIM}Press Enter to continue...{RESET}", end="")
    try:
        input()
    except (KeyboardInterrupt, EOFError):
        pass


def _exit():
    print(f"\n  {DIM}Goodbye.{RESET}\n")
    sys.exit(0)


# ─── Entry Point ─────────────────────────────────────────────────────────────

def main():
    # Handle direct watch shortcut: python scripts/launch.py watch <product>
    if len(sys.argv) >= 3 and sys.argv[1] == "watch":
        products = discover_products()
        name = sys.argv[2]
        match = next((p for p in products if p["name"] == name), None)
        if match:
            subprocess.run([sys.executable, str(match["manager"]), "watch"], cwd=str(ROOT))
        else:
            print(f"Product '{name}' not found.")
        return

    try:
        while True:
            product = screen_product_select()
            if product is None:
                _exit()
            screen_product_dashboard(product)
    except (KeyboardInterrupt, EOFError):
        _exit()


if __name__ == "__main__":
    main()
