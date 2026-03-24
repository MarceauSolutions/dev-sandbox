#!/usr/bin/env python3
"""
close_deal.py — Send a filled proposal + service agreement to a prospect and log the outreach.

USAGE EXAMPLE:
    python projects/marceau-solutions/digital/tools/web-dev/close_deal.py \
        --client-name "Mike Johnson" \
        --business-name "Johnson HVAC" \
        --email "mike@johnsonhvac.com" \
        --tier 1 \
        --pain-point "Missing calls after hours, no follow-up system"

TIERS:
    1 — Starter  ($297/mo + $500 setup)    STRIPE_AI_PAYMENT_LINK (live in .env)
    2 — Growth   ($497/mo + $750 setup)    STRIPE_TIER2_PAYMENT_LINK
    3 — Pro      ($997/mo + $1,000 setup)  STRIPE_TIER3_PAYMENT_LINK
    4 — Elite    ($1,497/mo + $1,500 setup) STRIPE_TIER4_PAYMENT_LINK

OUTPUTS:
    - Proposal PDF (temp, attached to email)
    - Service agreement PDF (temp, attached to email)
    - Log entry in projects/shared/lead-scraper/output/outreach_tracking_2026-03-23.json
"""

import argparse
import importlib.util
import json
import os
import smtplib
import sys
import uuid
from datetime import datetime
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Path setup — run from any working directory
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[5]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
load_dotenv(REPO_ROOT / ".env")

# Now that REPO_ROOT is on the path, engine imports work
from execution.branded_pdf_engine import BrandedPDFEngine  # noqa: E402

# ---------------------------------------------------------------------------
# Tier configuration
# ---------------------------------------------------------------------------
TIER_CONFIG = {
    1: {
        "name": "Tier 1 — Starter",
        "setup": "$500",
        "monthly": "$297/month",
        "env_key": "STRIPE_AI_PAYMENT_LINK",
        "fallback": "https://buy.stripe.com/9B66oH7tBaeI0Wk8H8g360f",
    },
    2: {
        "name": "Tier 2 — Growth",
        "setup": "$750",
        "monthly": "$497/month",
        "env_key": "STRIPE_TIER2_PAYMENT_LINK",
        "fallback": None,
    },
    3: {
        "name": "Tier 3 — Pro",
        "setup": "$1,000",
        "monthly": "$997/month",
        "env_key": "STRIPE_TIER3_PAYMENT_LINK",
        "fallback": None,
    },
    4: {
        "name": "Tier 4 — Elite",
        "setup": "$1,500",
        "monthly": "$1,497/month",
        "env_key": "STRIPE_TIER4_PAYMENT_LINK",
        "fallback": None,
    },
}


def get_payment_link(tier: int) -> str:
    """Return the Stripe payment link for the given tier."""
    config = TIER_CONFIG[tier]
    link = os.getenv(config["env_key"]) or config["fallback"]
    if not link:
        return f"[Payment link TBD — set {config['env_key']} in .env]"
    return link


# ---------------------------------------------------------------------------
# PDF generation
# ---------------------------------------------------------------------------

def generate_proposal_pdf(client_name: str, business_name: str, tier: int,
                           pain_point: str, output_path: str) -> str:
    """Generate a filled proposal PDF for this client."""
    config = TIER_CONFIG[tier]
    payment_link = get_payment_link(tier)

    data = {
        "client_name": client_name,
        "business_name": business_name,
        "industry": "Service Business",
        "problem_statement": pain_point,
        "solution": (
            f"We'll build you a custom AI phone and text intake system that captures every "
            f"lead, follows up automatically, and frees you from manual outreach. "
            f"Selected plan: {config['name']}."
        ),
        "solution_details": [
            "AI phone & text intake — answers calls and texts 24/7, qualifies leads",
            "Automated follow-up sequences via SMS + email",
            "Monthly optimization — prompt tuning, workflow improvements, reporting",
            "2-week free onboarding — you pay nothing until you decide to continue",
            "30-day cancellation policy — no long-term lock-in",
        ],
        "timeline": "2 weeks",
        "timeline_steps": [
            {"when": "Week 1", "what": "Kickoff call, gather business info, build & configure the system"},
            {"when": "Week 2", "what": "Testing, refinements, your review"},
            {"when": "End of Week 2", "what": "Go/no-go decision — continue with no obligation or activate subscription"},
        ],
        "investment": {
            "setup": config["setup"],
            "monthly": config["monthly"],
        },
        "guarantee": (
            "2-week free trial. If you don't see value, cancel with zero charges. "
            "After that, 30-day written notice to cancel at any time."
        ),
        "next_steps": (
            f"Reply to this email confirming you'd like to proceed — or click your payment link below. "
            f"I'll kick off the free 2-week build immediately.\n\n"
            f"Payment link ({config['name']}): {payment_link}"
        ),
    }

    engine = BrandedPDFEngine()
    engine.generate_to_file("proposal", data, output_path)
    return output_path


def generate_agreement_pdf(client_name: str, business_name: str, tier: int,
                            output_path: str) -> str:
    """Generate a filled service agreement PDF for this client."""
    config = TIER_CONFIG[tier]
    today = datetime.now().strftime("%B %d, %Y")

    data = {
        "client_business_name": business_name,
        "client_owner_name": client_name,
        "effective_date": today,
        "setup_fee": config["setup"],
        "monthly_rate": config["monthly"],
        "tier_name": config["name"],
        "client_title": "Owner",
    }

    engine = BrandedPDFEngine()
    engine.generate_to_file("agreement", data, output_path)
    return output_path


# ---------------------------------------------------------------------------
# Email
# ---------------------------------------------------------------------------

def _signing_block(signing_url: str) -> str:
    """Return HTML block for the signing button — extracted to avoid nested f-string (Python 3.9 compat)."""
    if not signing_url:
        return ""
    return (
        '<div style="background: #0d1117; border: 1px solid #30363d; border-radius: 10px;'
        ' padding: 16px 20px; margin: 0 0 24px; text-align: center;">'
        '<p style="font-size: 13px; color: #8b949e; margin-bottom: 10px;">Sign your agreement online — no printing required:</p>'
        '<a href="' + signing_url + '"'
        ' style="background: #C9963C; color: #1a1000; padding: 11px 24px; text-decoration: none;'
        ' border-radius: 7px; font-weight: 700; font-size: 14px; display: inline-block;">'
        'Review &amp; Sign Agreement &rarr;'
        '</a>'
        '<p style="font-size: 11px; color: #8b949e; margin-top: 8px; word-break: break-all;">' + signing_url + '</p>'
        '</div>'
    )


def build_email(client_name: str, business_name: str, tier: int,
                recipient_email: str, proposal_path: str, agreement_path: str,
                signing_url: str = "") -> MIMEMultipart:
    """Build the email with both PDFs attached."""
    sender_name = os.getenv("SENDER_NAME", "William Marceau")
    sender_email = os.getenv("SENDER_EMAIL", "wmarceau@marceausolutions.com")
    payment_link = get_payment_link(tier)
    config = TIER_CONFIG[tier]
    first_name = client_name.split()[0] if client_name else "there"

    msg = MIMEMultipart("mixed")
    msg["Subject"] = f"Your AI System Proposal — {business_name}"
    msg["From"] = f"{sender_name} <{sender_email}>"
    msg["To"] = recipient_email

    # Plain text body
    signing_line = f"\nSIGN YOUR AGREEMENT ONLINE:\n{signing_url}\n" if signing_url else ""
    text_body = f"""Hi {first_name},

Great talking with you. Here's your proposal and service agreement as discussed.

To get started, just reply confirming you'd like to proceed — or use the payment link below. I'll kick off the free 2-week build immediately. You owe nothing until you decide to continue after the trial.

SELECTED PACKAGE: {config['name']}
MONTHLY RATE: {config['monthly']}
FREE TRIAL: 2 weeks (no charge)
AFTER TRIAL: Cancel anytime with 30 days notice

PAYMENT LINK:
{payment_link}
{signing_line}
The two documents attached are:
  1. Your proposal — overview of what we're building and why
  2. Service agreement — terms, free trial details, and cancellation policy

Any questions, just reply here.

William Marceau
Marceau Solutions
wmarceau@marceausolutions.com
(239) 398-5676
marceausolutions.com
"""

    # HTML body
    payment_link_display = payment_link if "TBD" not in payment_link else "Payment link coming shortly"
    payment_button = (
        f'<a href="{payment_link}" style="background-color: #C9963C; color: #ffffff; '
        f'padding: 12px 28px; text-decoration: none; border-radius: 6px; font-weight: 600; '
        f'display: inline-block; font-size: 15px;">'
        f'Activate Your Free Trial &rarr;</a>'
        if "TBD" not in payment_link
        else f'<p style="color: #94a3b8; font-size: 14px;">Payment link coming shortly.</p>'
    )

    html_body = f"""
<html>
<head></head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
             line-height: 1.7; color: #1a1a2e; max-width: 600px; margin: 0 auto;
             padding: 20px; background-color: #f8f9fa;">

  <div style="background: linear-gradient(135deg, #333333, #2D2D2D); padding: 30px;
              border-radius: 12px 12px 0 0; text-align: center;">
    <h1 style="color: #C9963C; margin: 0; font-size: 22px;">Your AI System Proposal</h1>
    <p style="color: #94a3b8; margin: 8px 0 0; font-size: 14px;">{business_name}</p>
  </div>

  <div style="background: white; padding: 30px; border-radius: 0 0 12px 12px;
              box-shadow: 0 2px 10px rgba(0,0,0,0.1);">

    <p style="font-size: 16px;">Hi {first_name},</p>

    <p>Great talking with you. Here's your proposal and service agreement as discussed.</p>

    <p>To get started, just <strong>reply to this email</strong> confirming you'd like to
    proceed — or click the button below. I'll kick off the free 2-week build immediately.
    <strong>You owe nothing until you decide to continue after the trial.</strong></p>

    <div style="background: #FDF8EF; border-left: 4px solid #C9963C; padding: 16px 20px;
                margin: 24px 0; border-radius: 0 8px 8px 0;">
      <table style="width: 100%; font-size: 14px; border-collapse: collapse;">
        <tr>
          <td style="padding: 5px 0; color: #64748b; width: 50%;">Selected Package</td>
          <td style="padding: 5px 0; font-weight: 600;">{config['name']}</td>
        </tr>
        <tr>
          <td style="padding: 5px 0; color: #64748b;">Monthly Rate</td>
          <td style="padding: 5px 0; font-weight: 600;">{config['monthly']}</td>
        </tr>
        <tr>
          <td style="padding: 5px 0; color: #64748b;">Free Trial</td>
          <td style="padding: 5px 0; font-weight: 600; color: #C9963C;">2 weeks — no charge</td>
        </tr>
        <tr>
          <td style="padding: 5px 0; color: #64748b;">After Trial</td>
          <td style="padding: 5px 0;">Cancel anytime, 30 days notice</td>
        </tr>
      </table>
    </div>

    <div style="text-align: center; margin: 28px 0;">
      {payment_button}
      <p style="font-size: 12px; color: #94a3b8; margin-top: 8px;">
        Or simply reply to this email to confirm.
      </p>
    </div>

    {_signing_block(signing_url)}

    <p style="font-size: 14px; color: #475569;">
      <strong>Attached to this email:</strong><br>
      1. Your proposal — what we're building and why<br>
      2. Service agreement — free trial terms, cancellation, and billing details
    </p>

    <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 24px 0;">

    <p style="font-size: 15px;">Any questions, just reply here.</p>

    <p style="margin-top: 16px;">
      <strong>William Marceau</strong><br>
      <a href="mailto:wmarceau@marceausolutions.com" style="color: #C9963C;">
        wmarceau@marceausolutions.com</a><br>
      (239) 398-5676<br>
      <a href="https://marceausolutions.com" style="color: #C9963C;">marceausolutions.com</a>
    </p>
  </div>

  <p style="text-align: center; font-size: 11px; color: #94a3b8; margin-top: 16px;">
    Marceau Solutions | Naples, FL | Embrace the Pain &amp; Defy the Odds
  </p>
</body>
</html>
"""

    alt_part = MIMEMultipart("alternative")
    alt_part.attach(MIMEText(text_body, "plain"))
    alt_part.attach(MIMEText(html_body, "html"))
    msg.attach(alt_part)

    # Attach proposal PDF
    for path, label in [
        (proposal_path, f"Proposal_{business_name.replace(' ', '_')}.pdf"),
        (agreement_path, f"Service_Agreement_{business_name.replace(' ', '_')}.pdf"),
    ]:
        with open(path, "rb") as f:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", f'attachment; filename="{label}"')
        msg.attach(part)

    return msg


def send_email(msg: MIMEMultipart, recipient: str):
    """Send email via SMTP."""
    host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    port = int(os.getenv("SMTP_PORT", "587"))
    username = os.getenv("SMTP_USERNAME")
    password = os.getenv("SMTP_PASSWORD")

    if not username or not password:
        raise ValueError("SMTP_USERNAME and SMTP_PASSWORD must be set in .env")

    with smtplib.SMTP(host, port) as server:
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(username, password)
        server.send_message(msg)


# ---------------------------------------------------------------------------
# Signing portal integration
# ---------------------------------------------------------------------------

_SIGNING_PORTAL_MODELS = REPO_ROOT / "projects/shared/signing-portal/models.py"


def _load_signing_models():
    """Dynamically load signing-portal models (hyphenated dir can't be dot-imported)."""
    spec = importlib.util.spec_from_file_location(
        "signing_portal_models", str(_SIGNING_PORTAL_MODELS)
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def create_signing_agreement(
    client_name: str,
    business_name: str,
    client_email: str,
    tier: int,
) -> str:
    """
    Generate a UUID token, insert a pending agreement into the signing portal DB,
    and return the full signing URL.

    Returns:
        str: e.g. "https://sign.marceausolutions.com/<token>"  (or localhost equivalent)
    """
    token = str(uuid.uuid4())
    base_url = os.getenv("SIGNING_PORTAL_URL", "http://localhost:8797").rstrip("/")
    signing_url = f"{base_url}/{token}"

    config = TIER_CONFIG[tier]
    effective_date = datetime.now().strftime("%Y-%m-%d")

    try:
        models = _load_signing_models()
        conn = models.get_db()
        models.create_agreement(
            conn,
            token=token,
            business_name=business_name,
            client_name=client_name,
            client_email=client_email,
            tier=tier,
            monthly_rate=config["monthly"],
            effective_date=effective_date,
        )
        conn.close()
    except Exception as e:
        print(f"  [signing] Warning — could not write to signing portal DB: {e}")

    return signing_url


# ---------------------------------------------------------------------------
# Outreach tracking log
# ---------------------------------------------------------------------------

def log_outreach(client_name: str, business_name: str, email: str,
                 tier: int, pain_point: str, signing_url: str = ""):
    """Append a proposal_sent entry to the outreach tracking JSON."""
    log_path = REPO_ROOT / "projects/shared/lead-scraper/output/outreach_tracking_2026-03-23.json"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    existing = []
    if log_path.exists():
        try:
            existing = json.loads(log_path.read_text())
            if not isinstance(existing, list):
                existing = [existing]
        except json.JSONDecodeError:
            existing = []

    entry = {
        "timestamp": datetime.now().isoformat(),
        "client_name": client_name,
        "business_name": business_name,
        "email": email,
        "tier": tier,
        "tier_name": TIER_CONFIG[tier]["name"],
        "monthly_rate": TIER_CONFIG[tier]["monthly"],
        "pain_point": pain_point,
        "status": "proposal_sent",
        "payment_link": get_payment_link(tier),
        "signing_url": signing_url,
    }
    existing.append(entry)

    log_path.write_text(json.dumps(existing, indent=2))
    return log_path


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Generate and send a proposal + service agreement to a prospect.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--client-name", required=True, help="Contact person's full name")
    parser.add_argument("--business-name", required=True, help="Business name")
    parser.add_argument("--email", required=True, help="Client email address")
    parser.add_argument("--tier", required=True, type=int, choices=[1, 2, 3, 4],
                        help="Service tier: 1=Starter, 2=Growth, 3=Pro, 4=Elite")
    parser.add_argument("--pain-point", required=True,
                        help='Short description of their main pain point, e.g. "Missing after-hours calls"')
    parser.add_argument("--dry-run", action="store_true",
                        help="Generate PDFs and log, but do NOT send the email")

    args = parser.parse_args()

    print(f"\nClose Deal — {args.business_name}")
    print(f"  Client:     {args.client_name} <{args.email}>")
    print(f"  Tier:       {TIER_CONFIG[args.tier]['name']} ({TIER_CONFIG[args.tier]['monthly']})")
    print(f"  Pain Point: {args.pain_point}")
    print(f"  Payment:    {get_payment_link(args.tier)}")
    if args.dry_run:
        print("  Mode:       DRY RUN (no email sent)\n")
    else:
        print()

    # Save PDFs to a permanent output dir (not tempfile — so you can drag into Acrobat)
    slug = args.business_name.lower().replace(" ", "_").replace("/", "_")[:40]
    output_dir = REPO_ROOT / "projects/shared/sales-pipeline/data/proposals" / slug
    output_dir.mkdir(parents=True, exist_ok=True)
    proposal_path = str(output_dir / "proposal.pdf")
    agreement_path = str(output_dir / "agreement.pdf")

    print("  [1/4] Generating proposal PDF...")
    generate_proposal_pdf(
        args.client_name, args.business_name, args.tier,
        args.pain_point, proposal_path
    )
    print(f"        Saved: {proposal_path}")

    print("  [2/4] Generating service agreement PDF...")
    generate_agreement_pdf(
        args.client_name, args.business_name, args.tier,
        agreement_path
    )
    print(f"        Saved: {agreement_path}")

    # Create signing link
    print("  [2b]  Creating signing agreement link...")
    signing_url = create_signing_agreement(
        client_name=args.client_name,
        business_name=args.business_name,
        client_email=args.email,
        tier=args.tier,
    )
    print(f"        Signing URL: {signing_url}")

    print()
    print("  ┌─────────────────────────────────────────────────────────────┐")
    print("  │  ONLINE SIGNING LINK (send to client):                     │")
    print(f"  │  {signing_url[:61]:<61}│")
    print("  │                                                             │")
    print("  │  DRAG INTO ADOBE ACROBAT TO REQUEST E-SIGNATURE:           │")
    print(f"  │  {agreement_path[:61]:<61}│")
    print("  └─────────────────────────────────────────────────────────────┘")
    print()

    if not args.dry_run:
        print("  [3/4] Sending email...")
        msg = build_email(
            args.client_name, args.business_name, args.tier,
            args.email, proposal_path, agreement_path,
            signing_url=signing_url,
        )
        send_email(msg, args.email)
        print(f"        Sent to {args.email}.")
    else:
        print("  [3/4] Skipping email (dry run).")

    print("  [4/4] Logging outreach...")
    log_path = log_outreach(
        args.client_name, args.business_name, args.email,
        args.tier, args.pain_point, signing_url=signing_url,
    )
    print(f"        Logged to {log_path.relative_to(REPO_ROOT)}")

    status = "DRY RUN complete" if args.dry_run else "Done"
    print(f"\n  {status}. Proposal sent to {args.business_name}.")
    print(f"  PDFs saved to:  {output_dir}")
    print(f"  Signing URL:    {signing_url}\n")


if __name__ == "__main__":
    main()
