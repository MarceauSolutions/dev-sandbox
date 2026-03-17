#!/usr/bin/env python3
"""
Generate comprehensive Propane chargeback next-steps PDF.
Branded Marceau Solutions document with full action plan.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, KeepTogether
)

from execution.branded_pdf_engine import BrandConfig, _register_fonts, get_brand_styles

_register_fonts()

OUTPUT = os.path.join(os.path.dirname(__file__), "propane-chargeback-action-plan.pdf")

def build():
    doc = SimpleDocTemplate(
        OUTPUT, pagesize=letter,
        leftMargin=0.75*inch, rightMargin=0.75*inch,
        topMargin=0.75*inch, bottomMargin=0.75*inch
    )
    s = get_brand_styles()
    elements = []

    # Custom styles
    callout_style = ParagraphStyle(
        "Callout", fontName=BrandConfig.BODY_FONT_BOLD,
        fontSize=11, leading=16, textColor=BrandConfig.WHITE,
        backColor=BrandConfig.CHARCOAL, borderPadding=10,
    )
    warning_style = ParagraphStyle(
        "Warning", fontName=BrandConfig.BODY_FONT_BOLD,
        fontSize=10, leading=15, textColor=HexColor("#92400e"),
    )
    step_style = ParagraphStyle(
        "Step", fontName=BrandConfig.BODY_FONT,
        fontSize=10, leading=15, textColor=HexColor("#334155"),
        leftIndent=20, spaceAfter=6,
    )
    script_style = ParagraphStyle(
        "Script", fontName=BrandConfig.BODY_FONT,
        fontSize=9.5, leading=14, textColor=HexColor("#1e293b"),
        leftIndent=15, rightIndent=15, borderPadding=10,
        backColor=HexColor("#f8f6f0"),
    )

    # ===== TITLE =====
    elements.append(Paragraph("PROPANE FITNESS DISPUTE", s["title"]))
    elements.append(Paragraph("Chargeback Action Plan — March 13, 2026", s["subtitle"]))
    elements.append(HRFlowable(width="100%", thickness=2, color=BrandConfig.GOLD))
    elements.append(Spacer(1, 15))

    # ===== SITUATION SUMMARY =====
    elements.append(Paragraph("CURRENT SITUATION", s["h2"]))
    elements.append(Paragraph(
        "Today is <b>March 13, 2026</b> — the deadline you set in your final demand email (March 12). "
        "After three formal emails sent on March 6, March 7, and March 12, Jim Galvin at PropaneFitness "
        "has provided <b>zero substantive response</b>. His only reply (March 7) addressed foreign transaction "
        "fees alone, ignoring all 7 grounds for your refund request. He has breached his own terms Section 12.5 "
        "(7-day substantive response requirement). Propane continues to send you automated marketing emails "
        "as recently as today.", s["body"]
    ))
    elements.append(Spacer(1, 10))

    # Summary table
    summary_data = [
        ["Item", "Detail"],
        ["Total to recover", "$8,741.76 USD ($4,370.88 per card)"],
        ["Card 1 (ending 1007)", "$4,255.97 + $114.91 FTF = $4,370.88"],
        ["Card 2 (ending 1049)", "$4,255.97 + $114.91 FTF = $4,370.88"],
        ["Merchant name on statement", "PROPANEFITNESS.COM NEWCASTLE GB"],
        ["Transaction date", "March 2, 2026"],
        ["Refund requested", "March 6, 2026 (Day 4 of 14-day window)"],
        ["Deadline set", "March 13, 2026 (today — no response)"],
    ]
    t = Table(summary_data, colWidths=[2.2*inch, 4.5*inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BrandConfig.CHARCOAL),
        ("TEXTCOLOR", (0, 0), (-1, 0), BrandConfig.WHITE),
        ("FONTNAME", (0, 0), (-1, 0), BrandConfig.HEADING_FONT),
        ("FONTSIZE", (0, 0), (-1, 0), 10),
        ("FONTNAME", (0, 1), (-1, -1), BrandConfig.BODY_FONT),
        ("FONTSIZE", (0, 1), (-1, -1), 9),
        ("BACKGROUND", (0, 1), (-1, -1), HexColor("#faf9f6")),
        ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#e2e0d8")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 20))

    # ===== SECTION 1: TIMING =====
    elements.append(Paragraph("SECTION 1: TIMING — WHEN TO FILE", s["h2"]))
    elements.append(HRFlowable(width="100%", thickness=1, color=BrandConfig.GOLD))
    elements.append(Spacer(1, 8))

    elements.append(Paragraph("<b>Recommended: File on Friday, March 14, 2026</b>", s["body_bold"]))
    elements.append(Spacer(1, 6))
    elements.append(Paragraph(
        "Your deadline was stated as <b>'close of business on March 13'</b>. To be unassailable, "
        "wait until the morning of March 14. This accomplishes two things:", s["body"]
    ))
    elements.append(Spacer(1, 4))
    elements.append(Paragraph("1. It proves you honored your own deadline to the letter — you gave Jim the full day.", step_style))
    elements.append(Paragraph("2. It eliminates any argument that you filed prematurely or didn't give adequate time.", step_style))
    elements.append(Spacer(1, 6))
    elements.append(Paragraph(
        "<b>Do one final inbox check at 9 AM ET on March 14</b> before filing. Search for any email from "
        "jim@propanefitness.com, admin@propanefitness.com, or propanefitness.com (including spam/trash). "
        "If nothing has arrived, proceed immediately.", s["body"]
    ))
    elements.append(Spacer(1, 6))
    elements.append(Paragraph(
        "<b>Important — 14-day refund window:</b> Your 14-day window under their terms (and UK Consumer "
        "Contracts Regulations 2013) expires March 16. Filing on March 14 keeps you well within this window "
        "and strengthens your position. Do not delay beyond March 16.", warning_style
    ))
    elements.append(Spacer(1, 15))

    # ===== SECTION 2: FINAL EMAIL =====
    elements.append(Paragraph("SECTION 2: SEND ONE FINAL EMAIL — TODAY (MARCH 13)", s["h2"]))
    elements.append(HRFlowable(width="100%", thickness=1, color=BrandConfig.GOLD))
    elements.append(Spacer(1, 8))

    elements.append(Paragraph(
        "<b>Yes — send one short, final email today.</b> This is not a negotiation or a new argument. "
        "It is a formal notice that the deadline has passed and you are proceeding. This email serves as "
        "your final paper trail entry before filing and will be included as evidence in the chargeback.", s["body"]
    ))
    elements.append(Spacer(1, 8))

    elements.append(Paragraph("Email — Copy Exactly As Written:", s["h3"]))
    elements.append(Spacer(1, 4))
    elements.append(Paragraph("<b>To:</b> jim@propanefitness.com", s["body"]))
    elements.append(Paragraph("<b>CC:</b> admin@propanefitness.com", s["body"]))
    elements.append(Paragraph(
        "<b>Subject:</b> Re: Formal Refund Request — Propane Business Mentorship [Receipt #1257-2744 / #1001-9268]",
        s["body"]
    ))
    elements.append(Spacer(1, 6))

    email_text = (
        "Jim,<br/><br/>"
        "This email serves as formal notice that the March 13, 2026 deadline set in my emails of March 7 "
        "and March 12 has now passed without resolution.<br/><br/>"
        "To summarize the record:<br/>"
        "— March 6: Formal refund request sent (Day 4 of your 14-day refund window)<br/>"
        "— March 7: Follow-up sent after your reply addressed only foreign transaction fees<br/>"
        "— March 12: Final demand sent, citing 5 specific breaches of your own Terms of Use<br/>"
        "— March 13: Deadline expired — no refund, no substantive response, no refund form provided<br/><br/>"
        "I have acted in good faith throughout this process and have given you every reasonable opportunity "
        "to resolve this directly. You have not honored your own 14-day refund policy (Section 7.1), "
        "have not provided the refund request form required by Section 7.4, and have not provided a "
        "substantive response within the 7 days required by Section 12.5.<br/><br/>"
        "I am now proceeding with formal dispute proceedings through my card issuer, as is my right — "
        "a statutory right your own terms (Section 12.5, Exceptions) acknowledge cannot be waived "
        "by agreement.<br/><br/>"
        "If you wish to resolve this before the dispute is filed, a full refund of £6,300 to the original "
        "payment methods will close this matter immediately. I can be reached at this email address.<br/><br/>"
        "William Marceau<br/>"
        "wmarceau@marceausolutions.com"
    )
    elements.append(Paragraph(email_text, script_style))
    elements.append(Spacer(1, 8))

    elements.append(Paragraph("<b>Why this email matters:</b>", s["body_bold"]))
    elements.append(Paragraph("• It timestamps the moment you exhausted good-faith resolution.", step_style))
    elements.append(Paragraph("• It gives Jim one final off-ramp (refund before the dispute lands).", step_style))
    elements.append(Paragraph("• It preempts any argument that you 'skipped straight to chargeback.'", step_style))
    elements.append(Paragraph("• It explicitly references the sections of THEIR OWN terms they breached.", step_style))
    elements.append(Paragraph("• Amex dispute analysts read these email chains — this closes the loop cleanly.", step_style))
    elements.append(Spacer(1, 6))

    elements.append(Paragraph(
        "<b>Tone note:</b> This email is intentionally measured and professional — no anger, no threats "
        "beyond what you've already stated. Amex analysts and, if it escalates, regulators will review "
        "this correspondence. You want every email to read as reasonable, specific, and factual.", warning_style
    ))

    elements.append(PageBreak())

    # ===== SECTION 3: FILING THE CHARGEBACK =====
    elements.append(Paragraph("SECTION 3: FILING THE CHARGEBACK WITH AMEX", s["h2"]))
    elements.append(HRFlowable(width="100%", thickness=1, color=BrandConfig.GOLD))
    elements.append(Spacer(1, 8))

    elements.append(Paragraph("<b>File on: Friday, March 14, 2026 (morning)</b>", s["body_bold"]))
    elements.append(Paragraph(
        "You must file <b>two separate disputes</b> — one for each card. Both are under the same Amex account. "
        "You can file both in the same phone call or online session.", s["body"]
    ))
    elements.append(Spacer(1, 10))

    elements.append(Paragraph("Option A: File by Phone (Recommended)", s["h3"]))
    elements.append(Paragraph(
        "Filing by phone is recommended for disputes of this size ($8,700+). You speak to a dispute specialist "
        "who can note the complexity and ensure both disputes are linked. It also lets you add verbal context "
        "that may not fit in an online form.", s["body"]
    ))
    elements.append(Spacer(1, 6))
    elements.append(Paragraph("<b>Call:</b> 1-800-528-4800 (Amex Disputes)", s["body_bold"]))
    elements.append(Paragraph("<b>Hours:</b> 24/7, but weekday mornings get faster routing to senior reps", s["body"]))
    elements.append(Spacer(1, 8))

    elements.append(Paragraph("Phone Script — What to Say:", s["h3"]))
    elements.append(Spacer(1, 4))

    phone_script = (
        "<b>Opening (when connected to disputes):</b><br/><br/>"
        "\"Hi, I need to file two disputes for charges on my account from the same merchant. "
        "Both charges are from PROPANEFITNESS.COM NEWCASTLE GB, dated March 2, 2026. "
        "One is on my card ending 1007 for $4,255.97, and the other is on my card ending 1049 "
        "for the same amount. They're two halves of the same transaction — the merchant split "
        "a £6,300 charge across two of my cards.\"<br/><br/>"
        "<b>When asked for the reason:</b><br/><br/>"
        "\"The service I received is materially different from what was sold to me. I purchased a "
        "12-week business mentorship that was sold as including dedicated weekly one-on-one Zoom "
        "coaching sessions with a personal coach. After I paid, I was told that weekly one-on-one "
        "calls are no longer offered and the program is primarily group coaching and a community "
        "chat platform. The seller's own written email confirms the one-on-one coaching promise. "
        "This is a bait-and-switch — the core service I paid for was not delivered as described.\"<br/><br/>"
        "<b>When asked if you contacted the merchant:</b><br/><br/>"
        "\"Yes. I contacted the merchant directly on March 6 — four days after purchase, well within "
        "their own 14-day refund policy. I sent three formal emails: March 6, March 7, and March 12. "
        "The merchant's only reply addressed a minor point about foreign transaction fees and ignored "
        "all of my refund grounds. The merchant also never provided the refund request form that their "
        "own terms require them to supply. I set a deadline of March 13, which passed yesterday with "
        "no resolution. I also sent a final notice yesterday confirming I would proceed with a dispute.\"<br/><br/>"
        "<b>When asked about the foreign transaction fees:</b><br/><br/>"
        "\"Each charge also has a $114.91 foreign transaction fee associated with it. I'd like those "
        "reversed as well if the disputes are successful. The merchant never disclosed that the charges "
        "would be in British pounds or that foreign transaction fees would apply.\"<br/><br/>"
        "<b>If asked about the merchant's terms/contract:</b><br/><br/>"
        "\"The merchant sent a link to their terms just 2 minutes before sending the payment links. "
        "Payment was processed within 5 minutes. The formal terms agreement wasn't actually signed "
        "until 3 days after they collected payment. So the terms weren't agreed to at the time of "
        "purchase.\"<br/><br/>"
        "<b>If asked to summarize what you want:</b><br/><br/>"
        "\"I'm requesting a full reversal of both charges plus the foreign transaction fees — "
        "$4,370.88 per card, $8,741.76 total. The service was misrepresented, the merchant failed "
        "to honor their own refund policy, and they've been unresponsive to my formal requests.\""
    )
    elements.append(Paragraph(phone_script, script_style))
    elements.append(Spacer(1, 12))

    elements.append(Paragraph("Option B: File Online", s["h3"]))
    elements.append(Paragraph("1. Log in to <b>global.americanexpress.com</b>", step_style))
    elements.append(Paragraph("2. Go to <b>Statements & Activity</b>", step_style))
    elements.append(Paragraph("3. Find the PROPANEFITNESS.COM charge on card ending <b>1007</b>", step_style))
    elements.append(Paragraph("4. Click the charge → <b>'Dispute This Charge'</b>", step_style))
    elements.append(Paragraph("5. Select reason: <b>'I didn't receive the goods/services as described'</b> or <b>'Merchandise/Service Not as Described'</b>", step_style))
    elements.append(Paragraph("6. Paste the dispute narrative (provided below) into the description field", step_style))
    elements.append(Paragraph("7. Upload supporting documents (list below)", step_style))
    elements.append(Paragraph("8. Submit → Repeat for card ending <b>1049</b>", step_style))
    elements.append(Spacer(1, 8))
    elements.append(Paragraph(
        "<b>Note:</b> The online form may have a character limit. If so, keep the narrative to the key points "
        "(bait-and-switch, within 14-day window, no response) and upload the full dispute letter as a PDF attachment.",
        warning_style
    ))

    elements.append(PageBreak())

    # ===== SECTION 4: DISPUTE NARRATIVE =====
    elements.append(Paragraph("SECTION 4: WRITTEN DISPUTE NARRATIVE", s["h2"]))
    elements.append(HRFlowable(width="100%", thickness=1, color=BrandConfig.GOLD))
    elements.append(Spacer(1, 8))

    elements.append(Paragraph(
        "Use this narrative for the online form or as the written statement you provide to the phone rep. "
        "This is for Card 1 (ending 1007). For Card 2 (ending 1049), add the sentence: "
        "\"This charge is the second of two payments split across two cards for the same transaction.\"",
        s["body"]
    ))
    elements.append(Spacer(1, 8))

    narrative = (
        "I am disputing a charge of $4,255.97 from PROPANEFITNESS.COM NEWCASTLE GB on March 2, 2026, "
        "along with the associated $114.91 foreign transaction fee.<br/><br/>"
        "I purchased a business mentorship program from PropaneFitness (UK company). I am requesting "
        "a chargeback on the following grounds:<br/><br/>"
        "<b>1. BAIT-AND-SWITCH ON CORE SERVICE:</b> The seller explicitly promised dedicated weekly "
        "one-on-one Zoom coaching sessions with a personal coach. The seller's follow-up email confirms "
        "in writing: 'Dedicated 1-2-1 coach for 12 weeks' with 'calls to customise the process to your "
        "business.' After payment, my assigned coach confirmed during the onboarding call that they no "
        "longer offer consistent weekly 1-on-1 calls and instead rely on group coaching clinics and "
        "community interaction. The core service I purchased was not delivered as represented.<br/><br/>"
        "<b>2. WITHIN MERCHANT'S OWN 14-DAY REFUND POLICY:</b> The merchant's published terms state: "
        "'Within 14 Days of Purchase: We offer a full refund if the refund request form has been "
        "successfully completed within the first 14 days.' I requested a refund on March 6 — Day 4 of 14. "
        "The merchant failed to provide the refund form required by their own Section 7.4.<br/><br/>"
        "<b>3. TERMS NOT AGREED BEFORE PAYMENT:</b> A link to terms was emailed at 15:27. Payment links "
        "were sent 2 minutes later at 15:29. The first charge was processed at 15:32. The formal terms "
        "agreement (Jotform) was not signed until March 5 — 3 days after both charges were already "
        "processed. The merchant's refund restrictions were not formally agreed at the time of purchase.<br/><br/>"
        "<b>4. MERCHANT UNRESPONSIVE TO FORMAL REFUND REQUESTS:</b> I sent formal refund emails on "
        "March 6, March 7, and March 12. The merchant's only reply (March 7) addressed foreign transaction "
        "fees alone and ignored all substantive grounds. The merchant's own terms (Section 12.5) require "
        "a substantive response within 7 days — they breached their own process. A final deadline of "
        "March 13 was set and passed with no resolution.<br/><br/>"
        "<b>5. HIGH-PRESSURE SALES:</b> The entire sequence from pricing email to full £6,300 payment "
        "was completed in 22 minutes, with only 2 minutes between the terms link and payment links.<br/><br/>"
        "I have not accessed or consumed any course content. I contacted the merchant well within their "
        "refund window, exhausted all direct resolution attempts, and sent a final notice on March 13 "
        "before proceeding with this dispute.<br/><br/>"
        "<b>Amount to dispute:</b> $4,255.97 + $114.91 FTF = $4,370.88"
    )
    elements.append(Paragraph(narrative, script_style))
    elements.append(Spacer(1, 15))

    # ===== SECTION 5: VERBIAGE STRATEGY =====
    elements.append(Paragraph("SECTION 5: VERBIAGE STRATEGY — HOW TO FRAME IT", s["h2"]))
    elements.append(HRFlowable(width="100%", thickness=1, color=BrandConfig.GOLD))
    elements.append(Spacer(1, 8))

    elements.append(Paragraph(
        "Amex dispute analysts evaluate claims based on specific chargeback reason codes. "
        "The words you use matter because they map to these codes. Here's how to frame your language:", s["body"]
    ))
    elements.append(Spacer(1, 8))

    verbiage_data = [
        ["Use This Language", "Avoid This Language", "Why"],
        [
            "\"Service not as described\"",
            "\"I changed my mind\"",
            "Maps to Amex reason code C31 (Goods/Services Not as Described) — strongest code for your case"
        ],
        [
            "\"Misrepresentation of service\"",
            "\"I'm unhappy with the service\"",
            "Dissatisfaction is weak; misrepresentation is a specific, provable claim"
        ],
        [
            "\"The seller promised X in writing, delivered Y\"",
            "\"I expected something different\"",
            "Written evidence of promises vs. delivery is the gold standard for disputes"
        ],
        [
            "\"I attempted to resolve directly\"",
            "\"They wouldn't give me my money back\"",
            "Shows you acted in good faith before escalating"
        ],
        [
            "\"Within the merchant's own refund policy\"",
            "\"I want a refund because...\"",
            "Frames the merchant as violating their own rules — very persuasive to analysts"
        ],
        [
            "\"The merchant was unresponsive to formal requests\"",
            "\"They ignored me\"",
            "Professional framing; analysts note merchant non-response as a significant factor"
        ],
    ]
    vt = Table(verbiage_data, colWidths=[2.1*inch, 2.1*inch, 2.5*inch])
    vt.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BrandConfig.CHARCOAL),
        ("TEXTCOLOR", (0, 0), (-1, 0), BrandConfig.WHITE),
        ("FONTNAME", (0, 0), (-1, 0), BrandConfig.HEADING_FONT),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("FONTNAME", (0, 1), (-1, -1), BrandConfig.BODY_FONT),
        ("FONTSIZE", (0, 1), (-1, -1), 8.5),
        ("BACKGROUND", (0, 1), (-1, -1), HexColor("#faf9f6")),
        ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#e2e0d8")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(vt)
    elements.append(Spacer(1, 10))

    elements.append(Paragraph("<b>Key phrase to use repeatedly:</b>", s["body_bold"]))
    elements.append(Paragraph(
        "\"The service I received is materially different from what the seller represented in writing at the point of sale.\"",
        script_style
    ))
    elements.append(Paragraph(
        "This single sentence hits the exact criteria for Amex reason code C31. Use it in the phone call, "
        "the online form, and any follow-up correspondence.", s["body"]
    ))

    elements.append(PageBreak())

    # ===== SECTION 6: SUPPORTING DOCUMENTS =====
    elements.append(Paragraph("SECTION 6: SUPPORTING DOCUMENTS TO UPLOAD/HAVE READY", s["h2"]))
    elements.append(HRFlowable(width="100%", thickness=1, color=BrandConfig.GOLD))
    elements.append(Spacer(1, 8))

    elements.append(Paragraph(
        "Gather these before filing. If filing by phone, have them ready to email or upload when Amex provides "
        "a case number and document submission link.", s["body"]
    ))
    elements.append(Spacer(1, 8))

    docs_data = [
        ["#", "Document", "What It Proves"],
        ["1", "Jim's sales email (March 2, 15:18)\nSubject: 'Next steps to secure your spot'",
         "Written promise of 'Dedicated 1-2-1 coach for 12 weeks' and 'immediate access'"],
        ["2", "Stripe receipt #1257-2744 (card 1007)",
         "Charge amount, date, merchant identity"],
        ["3", "Stripe receipt #1001-9268 (card 1049)",
         "Second charge amount, same merchant"],
        ["4", "Signed terms email (March 5, from Jotform)\nInvoice INV-6485333402225932830",
         "Terms signed 3 days AFTER payment — not agreed at time of purchase"],
        ["5", "Your refund request email (March 6)",
         "Refund requested within 14-day window (Day 4)"],
        ["6", "Your follow-up email (March 7)",
         "Escalation with 7 grounds and March 13 deadline"],
        ["7", "Your escalation email (March 12)",
         "Final demand citing 5 specific terms breaches"],
        ["8", "Your final notice email (March 13, today)",
         "Deadline expired, proceeding with dispute"],
        ["9", "Amex statements showing both charges + FTFs",
         "Actual amounts debited including undisclosed FTFs"],
        ["10", "Screenshot of propane-business.com/terms\n(Section 7.1 — 14-day refund policy)",
         "Merchant's own published refund policy they violated"],
    ]
    dt = Table(docs_data, colWidths=[0.4*inch, 2.8*inch, 3.5*inch])
    dt.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BrandConfig.CHARCOAL),
        ("TEXTCOLOR", (0, 0), (-1, 0), BrandConfig.WHITE),
        ("FONTNAME", (0, 0), (-1, 0), BrandConfig.HEADING_FONT),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("FONTNAME", (0, 1), (-1, -1), BrandConfig.BODY_FONT),
        ("FONTSIZE", (0, 1), (-1, -1), 8.5),
        ("BACKGROUND", (0, 1), (-1, -1), HexColor("#faf9f6")),
        ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#e2e0d8")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(dt)
    elements.append(Spacer(1, 15))

    # ===== SECTION 7: WHAT HAPPENS AFTER FILING =====
    elements.append(Paragraph("SECTION 7: WHAT HAPPENS AFTER YOU FILE", s["h2"]))
    elements.append(HRFlowable(width="100%", thickness=1, color=BrandConfig.GOLD))
    elements.append(Spacer(1, 8))

    elements.append(Paragraph("<b>Amex Chargeback Process Timeline:</b>", s["body_bold"]))
    elements.append(Spacer(1, 6))

    timeline_data = [
        ["Phase", "Timeframe", "What Happens"],
        ["Provisional credit", "Within 3-5 business days",
         "Amex issues a temporary credit to your account for the disputed amount while they investigate."],
        ["Merchant notification", "Within 7-10 days",
         "Amex notifies Propane's payment processor (Stripe) of the dispute. Propane has 20 days to respond with evidence."],
        ["Merchant response window", "20 days from notification",
         "If Propane does not respond, you win automatically. If they respond, Amex reviews both sides."],
        ["Amex decision", "45-90 days total",
         "Amex makes a final determination. Given the strength of your evidence (written promises, within refund window, merchant non-response), the odds are strongly in your favor."],
        ["Final resolution", "Up to 120 days",
         "If Propane challenges Amex's decision, there may be a second review. This is rare for disputes with strong documentation."],
    ]
    tt = Table(timeline_data, colWidths=[1.5*inch, 1.5*inch, 3.7*inch])
    tt.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BrandConfig.CHARCOAL),
        ("TEXTCOLOR", (0, 0), (-1, 0), BrandConfig.WHITE),
        ("FONTNAME", (0, 0), (-1, 0), BrandConfig.HEADING_FONT),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("FONTNAME", (0, 1), (-1, -1), BrandConfig.BODY_FONT),
        ("FONTSIZE", (0, 1), (-1, -1), 8.5),
        ("BACKGROUND", (0, 1), (-1, -1), HexColor("#faf9f6")),
        ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#e2e0d8")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(tt)

    elements.append(PageBreak())

    # ===== SECTION 8: ANTICIPATE PROPANE'S RESPONSE =====
    elements.append(Paragraph("SECTION 8: WHAT PROPANE WILL LIKELY ARGUE (AND YOUR COUNTER)", s["h2"]))
    elements.append(HRFlowable(width="100%", thickness=1, color=BrandConfig.GOLD))
    elements.append(Spacer(1, 8))

    elements.append(Paragraph(
        "Propane's payment processor (Stripe) will send them a dispute notification. If they respond, "
        "these are the most likely arguments and your prepared counters:", s["body"]
    ))
    elements.append(Spacer(1, 8))

    counters = [
        ("\"The customer signed the terms on March 5\"",
         "The terms were signed under economic duress — £6,300 had already been collected 3 days earlier. "
         "Access to course content was withheld until signing. The cardholder had no meaningful choice. "
         "Additionally, the cardholder has not accessed or consumed any course content even after signing."),
        ("\"The customer accessed the platform / engaged with the program\"",
         "The cardholder sent one introductory message on Circle.so (the community platform) and attended "
         "one onboarding Zoom call — during which the coach confirmed the 1-on-1 coaching promise was "
         "no longer offered. This is how the misrepresentation was discovered, not evidence of acceptance. "
         "The cardholder has not accessed any course modules, videos, or training materials."),
        ("\"Filing a chargeback breaches our contract (Section 7.5)\"",
         "The cardholder is not circumventing the refund policy — the cardholder followed it (requested "
         "within 14 days) and the merchant failed to honor it. A chargeback is the cardholder's statutory "
         "right, which the merchant's own terms (Section 12.5 Exceptions) acknowledge cannot be waived."),
        ("\"The customer didn't complete the refund eligibility conditions\"",
         "Section 7.2 requires 2 weeks of modules, 2 hotseat calls, and lead generation — all within 14 days. "
         "These conditions require substantial engagement with a service that was misrepresented. The claim "
         "is based on misrepresentation, not dissatisfaction after use."),
        ("\"1-on-1 coaching IS available through coaching clinics\"",
         "The seller promised 'Dedicated 1-2-1 coach for 12 weeks' with 'calls to customise the process.' "
         "What was delivered is group coaching clinics with no calendar or booking system for 1-on-1 sessions. "
         "The assigned coach verbally confirmed weekly 1-on-1 calls are no longer offered."),
    ]

    for arg, counter in counters:
        elements.append(Paragraph(f"<b>Their argument:</b> {arg}", s["body_bold"]))
        elements.append(Paragraph(f"<b>Your counter:</b> {counter}", step_style))
        elements.append(Spacer(1, 8))

    elements.append(Spacer(1, 10))

    # ===== SECTION 9: ADDITIONAL STEPS =====
    elements.append(Paragraph("SECTION 9: ADDITIONAL STEPS AFTER FILING", s["h2"]))
    elements.append(HRFlowable(width="100%", thickness=1, color=BrandConfig.GOLD))
    elements.append(Spacer(1, 8))

    elements.append(Paragraph("These are optional escalation steps. File the chargeback first — "
        "these are secondary measures if needed.", s["body"]))
    elements.append(Spacer(1, 8))

    elements.append(Paragraph("A. Screenshot the Terms Page (Do This Today)", s["h3"]))
    elements.append(Paragraph(
        "Go to <b>propane-business.com/terms</b> and take full-page screenshots of Sections 7.1 "
        "(14-day refund policy), 7.4 (refund form obligation), 11.4 (misrepresentation liability), "
        "and 12.5 (dispute resolution). Save these as PDFs. Merchants sometimes update terms pages "
        "after a dispute is filed. Capture the current version today.", s["body"]
    ))
    elements.append(Spacer(1, 8))

    elements.append(Paragraph("B. UK Trading Standards (If Chargeback Is Contested)", s["h3"]))
    elements.append(Paragraph(
        "File via Citizens Advice: <b>citizensadvice.org.uk/consumer</b> or call <b>0808 223 1133</b>. "
        "Grounds: misrepresentation of services under the Consumer Protection from Unfair Trading "
        "Regulations 2008. Mention the bait-and-switch on 1-on-1 coaching specifically.", s["body"]
    ))
    elements.append(Spacer(1, 8))

    elements.append(Paragraph("C. Competition and Markets Authority (Optional)", s["h3"]))
    elements.append(Paragraph(
        "Report at <b>gov.uk/cma-cases</b>. Grounds: unfair commercial practices — high-pressure "
        "22-minute sales timeline, misrepresentation of service, terms collected post-payment.", s["body"]
    ))
    elements.append(Spacer(1, 8))

    elements.append(Paragraph("D. Factual Reviews (After Resolution)", s["h3"]))
    elements.append(Paragraph(
        "Only post reviews <b>after</b> the chargeback is resolved. Keep reviews strictly factual — "
        "state what was promised, what was delivered, and the timeline. Do not editorialize or use "
        "emotional language. Platforms: Trustpilot (propanefitness.com) and Google Business.", s["body"]
    ))
    elements.append(Spacer(1, 8))

    elements.append(Paragraph("E. Stop All Engagement with Propane Immediately", s["h3"]))
    elements.append(Paragraph(
        "Do not open any course content, attend any calls, or engage on Circle.so. Any further engagement "
        "weakens the 'service not as described' argument. Unsubscribe from their automated emails. "
        "If they contact you through Circle.so or other informal channels, do not respond — redirect "
        "everything to email for the paper trail.", s["body"]
    ))

    elements.append(Spacer(1, 20))

    # ===== SECTION 10: ACTION CHECKLIST =====
    elements.append(Paragraph("SECTION 10: COMPLETE ACTION CHECKLIST", s["h2"]))
    elements.append(HRFlowable(width="100%", thickness=1, color=BrandConfig.GOLD))
    elements.append(Spacer(1, 8))

    checklist_data = [
        ["", "Action", "When"],
        ["☐", "Send final notice email to Jim (Section 2 above)", "Today — March 13"],
        ["☐", "Screenshot propane-business.com/terms (Sections 7.1, 7.4, 11.4, 12.5)", "Today — March 13"],
        ["☐", "Stop all engagement with Propane platform (no Circle, no calls, no content)", "Now — ongoing"],
        ["☐", "Gather all supporting documents (Section 6 list)", "Today/tonight"],
        ["☐", "Final inbox check (jim@, admin@, propanefitness.com — incl. spam)", "March 14, 9 AM ET"],
        ["☐", "Call Amex 1-800-528-4800 — file Dispute 1 (card 1007, $4,370.88)", "March 14, morning"],
        ["☐", "File Dispute 2 in same call (card 1049, $4,370.88)", "March 14, same call"],
        ["☐", "Request FTF reversal for both charges during the call", "March 14, same call"],
        ["☐", "Note Amex case numbers for both disputes", "March 14"],
        ["☐", "Upload supporting documents when Amex provides submission link", "March 14-15"],
        ["☐", "Unsubscribe from all Propane marketing emails", "March 14"],
        ["☐", "Monitor email for Amex confirmation and any Propane response", "Ongoing"],
    ]
    ct = Table(checklist_data, colWidths=[0.4*inch, 4.3*inch, 2*inch])
    ct.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BrandConfig.CHARCOAL),
        ("TEXTCOLOR", (0, 0), (-1, 0), BrandConfig.WHITE),
        ("FONTNAME", (0, 0), (-1, 0), BrandConfig.HEADING_FONT),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("FONTNAME", (0, 1), (-1, -1), BrandConfig.BODY_FONT),
        ("FONTSIZE", (0, 1), (-1, -1), 9),
        ("BACKGROUND", (0, 1), (-1, -1), HexColor("#faf9f6")),
        ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#e2e0d8")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("FONTNAME", (0, 1), (0, -1), BrandConfig.HEADING_FONT),
        ("FONTSIZE", (0, 1), (0, -1), 12),
        ("ALIGN", (0, 1), (0, -1), "CENTER"),
    ]))
    elements.append(ct)

    elements.append(Spacer(1, 25))
    elements.append(HRFlowable(width="100%", thickness=1, color=BrandConfig.GOLD))
    elements.append(Spacer(1, 8))
    elements.append(Paragraph(
        f"Prepared: {datetime.now().strftime('%B %d, %Y at %I:%M %p')} | Marceau Solutions",
        s["small"]
    ))
    elements.append(Paragraph(
        "This document is for personal use in filing a legitimate chargeback dispute. "
        "All claims are based on documented email evidence and the merchant's published terms.",
        s["small"]
    ))

    doc.build(elements)
    print(f"Generated: {OUTPUT}")


if __name__ == "__main__":
    build()
