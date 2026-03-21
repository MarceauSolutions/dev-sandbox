#!/usr/bin/env python3
"""
Generate Natural Remedies for Dystonia Pain & Spasticity — branded PDF.
Ranked from most to least effective based on evidence, efficacy, side effects, and outcomes.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT
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

def stitle(text):
    return section_title(text, S)

def blist(items):
    return bullet_list(items, S)

def btable(headers, rows, col_widths=None):
    return branded_table(headers, rows, col_widths=col_widths)

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
amber_callout = ParagraphStyle(
    "AmberCallout", fontName=BrandConfig.BODY_FONT_BOLD,
    fontSize=10, leading=15, textColor=HexColor("#92400e"),
    leftIndent=12, rightIndent=12, spaceBefore=6, spaceAfter=6,
    backColor=HexColor("#fef3c7"), borderPadding=8,
)
rank_style = ParagraphStyle(
    "Rank", fontName=BrandConfig.HEADING_FONT,
    fontSize=14, leading=18, textColor=BrandConfig.GOLD,
    spaceBefore=12, spaceAfter=4,
)
footer = ParagraphStyle(
    "Footer", fontName=BrandConfig.BODY_FONT,
    fontSize=8, leading=11, textColor=BrandConfig.TEXT_MUTED,
    alignment=TA_CENTER, spaceBefore=20,
)


def remedy_block(rank, name, category, efficacy_score, side_effect_score, overall_score,
                 mechanism, evidence, how_to_use, side_effects, cost, notes):
    """Build a KeepTogether block for a single remedy."""
    elements = []
    elements.append(Paragraph(f"#{rank} — {name}", rank_style))
    elements.append(Paragraph(f"<i>Category: {category}</i>", note))

    score_data = [
        ["Efficacy", "Safety", "Overall Score"],
        [f"{efficacy_score}/10", f"{side_effect_score}/10", f"{overall_score}/10"],
    ]
    elements.append(btable(score_data[0], score_data[1:], col_widths=[2.27*inch, 2.27*inch, 2.27*inch]))
    elements.append(Spacer(1, 6))

    elements.append(Paragraph(f"<b>How It Works:</b> {mechanism}", body))
    elements.append(Spacer(1, 4))
    elements.append(Paragraph(f"<b>Evidence:</b> {evidence}", body))
    elements.append(Spacer(1, 4))
    elements.append(Paragraph(f"<b>How to Use:</b> {how_to_use}", body))
    elements.append(Spacer(1, 4))
    elements.append(Paragraph(f"<b>Side Effects:</b> {side_effects}", body))
    elements.append(Spacer(1, 4))
    elements.append(Paragraph(f"<b>Approximate Cost:</b> {cost}", body))
    if notes:
        elements.append(Spacer(1, 4))
        elements.append(Paragraph(f"<b>Notes:</b> {notes}", note))
    elements.append(Spacer(1, 8))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=BrandConfig.MID_GRAY))
    elements.append(Spacer(1, 6))
    return elements


def build_pdf():
    output = os.path.join(os.path.dirname(__file__), "..",
                          "docs", "dystonia-natural-remedies-guide.pdf")
    doc = SimpleDocTemplate(
        output, pagesize=letter,
        leftMargin=0.75*inch, rightMargin=0.75*inch,
        topMargin=0.8*inch, bottomMargin=0.7*inch,
    )
    story = []

    # ==================== COVER ====================
    story.append(Spacer(1, 1.2*inch))
    story.append(accent_line())
    story.append(Spacer(1, 15))
    story.append(Paragraph("NATURAL REMEDIES FOR", cover_title))
    story.append(Paragraph("DYSTONIA PAIN &amp; SPASTICITY", cover_title))
    story.append(Spacer(1, 8))
    story.append(Paragraph("Evidence-Based Guide — Ranked by Effectiveness", cover_sub))
    story.append(Paragraph("Prepared March 21, 2026", cover_detail))
    story.append(Spacer(1, 10))
    story.append(accent_line())
    story.append(Spacer(1, 25))

    story.append(Paragraph(
        "This guide covers every natural and non-pharmaceutical remedy with published evidence "
        "for dystonia, muscle spasticity, and pain from involuntary contractions. Each remedy "
        "is ranked from most to least effective based on: (1) clinical evidence strength, "
        "(2) reported efficacy for dystonia/spasticity pain specifically, (3) safety profile "
        "and side effects, and (4) overall positive outcomes reported in the literature.",
        body
    ))
    story.append(Spacer(1, 10))
    story.append(Paragraph(
        "SCORING: Each remedy is rated on three scales of 1-10. Efficacy = how well it works "
        "for dystonia pain and spasticity. Safety = how few and mild the side effects are "
        "(10 = virtually no side effects). Overall = combined score weighting efficacy, safety, "
        "evidence quality, accessibility, and practical usability.",
        note
    ))
    story.append(Spacer(1, 10))
    story.append(Paragraph(
        "IMPORTANT: These are COMPLEMENTARY approaches. For severe dystonia pain like yours, "
        "natural remedies work best as adjuncts to medical treatment — not replacements. The "
        "goal is to layer these with your primary treatment to reduce pain and improve function.",
        amber_callout
    ))

    story.append(PageBreak())

    # ==================== QUICK REFERENCE ====================
    story.append(stitle("QUICK REFERENCE — ALL REMEDIES RANKED"))
    story.append(Spacer(1, 8))

    rank_data = [
        ["Rank", "Remedy", "Category", "Efficacy", "Safety", "Overall"],
        ["1", "CBD Topicals (localized)", "Cannabinoid", "7", "9", "8.5"],
        ["2", "Acupuncture", "Manual Therapy", "7", "9", "8.0"],
        ["3", "Magnesium Glycinate", "Supplement", "6", "9", "8.0"],
        ["4", "TENS Unit", "Electrotherapy", "6", "10", "7.5"],
        ["5", "Heat/Hydrotherapy", "Physical Modality", "6", "10", "7.5"],
        ["6", "Myofascial Release", "Manual Therapy", "6", "9", "7.5"],
        ["7", "Mindfulness/MBSR", "Mind-Body", "6", "10", "7.0"],
        ["8", "Dry Needling", "Manual Therapy", "6", "8", "7.0"],
        ["9", "CBD Oil (sublingual)", "Cannabinoid", "6", "8", "7.0"],
        ["10", "Yoga/Tai Chi", "Mind-Body/Movement", "5", "9", "7.0"],
        ["11", "Vitamin D", "Supplement", "5", "9", "6.5"],
        ["12", "CoQ10", "Supplement", "5", "9", "6.5"],
        ["13", "Turmeric/Curcumin", "Supplement", "5", "9", "6.5"],
        ["14", "Epsom Salt Baths", "Physical Modality", "4", "10", "6.0"],
        ["15", "Omega-3 Fatty Acids", "Supplement", "4", "9", "6.0"],
        ["16", "Alexander Technique", "Movement Reeducation", "5", "10", "6.0"],
        ["17", "Feldenkrais Method", "Movement Reeducation", "5", "10", "6.0"],
        ["18", "Biofeedback", "Neurofeedback", "5", "10", "6.0"],
        ["19", "Valerian Root", "Herbal", "4", "8", "5.5"],
        ["20", "Passionflower", "Herbal", "4", "8", "5.5"],
        ["21", "Vitamin B12", "Supplement", "4", "9", "5.5"],
        ["22", "Sensory Tricks", "Neurological", "4", "10", "5.0"],
    ]
    story.append(btable(rank_data[0], rank_data[1:],
                        col_widths=[0.4*inch, 1.8*inch, 1.4*inch, 0.7*inch, 0.7*inch, 0.7*inch]))

    story.append(PageBreak())

    # ==================== TIER 1: STRONGEST EVIDENCE ====================
    story.append(stitle("TIER 1: STRONGEST EVIDENCE (Overall 7.5-8.5)"))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        "These have the best combination of evidence, efficacy, and safety for dystonia "
        "pain and spasticity. Start here.",
        green_callout
    ))
    story.append(Spacer(1, 6))

    # #1 CBD Topicals
    story.extend(remedy_block(
        rank=1, name="CBD Topicals (Localized Application)",
        category="Cannabinoid — Non-Impairing",
        efficacy_score=7, side_effect_score=9, overall_score="8.5",
        mechanism="CBD interacts with cannabinoid receptors in the skin and underlying muscle tissue, "
                  "reducing local inflammation and pain perception WITHOUT entering the bloodstream. "
                  "Does not produce any psychoactive effects or cognitive impairment.",
        evidence="A 2023 Frontiers in Neurology study found 85% of dystonia patients experienced "
                 "significant pain relief with cannabis products. CBD topicals specifically target "
                 "localized pain. The endocannabinoid system is directly involved in motor coordination "
                 "and pain modulation.",
        how_to_use="Apply high-CBD topical cream directly to shoulder, trap, arm, and hand 2-3 times "
                   "daily. Look for products with at least 500mg CBD per container. Available at FL "
                   "dispensaries (MUV, Trulieve, Curaleaf) with a medical card.",
        side_effects="Virtually none when applied topically. Rare: mild skin irritation at application site.",
        cost="$30-80/month depending on product and frequency of use",
        notes="BEST OPTION for work hours — zero impairment, can apply at your desk. "
              "Combine with evening THC for round-the-clock coverage."
    ))

    # #2 Acupuncture
    story.extend(remedy_block(
        rank=2, name="Acupuncture",
        category="Manual Therapy — Traditional Chinese Medicine",
        efficacy_score=7, side_effect_score=9, overall_score="8.0",
        mechanism="Stimulates specific points to modulate pain pathways, release endorphins, and "
                  "reduce muscle tension. May help rebalance neuromuscular signaling that drives "
                  "dystonic contractions. Activates descending inhibitory pain systems.",
        evidence="2025 review (Wiener Medizinische Wochenschrift) supports acupuncture for dystonia "
                 "including post-stroke, CP-related, and cervical forms. In a study of 13,000+ chronic "
                 "pain patients, 56% of acupuncture recipients had at least 20% pain reduction vs. 21% "
                 "control. Every participant in a small dystonia-specific study reported improvement.",
        how_to_use="Find a licensed acupuncturist experienced with neurological conditions. Start with "
                   "8-12 weekly sessions to assess response. If helpful, transition to biweekly maintenance. "
                   "Effects may be cumulative over multiple sessions.",
        side_effects="Minimal — occasional minor bruising at needle sites, mild soreness. Very rare: "
                     "infection (when done by licensed practitioner, essentially zero risk).",
        cost="$75-150 per session. Some insurance plans cover acupuncture — the Collier County plan "
             "covers acupuncture at 80% after deductible (20 visits/year).",
        notes="THE COLLIER COUNTY PLAN COVERS THIS. 20 visits per year at 80% after deductible. "
              "This is a significant benefit — use it."
    ))

    # #3 Magnesium Glycinate
    story.extend(remedy_block(
        rank=3, name="Magnesium Glycinate",
        category="Mineral Supplement",
        efficacy_score=6, side_effect_score=9, overall_score="8.0",
        mechanism="Magnesium is essential for muscle relaxation and directly supports GABA receptor "
                  "function — the same pathway clonazepam works on. Deficiency causes muscle cramping, "
                  "spasms, and increased pain sensitivity. Glycinate form has the best absorption and "
                  "is least likely to cause GI issues.",
        evidence="Well-established role in muscle physiology and GABA signaling. Studies show correcting "
                 "magnesium deficiency reduces muscle spasms. Many dystonia patients are magnesium "
                 "deficient without knowing it. While not studied specifically for dystonia in RCTs, "
                 "the mechanistic evidence is strong.",
        how_to_use="200-400 mg magnesium glycinate at bedtime. Can split to 200mg morning + 200mg "
                   "bedtime. Start at 200mg and increase after 1 week. Take with food.",
        side_effects="Very mild at recommended doses. Possible: loose stools (less likely with glycinate "
                     "vs. other forms), mild drowsiness (which is actually beneficial at bedtime).",
        cost="$10-20/month (widely available OTC at any pharmacy or Amazon)",
        notes="This should be the FIRST supplement you start. Low cost, low risk, supports the same "
              "GABA pathway as clonazepam. May also improve sleep quality."
    ))

    story.append(PageBreak())

    # #4 TENS Unit
    story.extend(remedy_block(
        rank=4, name="TENS Unit (Transcutaneous Electrical Nerve Stimulation)",
        category="Electrotherapy Device",
        efficacy_score=6, side_effect_score=10, overall_score="7.5",
        mechanism="Delivers small electrical impulses through electrodes placed on the skin over "
                  "the affected area. Activates descending inhibitory pain systems in the central "
                  "nervous system, reducing hyperalgesia. May also promote local muscle relaxation.",
        evidence="Strong evidence for chronic pain management broadly (multiple systematic reviews). "
                 "Less studied specifically for dystonia but mechanism is well-understood. Adequate "
                 "intensity dosing is critical — low-intensity TENS is less effective.",
        how_to_use="Place electrode pads on the shoulder, trap, and upper arm area. Use for 20-30 "
                   "minutes, 2-3 times daily. Adjust intensity to a strong but comfortable level. "
                   "Can use during work (pads hidden under clothing).",
        side_effects="Essentially none. Rare: mild skin irritation from adhesive pads. "
                     "CAUTION: Do NOT place pads near your DBS implant/battery — consult neurologist "
                     "about safe electrode placement distances from DBS hardware.",
        cost="$30-50 one-time purchase (OTC at pharmacies, Amazon). Replacement pads ~$10/month.",
        notes="IMPORTANT: With your DBS implant, you MUST check with your neurologist about safe "
              "placement zones before using TENS. The electrical impulses could theoretically "
              "interfere with the DBS system if placed too close to the leads or battery."
    ))

    # #5 Heat/Hydrotherapy
    story.extend(remedy_block(
        rank=5, name="Heat Therapy &amp; Hydrotherapy",
        category="Physical Modality",
        efficacy_score=6, side_effect_score=10, overall_score="7.5",
        mechanism="Heat reduces muscle tone and spasm by increasing blood flow, reducing pain "
                  "receptor sensitivity, and elevating the pain threshold. Water immersion supports "
                  "reduction of muscle tone through buoyancy and hydrostatic pressure. Warm water "
                  "combines both thermal and mechanical benefits.",
        evidence="Established in rehabilitation medicine — heat and hydrotherapy both shown to reduce "
                 "muscle spasm and spasticity in upper motor neuron lesions. Pain threshold is elevated "
                 "by direct thermal effect on nerve endings.",
        how_to_use="Moist heat pad on shoulder/trap/arm for 20 minutes, 2-3x daily. Warm baths or "
                   "pool sessions (92-96F) for 20-30 minutes. Heated pool therapy is ideal — combines "
                   "heat, buoyancy, and gentle movement.",
        side_effects="None at appropriate temperatures. Avoid burns — do not exceed 104F for baths. "
                     "Stay hydrated during heat therapy.",
        cost="$15-30 for a heating pad. Pool/spa access varies. Epsom salt for baths: $5-10/bag.",
        notes="The most accessible remedy on this list. Can use multiple times daily with zero "
              "downside. Combine with gentle stretching during heat application for best results."
    ))

    # #6 Myofascial Release
    story.extend(remedy_block(
        rank=6, name="Myofascial Release / Trigger Point Therapy",
        category="Manual Therapy",
        efficacy_score=6, side_effect_score=9, overall_score="7.5",
        mechanism="Directly addresses secondary pain caused by sustained dystonic contractions. "
                  "Releases fascial adhesions, deactivates trigger points, and improves tissue mobility "
                  "in chronically contracted muscles. The shoulder, trap, and arm muscles develop "
                  "trigger points from sustained involuntary contraction.",
        evidence="Strong evidence for myofascial pain syndrome broadly. Less studied for dystonia "
                 "specifically, but the mechanism directly addresses your complaint — pain from "
                 "sustained muscle pulling. Clinical experience supports its use in movement disorders.",
        how_to_use="Find a licensed massage therapist or physical therapist with experience in "
                   "neuromuscular conditions. 1-2 sessions per week initially. Can also self-treat "
                   "with a foam roller or lacrosse ball on the trap and shoulder area.",
        side_effects="Temporary soreness for 24-48 hours after treatment (normal). Rare: bruising.",
        cost="$60-120 per professional session. Self-treatment tools: $15-30 one-time. "
             "Collier County plan covers outpatient therapies at 80% after deductible.",
        notes="Your muscles are in chronic contraction — they WILL develop trigger points and "
              "fascial adhesions. This directly treats the secondary pain. Highly recommended."
    ))

    story.append(PageBreak())

    # ==================== TIER 2 ====================
    story.append(stitle("TIER 2: GOOD EVIDENCE (Overall 7.0)"))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        "Solid evidence supports these approaches. Good additions to a Tier 1 foundation.",
        blue_callout
    ))
    story.append(Spacer(1, 6))

    # #7 Mindfulness/MBSR
    story.extend(remedy_block(
        rank=7, name="Mindfulness-Based Stress Reduction (MBSR)",
        category="Mind-Body Practice",
        efficacy_score=6, side_effect_score=10, overall_score="7.0",
        mechanism="Changes how the brain processes pain signals. Expert meditators show decreased "
                  "pain sensitivity with structural changes in the dorsal anterior cingulate cortex. "
                  "A 6-week MBSR course reduced subjective pain by increasing connectivity between "
                  "the anterior insular cortex and mid-cingulate cortex. Also reduces stress and "
                  "anxiety, which amplify dystonia symptoms.",
        evidence="Strong evidence for chronic pain management (systematic reviews, RCTs). A specific "
                 "combined CBT-mindfulness program was developed and tested for dystonia patients "
                 "(BMJ Open, 2016). Neurological evidence shows measurable brain changes in pain "
                 "processing regions.",
        how_to_use="8-week structured MBSR program (available online or in-person). 20-30 minutes "
                   "daily practice. Apps: Headspace, Calm, or Insight Timer for guided sessions. "
                   "Focus on body scan techniques — particularly useful for chronic pain.",
        side_effects="None.",
        cost="Free (apps have free tiers) to $70/month (premium apps). In-person programs: $300-500.",
        notes="This won't reduce the tone itself but can significantly change your relationship "
              "with pain. Particularly valuable on high-pain days when other treatments aren't enough."
    ))

    # #8 Dry Needling
    story.extend(remedy_block(
        rank=8, name="Dry Needling",
        category="Manual Therapy",
        efficacy_score=6, side_effect_score=8, overall_score="7.0",
        mechanism="Thin needles inserted directly into myofascial trigger points to release them. "
                  "Causes a local twitch response that resets the muscle fiber. Reduces spasticity "
                  "level, pain intensity, and improves range of motion.",
        evidence="Systematic review of 16 studies (7 RCTs) found dry needling improved spasticity, "
                 "pain intensity, and ROM in neurological patients. EMG-guided dry needling showed "
                 "particular promise for myofascial neck and shoulder pain.",
        how_to_use="Performed by a licensed physical therapist or trained practitioner. Target the "
                   "trap, shoulder, and arm trigger points. Sessions every 1-2 weeks initially.",
        side_effects="Moderate — temporary soreness (24-72 hours), occasional bruising, very rare "
                     "pneumothorax risk (essentially zero with trained practitioner on shoulder/arm).",
        cost="$75-150 per session. Often available through PT clinics. May be covered under "
             "outpatient therapy benefits.",
        notes="Similar to acupuncture but specifically targets motor trigger points rather than "
              "traditional meridian points. Some people respond better to one vs. the other."
    ))

    # #9 CBD Oil (Sublingual)
    story.extend(remedy_block(
        rank=9, name="CBD Oil (Sublingual / Oral)",
        category="Cannabinoid — Non-Impairing",
        efficacy_score=6, side_effect_score=8, overall_score="7.0",
        mechanism="Systemic CBD provides anti-inflammatory, anxiolytic, and muscle-relaxant effects "
                  "throughout the body. Modulates the endocannabinoid system which regulates motor "
                  "coordination and pain. Unlike THC, does not produce significant cognitive impairment.",
        evidence="The 2023 real-life dystonia study found sublingual oil showed 20% improvement "
                 "(vs. 80% for smoked cannabis, but with far less impairment). CBD has established "
                 "anti-inflammatory and anxiolytic properties. Less potent for pain than THC but "
                 "allows full function.",
        how_to_use="Start with 25mg CBD sublingual oil, 2x daily. Hold under tongue 60-90 seconds. "
                   "Increase by 25mg every week until you notice benefit. Some people need 50-100mg "
                   "2x daily. Available at FL dispensaries or OTC hemp-derived CBD.",
        side_effects="Mild — possible fatigue, dry mouth, diarrhea at high doses. Can interact with "
                     "some medications (check with pharmacist). Generally well-tolerated.",
        cost="$40-100/month depending on dose and product quality",
        notes="The key advantage over THC: you can function at work. Less potent for acute pain "
              "but the systemic anti-inflammatory effect builds over days/weeks of consistent use."
    ))

    # #10 Yoga/Tai Chi
    story.extend(remedy_block(
        rank=10, name="Yoga / Tai Chi",
        category="Mind-Body Movement Practice",
        efficacy_score=5, side_effect_score=9, overall_score="7.0",
        mechanism="Combines gentle movement, stretching, breathing, and mindfulness. Activates the "
                  "parasympathetic nervous system (reducing stress-driven muscle tension). Improves "
                  "flexibility, body awareness, and proprioception. Tai chi specifically shown to "
                  "reduce fibromyalgia severity more than aerobic exercise.",
        evidence="A 2018 RCT (226 adults with fibromyalgia) found tai chi reduced symptom severity "
                 "at 24 weeks more than supervised aerobic exercise. Growing evidence for movement "
                 "disorders — relaxation techniques help manage stress that worsens dystonia.",
        how_to_use="Gentle/restorative yoga or tai chi, 20-30 minutes, 3-5x weekly. Avoid poses that "
                   "strain the affected arm/shoulder. Focus on classes for chronic pain or modified "
                   "for physical limitations. Many free YouTube options.",
        side_effects="None if done gently. Avoid overextending the affected side. Listen to your body.",
        cost="Free (YouTube) to $15-20/class. Monthly studio memberships: $80-150.",
        notes="The gentle, flowing movements of tai chi may be easier than yoga given your left-side "
              "limitations. Both help with the stress-pain cycle."
    ))

    story.append(PageBreak())

    # ==================== TIER 3 ====================
    story.append(stitle("TIER 3: MODERATE EVIDENCE (Overall 5.5-6.5)"))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        "Supported by limited evidence or mechanistic reasoning. Worth trying as additional "
        "layers, especially given their low risk profiles.",
        body
    ))
    story.append(Spacer(1, 6))

    tier3 = [
        ["Rank", "Remedy", "Key Benefit", "Dose / Usage", "Side Effects", "Cost/Mo"],
        [
            "11", "Vitamin D",
            "Correcting deficiency reduces muscle spasm and improves strength. Case series showed improvement in chronic neck/back pain with spasm",
            "2000-5000 IU daily (get blood level tested first — aim for 40-60 ng/mL)",
            "Very safe at recommended doses. Toxicity only at extreme doses (>10,000 IU/day long-term)",
            "$5-10"
        ],
        [
            "12", "CoQ10\n(Coenzyme Q10)",
            "Deficiency directly causes dystonia and spasticity. Supplementation may improve muscle function. Supports mitochondrial energy production",
            "100-300 mg daily with a meal containing fat (for absorption)",
            "Very mild — rare GI upset, insomnia at high doses",
            "$15-30"
        ],
        [
            "13", "Turmeric/\nCurcumin",
            "Potent anti-inflammatory. Reduces joint and muscle inflammation. Studied extensively for chronic pain conditions",
            "500-1000 mg curcumin daily (must include piperine/black pepper extract for absorption)",
            "Mild — GI upset at high doses. Avoid with blood thinners",
            "$15-25"
        ],
        [
            "14", "Epsom Salt\nBaths",
            "Magnesium sulfate absorbed through skin. Combines magnesium delivery with heat therapy benefits. Relaxes muscles",
            "2 cups Epsom salt in warm bath (95-100F), soak 20-30 min, 3-4x/week",
            "None (external use). Stay hydrated. Avoid if open wounds",
            "$5-10"
        ],
        [
            "15", "Omega-3\nFatty Acids",
            "Anti-inflammatory. Reduces systemic inflammation that may contribute to pain sensitization",
            "2000-3000 mg EPA+DHA daily (fish oil or algae-based)",
            "Mild fishy aftertaste, GI upset. Slight blood-thinning effect",
            "$15-30"
        ],
        [
            "16", "Alexander\nTechnique",
            "Retrains movement patterns. Helps release unnecessary muscle tension. Improves postural awareness. Sustained benefits at 6-month follow-up",
            "Individual lessons with certified teacher, weekly for 20-30 sessions",
            "None",
            "$50-100/lesson"
        ],
        [
            "17", "Feldenkrais\nMethod",
            "Movement re-education. Improves awareness of habitual tension patterns. Helps find easier ways to move with the dystonia",
            "Group classes (Awareness Through Movement) or individual sessions (Functional Integration)",
            "None",
            "$50-100/lesson"
        ],
        [
            "18", "Biofeedback",
            "Uses sensors to show real-time muscle activity. Trains voluntary control over involuntary contractions. Helps eliminate muscle co-contraction patterns",
            "Clinical sessions with trained therapist, 8-12 sessions initially. EMG biofeedback most relevant for dystonia",
            "None",
            "$75-150/session"
        ],
        [
            "19", "Valerian\nRoot",
            "Mild GABAergic effect (same pathway as clonazepam, much weaker). Reduces muscle tension and improves sleep",
            "300-600 mg standardized extract, 30-60 min before bed",
            "Mild — drowsiness, headache, GI upset. Variable product quality. Do not combine with other sedatives",
            "$10-15"
        ],
        [
            "20", "Passionflower",
            "Mild anxiolytic and muscle relaxant. Increases GABA levels. May reduce stress-driven dystonia flares",
            "500 mg extract daily, or tea 2-3x daily",
            "Mild — drowsiness, dizziness. Do not combine with sedatives",
            "$10-15"
        ],
        [
            "21", "Vitamin B12",
            "Supports nerve function and myelin sheath. Deficiency causes muscle cramps, tingling, and disrupted nerve signaling",
            "1000 mcg sublingual methylcobalamin daily (get level tested first)",
            "Very safe — virtually no side effects at any dose",
            "$5-10"
        ],
        [
            "22", "Sensory\nTricks",
            "Touch or pressure to specific body areas can temporarily reduce dystonic contractions (geste antagoniste). Unique to dystonia — exploits sensory-motor feedback loop",
            "Experiment with light touch, pressure, or tactile cues on/near affected muscles. Some patients find specific postures or touches that reduce contractions",
            "None",
            "Free"
        ],
    ]
    story.append(btable(tier3[0], tier3[1:],
                        col_widths=[0.4*inch, 0.9*inch, 1.8*inch, 1.5*inch, 1.2*inch, 0.6*inch]))

    story.append(PageBreak())

    # ==================== RECOMMENDED STACK ====================
    story.append(stitle("RECOMMENDED DAILY STACK"))
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        "Based on the rankings above, here is a practical daily protocol that layers "
        "the most effective, safest natural remedies together. All of these can be used "
        "alongside medical treatment (clonazepam, etc.).",
        body
    ))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Morning Routine", h3))
    story.extend(blist([
        "Magnesium glycinate 200 mg with breakfast",
        "CBD topical applied to shoulder, trap, and arm",
        "Vitamin D 2000-5000 IU with breakfast (fat-containing meal)",
        "Omega-3 fish oil 1000 mg EPA+DHA",
        "Turmeric/curcumin 500 mg with piperine",
        "Gentle stretching or tai chi (15-20 min)",
    ]))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Midday (At Work)", h3))
    story.extend(blist([
        "Reapply CBD topical to affected areas",
        "TENS unit if pain flares (20-30 min, pads on trap/shoulder — CLEAR placement with neurologist re: DBS first)",
        "5-minute mindfulness breathing exercise during break",
    ]))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Evening Routine", h3))
    story.extend(blist([
        "Heat pad on shoulder/trap area (20 min)",
        "OR Epsom salt bath (2 cups, 20-30 min warm soak)",
        "CBD topical reapplication",
        "Magnesium glycinate 200 mg",
        "Valerian root 300-600 mg (if helpful for sleep)",
        "THC as needed for pain management (evening only if using)",
    ]))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Weekly Appointments", h3))
    story.extend(blist([
        "Acupuncture 1x/week (covered by Collier County plan — 20 visits/year at 80%)",
        "Myofascial release / trigger point therapy 1x/week",
        "Optional: dry needling alternating with acupuncture",
    ]))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Monthly Supplement Budget (Estimated)", h3))
    budget = [
        ["Item", "Cost"],
        ["Magnesium glycinate", "$10-15"],
        ["CBD topical (high-CBD cream)", "$40-60"],
        ["Vitamin D", "$5-10"],
        ["Omega-3 fish oil", "$15-20"],
        ["Turmeric/curcumin", "$15-20"],
        ["CoQ10", "$15-25"],
        ["Valerian root (optional)", "$10-15"],
        ["TOTAL SUPPLEMENTS", "$110-165/month"],
    ]
    story.append(btable(budget[0], budget[1:], col_widths=[3.4*inch, 3.4*inch]))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "Add acupuncture (covered by insurance) and a one-time TENS unit purchase ($30-50), "
        "and the total monthly investment is approximately $150-200 out of pocket for the "
        "supplement stack, with manual therapy sessions largely covered by your Collier County "
        "insurance plan.",
        note
    ))

    story.append(Spacer(1, 15))
    story.append(Paragraph(
        "REMEMBER: These are layers that stack on top of each other. No single natural remedy "
        "will match clonazepam for your dystonia — but a disciplined stack of the top 6-8 "
        "remedies, used consistently, can meaningfully reduce pain and improve daily function. "
        "The goal isn't to replace medical treatment — it's to build a foundation that reduces "
        "how much you need it.",
        green_callout
    ))

    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", thickness=1, color=BrandConfig.MID_GRAY))
    story.append(Paragraph(
        "Research compiled March 21, 2026. Sources include PubMed, Dystonia Medical Research "
        "Foundation, Frontiers in Neurology (2023), BMJ Open (2016), NIH National Center for "
        "Complementary and Integrative Health, Wiener Medizinische Wochenschrift (2025), "
        "and multiple systematic reviews and meta-analyses.",
        footer
    ))

    doc.build(story, onFirstPage=_on_page, onLaterPages=_on_page)
    print(f"PDF generated: {output}")
    return output


if __name__ == "__main__":
    path = build_pdf()
    os.system(f'open "{path}"')
