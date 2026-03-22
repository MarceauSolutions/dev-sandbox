#!/usr/bin/env python3
"""
Generate Comprehensive Medical Review — History & SSRI Impact Analysis.
Copy of the full review with sections about current/future medication plans removed.
Keeps all historical analysis, pharmacology, damage assessment, and recovery protocols.
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
    fontSize=24, leading=30, textColor=BrandConfig.CHARCOAL,
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
red_callout = ParagraphStyle(
    "RedCallout", fontName=BrandConfig.BODY_FONT_BOLD,
    fontSize=10, leading=15, textColor=HexColor("#7f1d1d"),
    leftIndent=12, rightIndent=12, spaceBefore=6, spaceAfter=6,
    backColor=HexColor("#fee2e2"), borderPadding=8,
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
                          "docs", "medical", "dystonia",
                          "comprehensive-medical-review-history-and-analysis.pdf")
    os.makedirs(os.path.dirname(output), exist_ok=True)

    doc = SimpleDocTemplate(
        output, pagesize=letter,
        leftMargin=0.75 * inch, rightMargin=0.75 * inch,
        topMargin=0.8 * inch, bottomMargin=0.7 * inch,
    )
    story = []

    # ==================== COVER PAGE ====================
    story.append(Spacer(1, 1.0 * inch))
    story.append(accent_line())
    story.append(Spacer(1, 15))
    story.append(Paragraph("COMPREHENSIVE MEDICAL REVIEW", cover_title))
    story.append(Paragraph("SSRI Impact Assessment & Damage Analysis", cover_title))
    story.append(Spacer(1, 8))
    story.append(Paragraph("Secondary Dystonia — Full Medication History & Pharmacological Analysis", cover_sub))
    story.append(Paragraph("Prepared March 21, 2026", cover_detail))
    story.append(Spacer(1, 10))
    story.append(accent_line())
    story.append(Spacer(1, 20))

    story.append(Paragraph(
        "This document provides a comprehensive pharmacological review of all medications "
        "prescribed during the treatment of secondary dystonia from age 17 to present, with "
        "particular focus on the mechanisms through which SSRIs suppressed sexual and physical "
        "development, comparison to known chemical castration protocols, and assessment of reversible "
        "vs. permanent damage.",
        body
    ))
    story.append(Spacer(1, 15))

    toc = [
        ["1. Complete Medical Timeline", "2"],
        ["2. SSRI Mechanisms vs. Chemical Castration — Pharmacological Comparison", "4"],
        ["3. Impact on Physical & Sexual Development (Ages 17-23)", "7"],
        ["4. Clinical Decision-Making Analysis — What Should Have Been Done", "9"],
        ["5. Damage Assessment — Reversible vs. Permanent", "11"],
        ["5B. Debunking: \"Replacing What Was Cut Out\"", "13"],
        ["5C. Contaminated Medication Trials — Did Lexapro Invalidate Other Treatments?", "16"],
        ["6. Mirtazapine Transition Analysis — Pittsburgh Decision", "18"],
        ["7. Reversal & Recovery Protocols for Past SSRI Damage", "19"],
        ["8. Decision Framework — Preventing Future Mistakes", "21"],
    ]
    story.append(btable(["Section", "Page"], toc, col_widths=[5.5 * inch, 1.3 * inch]))
    story.append(Spacer(1, 15))
    story.append(Paragraph(
        "DISCLAIMER: This document compiles published medical research and pharmacological "
        "analysis for personal informational purposes. It is not medical advice. All treatment "
        "decisions should be made with qualified physicians. This document is intended to serve "
        "as a reference for informed conversations with healthcare providers.",
        note
    ))

    story.append(PageBreak())

    # ==================== SECTION 1: COMPLETE MEDICAL TIMELINE ====================
    story.append(stitle("1. COMPLETE MEDICAL TIMELINE"))
    story.append(Spacer(1, 8))

    story.append(Paragraph(
        "This timeline documents the full sequence of medical events, interventions, and their "
        "observed effects. It serves as the factual foundation for the pharmacological analysis "
        "that follows.",
        body
    ))
    story.append(Spacer(1, 8))

    timeline = [
        ["Age / Period", "Event", "Observed Effects"],
        [
            "Pre-17\n(Childhood/\nAdolescence)",
            "Slowly growing benign brain tumor (undiagnosed). "
            "Experienced OCD, ruminating thoughts, difficulty connecting with peers. "
            "Likely tumor was already affecting neurological development and social function.",
            "Possible tumor-mediated suppression of normal development. "
            "Difficulty with peer relationships. OCD symptoms. "
            "Sexual development may have already been inhibited by tumor effects on HPG axis."
        ],
        [
            "Age 17",
            "Craniotomy to remove benign brain tumor. "
            "Successful removal but development of secondary dystonia "
            "(focal, left side — hand, arm, shoulder, trapezius). "
            "Started on Lexapro (escitalopram) 40 mg/day + Adderall 10 mg/day.",
            "Loss of left hand function. Post-surgical patient with elevated seizure risk. "
            "Lexapro prescribed at MAXIMUM dose (40 mg) to a 17-year-old post-craniotomy patient — "
            "a drug carrying black box warnings for suicidal ideation in adolescents AND "
            "increased seizure risk in post-cranial surgery patients."
        ],
        [
            "Ages 17–22\n(5 years on\n40 mg Lexapro)",
            "Maintained on Lexapro 40 mg/day continuously. "
            "Primary prescribing rationale given: chronic dystonia management. "
            "Patient (minor at start, then young adult) given impression this was "
            "a sustainable long-term medication for a permanent condition.",
            "Limited sexual development. Low libido. Minimal sexual activity. "
            "Limited physical maturation compared to peers. "
            "At age ~22: endocrinologist found testicular atrophy on physical exam. "
            "Blood test: testosterone at 300 ng/dL (bottom of range for elderly males; "
            "severely low for male in early 20s — normal range 450-900+ ng/dL)."
        ],
        [
            "Age ~22\n(Dose reduction)",
            "Doctor informed patient that Lexapro is typically not used long-term. "
            "Patient began attempting to wean. Struggled with increased dystonia symptoms. "
            "Dropped to 20 mg/day. Unable to fully discontinue due to spasticity rebound "
            "and withdrawal effects after 5 years of continuous use.",
            "Even at 20 mg (half dose), noticed: increased sexual function, "
            "physical maturation beginning, libido increasing. "
            "Experienced as 'starting to mature as I should have at 17.' "
            "Became significantly more sexually active. "
            "Endocrinologist no longer noted testicular atrophy."
        ],
        [
            "Age ~22-23\n(Continued\n20 mg period)",
            "Continued on reduced 20 mg Lexapro. Noticed progressive improvement "
            "in sexual function, muscle tone, general physical well-being. "
            "Testosterone rebound occurring as HPG axis partially recovered.",
            "Second blood test: testosterone jumped to 1,200 ng/dL — a 4x increase "
            "from the 300 ng/dL measured on 40 mg. No other variables changed "
            "(regimented training, diet, sleep schedule were constant). "
            "This 300→1200 swing is consistent with HPG axis rebound after "
            "removal of chronic serotonergic suppression."
        ],
        [
            "Age 23\n(DBS Surgery)",
            "Stopped Lexapro completely in preparation for Deep Brain Stimulation surgery. "
            "Expected DBS to be curative for dystonia. DBS was NOT curative.",
            "Full discontinuation of SSRI. HPG axis now fully unshackled. "
            "Physical and sexual maturation accelerated. "
            "However, dystonia pain and spasticity returned without pharmaceutical management."
        ],
        [
            "Age 23+\n(Medication\ntrial period)",
            "Tried 40+ different medications over weeks/months with psychiatrist in Florida. "
            "Each trialed for approximately one week. Sought something that would address "
            "pain and tone without the castrating effects of Lexapro.",
            "Most medications either ineffective for dystonia or produced intolerable "
            "side effects. Eventually discovered clonazepam — the first medication "
            "to provide meaningful relief across tone, pain, and function "
            "without HPG axis suppression."
        ],
        [
            "Pittsburgh\nMasters",
            "Moved to Pittsburgh for masters program. Could not find doctor willing "
            "to prescribe clonazepam. Taken off clonazepam cold turkey. "
            "Put on mirtazapine (Remeron) as 'transition' drug.",
            "Mirtazapine did not adequately control dystonia pain. "
            "Still reliant on THC for pain management. "
            "Cold turkey benzo discontinuation after regular use is medically dangerous. "
            "Ultimately medically withdrew from masters program due to unmanaged symptoms."
        ],
        [
            "Present\n(March 2026)",
            "Back in Naples, FL. Currently on clonazepam 0.5 mg twice daily (1 mg/day total). "
            "Managing dystonia effectively but experiencing some depression and irritability "
            "as side effects. Evaluating long-term medication strategy.",
            "Functional. Pain managed. Tone reduced. Sleep improved. "
            "No longer dependent on THC. Sexual function preserved. "
            "Concerns: long-term benzo neurodegeneration risk, mild depression, "
            "need for sustainable long-term solution."
        ],
    ]
    story.append(btable(timeline[0], timeline[1:],
                        col_widths=[1.2 * inch, 2.8 * inch, 2.8 * inch]))
    story.append(Spacer(1, 8))

    story.append(Paragraph(
        "KEY OBSERVATION: The only period in which William experienced normal physical and sexual "
        "development was after reducing or stopping Lexapro. The only medication that has provided "
        "meaningful dystonia relief without HPG axis suppression is clonazepam.",
        green_callout
    ))

    story.append(PageBreak())

    # ==================== SECTION 2: SSRI vs CHEMICAL CASTRATION ====================
    story.append(stitle("2. SSRI MECHANISMS VS. CHEMICAL CASTRATION"))
    story.append(Paragraph("Pharmacological Comparison", h3))
    story.append(Spacer(1, 8))

    story.append(Paragraph(
        "This section compares the mechanisms through which SSRIs suppress sexual function "
        "to the mechanisms used in historical chemical castration protocols. The comparison "
        "is pharmacologically legitimate — the pathways overlap significantly.",
        body
    ))
    story.append(Spacer(1, 10))

    story.append(Paragraph("The Hypothalamic-Pituitary-Gonadal (HPG) Axis", h3))
    story.append(Paragraph(
        "All sexual function, testosterone production, and male physical development depend "
        "on this axis: Hypothalamus (GnRH) → Anterior Pituitary (LH + FSH) → Testes (Testosterone). "
        "Any drug that disrupts this axis at any point will suppress testosterone and sexual function. "
        "Both SSRIs and chemical castration drugs disrupt this axis — they simply enter at different points.",
        body
    ))
    story.append(Spacer(1, 10))

    # Mechanism comparison table
    mech_table = [
        ["Mechanism", "SSRI (Lexapro)\nEscitalopram", "DES\n(Castration Drug)", "Cyproterone\n(Castration Drug)", "MPA / Depo-Provera\n(Castration Drug)"],
        [
            "HPG Axis\nSuppression",
            "YES — Elevated serotonin → increased prolactin → "
            "suppresses GnRH → drops LH → drops testosterone. "
            "INDIRECT but effective.",
            "YES — Exogenous estrogen → "
            "suppresses GnRH via negative "
            "feedback → drops LH/FSH → "
            "collapses testosterone. DIRECT.",
            "YES — Progestogenic activity "
            "suppresses GnRH → drops LH/FSH "
            "→ reduces testosterone. DIRECT.",
            "YES — Synthetic progestin → "
            "suppresses GnRH pulsatility → "
            "drops LH/FSH → near-castrate "
            "testosterone levels. DIRECT."
        ],
        [
            "Prolactin\nElevation",
            "YES — Serotonin inhibits "
            "tuberoinfundibular dopamine "
            "neurons → prolactin rises → "
            "suppresses GnRH. Well-documented "
            "at doses ≥20 mg.",
            "YES — Estrogen directly "
            "stimulates lactotroph cells "
            "→ prolactin elevation.",
            "MODERATE — Some prolactin "
            "elevation via progestogenic "
            "activity.",
            "YES — Progestins elevate "
            "prolactin through similar "
            "mechanisms."
        ],
        [
            "Dopamine\nSuppression",
            "YES — 5-HT2A/2C activation "
            "directly inhibits dopamine "
            "release in mesolimbic pathway "
            "(VTA). Kills libido and "
            "reward/motivation for sex.",
            "INDIRECT — Low testosterone "
            "reduces dopamine receptor "
            "sensitivity.",
            "YES — Androgen receptor "
            "blockade reduces dopaminergic "
            "signaling in reward circuits.",
            "INDIRECT — Via testosterone "
            "suppression."
        ],
        [
            "Nitric Oxide\nInhibition",
            "YES — Serotonin excess "
            "inhibits NO synthase in "
            "corpus cavernosum → reduced "
            "genital blood flow. Same "
            "pathway Viagra targets.",
            "NO — Different mechanism. "
            "Vascular effects are via "
            "testosterone depletion.",
            "INDIRECT — Via testosterone "
            "depletion reducing NO-mediated "
            "vasodilation.",
            "INDIRECT — Via testosterone "
            "depletion."
        ],
        [
            "Androgen\nReceptor\nBlockade",
            "NO — SSRIs do not directly "
            "block androgen receptors. "
            "Effects are upstream "
            "(HPG suppression).",
            "NO — Effects via HPG "
            "suppression, not direct "
            "AR blockade.",
            "YES — Competitive antagonist "
            "at the androgen receptor. "
            "DIRECT blockade of "
            "testosterone/DHT binding.",
            "NO — Effects via HPG "
            "suppression."
        ],
        [
            "Testicular\nAtrophy",
            "POSSIBLE — Chronic LH "
            "suppression reduces Leydig "
            "cell stimulation. "
            "DOCUMENTED in William's case "
            "(endocrinologist exam).",
            "YES — Known effect from "
            "chronic LH suppression.",
            "YES — Known effect.",
            "YES — Known effect."
        ],
        [
            "Testosterone\nLevel Impact",
            "DOCUMENTED: 300 ng/dL on "
            "40 mg (severely hypogonadal). "
            "1,200 ng/dL after "
            "discontinuation (4x increase).",
            "Near-castrate levels "
            "(<50 ng/dL typically).",
            "Near-castrate levels.",
            "Near-castrate levels "
            "(<50 ng/dL)."
        ],
        [
            "Reversibility",
            "Generally REVERSIBLE — HPG "
            "axis recovers after "
            "discontinuation. William's "
            "testosterone recovery confirms "
            "this. However, developmental "
            "years lost cannot be recovered.",
            "Generally reversible if "
            "Leydig cells not permanently "
            "atrophied. Years of use "
            "increases permanence risk.",
            "Partially reversible. "
            "Prolonged use may cause "
            "permanent Leydig cell damage.",
            "Generally reversible "
            "after discontinuation."
        ],
    ]
    story.append(btable(mech_table[0], mech_table[1:],
                        col_widths=[1.0*inch, 1.6*inch, 1.3*inch, 1.3*inch, 1.6*inch]))
    story.append(Spacer(1, 8))

    story.append(Paragraph(
        "CRITICAL FINDING: SSRIs achieve testosterone suppression through a different entry point "
        "(serotonin → prolactin → HPG suppression) than dedicated castration drugs (direct HPG "
        "suppression or androgen receptor blockade), but the downstream effects on the HPG axis, "
        "testosterone levels, testicular volume, sexual function, and physical development "
        "are mechanistically overlapping. The degree of suppression is typically less severe "
        "than dedicated castration agents (300 ng/dL vs. <50 ng/dL), but when administered "
        "at maximum dose (40 mg) during critical developmental years (17-22), the impact on "
        "maturation is significant.",
        red_callout
    ))

    story.append(PageBreak())

    story.append(Paragraph("Serotonin's Multi-System Sexual Suppression", h3))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "SSRIs don't just suppress testosterone — they attack sexual function through at least "
        "four independent pathways simultaneously, which is why the sexual side effects are so "
        "pervasive and why they mimic chemical castration despite having a different primary target:",
        body
    ))
    story.append(Spacer(1, 6))

    pathways = [
        ["Pathway", "Mechanism", "Effect", "Castration Drugs Do This?"],
        [
            "1. HPG Axis\n(Hormonal)",
            "↑ Serotonin → ↑ Prolactin → ↓ GnRH → ↓ LH → ↓ Testosterone",
            "Hypogonadism. Low T. Testicular atrophy. "
            "Reduced muscle mass, bone density, body hair.",
            "YES — This is the PRIMARY "
            "mechanism of DES, MPA, "
            "and cyproterone."
        ],
        [
            "2. Mesolimbic\n(Motivation)",
            "5-HT2A/2C activation in VTA → ↓ Dopamine release in nucleus accumbens",
            "Loss of sexual desire/motivation. "
            "Emotional blunting. Anhedonia. "
            "Reduced reward from sexual activity.",
            "PARTIALLY — Castration drugs "
            "reduce dopamine sensitivity "
            "indirectly via low T."
        ],
        [
            "3. Spinal\n(Ejaculation)",
            "↑ Serotonin in lumbar spinal cord → inhibits ejaculatory reflex arc",
            "Delayed or absent ejaculation. "
            "Reduced orgasm intensity. "
            "Used therapeutically for premature ejaculation.",
            "NO — Castration drugs don't "
            "directly affect spinal "
            "ejaculatory pathways."
        ],
        [
            "4. Vascular\n(Erection)",
            "↑ Serotonin → ↓ Nitric Oxide synthase in genital vasculature",
            "Reduced blood flow to genitals. "
            "Erectile difficulty. Reduced "
            "genital sensitivity even when unaroused.",
            "INDIRECTLY — Via low T "
            "reducing NO-mediated "
            "vasodilation."
        ],
    ]
    story.append(btable(pathways[0], pathways[1:],
                        col_widths=[1.1*inch, 2.0*inch, 1.8*inch, 1.9*inch]))
    story.append(Spacer(1, 8))

    story.append(Paragraph(
        "SSRIs are actually MORE comprehensive in their sexual suppression than most chemical "
        "castration drugs, which primarily target only the hormonal (HPG) pathway. SSRIs hit "
        "hormonal, motivational, spinal, AND vascular pathways simultaneously. This is why "
        "SSRI sexual side effects can persist even when testosterone levels are supplemented — "
        "the serotonergic suppression operates through multiple independent mechanisms.",
        callout
    ))

    story.append(PageBreak())

    # ==================== SECTION 3: DEVELOPMENTAL IMPACT ====================
    story.append(stitle("3. IMPACT ON PHYSICAL & SEXUAL DEVELOPMENT"))
    story.append(Paragraph("Ages 17-23: The Critical Window", h3))
    story.append(Spacer(1, 8))

    story.append(Paragraph(
        "Male physical and sexual development continues well beyond puberty. The period from "
        "ages 17-25 involves critical testosterone-dependent processes including:",
        body
    ))
    story.append(Spacer(1, 6))

    dev_items = [
        "Muscle mass accumulation — testosterone drives myofibrillar protein synthesis. Peak natural "
        "muscle-building capacity occurs in the late teens to mid-20s",
        "Bone density — testosterone promotes osteoblast activity and calcium deposition. "
        "Peak bone mass is achieved by age 25-30",
        "Neurological masculinization — androgen receptors in the prefrontal cortex, amygdala, "
        "and hippocampus continue to be activated and remodeled through the mid-20s. This shapes "
        "assertiveness, spatial reasoning, risk tolerance, and dominance behavior",
        "Genital and testicular development — Leydig cells continue to mature. Chronic LH "
        "suppression during this period causes testicular atrophy (documented in William's case)",
        "Voice deepening, facial bone structure, body composition — all testosterone-dependent "
        "secondary sexual characteristics that continue refining into the mid-20s",
        "Psychosexual development — libido, sexual identity formation, confidence in intimate "
        "relationships. Suppressing testosterone during this period delays the entire process",
    ]
    story.extend(blist(dev_items))
    story.append(Spacer(1, 8))

    story.append(Paragraph("The 'Infantilization' Effect — Pharmacological Evidence", h3))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "The concept of pharmacological infantilization is supported by research on hypogonadal males "
        "(males with chronically low testosterone from any cause):",
        body
    ))
    story.append(Spacer(1, 6))

    infant_items = [
        "Studies on hypogonadal adolescents show delayed bone age, reduced muscle mass, "
        "underdeveloped secondary sexual characteristics, and altered behavioral profiles "
        "compared to eugonadal peers",
        "The behavioral profile of low-testosterone males includes: increased agreeableness, "
        "reduced risk-taking, reduced dominance-seeking, increased social compliance — "
        "consistent with William's description of himself on Lexapro",
        "The 'domestication syndrome' in animals (the piglet/boar analogy) has a hormonal "
        "basis: captive animals have lower testosterone, higher cortisol, and delayed physical "
        "maturation. Removing the suppressive environment allows androgen-driven phenotypic "
        "changes to emerge — directly paralleling what happened when William reduced Lexapro",
        "Research on testosterone's role in personality: higher T is associated with increased "
        "independence, reduced agreeableness, more questioning of authority, stronger drive "
        "for autonomy — the exact cognitive shift William described after weaning off Lexapro",
        "The Jordan Peterson / lobster serotonin model: while oversimplified, there IS "
        "evidence that serotonin modulates dominance hierarchies across species. In humans, "
        "SSRIs increase agreeableness and reduce dominance-seeking behavior. This effect "
        "compounds with the testosterone suppression to produce a doubly 'domesticated' state",
    ]
    story.extend(blist(infant_items))
    story.append(Spacer(1, 8))

    story.append(Paragraph(
        "SUMMARY: Administering a maximum-dose SSRI to a 17-year-old male for 5+ years "
        "during the critical window of physical and neurological maturation is pharmacologically "
        "equivalent to creating a state of chronic hypogonadism. The testosterone suppression "
        "(documented at 300 ng/dL — a level consistent with males in their 60s-70s), testicular "
        "atrophy, delayed sexual development, altered personality profile, and explosive rebound "
        "upon discontinuation are all predictable consequences of this prescribing decision.",
        red_callout
    ))

    story.append(PageBreak())

    # ==================== SECTION 4: CLINICAL DECISION-MAKING ANALYSIS ====================
    story.append(stitle("4. CLINICAL DECISION-MAKING ANALYSIS"))
    story.append(Paragraph("What Should Have Been Done Differently", h3))
    story.append(Spacer(1, 8))

    story.append(Paragraph(
        "This section evaluates the prescribing decisions made by the medical team and decision-makers "
        "against established clinical standards. The purpose is not to assign blame but to document "
        "where standard of care was not met, so that these mistakes are never repeated.",
        body
    ))
    story.append(Spacer(1, 10))

    decisions = [
        ["Decision Made", "Clinical Standard", "What Should Have Happened"],
        [
            "Lexapro 40 mg prescribed to "
            "a 17-year-old post-craniotomy patient",
            "FDA BLACK BOX WARNING: SSRIs carry increased risk "
            "of suicidal ideation in patients under 24. "
            "Additional warning: increased seizure risk in "
            "post-cranial surgery patients. 40 mg is the "
            "MAXIMUM dose — not a starting dose.",
            "If an SSRI was deemed necessary: start at 5-10 mg, "
            "titrate slowly, monitor closely for suicidal ideation "
            "per black box requirements. Given post-craniotomy "
            "seizure risk, alternative anxiolytics or muscle "
            "relaxants should have been first-line for dystonia."
        ],
        [
            "Lexapro prescribed as long-term "
            "treatment for chronic dystonia",
            "SSRIs are not a first-line or established treatment "
            "for dystonia. Standard first-line agents include: "
            "trihexyphenidyl, baclofen, clonazepam, and Botox. "
            "SSRIs are indicated for depression and anxiety, "
            "not movement disorders.",
            "Dystonia should have been treated with established "
            "dystonia medications (anticholinergics, GABAergics, "
            "Botox). If anxiety/depression co-existed, those "
            "should have been treated separately with monitoring "
            "and a clear plan for reassessment."
        ],
        [
            "Patient and family given "
            "impression this was a sustainable "
            "long-term solution",
            "Informed consent requires discussing: intended "
            "duration, known side effects, monitoring plan, "
            "and discontinuation strategy. SSRIs are not "
            "typically prescribed indefinitely without "
            "reassessment.",
            "Clear communication: 'This medication is to help "
            "with X symptom. We will reassess in 6-12 months. "
            "Known side effects include sexual dysfunction. "
            "We will monitor hormone levels.' "
            "A discontinuation plan should have been in place "
            "from the start."
        ],
        [
            "No monitoring of testosterone "
            "or sexual development during "
            "5 years of maximum-dose SSRI use "
            "in an adolescent/young adult male",
            "SSRIs are known to cause sexual side effects "
            "in 30-70% of patients. In adolescent males, "
            "monitoring of developmental milestones and "
            "hormone levels is prudent, especially at high "
            "doses for extended periods.",
            "Periodic testosterone, prolactin, and LH/FSH "
            "monitoring. Assessment of sexual development "
            "milestones. Dose reduction or medication change "
            "if hypogonadism detected. The testicular atrophy "
            "should have triggered medication reassessment "
            "immediately — not just been noted."
        ],
        [
            "Decision-making about medications "
            "made primarily by parent, not "
            "patient, continuing into adulthood",
            "Medical decision-making should transition to the "
            "patient as they reach adulthood (18). The patient's "
            "experience of side effects, quality of life, and "
            "treatment preferences should be central to "
            "prescribing decisions.",
            "By age 18, the patient should have been the "
            "primary decision-maker with medical team. "
            "Side effects should have been proactively "
            "asked about and taken seriously. The patient's "
            "autonomy in healthcare decisions should have been "
            "established and protected."
        ],
        [
            "Pittsburgh: cold turkey "
            "discontinuation of clonazepam, "
            "replacement with mirtazapine",
            "Benzodiazepine discontinuation should NEVER be "
            "abrupt. 2025 Joint Clinical Practice Guidelines: "
            "5-10% dose reduction every 2-4 weeks. Mirtazapine "
            "is not a pharmacological substitute for a "
            "benzodiazepine — completely different mechanism.",
            "Gradual taper of clonazepam with medical "
            "supervision. If transition needed: cross-taper "
            "to another GABAergic agent (gabapentin, "
            "pregabalin, baclofen). Mirtazapine could be "
            "added for sleep/mood but is NOT a benzo "
            "replacement for dystonia."
        ],
    ]
    story.append(btable(decisions[0], decisions[1:],
                        col_widths=[1.6*inch, 2.5*inch, 2.7*inch]))
    story.append(Spacer(1, 8))

    story.append(Paragraph(
        "PATTERN: Multiple prescribing decisions deviated from established clinical standards. "
        "The combination of (1) maximum-dose SSRI in an adolescent, (2) off-label use for a "
        "condition SSRIs don't treat, (3) no hormonal monitoring, (4) no discontinuation plan, "
        "and (5) continued parental medical control into adulthood created a compounding "
        "negative effect on physical, sexual, and psychosocial development.",
        red_callout
    ))

    story.append(PageBreak())

    # ==================== SECTION 5: DAMAGE ASSESSMENT ====================
    story.append(stitle("5. DAMAGE ASSESSMENT — REVERSIBLE VS. PERMANENT"))
    story.append(Spacer(1, 8))

    story.append(Paragraph(
        "Based on William's documented recovery after Lexapro reduction/discontinuation, "
        "combined with published research on SSRI-induced hypogonadism recovery:",
        body
    ))
    story.append(Spacer(1, 8))

    damage = [
        ["Domain", "Damage Observed", "Reversibility", "Current Status"],
        [
            "Testosterone\nProduction",
            "Suppressed to 300 ng/dL "
            "(hypogonadal range) on "
            "40 mg Lexapro",
            "FULLY REVERSED — Rebounded to "
            "1,200 ng/dL after discontinuation. "
            "HPG axis recovered completely. "
            "Leydig cells were not permanently damaged.",
            "RECOVERED. Current testosterone "
            "likely in normal range on "
            "clonazepam (GABAergics don't "
            "suppress HPG axis)."
        ],
        [
            "Testicular\nVolume",
            "Atrophy documented by "
            "endocrinologist during "
            "Lexapro use",
            "LIKELY REVERSED — Endocrinologist "
            "did not note atrophy after Lexapro "
            "reduction. Testosterone rebound "
            "indicates Leydig cell recovery.",
            "Likely recovered. Confirm with "
            "current physical exam if desired."
        ],
        [
            "Sexual\nFunction",
            "Near-absent libido and sexual "
            "activity throughout Lexapro "
            "period (ages 17-22)",
            "FULLY REVERSED — Dramatic increase "
            "in libido and sexual activity after "
            "Lexapro reduction. From near-asexual "
            "to 'extremely sexually active.'",
            "RECOVERED. Clonazepam does not "
            "significantly suppress sexual "
            "function at current dose."
        ],
        [
            "Muscle Mass\n& Physical\nDevelopment",
            "Reduced muscle development "
            "during peak anabolic window "
            "(ages 17-22) due to "
            "hypogonadal state",
            "PARTIALLY REVERSIBLE — Muscle can "
            "be built at any age with adequate "
            "testosterone. However, the optimal "
            "5-year anabolic window was lost. "
            "Current capacity is normal but the "
            "developmental head start was missed.",
            "RECOVERABLE with training. "
            "Testosterone is normal. Muscle "
            "building capacity intact. The "
            "lost years of optimal "
            "development cannot be recaptured."
        ],
        [
            "Bone Density",
            "Potentially reduced accrual "
            "during critical bone-building "
            "years (peak bone mass by 25-30)",
            "PARTIALLY REVERSIBLE — Testosterone "
            "recovery supports bone formation, "
            "but peak bone mass may be lower "
            "than it would have been without "
            "5 years of hypogonadism.",
            "Consider DEXA scan to assess "
            "current bone density. "
            "Weight-bearing exercise + "
            "adequate calcium/D3 to optimize."
        ],
        [
            "Neurological\nMasculinization",
            "Reduced androgen receptor "
            "activation in PFC, amygdala, "
            "hippocampus during critical "
            "remodeling period",
            "PARTIALLY REVERSIBLE — The brain "
            "retains some plasticity, and "
            "testosterone-driven changes can "
            "still occur in the late 20s. "
            "However, the degree of remodeling "
            "possible decreases with age.",
            "Ongoing. Personality and "
            "cognitive changes noted after "
            "Lexapro discontinuation suggest "
            "neurological recovery is "
            "occurring. Maintaining normal "
            "testosterone supports this."
        ],
        [
            "Psychosexual\nDevelopment",
            "Delayed sexual identity "
            "formation, confidence, and "
            "intimate relationship skills "
            "during formative years",
            "RECOVERABLE but not reversible — "
            "The experiential learning that "
            "typically occurs during ages 17-22 "
            "was missed. This can be developed "
            "now but the timeline was delayed.",
            "In progress. Actively developing "
            "these skills and confidence in "
            "the post-Lexapro period."
        ],
        [
            "Social/Career\nDevelopment",
            "Reduced assertiveness, "
            "independence, and dominance "
            "behavior during critical "
            "career-building years. "
            "Increased dependency on others.",
            "RECOVERABLE — Personality traits "
            "are adapting with normal "
            "testosterone. Building business, "
            "asserting independence, seeking "
            "autonomy are all evidence of "
            "recovery.",
            "Actively recovering. Building "
            "business, making independent "
            "decisions, questioning "
            "dependency arrangements."
        ],
    ]
    story.append(btable(damage[0], damage[1:],
                        col_widths=[1.1*inch, 1.6*inch, 2.1*inch, 2.0*inch]))
    story.append(Spacer(1, 8))

    story.append(Paragraph(
        "GOOD NEWS: The most critical metric — HPG axis function and testosterone production — "
        "has fully recovered. The 300→1200 ng/dL rebound confirms that the SSRI damage to the "
        "hormonal axis was NOT permanent. The developmental years lost (ages 17-22) cannot be "
        "recovered, but the biological machinery is intact and functioning. Current focus should "
        "be on maximizing recovery and preventing further harm from medication choices.",
        green_callout
    ))

    story.append(PageBreak())

    # ==================== SECTION 5B: "REPLACING WHAT WAS CUT OUT" ====================
    story.append(stitle("5B. DEBUNKING: \"REPLACING WHAT WAS CUT OUT\""))
    story.append(Spacer(1, 8))

    story.append(Paragraph(
        "A justification offered for the Lexapro/Adderall prescribing decision was that the "
        "surgery to remove the benign tumor disrupted serotonin and dopamine production in the brain, "
        "and these drugs were \"just replacing what was cut out.\" This section examines that claim "
        "against established neuroanatomy and pharmacology.",
        body
    ))
    story.append(Spacer(1, 10))

    story.append(Paragraph("The Claim", h3))
    story.append(Paragraph(
        "\"The tumor removal affected serotonin and dopamine in the brain. Lexapro and Adderall "
        "were prescribed to replace what the surgery took away — like supplementing a deficit "
        "created by the operation.\"",
        quote_style
    ))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Why This Is Anatomically Incorrect", h3))
    story.append(Spacer(1, 4))
    story.extend(blist([
        "SEROTONIN is produced almost exclusively in the raphe nuclei, a cluster of nuclei in the "
        "brainstem (medulla, pons, midbrain). These are deep midline structures. Unless the tumor "
        "was sitting directly on the raphe nuclei — which would present as severe sleep disruption, "
        "autonomic dysfunction, and mood collapse, not OCD and social difficulty — removing a "
        "benign tumor elsewhere in the brain does not remove serotonin production capacity",
        "DOPAMINE is produced primarily in the substantia nigra (motor control) and ventral "
        "tegmental area (reward/motivation), both located in the midbrain. Again, these are deep "
        "structures. A cortical or subcortical benign tumor removal does not excise dopamine-producing "
        "neurons unless the tumor was directly in the midbrain — which would present as Parkinsonian "
        "symptoms (rigidity, tremor, bradykinesia), not the symptom profile described",
        "Neurotransmitter-producing nuclei are NOT distributed throughout the brain like blood "
        "vessels. They are discrete, localized structures that PROJECT widely but ORIGINATE from "
        "specific anatomical locations. Removing tissue from one brain region does not remove the "
        "neurotransmitter factories in another region",
    ]))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Why This Is Pharmacologically Incorrect", h3))
    story.append(Spacer(1, 4))
    story.extend(blist([
        "Lexapro (escitalopram) is a Selective Serotonin REUPTAKE Inhibitor. It does NOT add "
        "serotonin to the brain. It blocks the reuptake transporter (SERT) so that serotonin "
        "already being produced stays in the synaptic cleft longer. If serotonin production were "
        "genuinely deficient due to surgical damage, an SSRI would have almost nothing to work with — "
        "you cannot recycle a neurotransmitter that isn't being made",
        "Adderall (mixed amphetamine salts) does NOT replace dopamine. It forces release of "
        "existing dopamine from presynaptic vesicles AND blocks its reuptake. If dopamine "
        "production sites had been surgically damaged, Adderall would produce diminishing returns "
        "as presynaptic dopamine stores depleted without replenishment",
        "Neither drug is analogous to hormone replacement therapy (like insulin for diabetes or "
        "thyroid hormone for hypothyroidism). Those conditions involve a gland that cannot produce "
        "a substance, so you supply it exogenously. SSRIs and stimulants MODULATE existing "
        "neurotransmitter activity — they do not supply missing neurotransmitters",
        "If the clinical rationale were truly \"replacing a deficit,\" the appropriate intervention "
        "would have been direct neurotransmitter precursor supplementation (L-tryptophan or "
        "5-HTP for serotonin, L-DOPA or L-tyrosine for dopamine) — not reuptake inhibitors. "
        "The fact that reuptake inhibitors were prescribed indicates the prescribers knew the "
        "production system was intact and were modulating activity, not replacing a deficit",
    ]))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Playing Devil's Advocate — Could There Be Any Validity?", h3))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        "In the interest of intellectual honesty, here are the strongest possible arguments in "
        "favor of the prescribing decision, followed by why they still do not justify what happened:",
        body
    ))
    story.append(Spacer(1, 6))

    devils = [
        ["Argument in Favor", "Why It Still Doesn't Hold"],
        [
            "The tumor may have disrupted serotonergic "
            "PROJECTIONS (axonal pathways) even if it "
            "didn't damage the raphe nuclei themselves. "
            "Serotonergic axons project widely throughout "
            "the cortex, and a tumor in their path could "
            "reduce serotonergic signaling in specific "
            "regions.",
            "Even if true, this would be an argument for LOW-DOSE, "
            "TARGETED SSRI use with monitoring — not maximum dose "
            "(40 mg) for 5+ years without hormone monitoring or "
            "reassessment. A disrupted projection pathway would "
            "also not justify the specific drug choices: if the "
            "problem is reduced serotonergic tone in specific cortical "
            "areas, a more selective approach (lower dose, targeted "
            "duration) would be appropriate. 40 mg floods the ENTIRE "
            "serotonergic system, not just the disrupted projections."
        ],
        [
            "Post-surgical patients often experience "
            "depression and anxiety, which SSRIs treat. "
            "The Lexapro may have been prescribed for "
            "psychiatric symptoms (OCD, rumination, social "
            "difficulty) rather than for dystonia directly.",
            "This is the most defensible rationale — SSRIs DO treat "
            "OCD and anxiety. However: (1) the patient and family were "
            "told it was for the chronic dystonia condition, not for "
            "psychiatric symptoms specifically, (2) 40 mg is maximum "
            "dose and rarely the starting point even for severe OCD, "
            "(3) the black box warning for suicidal ideation in "
            "adolescents still applies, (4) there was no discontinuation "
            "plan or reassessment timeline, (5) no hormone monitoring "
            "despite known sexual side effects, and (6) even if this "
            "was the intent, framing it to the family as 'replacing "
            "what was cut out' is a misrepresentation that led to "
            "years of unnecessary continuation."
        ],
        [
            "The OCD and ruminating thoughts William "
            "experienced pre-surgery may indicate genuine "
            "serotonergic dysfunction from the tumor's "
            "mass effect. SSRIs were treating a real "
            "serotonergic problem.",
            "Possible — but the tumor's mass effect was removed with "
            "the tumor. If the OCD was caused by the tumor compressing "
            "serotonergic pathways, removing the tumor should have "
            "resolved the compression. Post-surgical SSRI use might "
            "be warranted SHORT-TERM while the brain recovered, but "
            "not for 5+ years at maximum dose. Additionally, the "
            "OCD and ruminating thoughts could equally have been caused "
            "by the tumor's direct neurological effects (mass effect "
            "on frontal/cingulate circuits), which would resolve with "
            "tumor removal — not require indefinite serotonergic "
            "augmentation."
        ],
        [
            "The prescribing doctor had clinical judgment "
            "and information not available in retrospect. "
            "Perhaps there were imaging findings or "
            "clinical observations that supported this "
            "specific approach.",
            "Clinical judgment deserves respect, but it does not "
            "override: (1) FDA black box warnings, (2) the standard "
            "of care for informed consent, (3) the obligation to "
            "monitor known side effects, (4) the requirement for "
            "a reassessment and discontinuation plan. Even granting "
            "the most generous interpretation of clinical intent, the "
            "EXECUTION — maximum dose, no monitoring, no plan, for "
            "5+ years in an adolescent — fell below standard of care "
            "regardless of the initial rationale."
        ],
        [
            "The Adderall may have been prescribed to "
            "counteract Lexapro's sedating effects, "
            "creating a functional balance.",
            "This is pharmacologically plausible — Adderall's "
            "dopaminergic/noradrenergic activity could offset SSRI "
            "sedation. However, using a Schedule II stimulant to "
            "counteract the side effects of a maximum-dose SSRI "
            "raises the question: why not reduce the SSRI dose "
            "instead of adding a second controlled substance? The "
            "need for Adderall may itself be evidence that 40 mg "
            "Lexapro was too high a dose."
        ],
    ]
    story.append(btable(devils[0], devils[1:],
                        col_widths=[3.0*inch, 3.8*inch]))
    story.append(Spacer(1, 8))

    story.append(Paragraph(
        "CONCLUSION: Even granting every possible charitable interpretation of the prescribing "
        "intent, the execution was indefensible. No version of \"replacing what was cut out\" "
        "justifies maximum-dose SSRI treatment for 5+ years in an adolescent male without hormone "
        "monitoring, without informed consent about sexual side effects, without a discontinuation "
        "plan, and with the framing that this was a sustainable long-term solution for a chronic "
        "condition. The explanation given to the family was either a gross oversimplification used "
        "to avoid a harder conversation, or a fundamental misunderstanding of the pharmacology — "
        "and in either case, it led to years of preventable harm.",
        red_callout
    ))

    story.append(PageBreak())

    # ==================== SECTION 5C: CONTAMINATED MEDICATION TRIALS ====================
    story.append(stitle("5C. CONTAMINATED MEDICATION TRIALS"))
    story.append(Paragraph("Did Maximum-Dose Lexapro Invalidate Other Treatment Responses?", h3))
    story.append(Spacer(1, 8))

    story.append(Paragraph(
        "During the initial treatment period with the first neurologist, multiple dystonia "
        "medications were tried while William was simultaneously on 40 mg Lexapro. These included "
        "baclofen and Parkinson's medications, among others. Most were discontinued due to "
        "intolerable side effects — primarily excessive sedation. This raises a critical question: "
        "were these medications actually ineffective for the dystonia, or were they intolerable "
        "because they were being trialed on top of a maximally CNS-suppressive SSRI baseline?",
        body
    ))
    story.append(Spacer(1, 10))

    story.append(Paragraph("The Pharmacological Problem", h3))
    story.append(Spacer(1, 4))
    story.extend(blist([
        "40 mg escitalopram is already producing significant CNS depression through serotonergic "
        "flooding. Sedation, fatigue, and cognitive slowing are documented dose-dependent side effects",
        "Adding ANY additional CNS depressant on top of maximum-dose Lexapro creates a compounding "
        "sedative effect. The patient's CNS is already operating at reduced excitability — "
        "additional suppression pushes past the threshold of tolerability much faster",
        "This means the therapeutic window for add-on medications was artificially narrowed. "
        "A drug that might be perfectly tolerable on its own (or on a lower SSRI dose) becomes "
        "intolerable because the patient is already at the edge of sedation tolerance",
    ]))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Baclofen — A Case Study in Contaminated Trials", h3))
    story.append(Spacer(1, 4))
    story.extend(blist([
        "Baclofen is a GABA-B agonist — it directly reduces muscle tone and spasticity. It is "
        "a first-line treatment for spasticity and has evidence for dystonia. It addresses the "
        "exact complaint (tone and pain from contractions)",
        "Primary side effect: sedation/drowsiness — this is dose-limiting in most patients",
        "William's experience: baclofen was tried while on 40 mg Lexapro and was discontinued "
        "due to excessive sedation",
        "The question: Was baclofen ineffective for the dystonia, or was it intolerable because "
        "40 mg Lexapro had already consumed most of William's sedation tolerance?",
        "Consider: William later found clonazepam (a GABA-A modulator — same GABA system, "
        "different receptor subtype) to be effective and tolerable. Clonazepam was trialed "
        "AFTER stopping Lexapro, when his CNS was no longer pre-suppressed by maximum-dose SSRI. "
        "If clonazepam is tolerable off Lexapro, baclofen may well have been tolerable off Lexapro too",
    ]))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Parkinson's Medications — Same Problem", h3))
    story.append(Spacer(1, 4))
    story.extend(blist([
        "Dopaminergic medications (levodopa, dopamine agonists) used for Parkinson's are sometimes "
        "trialed for dystonia. Common side effects include dizziness, sedation, and nausea",
        "SSRIs directly antagonize dopaminergic signaling via 5-HT2A/2C receptor activation — "
        "this means Lexapro was actively working AGAINST the mechanism these drugs were trying to use",
        "Trying dopaminergic dystonia treatments while on a drug that suppresses dopamine is "
        "pharmacologically contradictory. It's like pressing the accelerator and the brake simultaneously "
        "— the therapeutic effect is blunted while the side effects compound",
        "Any dopaminergic medication trial conducted while on 40 mg escitalopram cannot be considered "
        "a valid test of that medication's efficacy for dystonia. The SSRI was actively interfering "
        "with the mechanism of action",
    ]))
    story.append(Spacer(1, 8))

    contaminated = [
        ["Drug Class Tried", "Mechanism", "How 40mg Lexapro Contaminated the Trial", "Should Be Re-evaluated?"],
        [
            "Baclofen\n(GABA-B agonist)",
            "Reduces motor neuron "
            "excitability via GABA-B "
            "receptor activation. "
            "Directly reduces tone.",
            "Additive CNS depression. Patient's "
            "sedation threshold already consumed "
            "by maximum-dose SSRI. Baclofen's "
            "dose-limiting side effect (sedation) "
            "reached at sub-therapeutic doses.",
            "YES — William tolerates clonazepam "
            "(GABA-A) off Lexapro. Baclofen "
            "(GABA-B) may be tolerable and "
            "effective without the SSRI "
            "sedation baseline. Worth "
            "re-trialing as adjunct to "
            "low-dose clonazepam."
        ],
        [
            "Dopaminergic agents\n(Parkinson's drugs)",
            "Increase dopamine signaling "
            "in motor circuits to "
            "normalize movement.",
            "Lexapro ACTIVELY SUPPRESSES "
            "dopaminergic signaling via "
            "5-HT2A/2C activation. The SSRI "
            "was pharmacologically opposing "
            "the dopaminergic medication's "
            "mechanism. Efficacy was blunted; "
            "side effects compounded.",
            "POSSIBLY — If dystonia has a "
            "dopaminergic component (likely "
            "given basal ganglia involvement), "
            "these drugs may work differently "
            "without serotonergic interference. "
            "Lower priority than GABAergic "
            "retrial but not invalid."
        ],
        [
            "Other trialed\nmedications\n(unspecified)",
            "Various mechanisms",
            "Any CNS-active drug trialed on "
            "top of 40 mg Lexapro was operating "
            "in a pharmacologically distorted "
            "environment. Side effect thresholds "
            "were lower, therapeutic windows "
            "were narrower, and drug interactions "
            "may have altered metabolism.",
            "ANY medication previously "
            "discontinued due to side effects "
            "(not due to lack of efficacy) "
            "while on high-dose Lexapro "
            "should be flagged for potential "
            "re-evaluation."
        ],
    ]
    story.append(btable(contaminated[0], contaminated[1:],
                        col_widths=[1.3*inch, 1.5*inch, 2.0*inch, 2.0*inch]))
    story.append(Spacer(1, 8))

    story.append(Paragraph(
        "IMPLICATION: The 40 mg Lexapro was not just causing direct harm through HPG axis "
        "suppression — it was also potentially preventing the discovery of effective dystonia "
        "treatments by contaminating every medication trial conducted during that period. "
        "Medications that were labeled 'failed' or 'intolerable' may have been effective and "
        "tolerable if tried without the maximum-dose SSRI sedation baseline. This means years of "
        "medication trials may need to be re-evaluated — particularly baclofen, which targets the "
        "same GABA system that William later found effective via clonazepam.",
        red_callout
    ))
    story.append(Spacer(1, 8))

    story.append(Paragraph(
        "RECOMMENDATION: Discuss with the movement disorder neurologist the possibility of "
        "re-trialing baclofen (oral or intrathecal pump) as a complement to low-dose clonazepam. "
        "Baclofen acts on GABA-B (different receptor subtype from clonazepam's GABA-A), meaning "
        "they could have synergistic effects without full dose-stacking. A combination of low-dose "
        "clonazepam + low-dose baclofen could potentially provide better dystonia control than "
        "either alone, at doses where neither produces intolerable sedation.",
        green_callout
    ))

    story.append(PageBreak())

    # ==================== SECTION 6: MIRTAZAPINE TRANSITION (renumbered from 7) ====================
    # [Sections 6 (Current Med Comparison), 8 (Go-Forward Plan), and 9 (Mitigating Side Effects)
    #  from the full version are excluded from this copy]
    story.append(stitle("6. MIRTAZAPINE TRANSITION — PITTSBURGH ANALYSIS"))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Was the Pittsburgh Decision Medically Sound?", h3))
    story.append(Spacer(1, 6))

    story.append(Paragraph(
        "When William moved to Pittsburgh for his masters program, his new medical team took him off "
        "clonazepam (which was working) and substituted mirtazapine. This decision can be evaluated "
        "on three axes: pharmacological appropriateness, transition safety, and outcome.",
        body
    ))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Pharmacological Appropriateness", bold))
    story.extend(blist([
        "Clonazepam addresses dystonia through GABA-A modulation — the mechanism William's dystonia responds to",
        "Mirtazapine acts on alpha-2 adrenergic, 5-HT2A/2C/3, and H1 receptors — NONE of these are the GABA pathway",
        "These drugs are not pharmacological equivalents. Substituting mirtazapine for clonazepam for dystonia "
        "is like substituting an antihistamine for an antibiotic — they are completely different drug classes "
        "treating through completely different mechanisms",
        "The only overlapping indication is sleep improvement (both are sedating), but sleep was not the primary complaint",
    ]))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Transition Safety", bold))
    story.extend(blist([
        "William was on clonazepam 0.5 mg twice daily — a therapeutic dose that produces physical dependence",
        "Cold turkey benzodiazepine discontinuation is medically DANGEROUS: can cause seizures, psychosis, "
        "and status epilepticus in severe cases",
        "2025 Joint Clinical Practice Guidelines explicitly state: benzodiazepine discontinuation should "
        "proceed at 5-10% dose reduction every 2-4 weeks, NEVER abruptly",
        "This is ESPECIALLY dangerous in a post-craniotomy patient with elevated baseline seizure risk",
        "A safe transition would have been: gradual clonazepam taper over weeks/months, with cross-titration "
        "to another GABAergic agent (gabapentin, pregabalin, baclofen) if the goal was to discontinue the benzo",
    ]))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Outcome", bold))
    story.extend(blist([
        "Mirtazapine did not adequately control dystonia pain",
        "William remained heavily reliant on THC for pain management",
        "Ultimately medically withdrew from masters program due to unmanaged symptoms",
        "The cost: a masters degree, career progression, and months of unnecessary suffering",
    ]))
    story.append(Spacer(1, 8))

    story.append(Paragraph(
        "ASSESSMENT: The Pittsburgh transition was not medically sound. The substitution was "
        "pharmacologically inappropriate (wrong mechanism), the transition method was dangerous "
        "(cold turkey benzo discontinuation), and the outcome was predictably poor. A doctor "
        "refusing to prescribe a medication that works because of prescribing stigma, while "
        "substituting a pharmacologically unrelated drug AND discontinuing the working medication "
        "unsafely, directly caused the loss of William's masters program.",
        red_callout
    ))

    story.append(PageBreak())

    # ==================== SECTION 7: REVERSAL PROTOCOLS (renumbered from 10) ====================
    story.append(stitle("7. REVERSAL & RECOVERY PROTOCOLS"))
    story.append(Paragraph("Addressing Damage from 5+ Years of SSRI-Induced Hypogonadism", h3))
    story.append(Spacer(1, 8))

    story.append(Paragraph(
        "Your testosterone has recovered (300→1200 ng/dL rebound), confirming the HPG axis damage "
        "was not permanent. The focus now is on optimizing the recovery of the downstream systems "
        "that were affected by 5+ years of chronic hypogonadism during a critical developmental window.",
        body
    ))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Musculoskeletal Recovery", h3))
    story.extend(blist([
        "Progressive resistance training — your testosterone is now normal, so the anabolic "
        "response to training should be robust. Focus on compound movements (squat, deadlift, "
        "bench, rows) that maximize testosterone utilization and muscle protein synthesis",
        "Protein intake: 1.6-2.2 g/kg bodyweight/day — this is the evidence-based range for "
        "maximizing muscle protein synthesis in trained individuals",
        "Creatine monohydrate 5g/day — most studied sports supplement, supports muscle development, "
        "AND has neuroprotective properties (relevant given benzo neurodegeneration concern)",
        "Vitamin D3: test levels and supplement to 50-80 ng/mL. Vitamin D acts as a neurosteroid "
        "and supports testosterone, bone density, and immune function. Critical in FL despite sun exposure",
        "DEXA scan recommended to assess current bone density baseline — if below expected for age, "
        "discuss with endocrinologist",
    ]))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Neurological Recovery", h3))
    story.extend(blist([
        "The brain remains plastic through the late 20s — androgen-dependent remodeling can still "
        "occur. Maintaining normal testosterone is the single most important factor",
        "Cognitive challenges that push neuroplasticity: learning new skills, language, music, "
        "complex problem-solving (building a business qualifies)",
        "Avoid substances that further suppress neuroplasticity: excessive alcohol, chronic THC use, "
        "unnecessary medications that affect cognition",
        "Sleep optimization — this is when neuroplasticity consolidation occurs. Clonazepam helps "
        "here. Aim for 7-9 hours of consistent sleep",
        "Omega-3s (2-4g EPA+DHA/day) + magnesium L-threonate — support neuronal membrane integrity "
        "and synaptic function",
        "NAD+ precursors (NMN 500-1000 mg/day or NR 300-600 mg/day) — NAD+ declines with age and "
        "is depleted by oxidative stress. It is the essential cofactor for SIRT1 (DNA repair, "
        "anti-neuroinflammation), mitochondrial Complex I (neuronal ATP production), and PARP "
        "(DNA damage repair). Supports neuroplasticity at the metabolic level. Among the strongest "
        "evidence-based neuroprotective supplements — particularly relevant given both the prior "
        "SSRI-induced oxidative stress and current benzo neurodegeneration concern",
    ]))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Hormonal Optimization", h3))
    story.extend(blist([
        "Get a comprehensive hormone panel: total testosterone, free testosterone, SHBG, "
        "estradiol, LH, FSH, prolactin, thyroid panel (TSH, free T3, free T4), cortisol",
        "Monitor annually — this is your early warning system for any medication-induced "
        "hormonal disruption. If ANY future medication drops T below 400 ng/dL, reassess immediately",
        "Natural testosterone optimization: sleep 7-9hrs, resistance training, adequate zinc "
        "(15-30 mg/day), adequate dietary fat (20-35% calories), minimize chronic stress",
        "Avoid environmental endocrine disruptors: minimize plastic food containers, avoid "
        "BPA, limit soy-based processed foods (phytoestrogens)",
        "If testosterone is suboptimal despite recovery: consult endocrinologist about "
        "clomiphene citrate (stimulates LH production without exogenous testosterone) before "
        "considering TRT. At your age, preserving natural HPG function is preferred",
    ]))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Psychological Recovery", h3))
    story.extend(blist([
        "Recognize that personality changes after Lexapro discontinuation are RECOVERY, not instability. "
        "Increased assertiveness, independence, questioning, and sexual confidence are normal male "
        "development that was pharmacologically delayed",
        "The inconsistency you've experienced between medication states is real — you are literally "
        "a different person on different medications because brain chemistry dictates cognition and personality. "
        "This is not a character flaw; it is pharmacology",
        "The frustration you feel about decisions made by adults during your medical care is legitimate. "
        "The pharmacological evidence supports your experience — you were not imagining the effects",
        "Consider working with a therapist who understands medical trauma and understands the distinction "
        "between psychological issues and iatrogenic (medically-caused) harm",
        "Building autonomous systems and reducing dependency (on people, on tools, on medication where possible) "
        "is a healthy expression of the independence drive that was suppressed for years",
    ]))

    story.append(PageBreak())

    # ==================== SECTION 8: DECISION FRAMEWORK (renumbered from 11) ====================
    story.append(stitle("8. DECISION FRAMEWORK — PREVENTING FUTURE MISTAKES"))
    story.append(Spacer(1, 8))

    story.append(Paragraph(
        "This framework exists to ensure that the prescribing mistakes of the past are never repeated. "
        "Every medication decision going forward should be evaluated against these criteria.",
        body
    ))
    story.append(Spacer(1, 10))

    story.append(Paragraph("The Non-Negotiable Questions", h3))
    story.append(Paragraph(
        "Before starting ANY new medication, these questions must be answered:",
        body
    ))
    story.append(Spacer(1, 6))

    questions = [
        "MECHANISM: Does this drug target the pathway my dystonia actually responds to (GABAergic)? "
        "If not, what is the specific rationale for using a different mechanism?",
        "HPG IMPACT: What is this drug's documented effect on testosterone, prolactin, LH, and "
        "sexual function? Will I have hormone monitoring while taking it?",
        "DURATION: How long is this intended to be taken? What is the reassessment timeline? "
        "What is the discontinuation plan from day one?",
        "EVIDENCE: Is there published evidence for this drug treating secondary dystonia specifically? "
        "Or is this being prescribed off-label based on a different indication?",
        "TRANSITION: If replacing a current medication, what is the taper protocol? Is the "
        "transition pharmacologically safe (same or overlapping mechanism), or am I being switched "
        "to an unrelated drug class?",
        "MONITORING: What blood work and clinical assessments will be done at baseline and "
        "during treatment? At minimum: comprehensive metabolic, testosterone, prolactin",
        "AUTONOMY: Am I the one making this decision, with full information about benefits AND risks? "
        "Or is someone else directing my medical care without my informed, autonomous consent?",
    ]
    story.extend(blist(questions))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Red Flags — When to Refuse or Seek a Second Opinion", h3))
    story.extend(blist([
        "Any doctor who refuses to prescribe a medication that has PROVEN efficacy for your condition "
        "without offering a pharmacologically equivalent alternative — this is prescribing stigma, "
        "not clinical judgment",
        "Any doctor who wants to abruptly discontinue a benzodiazepine rather than taper — this is "
        "medically dangerous and violates current clinical guidelines",
        "Any doctor who prescribes a pharmacologically unrelated drug as a 'substitute' for a "
        "medication from a different class (e.g., mirtazapine for clonazepam)",
        "Any doctor who prescribes a maximum-dose SSRI without discussing sexual side effects, "
        "hormone monitoring, intended duration, or discontinuation plan",
        "Any medical decision being made by someone other than you without your full, informed consent — "
        "you are an adult capable of making your own healthcare decisions",
        "Any prescriber who dismisses your reported side effects or treatment responses — your "
        "body's documented reaction (300→1200 ng/dL testosterone swing) is clinical evidence",
    ]))
    story.append(Spacer(1, 10))

    story.append(Paragraph("The Medication Hierarchy for YOUR Dystonia", h3))
    story.append(Paragraph(
        "Based on your documented treatment responses, this is the evidence-based hierarchy "
        "for medication choices, specific to your case:",
        body
    ))
    story.append(Spacer(1, 6))

    hierarchy = [
        ["Tier", "Medications", "Rationale"],
        [
            "TIER 1\nFirst-Line\n(Proven for YOU)",
            "Clonazepam (current)\n"
            "Clonazepam + Trihexyphenidyl\n"
            "Clonazepam + Gabapentin/Pregabalin",
            "Clonazepam is the ONLY medication proven effective for your dystonia. "
            "Combinations per 2024 RCT may enhance efficacy while keeping "
            "benzo dose low."
        ],
        [
            "TIER 2\nAdjuncts\n(Add to Tier 1)",
            "Low-Dose Naltrexone (LDN)\n"
            "CBD Topicals\n"
            "Acupuncture\n"
            "Bupropion (for depression)",
            "Low risk, complementary mechanisms. Can reduce reliance on "
            "clonazepam over time. LDN's anti-inflammatory mechanism is "
            "novel and promising. Bupropion addresses depression without "
            "HPG suppression."
        ],
        [
            "TIER 3\nInvestigational\n(Promising but\nnot yet proven)",
            "TMS (clinical trials)\n"
            "Ketamine infusions\n"
            "Tizanidine\n"
            "Diazepam (if clonazepam unavailable)",
            "These have potential but haven't been tried or have less evidence "
            "for your specific case. Worth pursuing in parallel with Tier 1."
        ],
        [
            "TIER 4\nAVOID UNLESS\nNO ALTERNATIVE",
            "SSRIs (any)\n"
            "Mirtazapine (high dose)\n"
            "Any drug with documented "
            "HPG axis suppression",
            "Documented severe hypogonadism in your case (T=300 ng/dL). "
            "Do not target the wrong mechanism (serotonin vs GABA) while "
            "simultaneously causing the worst side effect profile for you. "
            "Only if ALL Tier 1-3 options have failed AND with full "
            "hormone monitoring."
        ],
    ]
    story.append(btable(hierarchy[0], hierarchy[1:],
                        col_widths=[1.2*inch, 2.3*inch, 3.3*inch]))
    story.append(Spacer(1, 10))

    story.append(Paragraph("The Consistency Imperative", h3))
    story.append(Paragraph(
        "You identified the most important point yourself: consistency. You cannot build a life, "
        "a business, or relationships while switching medications and experiencing personality "
        "shifts every few months. Each medication change resets your emotional baseline, your "
        "decision-making patterns, your relationships, and your work momentum. The goal is to "
        "find a medication regimen that works, commit to it, and build your life ON that stable "
        "foundation — not to chase the perfect drug that doesn't exist. Clonazepam with adjuncts "
        "is that foundation right now. The risks are real but manageable. The alternative — "
        "constant switching, inconsistency, and rebuilding from scratch every few months — is worse.",
        green_callout
    ))

    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", thickness=1, color=BrandConfig.MID_GRAY))
    story.append(Paragraph(
        "Comprehensive Medical Review — Compiled March 21, 2026. Sources include PubMed, "
        "FDA prescribing information, Dystonia Coalition Treatment Guidelines, American Journal "
        "of Psychiatry (2024), 2025 Joint Clinical Practice Guidelines on Benzodiazepine "
        "Tapering (ASAM/ACMT), Frontiers in Neurology (2023), endocrinology literature on "
        "SSRI-induced hypogonadism, and the Dystonia Medical Research Foundation. "
        "This document is for personal informational use and should be shared with healthcare "
        "providers to facilitate informed decision-making.",
        footer
    ))

    doc.build(story, onFirstPage=_on_page, onLaterPages=_on_page)
    print(f"PDF generated: {output}")
    return output


if __name__ == "__main__":
    path = build_pdf()
    os.system(f'open "{path}"')
