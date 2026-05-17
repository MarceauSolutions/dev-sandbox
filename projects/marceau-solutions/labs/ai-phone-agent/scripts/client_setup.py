#!/usr/bin/env python3
"""
client_setup.py — Provision a new AI phone agent client.

What this does (in order):
  1. Validates the client config payload.
  2. Creates a Twilio subaccount under the main Marceau account.
  3. Creates an ElevenLabs Conversational AI agent cloned from the master template.
  4. Writes a tenant row to the SQLite DB so app.py can route by `To` number.

What this does NOT do (yet):
  - Purchase a Twilio phone number — recommend doing that manually so you can
    pick the area code and verify caller-ID before going live.
  - Configure Twilio number webhooks — script prints the exact webhook URLs
    to paste into the Twilio console for the new subaccount.

Usage:
    python3 scripts/client_setup.py --config clients/naples-hvac.json

Config schema (clients/<slug>.json):
{
  "tenant_id": "naples-hvac",
  "business_name": "Naples HVAC Pros",
  "persona_name": "Sandra",
  "telegram_chat_id": "5692454753",
  "transfer_target_cell": "+12395550100",
  "persona_first_message": "Hi, thanks for calling Naples HVAC Pros! ...",
  "qualifying_questions": [...],
  "kb_facts": {"pricing": "...", "coverage_area": "..."}
}

Required env vars (already in repo .env):
  TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN
  ELEVENLABS_API_KEY
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Optional

import requests
from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[4]
load_dotenv(REPO_ROOT / ".env")

# Make src/ importable so we can write tenants via db.py
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import db  # noqa: E402

TWILIO_SID = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
ELEVENLABS_KEY = os.environ.get("ELEVENLABS_API_KEY")
MASTER_AGENT_ID = os.environ.get(
    "ELEVENLABS_AGENT_ID", "agent_9801kmgjg670fb7bdv5z9r96y66d",
)


def _need(var: str, value: Any) -> None:
    if not value:
        sys.exit(f"ERROR: missing required env var or value: {var}")


def create_twilio_subaccount(friendly_name: str) -> dict[str, Any]:
    """
    Creates a Twilio subaccount. Returns {sid, auth_token, friendly_name}.

    Twilio docs: https://www.twilio.com/docs/iam/api/subaccount
    """
    _need("TWILIO_ACCOUNT_SID", TWILIO_SID)
    _need("TWILIO_AUTH_TOKEN", TWILIO_TOKEN)

    resp = requests.post(
        f"https://api.twilio.com/2010-04-01/Accounts.json",
        auth=(TWILIO_SID, TWILIO_TOKEN),
        data={"FriendlyName": friendly_name},
        timeout=15,
    )
    if resp.status_code >= 300:
        sys.exit(f"ERROR: Twilio subaccount create failed: {resp.status_code} {resp.text}")
    sub = resp.json()
    return {
        "sid": sub["sid"],
        "auth_token": sub["auth_token"],
        "friendly_name": sub["friendly_name"],
        "status": sub["status"],
    }


def fetch_master_agent_config() -> dict[str, Any]:
    """Read the master ElevenLabs agent's config so we can clone its structure."""
    _need("ELEVENLABS_API_KEY", ELEVENLABS_KEY)
    resp = requests.get(
        f"https://api.elevenlabs.io/v1/convai/agents/{MASTER_AGENT_ID}",
        headers={"xi-api-key": ELEVENLABS_KEY},
        timeout=15,
    )
    if resp.status_code >= 300:
        sys.exit(f"ERROR: fetch master agent failed: {resp.status_code} {resp.text}")
    return resp.json()


def create_elevenlabs_agent(client_cfg: dict[str, Any]) -> str:
    """
    Create a new ElevenLabs agent cloned from the master, with client-specific
    first_message, persona, and qualifying questions. Returns new agent_id.
    """
    _need("ELEVENLABS_API_KEY", ELEVENLABS_KEY)
    master = fetch_master_agent_config()

    # Build the new agent payload from the master. We override:
    #   - name
    #   - first_message (with FL recording disclosure)
    #   - system prompt (encodes persona + qualifying questions)
    first_msg = client_cfg.get("persona_first_message") or (
        f"Hi, thanks for calling {client_cfg['business_name']}! "
        "Just so you know, this call may be recorded for quality and training "
        f"purposes. I'm {client_cfg.get('persona_name', 'the assistant')} — "
        "I help connect callers with the right person. Can I ask a few quick "
        "questions to make sure I get you where you need to go?"
    )

    system_prompt = _build_system_prompt(client_cfg)

    conv_cfg = (master.get("conversation_config") or {}).copy()
    agent_block = (conv_cfg.get("agent") or {}).copy()
    agent_block["first_message"] = first_msg
    prompt_block = (agent_block.get("prompt") or {}).copy()
    prompt_block["prompt"] = system_prompt
    agent_block["prompt"] = prompt_block
    conv_cfg["agent"] = agent_block

    payload = {
        "name": f"Marceau Solutions — {client_cfg['business_name']}",
        "conversation_config": conv_cfg,
    }

    resp = requests.post(
        "https://api.elevenlabs.io/v1/convai/agents/create",
        headers={"xi-api-key": ELEVENLABS_KEY, "Content-Type": "application/json"},
        json=payload,
        timeout=30,
    )
    if resp.status_code >= 300:
        sys.exit(f"ERROR: ElevenLabs agent create failed: {resp.status_code} {resp.text}")
    data = resp.json()
    return data.get("agent_id") or data.get("id") or sys.exit(
        f"ERROR: ElevenLabs response missing agent_id: {data}")


def _build_system_prompt(cfg: dict[str, Any]) -> str:
    qs = cfg.get("qualifying_questions") or []
    kb = cfg.get("kb_facts") or {}
    business = cfg.get("business_name", "the business")
    persona = cfg.get("persona_name", "the AI assistant")

    lines = [
        f"You are {persona}, the AI receptionist for {business}.",
        "Your job: qualify the caller, answer factual questions from the knowledge base, "
        "and transfer or take a message when appropriate.",
        "",
        "Voice rules:",
        "- Keep responses short (under 30 words). This is a phone call, not chat.",
        "- Never hallucinate. If you don't know, say so and offer to take a message.",
        "- If the caller asks to speak to a human, use the transfer_to_william tool.",
        "",
    ]

    if qs:
        lines.append("Qualifying questions (ask in order, one at a time):")
        for q in qs:
            lines.append(f"- {q}")
        lines.append("")

    if kb:
        lines.append("Knowledge base — answer these factually, never improvise:")
        for k, v in kb.items():
            lines.append(f"- {k}: {v}")
        lines.append("")

    lines.append(
        "At the end of the call, summarize what the caller wants in 1-2 sentences "
        "so the business owner knows what to follow up on."
    )
    return "\n".join(lines)


def provision(config_path: Path, skip_twilio: bool = False, skip_elevenlabs: bool = False) -> dict[str, Any]:
    cfg = json.loads(config_path.read_text(encoding="utf-8"))
    required = {"tenant_id", "business_name", "telegram_chat_id", "transfer_target_cell"}
    missing = required - cfg.keys()
    if missing:
        sys.exit(f"ERROR: config missing required fields: {missing}")

    print(f"\n=== Provisioning client: {cfg['business_name']} ({cfg['tenant_id']}) ===\n")

    # Step 1: Twilio subaccount
    twilio_info: Optional[dict[str, Any]] = None
    if not skip_twilio:
        print("→ Creating Twilio subaccount...")
        twilio_info = create_twilio_subaccount(friendly_name=cfg["business_name"])
        print(f"  ✓ Subaccount SID: {twilio_info['sid']}")
        print(f"  ✓ Status: {twilio_info['status']}")
    else:
        print("→ Skipping Twilio subaccount creation (--skip-twilio)")

    # Step 2: ElevenLabs agent
    new_agent_id: Optional[str] = cfg.get("elevenlabs_agent_id_override")
    if not skip_elevenlabs and not new_agent_id:
        print("→ Creating ElevenLabs agent...")
        new_agent_id = create_elevenlabs_agent(cfg)
        print(f"  ✓ Agent ID: {new_agent_id}")
    elif new_agent_id:
        print(f"→ Using override ElevenLabs agent: {new_agent_id}")
    else:
        print("→ Skipping ElevenLabs agent creation (--skip-elevenlabs)")

    # Step 3: Tenant row in SQLite
    tenant_row = {
        "tenant_id": cfg["tenant_id"],
        "twilio_number": cfg.get("twilio_number", ""),
        "business_name": cfg["business_name"],
        "persona_name": cfg.get("persona_name", ""),
        "telegram_chat_id": str(cfg["telegram_chat_id"]),
        "elevenlabs_agent_id": new_agent_id or "",
        "transfer_target_cell": cfg["transfer_target_cell"],
        "config": {
            "twilio_subaccount_sid": twilio_info["sid"] if twilio_info else None,
            "qualifying_questions": cfg.get("qualifying_questions", []),
            "kb_facts": cfg.get("kb_facts", {}),
        },
        "active": True,
    }
    print("→ Writing tenant row to SQLite...")
    tenant = db.upsert_tenant(tenant_row)
    print(f"  ✓ tenant_id: {tenant['tenant_id']}")

    # Step 4: Manual follow-ups
    print("\n=== Manual follow-up (do these in the consoles) ===")
    if twilio_info:
        print(f"1. Buy a phone number under subaccount {twilio_info['sid']}:")
        print("   https://console.twilio.com/console/phone-numbers/search")
        print("2. Configure the number's Voice webhook to:")
        print("   POST https://ai-phone.marceausolutions.com/incoming-call")
        print("3. Configure the Status Callback to:")
        print("   POST https://ai-phone.marceausolutions.com/call-status")
    print(f"4. Update the tenant row's twilio_number once you've bought it:")
    print(f"   python3 -c \"import sys; sys.path.insert(0, 'src'); import db; "
          f"db.upsert_tenant({{'tenant_id':'{cfg['tenant_id']}', 'twilio_number':'+1XXXXXXXXXX'}})\"")
    if new_agent_id:
        print(f"5. Verify the new ElevenLabs agent in the dashboard:")
        print(f"   https://elevenlabs.io/app/conversational-ai/{new_agent_id}")

    return {
        "tenant": tenant,
        "twilio_subaccount": twilio_info,
        "elevenlabs_agent_id": new_agent_id,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--config", required=True, help="Path to client config JSON")
    parser.add_argument("--skip-twilio", action="store_true", help="Don't create a Twilio subaccount")
    parser.add_argument("--skip-elevenlabs", action="store_true", help="Don't create an ElevenLabs agent")
    parser.add_argument("--dry-run", action="store_true", help="Validate config and exit without any API calls")
    args = parser.parse_args()

    cfg_path = Path(args.config)
    if not cfg_path.exists():
        sys.exit(f"ERROR: config not found: {cfg_path}")

    if args.dry_run:
        cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
        print("→ DRY RUN — config validates ok:")
        print(json.dumps(cfg, indent=2))
        return

    result = provision(cfg_path, skip_twilio=args.skip_twilio, skip_elevenlabs=args.skip_elevenlabs)
    print("\n=== Done ===")
    print(json.dumps({k: v for k, v in result.items() if k != "tenant"}, indent=2, default=str))


if __name__ == "__main__":
    main()
