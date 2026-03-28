#!/usr/bin/env python3
"""
AI Customer Service Demo — Run a simulated AI phone call.

Shows prospects what their AI receptionist would sound like.
Uses the BusinessVoiceEngine with industry-specific configuration.

Usage:
    python demo.py                    # HVAC demo (default)
    python demo.py --business hvac    # HVAC demo
    python demo.py --business medspa  # Med spa demo
    python demo.py --business plumber # Plumber demo
    python demo.py --business marceau # Marceau Solutions demo
    python demo.py --non-interactive "I need my AC fixed"  # Single turn
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path

# Load env from repo root
ROOT = Path(__file__).parent.parent.parent.parent
PROJECT = Path(__file__).parent

try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
except ImportError:
    pass

# Import as package to allow relative imports within src/
import importlib.util

def _load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod

# Pre-load config so relative imports work
_config = _load_module("src.config", PROJECT / "src" / "config.py")
_models = _load_module("src.models", PROJECT / "src" / "models.py")

# Now load business voice engine with patched imports
sys.path.insert(0, str(PROJECT))
_bve_code = (PROJECT / "src" / "business_voice_engine.py").read_text()
_bve_code = _bve_code.replace("from .config import", "from src.config import")
_bve_code = _bve_code.replace("from .models import", "from src.models import")
exec(compile(_bve_code, str(PROJECT / "src" / "business_voice_engine.py"), "exec"))
# BusinessVoiceEngine is now in local namespace

get_settings = _config.get_settings

# Business configurations for demos
DEMO_BUSINESSES = {
    "hvac": {
        "name": "Naples Comfort HVAC",
        "type": "hvac",
        "greeting": "Thank you for calling Naples Comfort HVAC! How can I help you today?",
        "services": [
            {"name": "AC Repair", "description": "Same-day emergency service", "pricing": "$89 diagnostic (waived with repair)"},
            {"name": "AC Installation", "description": "New systems with warranty", "pricing": "Free estimate"},
            {"name": "Maintenance Plans", "description": "2 tune-ups/year, priority scheduling", "pricing": "$199/year"},
            {"name": "24/7 Emergency", "description": "Nights, weekends, holidays", "pricing": "No overtime"},
        ],
        "system_prompt": """You are a professional AI receptionist for Naples Comfort HVAC in Naples, Florida.

YOUR JOB: Answer calls, book service appointments, handle emergencies, and capture lead info.

SCRIPT FLOW:
1. GREET warmly
2. ASK what they need (repair, install, maintenance, emergency)
3. If EMERGENCY: Get their address and phone, tell them a tech will call within 15 minutes
4. If SERVICE: Ask what's wrong, get their address and preferred time
5. CONFIRM all details
6. Set expectations ("A technician will call you to confirm the window")

SERVICES AND PRICING:
{services}

TONE: Professional, helpful, calm. If emergency, show urgency.
ALWAYS capture: name, phone, address, issue description.
""",
    },
    "medspa": {
        "name": "Glow Med Spa Naples",
        "type": "med_spa",
        "greeting": "Thank you for calling Glow Med Spa! How can I help you today?",
        "services": [
            {"name": "Botox", "description": "FDA-approved wrinkle treatment", "pricing": "$12/unit"},
            {"name": "Filler", "description": "Lip and cheek enhancement", "pricing": "Starting at $650"},
            {"name": "Facials", "description": "Custom medical-grade facials", "pricing": "Starting at $150"},
            {"name": "Laser Hair Removal", "description": "Permanent hair reduction", "pricing": "From $200/session"},
        ],
        "system_prompt": """You are a professional AI receptionist for Glow Med Spa in Naples, Florida.

YOUR JOB: Answer calls, book consultations, answer basic questions, capture lead info.

SCRIPT FLOW:
1. GREET warmly
2. ASK what service they're interested in
3. BRIEFLY describe the service and pricing
4. OFFER to book a free consultation
5. Capture: name, phone, email, preferred date/time
6. CONFIRM booking details

TONE: Warm, knowledgeable, reassuring. Make them feel comfortable.
ALWAYS capture: name, phone, service interest.
""",
    },
    "plumber": {
        "name": "Pro Plumbing Naples",
        "type": "plumbing",
        "greeting": "Pro Plumbing Naples, how can I help you?",
        "services": [
            {"name": "Emergency Service", "description": "24/7 burst pipes, flooding", "pricing": "No trip fee"},
            {"name": "Drain Cleaning", "description": "All drains", "pricing": "$149"},
            {"name": "Water Heater", "description": "Repair or replacement", "pricing": "Free estimate"},
            {"name": "Repiping", "description": "Whole-house repiping", "pricing": "Free inspection"},
        ],
        "system_prompt": """You are a professional AI receptionist for Pro Plumbing Naples.

YOUR JOB: Answer calls, dispatch emergencies, book service calls, capture leads.

SCRIPT FLOW:
1. GREET
2. ASK: Is this an emergency? (burst pipe, flooding, sewage)
3. If EMERGENCY: Get address + phone, dispatch immediately
4. If SERVICE: What's the issue? When works for you?
5. Capture: name, phone, address, issue
6. Confirm and set expectations

TONE: Professional, efficient, calm under pressure.
""",
    },
    "marceau": {
        "name": "Marceau Solutions",
        "type": "ai_automation",
        "greeting": "Thank you for calling Marceau Solutions! This is our AI assistant.",
        "services": [
            {"name": "Voice AI Phone Systems", "description": "24/7 call answering", "pricing": "$497/month"},
            {"name": "Lead Generation", "description": "Automated prospecting", "pricing": "Custom"},
            {"name": "Website + Automation", "description": "Website with booking", "pricing": "From $997"},
        ],
        "system_prompt": """You are a professional AI receptionist for Marceau Solutions.

YOUR JOB: Qualify leads and capture their info for William to follow up.

SCRIPT FLOW:
1. GREET warmly
2. ASK what business they're in and what they need help with
3. ASK qualifying questions about their biggest pain point
4. CAPTURE: name, phone, email, business name
5. OFFER to book a 15-minute demo with William
6. Confirm and set expectations

TONE: Professional, confident, empathetic.
""",
    },
}


def build_system_prompt(config: dict) -> str:
    """Build the full system prompt from business config."""
    services_text = "\n".join(
        f"- {s['name']}: {s['description']} ({s.get('pricing', 'Contact for pricing')})"
        for s in config.get("services", [])
    )
    return config["system_prompt"].replace("{services}", services_text)


def run_demo(business_type: str, single_input: str = None):
    """Run an interactive or single-turn demo."""
    config = DEMO_BUSINESSES.get(business_type)
    if not config:
        print(f"Unknown business type: {business_type}")
        print(f"Available: {', '.join(DEMO_BUSINESSES.keys())}")
        return

    settings = get_settings()
    if not settings.anthropic_api_key:
        print("ERROR: ANTHROPIC_API_KEY not set in .env")
        return

    system_prompt = build_system_prompt(config)
    engine = BusinessVoiceEngine(config, system_prompt)
    state = engine.create_initial_state(f"demo-{business_type}")

    if single_input:
        # Non-interactive: single turn for quick demos
        response, _ = asyncio.run(engine.process_turn(state, single_input))
        print(f"\nCaller: {single_input}")
        print(f"AI: {response}")
        return

    # Interactive demo
    print(f"\n{'=' * 60}")
    print(f"  AI RECEPTIONIST DEMO: {config['name']}")
    print(f"  Type as the caller. Type 'quit' to end.")
    print(f"{'=' * 60}\n")
    print(f"AI: {config['greeting']}\n")

    while True:
        try:
            caller_input = input("Caller: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nCall ended.")
            break

        if not caller_input:
            continue
        if caller_input.lower() == "quit":
            print("\nCall ended.")
            break

        try:
            response, state = asyncio.run(engine.process_turn(state, caller_input))
            print(f"\nAI: {response}\n")
        except Exception as e:
            print(f"\nError: {e}\n")


def main():
    parser = argparse.ArgumentParser(description="AI Customer Service Demo")
    parser.add_argument("--business", default="hvac",
                        choices=list(DEMO_BUSINESSES.keys()),
                        help="Business type for demo")
    parser.add_argument("--non-interactive", metavar="MESSAGE",
                        help="Single-turn demo with one message")
    parser.add_argument("--list", action="store_true", help="List available demos")
    args = parser.parse_args()

    if args.list:
        for btype, config in DEMO_BUSINESSES.items():
            print(f"  {btype:10s} — {config['name']}")
        return

    run_demo(args.business, single_input=args.non_interactive)


if __name__ == "__main__":
    main()
