#!/usr/bin/env python3
"""
Generate Dystonia Treatment Decision Guide — branded PDF.
Comprehensive cost-benefit analysis of clonazepam, alternative medications,
and non-pharmaceutical treatments for secondary dystonia pain.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.colors import HexColor
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, KeepTogether
)
from execution.branded_pdf_engine import (
    BrandConfig, _register_fonts, get_brand_styles,
    branded_table, accent_line, section_title, bullet_list,
    _on_page
)

_register_fonts()
S = get_brand_styles()

# Helpers
def stitle(text):
    return section_title(text, S)

def blist(items):
    return bullet_list(items, S)

def btable(headers, rows, col_widths=None):
    return branded_table(headers, rows, col_widths=col_widths)

# Styles
body = S["body"]
bold = S["body_bold"]
h3 = S["h3"]

cover_title = ParagraphStyle(
    "CoverTitle", fontName=BrandConfig.HEADING_FONT,
    fontSize=26, leading=32, textColor=BrandConfig.CHARCOAL,
    alignment=TA_CENTER, spaceAfter=8,
)
cover_sub = ParagraphStyle(
    "CoverSub", fontName=BrandConfig.BODY_FONT,
    fontSize=12, leading=17, textColor=BrandConfig.DARK_GRAY,
    alignment=TA_CENTER, spaceAfter=6,
)
cover_detail = ParagraphStyle(
    "CoverDetail", fontName=BrandConfig.BODY_FONT,
    fontSize=11, leading=16, textColor=BrandConfig.CHARCOAL,
    alignment=TA_CENTER, spaceAfter=4,
)
note = ParagraphStyle(
    "Note", fontName=BrandConfig.BODY_FONT,
    fontSize=8, leading=11, textColor=BrandConfig.DARK_GRAY,
    leftIndent=6, spaceBefore=4, spaceAfter=4,
)
callout = ParagraphStyle(
    "Callout", fontName=BrandConfig.BODY_FONT_BOLD,
    fontSize=10, leading=15, textColor=HexColor("#92400e"),
    leftIndent=12, rightIndent=12, spaceBefore=6, spaceAfter=6,
    backColor=HexColor("#fef3c7"), borderPadding=8,
)
green_callout = ParagraphStyle(
    "GreenCallout", fontName=BrandConfig.BODY_FONT_BOLD,
    fontSize=10, leading=15, textColor=HexColor("#065f46"),
    leftIndent=12, rightIndent=12, spaceBefore=6, spaceAfter=6,
    backColor=HexColor("#d1fae5"), borderPadding=8,
)
blue_callout = ParagraphStyle(
    "BlueCallout", fontName=BrandConfig.BODY_FONT_BOLD,
    fontSize=10, leading=15, textColor=HexColor("#1e3a5f"),
    leftIndent=12, rightIndent=12, spaceBefore=6, spaceAfter=6,
    backColor=HexColor("#dbeafe"), borderPadding=8,
)
footer = ParagraphStyle(
    "Footer", fontName=BrandConfig.BODY_FONT,
    fontSize=8, leading=11, textColor=BrandConfig.TEXT_MUTED,
    alignment=TA_CENTER, spaceBefore=20,
)
quote_style = ParagraphStyle(
    "Quote", fontName=BrandConfig.BODY_FONT,
    fontSize=9, leading=13, textColor=HexColor("#555555"),
    leftIndent=20, rightIndent=20, spaceBefore=4, spaceAfter=4,
    borderPadding=6, backColor=HexColor("#f8f6f0"),
)


def build_pdf():
    output = os.path.join(os.path.dirname(__file__), "..",
                          "docs", "dystonia-treatment-decision-guide.pdf")
    doc = SimpleDocTemplate(
        output, pagesize=letter,
        leftMargin=0.75 * inch, rightMargin=0.75 * inch,
        topMargin=0.8 * inch, bottomMargin=0.7 * inch,
    )
    story = []

    # ==================== COVER PAGE ====================
    story.append(Spacer(1, 1.2 * inch))
    story.append(accent_line())
    story.append(Spacer(1, 15))
    story.append(Paragraph("DYSTONIA TREATMENT", cover_title))
    story.append(Paragraph("DECISION GUIDE", cover_title))
    story.append(Spacer(1, 8))
    story.append(Paragraph("A Research-Based Framework for Informed Decision-Making", cover_sub))
    story.append(Paragraph("Prepared March 21, 2026", cover_detail))
    story.append(Spacer(1, 10))
    story.append(accent_line())
    story.append(Spacer(1, 25))

    story.append(Paragraph(
        "This guide compiles current medical evidence to help evaluate treatment options "
        "for secondary dystonia with severe pain. It covers clonazepam (the one medication "
        "that worked), alternative medications, non-pharmaceutical interventions, and "
        "practical cannabis strategies — with honest cost-benefit analysis for each.",
        body
    ))
    story.append(Spacer(1, 15))

    toc = [
        ["Section", "Page"],
        ["1. Your Situation — Decision Framework", "2"],
        ["2. Clonazepam Deep Dive — Benefits vs. Risks", "3"],
        ["3. The Prescribing Landscape — How to Get It", "5"],
        ["4. Alternative Medications You Haven't Tried", "6"],
        ["5. Non-Pharmaceutical Interventions", "8"],
        ["6. Cannabis Strategy — Functional Alternatives to THC", "10"],
        ["7. Cost-Benefit Comparison Matrix", "11"],
        ["8. Recommended Path Forward", "12"],
    ]
    story.append(btable(["Section", "Page"], toc[1:], col_widths=[5.5 * inch, 1.3 * inch]))
    story.append(Spacer(1, 15))
    story.append(Paragraph(
        "DISCLAIMER: This document compiles published medical research for informational "
        "purposes. It is not medical advice. All treatment decisions should be made with "
        "a qualified physician who understands your full medical history.",
        note
    ))

    story.append(PageBreak())

    # ==================== SECTION 1: DECISION FRAMEWORK ====================
    story.append(stitle("1. YOUR SITUATION — DECISION FRAMEWORK"))
    story.append(Spacer(1, 8))
    story.append(Paragraph("The Core Problem", h3))
    story.extend(blist([
        "Secondary dystonia (left hand, arm, shoulder, trap) with progressive worsening",
        "The PAIN is the disabling factor — tone alone would be manageable",
        "Clonazepam is the only medication that provided significant relief",
        "Lost access due to prescribing reluctance in Pittsburgh — medically withdrew from masters program",
        "Currently managing with THC — works for pain but impairs daily function at work",
    ]))
    story.append(Spacer(1, 8))
    story.append(Paragraph("The Decision You're Making", h3))
    story.append(Paragraph(
        "Should you go back on clonazepam given: (a) its proven efficacy for your dystonia, "
        "(b) the real risks of long-term benzodiazepine use, and (c) the absence of any "
        "equally effective alternative? Or should you pursue untried alternatives first?",
        body
    ))
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        "KEY INSIGHT: This is not a binary choice. The evidence supports a staged approach — "
        "restart clonazepam at the lowest effective dose for immediate pain relief while "
        "systematically trying alternatives that could supplement or eventually replace it.",
        green_callout
    ))

    story.append(PageBreak())

    # ==================== SECTION 2: CLONAZEPAM DEEP DIVE ====================
    story.append(stitle("2. CLONAZEPAM DEEP DIVE — BENEFITS VS. RISKS"))
    story.append(Spacer(1, 8))

    story.append(Paragraph("How It Works for Dystonia", h3))
    story.append(Paragraph(
        "Clonazepam is a long-acting, high-potency benzodiazepine that enhances GABA-A "
        "receptor activity, increasing the frequency of chloride channel opening and "
        "hyperpolarizing neurons. GABA directly regulates muscle tone — enhancing GABAergic "
        "transmission modulates the abnormal muscle firing patterns that cause dystonic "
        "contractions. Its long half-life (18-50 hours) provides sustained, even coverage "
        "throughout the day, which is why it's preferred over shorter-acting benzodiazepines "
        "for movement disorders.",
        body
    ))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Efficacy Evidence", h3))
    story.extend(blist([
        "A 2024 RCT found clonazepam + trihexyphenidyl significantly outperformed trihexyphenidyl alone for dystonia severity, pain, upper limb function, and quality of life (PubMed: 38945037)",
        "Greene (1988) found benefit in 16% of 115 patients with various dystonia forms — modest but real for a notoriously treatment-resistant condition",
        "Most useful for dystonias with jerky or tremulous quality and blepharospasm",
        "Recognized as second-line agent in Dystonia Coalition treatment guidelines alongside baclofen",
        "Patient-reported studies show clonazepam among the top-rated medications for dystonia symptom relief",
    ]))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Dosing for Dystonia", h3))
    story.append(btable(
        ["Parameter", "Detail"],
        [
            ["Typical range", "0.5–6 mg/day in 2-4 divided doses"],
            ["Starting dose", "0.25–0.5 mg at bedtime, titrate slowly"],
            ["Low dose threshold", "≤0.5 mg/day (10 mg diazepam equivalent)"],
            ["Smallest available tablet", "0.125 mg (allows very fine titration)"],
            ["Half-life", "18–50 hours (long-acting, smooth coverage)"],
            ["Peak effect", "1–4 hours after oral dose"],
        ],
        col_widths=[2.2 * inch, 4.6 * inch]
    ))
    story.append(Spacer(1, 10))

    # Benefits vs Risks table
    story.append(Paragraph("Honest Cost-Benefit Analysis", h3))
    story.append(btable(
        ["BENEFITS", "RISKS"],
        [
            [
                "Proven effective for YOUR dystonia — not theoretical",
                "Physical dependence develops in ~1/3 of patients after 4+ weeks"
            ],
            [
                "Long half-life = steady symptom control (no peaks/valleys)",
                "Tolerance to anti-seizure effects is common (tolerance to muscle-relaxant effects is less clear)"
            ],
            [
                "Allows full cognitive function at stable therapeutic dose",
                "Withdrawal can be dangerous — seizures, psychosis possible if stopped abruptly"
            ],
            [
                "Reduces both tone AND pain (your primary complaint)",
                "Sedation, especially during dose changes"
            ],
            [
                "2024 RCT confirms benefit when combined with trihexyphenidyl",
                "Cognitive effects at higher doses (impaired mentation, coordination)"
            ],
            [
                "Well-studied medication with 50+ years of clinical use",
                "Stigma makes finding a prescriber difficult"
            ],
            [
                "Enables work, daily function — unlike THC",
                "Depression risk may increase in susceptible individuals"
            ],
        ],
        col_widths=[3.4 * inch, 3.4 * inch]
    ))
    story.append(Spacer(1, 8))

    story.append(Paragraph("What the Evidence Actually Says About Long-Term Risk", h3))
    story.append(Paragraph(
        "The largest benzodiazepine study in history (950,000+ patients, American Journal of "
        "Psychiatry 2024) found that 85% discontinued during the first year, 97% by 7 years, "
        "and only 0.35% escalated to doses above recommended levels. The study's authors "
        "explicitly state that \"weak science, alarming FDA black box warnings, and media "
        "reporting have fueled an anti-benzodiazepine movement that at times portrays "
        "appropriate prescribing as a gateway to long-term dose escalation, tolerance, and "
        "drug misuse, creating an atmosphere of fear and stigma.\"",
        body
    ))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        "CONTEXT: The stigma around benzodiazepines is largely driven by their misuse in "
        "combination with opioids, not by their legitimate use for neurological conditions "
        "like dystonia. When taken as prescribed at stable doses for a specific condition, "
        "the risk profile is materially different from recreational or escalating use.",
        blue_callout
    ))
    story.append(Spacer(1, 8))

    # Withdrawal
    story.append(Paragraph("Withdrawal — The Real Concern", h3))
    story.extend(blist([
        "Withdrawal symptoms include anxiety, insomnia, tremors, sweating, confusion, and in severe cases, seizures",
        "Acute symptoms peak ~2 weeks after stopping; subtle effects can persist weeks to months",
        "A 2025 Joint Clinical Practice Guideline recommends tapering at 5-10% dose reduction every 2-4 weeks",
        "NEVER stop clonazepam abruptly — always taper with medical supervision",
        "At low therapeutic doses (0.5-1 mg/day), withdrawal is manageable with proper tapering",
        "Clonazepam's long half-life actually makes it one of the EASIER benzodiazepines to taper",
    ]))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "BOTTOM LINE: The withdrawal risk is real but manageable. It's a reason for caution "
        "and a proper tapering plan — not a reason to suffer in untreated pain.",
        green_callout
    ))

    story.append(PageBreak())

    # ==================== SECTION 3: PRESCRIBING LANDSCAPE ====================
    story.append(stitle("3. THE PRESCRIBING LANDSCAPE — HOW TO GET IT"))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Why Doctors Won't Prescribe", h3))
    story.extend(blist([
        "DEA Schedule IV classification creates paperwork and liability concerns",
        "Post-opioid-crisis environment has created blanket anti-controlled-substance culture",
        "Many PCPs have internal policies or insurance requirements limiting benzodiazepine prescribing",
        "New doctors often default to guidelines that emphasize short-term use only",
        "The 2024 AJP study explicitly criticizes this climate for harming legitimate patients",
    ]))
    story.append(Spacer(1, 8))

    story.append(Paragraph("How to Find a Willing Prescriber", h3))
    story.extend(blist([
        "TARGET: Movement disorder neurologist (NOT a general neurologist). They understand dystonia-specific pharmacology and are most comfortable prescribing clonazepam for it",
        "The Dystonia Medical Research Foundation (dystonia-foundation.org) maintains a provider directory",
        "The Dystonia Coalition (rarediseasesnetwork.org) lists specialists by region",
        "Ask specifically: \"Do you have experience treating secondary dystonia with benzodiazepines?\"",
        "Bring documentation: your diagnosis history, treatments tried, specific response to clonazepam",
        "Frame it as: \"I'm looking for a physician who can manage my dystonia long-term, including medications that have previously worked for me\"",
        "If in Naples FL, nearest major movement disorder centers: USF Tampa, University of Miami, Mayo Clinic Jacksonville",
    ]))
    story.append(Spacer(1, 8))

    story.append(Paragraph("What to Bring to the Appointment", h3))
    story.extend(blist([
        "Written timeline of your dystonia progression and all treatments tried",
        "Documentation of clonazepam's previous efficacy (any prior medical records)",
        "The 2024 RCT showing clonazepam + trihexyphenidyl efficacy (PubMed: 38945037)",
        "Documentation of your Pittsburgh experience (medical withdrawal due to medication access)",
        "List of everything else you've tried: Botox, baclofen, DBS, PT — showing you've exhausted other options",
        "Your willingness to use lowest effective dose with monitoring",
    ]))

    story.append(PageBreak())

    # ==================== SECTION 4: ALTERNATIVE MEDICATIONS ====================
    story.append(stitle("4. ALTERNATIVE MEDICATIONS YOU HAVEN'T TRIED"))
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        "These are medications with evidence for dystonia that you may not have tried. "
        "Rated by evidence strength and likelihood of helping with your specific "
        "complaint (pain from contractions).",
        body
    ))
    story.append(Spacer(1, 8))

    meds = [
        ["Medication", "Mechanism", "Evidence for Dystonia Pain", "Side Effects", "Worth Trying?"],
        [
            "Gabapentin\n(Neurontin)\n300-3600 mg/day",
            "Calcium channel modulator; reduces neuronal excitability",
            "Moderate — shown to improve dystonia severity and QoL in pediatric studies. Good for neuropathic pain component. CAUTION: can paradoxically worsen dystonia in rare cases",
            "Sedation, dizziness, weight gain. Generally well-tolerated",
            "YES — High priority. Addresses pain directly, may complement clonazepam"
        ],
        [
            "Pregabalin\n(Lyrica)\n150-600 mg/day",
            "Similar to gabapentin but more potent and predictable absorption",
            "Strong evidence for neuropathic pain (2025 meta-analysis). Less studied specifically for dystonia",
            "Similar to gabapentin. Dizziness, somnolence",
            "YES — If gabapentin doesn't work or isn't tolerated"
        ],
        [
            "Tizanidine\n(Zanaflex)\n2-36 mg/day",
            "Alpha-2 adrenergic agonist; reduces spasticity centrally",
            "Used for muscle pulling pain in dystonia. \"Particularly useful in patients who develop pain from uncontrolled muscle pulling\" — Movement Disorders literature",
            "Drowsiness, dry mouth, liver function monitoring needed",
            "YES — Directly targets your complaint (pain from pulling)"
        ],
        [
            "Trihexyphenidyl\n(Artane)\n6-60 mg/day",
            "Anticholinergic — first-line for dystonia in guidelines",
            "First-line per Dystonia Coalition guidelines. 2024 RCT showed even better results when combined with clonazepam",
            "Dry mouth, blurred vision, constipation, cognitive effects at high doses",
            "YES — Strongest evidence base for dystonia. Consider combining with clonazepam per 2024 study"
        ],
        [
            "Low-Dose Naltrexone\n(LDN)\n1.5-4.5 mg/day",
            "Anti-inflammatory via microglial modulation (not opioid blockade at low doses)",
            "Emerging — 64% response rate in chronic pain. Case reports of CRPS dystonic spasms remitting. Novel anti-inflammatory mechanism",
            "Minimal — transient nausea, vivid dreams. No dependence risk",
            "YES — Low risk, novel mechanism. Takes 1-3 months for effect"
        ],
        [
            "Diazepam\n(Valium)\n2-40 mg/day",
            "Benzodiazepine with strong muscle relaxant properties",
            "Similar mechanism to clonazepam. Some dystonia patients respond better to one vs. the other",
            "Similar benzo risks but shorter half-life = more fluctuation",
            "MAYBE — Backup if clonazepam access fails. Same prescribing barriers"
        ],
        [
            "Tetrabenazine\n(Xenazine)",
            "Depletes dopamine by inhibiting VMAT2",
            "Used for hyperkinetic movement disorders. Less evidence for dystonic pain specifically",
            "Depression (serious risk), sedation, parkinsonism",
            "LOW PRIORITY — Side effect profile is heavy; pain relief uncertain"
        ],
    ]
    story.append(btable(meds[0], meds[1:], col_widths=[1.1*inch, 1.2*inch, 1.7*inch, 1.2*inch, 1.6*inch]))
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        "TOP PICKS to discuss with your doctor: (1) Gabapentin/Pregabalin for pain, "
        "(2) Tizanidine for muscle pulling pain, (3) Trihexyphenidyl as first-line dystonia "
        "agent (combine with clonazepam per 2024 RCT), (4) Low-Dose Naltrexone as a "
        "low-risk adjunct.",
        green_callout
    ))

    story.append(PageBreak())

    # ==================== SECTION 5: NON-PHARMACEUTICAL ====================
    story.append(stitle("5. NON-PHARMACEUTICAL INTERVENTIONS"))
    story.append(Spacer(1, 8))

    nonpharma = [
        ["Intervention", "Evidence Level", "How It Could Help", "Practical Notes"],
        [
            "Acupuncture",
            "Moderate — 2025 review supports use for dystonia. Small studies show every participant reported improvement including pain reduction",
            "May modulate pain pathways and reduce muscle tension. Best as adjunct, not standalone",
            "Seek practitioner experienced with neurological conditions. 8-12 sessions to assess. Insurance may cover with neurology referral"
        ],
        [
            "Transcranial Magnetic Stimulation (TMS)",
            "Emerging — Duke University running trials for focal hand dystonia and cervical dystonia. Non-invasive. Not yet FDA-approved for dystonia",
            "Modulates cortical excitability in motor areas. Could address root cause of abnormal signaling",
            "Ask your neurologist about clinical trial eligibility. Available at academic medical centers"
        ],
        [
            "CBD Topicals\n(non-impairing)",
            "Moderate — interacts with local cannabinoid receptors without entering bloodstream. No cognitive impairment",
            "Localized pain and inflammation relief in shoulder/trap/arm. No psychoactive effects. Can use at work",
            "Available at FL dispensaries (MUV, Trulieve). Look for high-CBD topical creams. Apply directly to affected areas 2-3x daily"
        ],
        [
            "TENS Unit",
            "Low-Moderate — established for chronic pain, less studied for dystonia specifically",
            "Electrical stimulation may override pain signals and promote muscle relaxation in affected area",
            "Inexpensive ($30-50 OTC). Try on shoulder/trap area. No side effects. Use as needed"
        ],
        [
            "Mindfulness-Based Stress Reduction (MBSR)",
            "Moderate — strong evidence for chronic pain conditions. Not studied specifically for dystonia pain",
            "Won't reduce tone but may significantly improve pain perception and suffering. Reduces stress-related flare-ups",
            "8-week structured program. Available online. Free apps (Headspace, Calm). Complementary to any medication"
        ],
        [
            "Myofascial Release / Trigger Point Therapy",
            "Low-Moderate — clinical experience supports use for dystonia-related muscle pain",
            "Directly addresses secondary pain from sustained contractions. Releases adhesions and trigger points in affected muscles",
            "Find therapist experienced with movement disorders. 1-2x/week initially. Combines well with stretching program"
        ],
        [
            "Dry Needling",
            "Low — limited dystonia-specific evidence but promising for myofascial pain",
            "Targets specific trigger points in hypertonic muscles. May provide temporary relief from contracture pain",
            "Available through PT clinics in FL. Similar to acupuncture but targets motor points"
        ],
        [
            "Magnesium\nSupplement",
            "Low-Moderate — involved in muscle relaxation and GABA function. Deficiency worsens muscle cramping",
            "May support GABAergic function (same pathway as clonazepam). Reduces muscle cramping",
            "Magnesium glycinate 200-400 mg at bedtime. Low risk. May also improve sleep. Avoid magnesium oxide (poor absorption)"
        ],
        [
            "Ketamine Infusions",
            "Moderate for neuropathic pain — CRPS evidence strongest. Not studied specifically for dystonia",
            "NMDA receptor antagonism provides pain relief lasting up to 12 weeks per infusion cycle",
            "Expensive ($400-800/session). Available at pain clinics. Consider if pain has neuropathic component"
        ],
    ]
    story.append(btable(nonpharma[0], nonpharma[1:],
                        col_widths=[1.1*inch, 1.7*inch, 1.7*inch, 2.3*inch]))

    story.append(PageBreak())

    # ==================== SECTION 6: CANNABIS STRATEGY ====================
    story.append(stitle("6. CANNABIS STRATEGY — FUNCTIONAL ALTERNATIVES"))
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        "You're using THC for pain management but can't function at work. Here's what the "
        "research says about making cannabis work without the impairment.",
        body
    ))
    story.append(Spacer(1, 8))

    story.append(Paragraph("What the Dystonia Cannabis Study Found (Frontiers in Neurology, 2023)", h3))
    story.extend(blist([
        "Pain efficacy rated 3.8/5 — higher than dystonia symptom relief (3.3/5)",
        "THC-rich products were more effective than CBD-rich for dystonia and pain",
        "Average effective THC dose was ~100 mg/day (relatively high)",
        "Smoked cannabis showed 80% improvement vs. 20% for sublingual oil",
        "Side effects: dry mouth (65%), sedation (43%), dizziness (39%), psychiatric effects (26%)",
        "85% of patients experienced significant pain relief overall",
    ]))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Strategies for Functional Cannabis Use", h3))

    cannabis = [
        ["Strategy", "How It Works", "Impairment Level"],
        [
            "CBD Topicals\n(shoulder/trap/arm)",
            "Apply high-CBD cream directly to affected muscles. Interacts with local receptors. Does NOT enter bloodstream",
            "ZERO — no cognitive effects. Can use at work, anytime"
        ],
        [
            "High-CBD / Low-THC\noral products",
            "Ratios like 20:1 or 10:1 CBD:THC. Provides anti-inflammatory and muscle-relaxant effects with minimal psychoactivity",
            "MINIMAL — slight relaxation, no \"high.\" Most people can work normally"
        ],
        [
            "THC Microdosing\n(2.5-5 mg)",
            "Sub-psychoactive doses of THC. Threshold for most people is 5-10 mg. Stay below your threshold",
            "LOW — may feel slight effect but cognitive function preserved at true micro-doses"
        ],
        [
            "Evening-only THC\n+ daytime CBD",
            "Use full-strength THC only after work. CBD topicals and low-THC products during day",
            "SPLIT — impaired evenings, functional days"
        ],
        [
            "THC:CBD 1:1 ratio\nproducts",
            "CBD modulates THC's psychoactive effects. The entourage effect may provide better pain relief than either alone",
            "MODERATE — less impairment than pure THC. Test on a day off first"
        ],
    ]
    story.append(btable(cannabis[0], cannabis[1:], col_widths=[1.5*inch, 3.3*inch, 2.0*inch]))
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        "FLORIDA NOTE: With a FL medical cannabis card, you have access to topicals, "
        "tinctures, capsules, and specific ratio products at licensed dispensaries "
        "(MUV, Trulieve, Curaleaf, Surterra). A qualifying physician can recommend "
        "specific routes and ratios. Dystonia qualifies under \"muscle spasms\" or "
        "chronic pain conditions.",
        blue_callout
    ))

    story.append(PageBreak())

    # ==================== SECTION 7: COMPARISON MATRIX ====================
    story.append(stitle("7. COST-BENEFIT COMPARISON MATRIX"))
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        "Rating scale: 1 (poor) to 5 (excellent). Based on published evidence and "
        "clinical applicability to your specific case (secondary dystonia, pain-dominant, "
        "left upper extremity, treatment-resistant).",
        body
    ))
    story.append(Spacer(1, 8))

    matrix = [
        ["Treatment", "Pain Relief", "Function at Work", "Side Effect Risk", "Dependence Risk", "Evidence Level", "TOTAL /25"],
        ["Clonazepam (proven)", "5", "4", "3", "2", "4", "18"],
        ["THC (current)", "4", "1", "3", "2", "3", "13"],
        ["Gabapentin", "3", "4", "4", "1 (low)", "3", "15"],
        ["Tizanidine", "3", "4", "3", "1 (low)", "2", "13"],
        ["Trihexyphenidyl", "3", "3", "3", "1 (low)", "4", "14"],
        ["LDN", "2-3", "5", "5", "1 (none)", "2", "15-16"],
        ["CBD Topicals", "2", "5", "5", "1 (none)", "2", "15"],
        ["Acupuncture", "2", "5", "5", "1 (none)", "2", "15"],
        ["Clonazepam + Gabapentin\n(combination)", "5", "4", "3", "2", "3", "17"],
        ["Clonazepam + CBD Topicals\n(combination)", "5", "4", "4", "2", "3", "18"],
    ]
    story.append(btable(matrix[0], matrix[1:],
                        col_widths=[1.5*inch, 0.7*inch, 0.85*inch, 0.8*inch, 0.85*inch, 0.8*inch, 0.7*inch]))
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        "NOTE: Clonazepam scores highest for pain relief because it's the only treatment "
        "with PROVEN efficacy for your specific case. Its total score is brought down by "
        "dependence risk — but this is a manageable risk, not a disqualifying one. "
        "The combination strategies score highest overall.",
        note
    ))

    story.append(PageBreak())

    # ==================== SECTION 8: RECOMMENDED PATH FORWARD ====================
    story.append(stitle("8. RECOMMENDED PATH FORWARD"))
    story.append(Spacer(1, 10))

    story.append(Paragraph(
        "Based on all available evidence, here is a staged approach that maximizes "
        "pain relief while minimizing risk:",
        body
    ))
    story.append(Spacer(1, 8))

    story.append(Paragraph("PHASE 1: IMMEDIATE (Weeks 1-4)", h3))
    story.extend(blist([
        "Find a movement disorder neurologist (USF Tampa, UMiami, or Mayo Jax) — bring your treatment history and this document",
        "Discuss restarting clonazepam at the LOWEST effective dose (0.25-0.5 mg/day)",
        "Switch THC to: CBD topicals during the day (shoulder/trap/arm) + THC only evenings",
        "Start magnesium glycinate 200-400 mg at bedtime (supports GABA, reduces cramping)",
        "Get a TENS unit ($30-50 OTC) for localized pain relief during work hours",
    ]))
    story.append(Spacer(1, 8))

    story.append(Paragraph("PHASE 2: EXPAND OPTIONS (Weeks 4-12)", h3))
    story.extend(blist([
        "Ask neurologist about adding gabapentin or pregabalin for the pain component specifically",
        "Discuss trihexyphenidyl — the 2024 RCT showed significant benefit when combined with clonazepam",
        "Start acupuncture trial (8-12 sessions, every 1-2 weeks) — every participant in published studies reported improvement",
        "Ask about Low-Dose Naltrexone as a low-risk adjunct (takes 1-3 months to see effect)",
        "Begin myofascial release / trigger point therapy for the shoulder and trap (1-2x/week)",
    ]))
    story.append(Spacer(1, 8))

    story.append(Paragraph("PHASE 3: OPTIMIZE (Months 3-6)", h3))
    story.extend(blist([
        "Assess what's working — adjust clonazepam dose based on response",
        "If gabapentin/pregabalin provides significant pain relief, may be able to reduce clonazepam dose",
        "Explore TMS clinical trials (Duke has active trials for focal hand dystonia)",
        "If pain has a neuropathic component that isn't responding, discuss ketamine infusion trial",
        "Evaluate: are you functional at work? Is pain at a level you can live with? Adjust accordingly",
    ]))
    story.append(Spacer(1, 8))

    story.append(Paragraph("LONG-TERM HARM REDUCTION (If on Clonazepam)", h3))
    story.extend(blist([
        "Use the lowest dose that provides meaningful relief — not necessarily complete relief",
        "Distribute doses evenly throughout the day (e.g., 3-4 small doses vs. 1-2 large ones)",
        "Regular follow-ups with prescribing neurologist (every 3-6 months)",
        "Never stop abruptly — if ever discontinuing, taper at 5-10% every 2-4 weeks per 2025 guidelines",
        "Avoid combining with opioids, alcohol, or other CNS depressants",
        "Document your functional improvement (work ability, pain levels) — this supports continued prescribing",
    ]))

    story.append(Spacer(1, 15))
    story.append(Paragraph(
        "THE HONEST ANSWER: Clonazepam is not a perfect drug. But you're not in a perfect "
        "situation. You have a progressive, painful, treatment-resistant condition that has "
        "already cost you a masters degree. The evidence says: use the medication that works "
        "at the lowest effective dose, add complementary treatments to reduce reliance on it, "
        "and manage the risks proactively with a knowledgeable neurologist. Suffering in "
        "untreated pain is not a safer alternative.",
        green_callout
    ))

    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", thickness=1, color=BrandConfig.MID_GRAY))
    story.append(Paragraph(
        "Research compiled March 21, 2026. Sources include PubMed, Dystonia Coalition "
        "Treatment Guidelines, American Journal of Psychiatry (2024), Frontiers in Neurology "
        "(2023), 2025 Joint Clinical Practice Guidelines on Benzodiazepine Tapering (ASAM/ACMT), "
        "and the Dystonia Medical Research Foundation.",
        footer
    ))

    doc.build(story, onFirstPage=_on_page, onLaterPages=_on_page)
    print(f"PDF generated: {output}")
    return output


if __name__ == "__main__":
    path = build_pdf()
    os.system(f'open "{path}"')
