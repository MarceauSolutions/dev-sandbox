#!/usr/bin/env python3
"""
Deploy Trial-to-Paid Conversion Sequence to n8n.

Builds and POSTs the workflow JSON to n8n API on EC2.
Run: python3 projects/shared/lead-scraper/src/deploy_trial_conversion_workflow.py

Twilio auth is embedded directly in the request URL (no n8n credential store needed).
"""

import os
import sys
import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "../../../../.env"))

N8N_BASE           = "https://n8n.marceausolutions.com"
N8N_API_KEY        = os.getenv("N8N_API_KEY")
STRIPE_LINK        = "https://buy.stripe.com/9B66oH7tBaeI0Wk8H8g360f"
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN  = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_FROM        = os.getenv("TWILIO_PHONE_NUMBER", "+18552399364")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID", "5692454753")

# Twilio URL with Basic Auth embedded — no n8n credential dependency
TWILIO_URL = (
    f"https://{TWILIO_ACCOUNT_SID}:{TWILIO_AUTH_TOKEN}"
    f"@api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/Messages.json"
)
TELEGRAM_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"


def _twilio_sms_node(node_id: str, name: str, x: int, y: int, to_expr: str, body: str) -> dict:
    """Build a Twilio SMS HTTP Request node (Basic Auth in URL, no credential store)."""
    return {
        "id": node_id,
        "name": name,
        "type": "n8n-nodes-base.httpRequest",
        "typeVersion": 4.2,
        "position": [x, y],
        "parameters": {
            "method": "POST",
            "url": TWILIO_URL,
            "authentication": "none",
            "sendBody": True,
            "contentType": "form-urlencoded",
            "bodyParameters": {
                "parameters": [
                    {"name": "From", "value": TWILIO_FROM},
                    {"name": "To",   "value": to_expr},
                    {"name": "Body", "value": body}
                ]
            },
            "options": {}
        }
    }


def _telegram_node(node_id: str, name: str, x: int, y: int, text_expr: str) -> dict:
    """Build a Telegram sendMessage HTTP Request node."""
    return {
        "id": node_id,
        "name": name,
        "type": "n8n-nodes-base.httpRequest",
        "typeVersion": 4.2,
        "position": [x, y],
        "parameters": {
            "method": "POST",
            "url": TELEGRAM_URL,
            "authentication": "none",
            "sendBody": True,
            "contentType": "json",
            "body": (
                f'{{"chat_id":"{TELEGRAM_CHAT_ID}",'
                f'"text":{text_expr},'
                '"parse_mode":"Markdown"}}'
            ),
            "options": {}
        }
    }


WORKFLOW = {
    "name": "Trial-to-Paid-Conversion-Sequence",
    "nodes": [
        # ── 1. Schedule Trigger (9am ET = 14:00 UTC) ─────────────────────────
        {
            "id": "schedule-trigger",
            "name": "Daily 9am ET",
            "type": "n8n-nodes-base.scheduleTrigger",
            "typeVersion": 1.2,
            "position": [240, 300],
            "parameters": {
                "rule": {
                    "interval": [
                        {
                            "field": "cronExpression",
                            "expression": "0 0 14 * * *"
                        }
                    ]
                }
            }
        },

        # ── 2. Code Node: Query pipeline.db directly (runs on EC2) ──────────
        {
            "id": "query-trials",
            "name": "Query Trial Active Deals",
            "type": "n8n-nodes-base.code",
            "typeVersion": 2,
            "position": [480, 300],
            "parameters": {
                "language": "python",
                "pythonCode": (
                    "import sqlite3\n"
                    "from datetime import datetime, date\n"
                    "\n"
                    "DB_PATH = '/home/clawdbot/data/pipeline.db'\n"
                    "\n"
                    "conn = sqlite3.connect(DB_PATH)\n"
                    "conn.row_factory = sqlite3.Row\n"
                    "cur = conn.cursor()\n"
                    "cur.execute(\n"
                    "    'SELECT id, company, contact_name, contact_phone, contact_email,\n"
                    "     trial_start_date, trial_end_date FROM deals\n"
                    "     WHERE stage = :stage AND trial_start_date IS NOT NULL',\n"
                    "    {'stage': 'Trial Active'}\n"
                    ")\n"
                    "rows = cur.fetchall()\n"
                    "conn.close()\n"
                    "\n"
                    "today = date.today()\n"
                    "output = []\n"
                    "for row in rows:\n"
                    "    r = dict(row)\n"
                    "    try:\n"
                    "        start = datetime.strptime(r['trial_start_date'], '%Y-%m-%d').date()\n"
                    "        r['days_elapsed'] = (today - start).days\n"
                    "        output.append(r)\n"
                    "    except Exception:\n"
                    "        pass\n"
                    "\n"
                    "return output\n"
                )
            }
        },

        # ── 3. Split into one item per deal ──────────────────────────────────
        {
            "id": "split-deals",
            "name": "Split Into Items",
            "type": "n8n-nodes-base.splitInBatches",
            "typeVersion": 3,
            "position": [720, 300],
            "parameters": {
                "batchSize": 1,
                "options": {}
            }
        },

        # ── 4. Switch: route by days_elapsed ─────────────────────────────────
        {
            "id": "route-by-day",
            "name": "Route by Day",
            "type": "n8n-nodes-base.switch",
            "typeVersion": 3,
            "position": [960, 300],
            "parameters": {
                "mode": "rules",
                "rules": {
                    "values": [
                        {
                            "conditions": {
                                "combinator": "and",
                                "conditions": [
                                    {
                                        "leftValue": "={{ $json.days_elapsed }}",
                                        "rightValue": 10,
                                        "operator": {"type": "number", "operation": "equals"}
                                    }
                                ]
                            },
                            "renameOutput": True,
                            "outputKey": "Day10"
                        },
                        {
                            "conditions": {
                                "combinator": "and",
                                "conditions": [
                                    {
                                        "leftValue": "={{ $json.days_elapsed }}",
                                        "rightValue": 13,
                                        "operator": {"type": "number", "operation": "equals"}
                                    }
                                ]
                            },
                            "renameOutput": True,
                            "outputKey": "Day13"
                        },
                        {
                            "conditions": {
                                "combinator": "and",
                                "conditions": [
                                    {
                                        "leftValue": "={{ $json.days_elapsed }}",
                                        "rightValue": 14,
                                        "operator": {"type": "number", "operation": "equals"}
                                    }
                                ]
                            },
                            "renameOutput": True,
                            "outputKey": "Day14"
                        }
                    ]
                },
                "options": {}
            }
        },

        # ── 5a. Day 10 SMS ─────────────────────────────────────────────────
        _twilio_sms_node(
            "sms-day10", "SMS Day 10 — Check-In", 1200, 80,
            to_expr="={{ $json.contact_phone }}",
            body=(
                "Hi {{ $json.contact_name }}, it's William from Marceau Solutions. "
                "Your AI system has been running for 10 days — wanted to share a quick update. "
                "Your missed-call text-back has been active 24/7. "
                "How is it going so far? Reply anytime."
            )
        ),

        # ── 5b. Day 10 Telegram alert ──────────────────────────────────────
        _telegram_node(
            "telegram-day10", "Telegram Day 10 Alert", 1200, 240,
            text_expr=(
                '"Trial Day 10 — Check-In Sent\\n\\n"'
                ' + "Company: " + $json.company + "\\n"'
                ' + "Contact: " + $json.contact_name + "\\n"'
                ' + "Phone: " + $json.contact_phone + "\\n"'
                ' + "\\nSMS check-in sent. Watch for a reply."'
            )
        ),

        # ── 6a. Day 13 SMS ─────────────────────────────────────────────────
        _twilio_sms_node(
            "sms-day13", "SMS Day 13 — Trial Ending", 1200, 400,
            to_expr="={{ $json.contact_phone }}",
            body=(
                f"Hi {{{{ $json.contact_name }}}}, just a heads up — your free trial ends in 1 day. "
                f"To keep your AI system running: {STRIPE_LINK} "
                f"Takes 2 min. Reply STOP to cancel. - William"
            )
        ),

        # ── 6b. Day 13 Telegram alert ──────────────────────────────────────
        _telegram_node(
            "telegram-day13", "Telegram Day 13 Alert", 1200, 560,
            text_expr=(
                '"Trial Ending Tomorrow — Day 13\\n\\n"'
                ' + "Company: " + $json.company + "\\n"'
                ' + "Contact: " + $json.contact_name + "\\n"'
                ' + "Phone: " + $json.contact_phone + "\\n"'
                ' + "Email: " + $json.contact_email + "\\n"'
                f' + "\\nPayment SMS sent. Consider a personal call if no reply.\\n"'
                f' + "Stripe: {STRIPE_LINK}"'
            )
        ),

        # ── 7. Day 14 SMS ──────────────────────────────────────────────────
        _twilio_sms_node(
            "sms-day14", "SMS Day 14 — Trial Ended", 1200, 720,
            to_expr="={{ $json.contact_phone }}",
            body=(
                f"Hi {{{{ $json.contact_name }}}}, your free trial has ended. "
                f"To reactivate: {STRIPE_LINK} "
                f"Or reply to this message and we can talk. Thanks for trying it — William"
            )
        )
    ],

    "connections": {
        "Daily 9am ET": {
            "main": [[{"node": "Query Trial Active Deals", "type": "main", "index": 0}]]
        },
        "Query Trial Active Deals": {
            "main": [[{"node": "Split Into Items", "type": "main", "index": 0}]]
        },
        "Split Into Items": {
            "main": [[{"node": "Route by Day", "type": "main", "index": 0}]]
        },
        "Route by Day": {
            "Day10": [
                [{"node": "SMS Day 10 — Check-In",   "type": "main", "index": 0}],
                [{"node": "Telegram Day 10 Alert",    "type": "main", "index": 0}]
            ],
            "Day13": [
                [{"node": "SMS Day 13 — Trial Ending", "type": "main", "index": 0}],
                [{"node": "Telegram Day 13 Alert",     "type": "main", "index": 0}]
            ],
            "Day14": [
                [{"node": "SMS Day 14 — Trial Ended", "type": "main", "index": 0}]
            ]
        }
    },

    "settings": {
        "executionOrder": "v1",
        "saveManualExecutions": True,
        "callerPolicy": "workflowsFromSameOwner",
        "errorWorkflow": "Ob7kiVvCnmDHAfNW"
    }
}


def deploy():
    headers = {
        "X-N8N-API-KEY": N8N_API_KEY,
        "Content-Type": "application/json"
    }

    # Check if workflow already exists
    print("Checking for existing workflow...")
    resp = requests.get(
        f"{N8N_BASE}/api/v1/workflows?limit=200",
        headers=headers,
        timeout=15
    )
    resp.raise_for_status()
    existing_id = None
    for w in resp.json().get("data", []):
        if w["name"] == WORKFLOW["name"]:
            existing_id = w["id"]
            print(f"Existing workflow found: {existing_id} — updating.")
            break

    if existing_id:
        resp = requests.put(
            f"{N8N_BASE}/api/v1/workflows/{existing_id}",
            headers=headers,
            json=WORKFLOW,
            timeout=15
        )
    else:
        print("Creating new workflow...")
        resp = requests.post(
            f"{N8N_BASE}/api/v1/workflows",
            headers=headers,
            json=WORKFLOW,
            timeout=15
        )

    if resp.status_code not in (200, 201):
        print(f"Deployment failed: {resp.status_code}")
        print(resp.text[:600])
        sys.exit(1)

    workflow_id = resp.json()["id"]
    print(f"Workflow saved: {workflow_id}")

    # Activate via POST /activate endpoint
    act = requests.post(
        f"{N8N_BASE}/api/v1/workflows/{workflow_id}/activate",
        headers=headers,
        timeout=15
    )
    if act.status_code in (200, 201):
        print("Workflow activated.")
    else:
        print(f"Activation response: {act.status_code} — {act.text[:200]}")

    return workflow_id


if __name__ == "__main__":
    if not N8N_API_KEY:
        print("ERROR: N8N_API_KEY not found in .env")
        sys.exit(1)
    if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN:
        print("ERROR: TWILIO_ACCOUNT_SID / TWILIO_AUTH_TOKEN not found in .env")
        sys.exit(1)
    if not TELEGRAM_BOT_TOKEN:
        print("ERROR: TELEGRAM_BOT_TOKEN not found in .env")
        sys.exit(1)

    wf_id = deploy()
    print(f"\nDone. Workflow ID: {wf_id}")
    print("Name: Trial-to-Paid-Conversion-Sequence")
    print("Schedule: Daily 9am ET (0 0 14 * * * UTC)")
    print("SMS triggers: Trial days 10, 13, 14")
    print("Telegram alerts: Days 10 and 13")
    print(f"View: https://n8n.marceausolutions.com/workflow/{wf_id}")
