"""ClaimBack Letter Generator — AI-powered dispute letters and billing code optimization.

This module is a weapon. The medical system uses deliberate tactics to deny, delay,
and discourage patients from getting the care and coverage they're entitled to.
This module identifies every tactic being used and generates the precise counter-attack.

TACTICS THIS SYSTEM COUNTERS:
1. Wrong billing codes — providers submit suboptimal codes; we find the right ones
2. "Not medically necessary" — reclassifying essential procedures as elective/cosmetic
3. Aesthetic reclassification — calling functional procedures "aesthetic" to deny coverage
4. Prior auth denial — retroactive or delayed prior authorization denials
5. Balance billing — billing patients beyond allowed amounts
6. Surprise billing — out-of-network charges at in-network facilities
7. Upcoding / unbundling — inflating charges through code manipulation
8. Collections threats — using debt collectors to pressure patients into paying invalid bills
9. Technicality denials — wrong form, missed deadline, incomplete paperwork
10. Coverage misrepresentation — claiming something "isn't covered" when it is
"""

import os
import json
from anthropic import Anthropic

client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

LETTER_PROMPT = """You are a medical billing advocate, coding specialist, and patient rights enforcer. You write letters that WIN disputes. You know every dirty trick insurance companies and providers use, and you have a counter for each one.

THE SYSTEM'S PLAYBOOK (tactics you must identify and counter):
1. WRONG CODES: Providers submit suboptimal CPT/ICD-10 codes. You find the codes that maximize coverage.
2. "NOT MEDICALLY NECESSARY": Insurance reclassifies essential procedures as elective. You cite clinical guidelines proving necessity.
3. AESTHETIC RECLASSIFICATION: Calling functional procedures "cosmetic" or "aesthetic" to deny. Example: denying hand reattachment surgery because the non-dominant hand is "aesthetic." You destroy this with functional necessity arguments and AMA guidelines.
4. PRIOR AUTH GAMES: Denying because prior auth wasn't obtained — even when it's an emergency or the provider failed to obtain it (which is NOT the patient's fault).
5. BALANCE BILLING: Billing patients beyond contracted rates. You cite No Surprises Act and state protections.
6. SURPRISE BILLING: Out-of-network charges at in-network facilities. Federal law prohibits this.
7. UPCODING/UNBUNDLING: Inflating charges by splitting procedures or using higher-level codes. You identify and call it out.
8. COLLECTIONS HARASSMENT: Using debt collectors on disputed bills. FDCPA violations. You shut this down.
9. TECHNICALITY DENIALS: "Wrong form," "missed deadline," "incomplete paperwork." You cite good-faith compliance and regulatory protections.
10. COVERAGE LIES: Claiming something "isn't covered" when the plan document says it is. You find the plan language that proves coverage.
11. DELAY TACTICS: Slow-walking approvals hoping patients give up or miss deadlines. You set hard deadlines with regulatory consequences.
12. PEER-TO-PEER MANIPULATION: Using biased "peer reviewers" to rubber-stamp denials. You demand independent external review.

YOUR MISSION: Generate letters that make it more expensive for the system to fight the patient than to pay the claim. Every letter should make the recipient realize they will lose if this goes further.

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

AI ANALYSIS:
{analysis_summary}

Generate the following as a JSON object:

{letter_instructions}

Additionally, ALWAYS include these keys:

"billing_code_analysis": A detailed analysis including:
- What CPT/ICD-10/HCPCS codes the provider likely submitted
- What codes SHOULD have been used for maximum coverage
- Specific code numbers with descriptions
- How resubmitting with correct codes changes the coverage determination
- Modifier codes that could improve coverage
- If the denial involves "medical necessity" or "aesthetic" reclassification, identify the codes and clinical guidelines that prove the procedure is medically necessary and functional, not cosmetic

"system_tactics_identified": Which of the 12 tactics above are being used in this case, with specific evidence from the dispute details.

"nuclear_options": If the standard dispute process fails, what escalation paths exist:
- State insurance commissioner complaint
- State attorney general complaint
- CMS complaint (for Medicare/Medicaid)
- Department of Labor complaint (for ERISA plans)
- OIG fraud hotline (if fraud is suspected)
- Bad faith insurance lawsuit (when insurer acts in bad faith)
- Media/public pressure strategies
- Congressional representative intervention

LETTER GUIDELINES:
- Formal business letter format (date, addresses, re: line, body, signature)
- Use [PATIENT NAME] and [PATIENT ADDRESS] as placeholders
- Reference specific claim numbers, dates, and dollar amounts
- Cite applicable federal and state laws BY NAME AND SECTION NUMBER
- Include specific deadlines and consequences for non-response
- Be firm, precise, and relentless — every sentence should carry weight
- Include a clear "requested resolution" paragraph with specific dollar amounts
- Reference specific billing codes when applicable
- When insurance denies something as "not medically necessary" or "aesthetic," include specific AMA/clinical guideline citations that prove otherwise
- End with notice that copies are being sent to relevant regulatory bodies
- Make it clear that escalation WILL happen if not resolved
- Date the letters as [DATE]

Respond ONLY with valid JSON. No markdown wrapping."""


def generate_dispute_letters(dispute: dict) -> dict:
    """Generate dispute/appeal letters for a medical billing dispute.

    Args:
        dispute: Dict with dispute details including ai_analysis.

    Returns:
        Dict mapping letter_type to letter content string.
    """
    dispute_type = dispute.get("dispute_type", "billing_error")
    analysis = {}
    if dispute.get("ai_analysis"):
        try:
            analysis = json.loads(dispute["ai_analysis"])
        except (json.JSONDecodeError, TypeError):
            pass

    analysis_summary = analysis.get("summary", "No AI analysis available.")

    letter_instructions = _get_letter_instructions(dispute_type)

    prompt = LETTER_PROMPT.format(
        dispute_type=dispute_type,
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
        analysis_summary=analysis_summary,
        letter_instructions=letter_instructions,
    )

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=8192,
        messages=[{"role": "user", "content": prompt}],
    )

    text = response.content[0].text.strip()

    if text.startswith("```"):
        text = text.split("\n", 1)[1]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

    return json.loads(text)


def _get_letter_instructions(dispute_type: str) -> str:
    """Return letter generation instructions based on dispute type."""
    base_letters = {
        "insurance_denial": """
1. "appeal_letter": Internal appeal letter to the insurance company. Cite ACA Section 2719, ERISA (if employer plan), and state-specific appeal rights. If denied as "not medically necessary" or "aesthetic/cosmetic," include specific AMA guidelines, clinical evidence, and functional necessity arguments that demolish that classification. If the denial is code-related, include the CORRECT codes. Make them understand this appeal has teeth.

2. "external_review_request": Request for independent external review. Reference the patient's right under ACA. Note that external reviewers overturn 40-60% of denials — make the insurance company aware you know this.

3. "code_correction_request": Letter to the provider requesting they resubmit the claim with the correct CPT/ICD-10 codes. Many denials are fixed by using the right code — the patient shouldn't have to know this, but now they do.

4. "state_complaint": Complaint letter to the state insurance commissioner. Reference specific state insurance code violations. This is the escalation that insurance companies actually fear.

5. "patient_phone_script": A plain-language script the patient can read when calling their insurance company. Include the exact codes to reference, the laws to cite, and the magic words that trigger supervisory review. Written so anyone can use it confidently.""",

        "billing_error": """
1. "dispute_letter_provider": Letter to the provider disputing the charges. Request itemized bill review, cite specific errors (upcoding, unbundling, duplicate charges), and demand correction with correct billing codes.

2. "dispute_letter_insurer": Letter to insurance company requesting re-processing with correct codes/amounts.

3. "debt_dispute": FDCPA-compliant debt dispute letter if the bill has been sent to collections. This letter stops collections activity and forces validation.

4. "patient_phone_script": Plain-language script for calling the provider's billing department with the exact errors and correct codes.""",

        "surprise_bill": """
1. "nsa_dispute": Letter citing the No Surprises Act. Reference specific NSA protections. Demand billing be adjusted to in-network rates. Include the qualifying payment amount (QPA) requirement.

2. "provider_notice": Notice to the provider that balance billing is prohibited under NSA for this service. Include penalties for NSA violations ($10,000 per violation).

3. "idre_request": If applicable, request for Independent Dispute Resolution Entity (IDRE) process under the No Surprises Act.

4. "state_complaint": Complaint to state attorney general and insurance commissioner about illegal surprise billing.""",

        "balance_billing": """
1. "balance_billing_dispute": Letter to provider citing state and federal balance billing protections. Demand withdrawal of the balance bill with specific legal citations.

2. "insurer_notice": Letter to insurance company requesting they notify the provider of contracted rates and balance billing prohibitions.

3. "state_complaint": Complaint to state insurance commissioner about illegal balance billing.

4. "collections_preempt": Preemptive letter warning provider that if this disputed bill is sent to collections, it violates FDCPA and will result in regulatory complaints.""",

        "service_not_rendered": """
1. "dispute_letter_provider": Letter to provider disputing charges for services not rendered. Demand full refund. Note that billing for services not rendered is healthcare fraud.

2. "fraud_report": Report template for the OIG Medicare/Medicaid fraud hotline AND state medical board. Billing for services not rendered is a federal crime.

3. "insurer_notice": Letter to insurance company requesting claim reversal for services not actually provided.

4. "law_enforcement_notice": If pattern of fraud suspected, template for reporting to state AG healthcare fraud division.""",

        "wrong_code": """
1. "coding_dispute": Letter to provider identifying incorrect CPT/ICD-10 codes and requesting correction. Include the SPECIFIC correct codes with descriptions. If the wrong code caused a denial or higher patient cost, quantify the dollar impact.

2. "insurer_reprocess": Letter to insurance company requesting reprocessing with correct codes. Include the correct codes directly so they can reprocess immediately.

3. "patient_code_reference": Plain-language guide explaining which codes to reference when calling insurance. Written so a non-medical person can confidently say "the correct code for my treatment is X" on the phone — because that's literally all it takes to flip a denial into full coverage.

4. "state_complaint": Complaint letter if provider refuses to correct coding errors. Persistent miscoding may constitute fraud.""",
    }

    return base_letters.get(dispute_type, base_letters["billing_error"])
