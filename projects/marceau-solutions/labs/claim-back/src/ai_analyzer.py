"""ClaimBack AI Analyzer — Claude-powered medical bill analysis."""

import os
import json
from anthropic import Anthropic

client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

ANALYSIS_PROMPT = """You are a medical billing expert and patient advocate AI. Analyze the following medical billing dispute and provide a detailed assessment.

DISPUTE DETAILS:
- Type: {dispute_type}
- Provider: {provider_name}
- Insurance: {insurance_company}
- Insurance Type: {insurance_type}
- State: {state}
- Date of Service: {date_of_service}
- Claim Number: {claim_number}
- Billed Amount: ${billed_amount:.2f}
- Insurance Paid: ${insurance_paid:.2f}
- Patient Responsibility: ${patient_responsibility:.2f}
- Denial Reason: {denial_reason}

PATIENT DESCRIPTION:
{description}

{documents_text}

Analyze this dispute and respond with a JSON object containing:

1. "summary": A 2-3 paragraph analysis of the situation, key issues, and the patient's position.

2. "strength_score": Integer 1-10 rating of case strength (10 = slam dunk, 1 = very weak).

3. "errors_found": Array of specific billing errors, overcharges, or violations identified. Be specific about what's wrong and reference amounts where possible.

4. "applicable_laws": Array of federal and state laws/regulations that apply. Include:
   - No Surprises Act (if surprise/balance billing)
   - ERISA (if employer plan)
   - ACA appeal rights
   - FDCPA (if debt collection involved)
   - State-specific balance billing protections
   - Any other relevant regulations

5. "recommended_actions": Array of specific next steps in priority order. Include who to contact, what to say, and deadlines.

6. "key_arguments": Array of the strongest arguments for the patient's case.

7. "potential_savings": Estimated dollar amount the patient could save if successful.

8. "appeal_deadline": Estimated deadline for filing an appeal based on dispute type and state law.

9. "risk_assessment": Brief note on risks or weaknesses in the case.

Respond ONLY with valid JSON. No markdown, no explanation outside the JSON."""


def analyze_dispute(dispute: dict, documents_text: str = "") -> dict:
    """Analyze a medical billing dispute using Claude.

    Args:
        dispute: Dict with dispute details from the database.
        documents_text: Optional extracted text from uploaded documents.

    Returns:
        Dict with analysis results.
    """
    doc_section = ""
    if documents_text:
        doc_section = f"\nEXTRACTED DOCUMENT TEXT:\n{documents_text}\n"

    prompt = ANALYSIS_PROMPT.format(
        dispute_type=dispute.get("dispute_type", "unknown"),
        provider_name=dispute.get("provider_name", "Unknown"),
        insurance_company=dispute.get("insurance_company", "Unknown"),
        insurance_type=dispute.get("insurance_type", "Unknown"),
        state=dispute.get("state", "Unknown"),
        date_of_service=dispute.get("date_of_service", "Unknown"),
        claim_number=dispute.get("claim_number", "N/A"),
        billed_amount=float(dispute.get("billed_amount") or 0),
        insurance_paid=float(dispute.get("insurance_paid") or 0),
        patient_responsibility=float(dispute.get("patient_responsibility") or 0),
        denial_reason=dispute.get("denial_reason", "Not specified"),
        description=dispute.get("description", "No description provided."),
        documents_text=doc_section,
    )

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )

    text = response.content[0].text.strip()

    # Handle potential markdown code fences
    if text.startswith("```"):
        text = text.split("\n", 1)[1]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

    return json.loads(text)
