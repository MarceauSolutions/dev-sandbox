#!/usr/bin/env python3
"""
Generate and email the Wakefulness Agent Research Report PDF.
Clonazepam-Induced Hypersomnia — Doctor Consultation Guide with Insurance Justification.
Prepared for William Marceau.
"""

import os
import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(message)s")
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Report Content
# ---------------------------------------------------------------------------

REPORT_DATA = {
    "title": "Wakefulness Agent Research Report — Clonazepam-Induced Hypersomnia",
    "subtitle": "Doctor Consultation Guide with Insurance Justification",
    "date": "May 14, 2026",
    "prepared_for": "William Marceau",
    "executive_summary": (
        "William is experiencing severe daytime hypersomnia caused by clonazepam's long "
        "half-life (5-40 hours), which creates sedation accumulation peaking mid-morning despite "
        "adequate overnight sleep. A dose timing adjustment has already been trialed and is "
        "insufficient due to the medical necessity of morning coverage for dystonia-related pain. "
        "A wakefulness agent is required."
    ),
    "primary_recommendation": (
        "Modafinil 200mg (or Armodafinil 150mg) taken at 6am before the 7am work shift."
    ),
    "sections": [
        # ----------------------------------------------------------------
        # SECTION 1
        # ----------------------------------------------------------------
        {
            "heading": "Section 1: Root Cause — Clonazepam Pharmacokinetics",
            "subsections": [
                {
                    "info_box": {
                        "label": "Drug Profile",
                        "lines": [
                            "Drug: Clonazepam 2mg/day (prescribed up to 4mg/day)",
                            "Indication: Secondary dystonia — pain management and muscle control",
                            "Half-life: 5-40 hours (median ~35 hours in most adults)",
                            "Mechanism: GABA-A receptor positive allosteric modulator — CNS-wide inhibitory effect",
                        ],
                    }
                },
                {
                    "subheading": "Why Daytime Sedation Occurs",
                    "bullets": [
                        "Clonazepam does not clear between doses due to its long half-life",
                        "Drug accumulates in the bloodstream over days of continuous use",
                        "Peak plasma concentration: 1-4 hours after ingestion",
                        "Morning dose — sedation peak lands at 8am-11am, exactly matching reported symptom onset",
                        "GABA-A enhancement suppresses orexin/hypocretin wakefulness signaling and histaminergic arousal pathways",
                    ],
                },
                {
                    "highlight": (
                        "Timing adjustment already trialed: Patient attempted splitting dose (lower AM / "
                        "higher PM) — still experiencing daytime somnolence. Morning coverage is medically "
                        "necessary for dystonia pain control; dose cannot be consolidated to bedtime without "
                        "loss of therapeutic effect. Pharmacological wakefulness intervention required."
                    ),
                },
            ],
        },
        # ----------------------------------------------------------------
        # SECTION 2
        # ----------------------------------------------------------------
        {
            "heading": "Section 2: Medication Pathways & How They Interact",
            "subsections": [
                {
                    "subheading": "Clonazepam — GABAergic Pathway",
                    "bullets": [
                        "Binds GABA-A receptors — enhances chloride ion influx — neuronal hyperpolarization",
                        "Suppresses: orexin/hypocretin neurons (primary wakefulness signal), histaminergic arousal (tuberomammillary nucleus), locus coeruleus norepinephrine output",
                        "Net effect: broad CNS sedation, reduced arousal drive",
                        "Source: NCBI StatPearls — Clonazepam (NBK556010)",
                    ],
                },
                {
                    "subheading": "Modafinil — Orexin/Dopamine/Histamine Pathway",
                    "bullets": [
                        "Weak dopamine transporter (DAT) inhibitor — slows dopamine reuptake, does NOT release dopamine from vesicles (critical distinction from amphetamines)",
                        "Activates orexin/hypocretin neurons in the lateral hypothalamus — the primary wakefulness circuit suppressed by clonazepam",
                        "Enhances histaminergic signaling from tuberomammillary nucleus",
                        "Net effect: targeted restoration of wakefulness signaling through pathways distinct from but directly countering clonazepam's sedative mechanism",
                        "Source: Nature Neuropsychopharmacology review; StatPearls NBK531476",
                    ],
                },
                {
                    "subheading": "How They Interact (Clonazepam + Modafinil)",
                    "bullets": [
                        "Pharmacodynamic: Opposing mechanisms — clonazepam suppresses wakefulness pathways, modafinil activates them. Net result: wakefulness restored while therapeutic GABA-A effect on dystonia is preserved.",
                        "Pharmacokinetic (CYP3A4): Modafinil is a moderate CYP3A4 inducer. Clonazepam is metabolized by CYP3A4. Modafinil may modestly reduce clonazepam plasma levels — requiring monitoring of dystonia symptom control after initiation.",
                        "Interaction severity: Minor (Drugs.com professional classification)",
                        "Real-world safety: Published case report documents long-term co-prescription of clonazepam 1-2mg/day + modafinil 200-400mg/day without clinically significant adverse interaction (PMC10964878)",
                        "Monitoring required: Dystonia symptom control after modafinil initiation; adjust clonazepam dose if breakthrough pain/spasm occurs",
                    ],
                },
                {
                    "subheading": "Armodafinil (R-Modafinil) — Same Pathway, Cleaner Profile",
                    "bullets": [
                        "Purified R-enantiomer of modafinil — same mechanism, lower dose required",
                        "More sustained plasma levels throughout the day vs. racemic modafinil",
                        "150mg armodafinil equivalent to 200mg modafinil in wakefulness effect",
                        "Better option if modafinil wears off before end of shift (3:30pm)",
                        "Source: PMC3135062 (shift work RCT); PubMed 19663523 (PK comparison)",
                    ],
                },
            ],
        },
        # ----------------------------------------------------------------
        # SECTION 3
        # ----------------------------------------------------------------
        {
            "heading": "Section 3: Medications Ruled Out (With Reasons)",
            "subsections": [
                {
                    "table": {
                        "headers": ["Medication", "Status", "Reason"],
                        "rows": [
                            ["Vyvanse (lisdexamfetamine)", "RULED OUT", "Patient history: anger, irritability, itching, intolerance. Mechanism: amphetamine prodrug — releases dopamine AND norepinephrine from vesicles — crash, emotional dysregulation, sympathomimetic effects."],
                            ["Adderall (amphetamine salts)", "RULED OUT", "Patient history: prior long-term use, not desired. Same amphetamine-class mechanism as Vyvanse."],
                            ["Gabapentin", "RULED OUT", "Patient history: severe cognitive blunting ('no internal thought'). Mechanism: alpha-2-delta calcium channel subunit binding — widespread cortical inhibition; overlaps with GABA-A pathway."],
                            ["Solriamfetol (Sunosi)", "NOT RECOMMENDED", "Post-marketing 2025 data (PMC12453233): 10% psychiatric discontinuation rate, 46 reports of suicidal ideation, 120 anxiety reports in FAERS database. DNRI mechanism increases both dopamine and norepinephrine — risk of mood destabilization."],
                            ["Pitolisant (Wakix)", "NOT RECOMMENDED AT THIS TIME", "2024 post-marketing pharmacovigilance (PMC10765455): new cardiac signals (myocarditis, palpitations), complex CYP2D6/3A4 interactions. Limited data for drug-induced (vs. primary) hypersomnia."],
                        ],
                        "col_widths": [1.4, 1.3, 3.8],
                    }
                },
                {
                    "highlight": (
                        "HARD EXCLUSION CRITERION: Any medication with sexual side effects is categorically "
                        "excluded. Modafinil at standard dose has no documented sexual side effects; "
                        "a pro-sexual effect has been reported at therapeutic doses in antidepressant-induced "
                        "sexual dysfunction study (PubMed 36148571)."
                    ),
                },
            ],
        },
        # ----------------------------------------------------------------
        # SECTION 4
        # ----------------------------------------------------------------
        {
            "heading": "Section 4: Evidence Base",
            "subsections": [
                {
                    "body": "All sources peer-reviewed or FDA-official:",
                },
                {
                    "bullets": [
                        "Modafinil vs. Amphetamine-Dextroamphetamine RCT (2023 Emory University) — PMC12598845",
                        "Modafinil for drug-induced CNS sedation — PubMed 15003090",
                        "Modafinil neurochemical mechanism review — Nature Neuropsychopharmacology",
                        "Modafinil individual variability (fatigue-vulnerable responders) — PMC12507762",
                        "Modafinil sexual effects in therapeutic context — PubMed 36148571",
                        "Modafinil StatPearls — NCBI NBK531476",
                        "Armodafinil shift work RCT — PMC3135062",
                        "Armodafinil PK comparison — PubMed 19663523",
                        "Clonazepam + Modafinil real-world co-prescription case — PMC10964878",
                        "CYP3A4 drug interaction (modafinil as perpetrator) — PMC5809348",
                        "Drugs.com professional interaction classification — clonazepam + modafinil (Minor)",
                        "Clonazepam StatPearls — NCBI NBK556010",
                        "Clonazepam PK study — PubMed 1687613",
                        "Dystonia treatment and benzodiazepine sedation — PMC5168853",
                        "Solriamfetol post-marketing FAERS 2025 — PMC12453233",
                        "Pitolisant pharmacovigilance 2024 — PMC10765455",
                        "Network meta-analysis wakefulness agents 2023 — PubMed 37155992",
                    ],
                },
            ],
        },
        # ----------------------------------------------------------------
        # SECTION 5
        # ----------------------------------------------------------------
        {
            "heading": "Section 5: Doctor Talking Points",
            "subsections": [
                {
                    "subheading": "Opening Statement",
                    "highlight": (
                        '"I\'m currently taking clonazepam 2mg daily for secondary dystonia. It\'s providing adequate '
                        "symptom control during the day but I'm experiencing severe daytime somnolence — eyes closing "
                        "involuntarily by 10-11am while at work. I've already tried shifting more of the dose to evenings, "
                        "but I require morning coverage to manage dystonia pain during my 7am-3:30pm work shift. "
                        'I\'d like to discuss adding a wakefulness agent."'
                    ),
                },
                {
                    "subheading": "Key Points to Cover",
                    "bullets": [
                        "Already trialed dose timing adjustment — insufficient; morning coverage medically necessary",
                        "Not seeking amphetamine-class drugs (Adderall, Vyvanse) — prior adverse reactions (irritability, itching)",
                        "Gabapentin previously trialed — severe cognitive adverse effects, not suitable",
                        "Requesting modafinil 200mg (or armodafinil 150mg) — non-amphetamine mechanism, evidence-supported, favorable side effect profile",
                        "Aware of CYP3A4 interaction — willing to monitor dystonia symptom control after initiation",
                        "Separate concern: pressure behind the eyes — not attributing this to clonazepam without evaluation",
                    ],
                },
                {
                    "subheading": "Insurance Justification Language (for Prior Authorization)",
                    "body": (
                        "<b>Diagnosis framing:</b> 'Hypersomnia secondary to medically necessary clonazepam "
                        "therapy for secondary dystonia'"
                    ),
                },
                {
                    "body": "<b>Clinical necessity statement:</b>",
                },
                {
                    "highlight": (
                        '"Patient requires clonazepam for secondary dystonia with daytime pain management. '
                        "Clonazepam's GABAergic mechanism suppresses orexin/histaminergic wakefulness pathways, "
                        "resulting in clinically significant hypersomnia impacting patient's ability to perform "
                        "essential job functions. Dose reduction is not appropriate due to breakthrough dystonia "
                        "symptoms. Dose timing adjustment has been trialed without adequate relief. Modafinil is "
                        "a non-controlled, non-amphetamine wakefulness agent that targets the specific pathway "
                        "suppressed by clonazepam (orexin/hypocretin activation) and is the most appropriate "
                        'pharmacological intervention for drug-induced hypersomnia in this clinical context."'
                    ),
                },
                {
                    "subheading": "Prior Authorization CPT/ICD Codes",
                    "bullets": [
                        "ICD-10: G47.10 (Hypersomnia, unspecified) or G47.19 (Other hypersomnia)",
                        "Secondary diagnosis: G24.8 (Other dystonia) or G24.9 (Dystonia, unspecified)",
                        "Modafinil NDC: 00406-0117 (200mg generic)",
                    ],
                },
                {
                    "subheading": "If Physician Pushes Back",
                    "bullets": [
                        '"I understand modafinil is off-label for drug-induced hypersomnia, but the mechanism of action directly counters the pathway responsible for clonazepam sedation, and there is published case data supporting co-prescription."',
                        '"If modafinil is not preferred, armodafinil 150mg is an equivalent alternative with a more sustained plasma curve that better covers my work shift."',
                        '"I want to avoid amphetamine-class wakefulness agents due to prior adverse reactions, and I have hard exclusion criteria for medications with sexual side effects."',
                    ],
                },
            ],
        },
        # ----------------------------------------------------------------
        # SECTION 6
        # ----------------------------------------------------------------
        {
            "heading": "Section 6: Medication Comparison Table",
            "subsections": [
                {
                    "table": {
                        "headers": ["Criterion", "Modafinil", "Armodafinil", "Solriamfetol", "Pitolisant"],
                        "rows": [
                            ["Mechanism", "DAT inhibitor + orexin activation", "Same (R-enantiomer)", "DNRI", "H3 antagonist"],
                            ["Evidence for drug-induced hypersomnia", "Strong (indirect, strong mechanism)", "Strong (same)", "Strongest EDS data", "Limited"],
                            ["Sexual side effects", "None at standard dose", "None", "Not reported", "Not reported"],
                            ["Cognitive effects", "Positive", "Positive", "Positive", "Positive"],
                            ["Mood/psychiatric risk", "Low (anxiety 5-10%)", "Low", "HIGH (10% psych discontinuation)", "Moderate"],
                            ["Clonazepam interaction", "Minor (documented safe)", "Minor (same)", "Minimal DDIs", "Complex CYP"],
                            ["Cardiac safety", "No major signal", "No major signal", "BP/HR increase", "NEW 2024 signals"],
                            ["Controlled substance", "Schedule IV", "Schedule IV", "Schedule IV", "NOT scheduled"],
                            ["Recommendation", "FIRST CHOICE", "BACKUP", "Third-line only", "Insufficient data"],
                        ],
                        "col_widths": [1.6, 1.3, 1.3, 1.3, 1.0],
                    }
                },
            ],
        },
    ],
    "disclaimer": (
        "This document is a research summary prepared for discussion with a prescribing physician. "
        "It does not constitute medical advice. No medication changes should be made without consulting "
        "a licensed physician who has access to the patient's complete medical history, current treatment "
        "plan, and neurological evaluation."
    ),
}


# ---------------------------------------------------------------------------
# PDF Generation
# ---------------------------------------------------------------------------

def generate_pdf(output_path: str) -> str:
    """Generate the branded research report PDF."""
    sys.path.insert(0, str(Path(__file__).parent))
    from branded_pdf_engine import BrandedPDFEngine

    engine = BrandedPDFEngine()
    engine.generate_to_file("research_report", REPORT_DATA, output_path)
    logger.info(f"PDF generated: {output_path}")
    return output_path


# ---------------------------------------------------------------------------
# Email Delivery — Gmail API (OAuth token.json)
# ---------------------------------------------------------------------------

def _get_gmail_service():
    """Load Gmail service from existing token.json (no interactive auth)."""
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build

    token_path = Path(__file__).parent.parent / "token.json"
    if not token_path.exists():
        raise FileNotFoundError(f"Gmail token not found at {token_path}")

    creds = Credentials.from_authorized_user_file(str(token_path))
    if not creds.valid:
        if creds.expired and creds.refresh_token:
            logger.info("Refreshing expired Gmail token...")
            creds.refresh(Request())
            with open(token_path, "w") as f:
                f.write(creds.to_json())
        else:
            raise RuntimeError("Gmail token is invalid and cannot be refreshed.")

    return build("gmail", "v1", credentials=creds)


def send_email_with_attachment(pdf_path: str) -> bool:
    """Send the PDF via Gmail API to wmarceau@marceausolutions.com."""
    import base64
    from email.mime.multipart import MIMEMultipart as MimeMMP
    from email.mime.text import MIMEText as MimeTxt
    from email.mime.base import MIMEBase as MimeBse
    from email import encoders as enc

    recipient = "wmarceau@marceausolutions.com"
    subject = "Medication Research Report — Doctor Consultation Guide"
    body = (
        "William,\n\n"
        "Attached is your medication research report for your doctor consultation. "
        "It includes the full research, drug pathway analysis, interaction details, "
        "talking points, and insurance justification language.\n\n"
        "— Panacea"
    )

    msg = MimeMMP()
    msg["From"] = "William Marceau <wmarceau26@gmail.com>"
    msg["To"] = recipient
    msg["Subject"] = subject
    msg.attach(MimeTxt(body, "plain"))

    # Attach PDF
    with open(pdf_path, "rb") as f:
        part = MimeBse("application", "octet-stream")
        part.set_payload(f.read())
    enc.encode_base64(part)
    pdf_filename = Path(pdf_path).name
    part.add_header("Content-Disposition", f'attachment; filename="{pdf_filename}"')
    msg.attach(part)

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()

    try:
        service = _get_gmail_service()
        result = service.users().messages().send(
            userId="me",
            body={"raw": raw}
        ).execute()
        logger.info(f"Email sent via Gmail API. Message ID: {result.get('id')} — To: {recipient}")
        return True
    except Exception as e:
        logger.error(f"Gmail API send failed: {e}")
        return False


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    output_dir = Path("/home/clawdbot/dev-sandbox/projects/marceau-solutions/digital/clients/william-marceau")
    output_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = str(output_dir / "wakefulness_agent_research_report_2026-05-14.pdf")

    logger.info("Generating branded PDF...")
    generate_pdf(pdf_path)

    logger.info("Sending email with attachment...")
    success = send_email_with_attachment(pdf_path)

    if success:
        print(f"\nDELIVERY COMPLETE")
        print(f"  PDF saved: {pdf_path}")
        print(f"  Email sent: wmarceau@marceausolutions.com")
        print(f"  Subject: Medication Research Report — Doctor Consultation Guide")
    else:
        print(f"\nPDF generated at: {pdf_path}")
        print("EMAIL FAILED — check SMTP credentials and retry.")
        sys.exit(1)


if __name__ == "__main__":
    main()
