#!/usr/bin/env python3
"""Generate branded PDF: Alex Hormozi Frameworks Research Guide."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from execution.branded_pdf_engine import (
    get_brand_styles, BrandConfig, _on_page, accent_line,
    section_title, coach_note_box, branded_table,
    _register_fonts
)
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.colors import HexColor
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, KeepTogether, HRFlowable
)
from datetime import datetime

OUTPUT = os.path.expanduser("~/dev-sandbox/docs/hormozi-frameworks-research.pdf")

def bullet(text, styles, indent=18):
    """Create a bullet point paragraph."""
    s = ParagraphStyle("Bullet", parent=styles["body"], leftIndent=indent, bulletIndent=6,
                        spaceBefore=2, spaceAfter=2)
    return Paragraph(f"<bullet>&bull;</bullet> {text}", s)

def numbered(num, text, styles, indent=18):
    s = ParagraphStyle("Numbered", parent=styles["body"], leftIndent=indent, bulletIndent=0,
                        spaceBefore=2, spaceAfter=2)
    return Paragraph(f"<b>{num}.</b> {text}", s)

def gold_box(text, styles):
    """Gold-bordered emphasis box."""
    data = [[Paragraph(text, styles["body"])]]
    t = Table(data, colWidths=[6.5 * inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BrandConfig.GOLD_BG),
        ("BOX", (0, 0), (-1, -1), 2, BrandConfig.GOLD),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
    ]))
    return t

def quote_box(text, attribution, styles):
    """Styled quote box."""
    q_style = ParagraphStyle("Quote", parent=styles["body"], fontSize=11, leading=16,
                              textColor=BrandConfig.CHARCOAL, fontName=BrandConfig.BODY_FONT_BOLD)
    a_style = ParagraphStyle("QuoteAttr", parent=styles["small"], alignment=TA_LEFT,
                              textColor=BrandConfig.GOLD_DARK)
    data = [[Paragraph(f'<i>"{text}"</i>', q_style)],
            [Paragraph(f"-- {attribution}", a_style)]]
    t = Table(data, colWidths=[6.5 * inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), HexColor("#F9F6F0")),
        ("BOX", (0, 0), (-1, -1), 0, BrandConfig.WHITE),
        ("LINEBEFOREDECOR", (0, 0), (0, -1), 3, BrandConfig.GOLD),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 16),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
    ]))
    return t

def build():
    doc = SimpleDocTemplate(OUTPUT, pagesize=letter,
                            topMargin=1.1*inch, bottomMargin=0.8*inch,
                            leftMargin=0.7*inch, rightMargin=0.7*inch)
    s = get_brand_styles()
    story = []

    # --- TITLE PAGE ---
    story.append(Spacer(1, 1.5*inch))
    title_s = ParagraphStyle("BigTitle", parent=s["title"], fontSize=28, leading=34,
                              alignment=TA_CENTER, textColor=BrandConfig.CHARCOAL)
    story.append(Paragraph("Alex Hormozi", title_s))
    story.append(Spacer(1, 6))
    sub_s = ParagraphStyle("BigSub", parent=s["title"], fontSize=20, leading=26,
                            alignment=TA_CENTER, textColor=BrandConfig.GOLD)
    story.append(Paragraph("Complete Frameworks Research Guide", sub_s))
    story.append(Spacer(1, 20))
    story.append(accent_line())
    story.append(Spacer(1, 12))
    story.append(Paragraph("From $100M Offers, $100M Leads, Gym Launch Secrets,<br/>and Acquisition.com Content",
                           ParagraphStyle("TitleDesc", parent=s["body"], alignment=TA_CENTER, fontSize=11, leading=16)))
    story.append(Spacer(1, 30))
    story.append(Paragraph(f"Compiled {datetime.now().strftime('%B %d, %Y')}",
                           ParagraphStyle("TitleDate", parent=s["small"], alignment=TA_CENTER)))
    story.append(Spacer(1, 8))
    story.append(Paragraph("Applied context: AI tools + fitness coaching infrastructure, zero paying clients",
                           ParagraphStyle("Context", parent=s["body"], alignment=TA_CENTER,
                                          textColor=BrandConfig.GOLD_DARK, fontSize=10)))
    story.append(PageBreak())

    # --- TABLE OF CONTENTS ---
    story.append(section_title("TABLE OF CONTENTS", s))
    story.append(Spacer(1, 8))
    toc_items = [
        "1. The Value Equation -- Making Irresistible Offers",
        "2. Grand Slam Offer Creation -- Step by Step",
        "3. The Core Four -- Lead Generation Methods",
        "4. The Rule of 100 -- Daily Action Framework",
        "5. Getting Your First 5 Customers -- Zero to Revenue",
        "6. Pricing Strategy -- Charge More, Not Less",
        "7. Lead Magnets -- Give Away Your Best Stuff",
        "8. Market Selection -- Starving Crowds",
        "9. Skills vs Passion vs Market Demand",
        "10. Gym Launch & Fitness Business Strategies",
        "11. If Starting a Business in 2026",
        "12. Applied Action Plan -- Your Situation"
    ]
    for item in toc_items:
        story.append(Paragraph(item, ParagraphStyle("TOC", parent=s["body"], fontSize=11, leading=18,
                                                     leftIndent=12, textColor=BrandConfig.CHARCOAL)))
    story.append(PageBreak())

    # ==========================================================================
    # SECTION 1: VALUE EQUATION
    # ==========================================================================
    story.append(section_title("1. THE VALUE EQUATION", s))
    story.append(Paragraph("The foundation of everything Hormozi teaches. This is how humans perceive value.", s["body"]))
    story.append(Spacer(1, 12))

    # Formula box
    formula_s = ParagraphStyle("Formula", parent=s["title"], fontSize=16, leading=22,
                                alignment=TA_CENTER, textColor=BrandConfig.CHARCOAL)
    formula_data = [[Paragraph(
        '<b>Value = (Dream Outcome x Perceived Likelihood of Achievement) / (Time Delay x Effort &amp; Sacrifice)</b>',
        formula_s)]]
    ft = Table(formula_data, colWidths=[6.5*inch])
    ft.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BrandConfig.GOLD_BG),
        ("BOX", (0, 0), (-1, -1), 3, BrandConfig.GOLD),
        ("TOPPADDING", (0, 0), (-1, -1), 16),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 16),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
    ]))
    story.append(ft)
    story.append(Spacer(1, 12))

    story.append(Paragraph("<b>The Four Drivers:</b>", s["body_bold"]))
    story.append(Spacer(1, 4))

    ve_table = branded_table(
        ["Driver", "Direction", "What It Means", "How to Optimize"],
        [
            ["Dream Outcome", "MAXIMIZE", "The idealized result your client envisions -- the emotional, aspirational end state",
             "Paint the vivid picture. Use testimonials. Show before/after. Make it specific and measurable."],
            ["Perceived Likelihood", "MAXIMIZE", "How confident they are that YOUR solution will work FOR THEM specifically",
             "Case studies, guarantees, social proof, credentials, specificity to their situation."],
            ["Time Delay", "MINIMIZE", "Gap between paying you and getting the result. Shorter = more valuable.",
             "Quick wins in first 48 hours. Show progress milestones. Compress onboarding."],
            ["Effort & Sacrifice", "MINIMIZE", "What they must give up or endure to get the result.",
             "Done-for-you > Done-with-you > DIY. Remove friction. Make it easy."],
        ],
        col_widths=[1.1*inch, 0.8*inch, 2.2*inch, 2.4*inch]
    )
    story.append(ve_table)
    story.append(Spacer(1, 12))

    story.append(quote_box(
        "Most businesses focus on the top of the equation (Dream Outcome). But the bottom is where the magic is. "
        "Reducing time delay and effort is often easier and more impactful than promising a bigger dream.",
        "Alex Hormozi, $100M Offers", s))
    story.append(Spacer(1, 8))

    story.append(coach_note_box(
        "<b>Applied to your situation:</b> Your AI fitness tools reduce EFFORT (automated meal plans, workout programming). "
        "Your 1:1 coaching increases PERCEIVED LIKELIHOOD (personal attention). Your tech stack compresses TIME DELAY "
        "(instant onboarding, immediate first workout). These are competitive advantages -- lead with them.", s))
    story.append(PageBreak())

    # ==========================================================================
    # SECTION 2: GRAND SLAM OFFER
    # ==========================================================================
    story.append(section_title("2. GRAND SLAM OFFER CREATION", s))
    story.append(Paragraph(
        "A Grand Slam Offer is so valuable that people feel stupid saying no. "
        "It is NOT about discounting. It is about stacking so much value that the price becomes irrelevant.", s["body"]))
    story.append(Spacer(1, 10))

    story.append(Paragraph("<b>Step 1: Identify the Dream Outcome</b>", s["h3"]))
    story.append(Paragraph(
        "What does your ideal client ACTUALLY want? Not what they need -- what they desire. "
        "For fitness: they want to look good naked, feel confident, have energy, get compliments. "
        "They do NOT want a workout program. The program is the vehicle, not the destination.", s["body"]))
    story.append(Spacer(1, 8))

    story.append(Paragraph("<b>Step 2: List Every Obstacle</b>", s["h3"]))
    story.append(Paragraph(
        "Write down every problem, objection, fear, and barrier that prevents them from achieving the dream outcome. "
        "Each problem has four negative dimensions (aligned with the value equation):", s["body"]))
    story.append(Spacer(1, 4))
    for b in [
        "What bad thing will happen if they try? (perceived risk)",
        "What good thing will they miss out on? (opportunity cost)",
        "How long will it take? (time fear)",
        "How hard/painful will it be? (effort fear)",
    ]:
        story.append(bullet(b, s))
    story.append(Spacer(1, 8))

    story.append(Paragraph("<b>Step 3: Transform Problems into Solutions</b>", s["h3"]))
    story.append(Paragraph(
        "For EACH obstacle, create a specific solution. This is where your offer gets built. "
        "The more obstacles you solve, the more valuable the offer becomes.", s["body"]))
    story.append(Spacer(1, 8))

    story.append(Paragraph("<b>Step 4: Create Delivery Vehicles</b>", s["h3"]))
    story.append(Paragraph(
        "Determine HOW you deliver each solution. Consider the value hierarchy:", s["body"]))
    story.append(Spacer(1, 4))

    dv_table = branded_table(
        ["Delivery Level", "Value Perception", "Example"],
        [
            ["Done-For-You (DFY)", "HIGHEST", "You build their meal plan, program their workouts, handle everything"],
            ["Done-With-You (DWY)", "HIGH", "1:1 coaching calls, you guide them through decisions"],
            ["Do-It-Yourself (DIY)", "MEDIUM", "Course, templates, app access"],
        ],
        col_widths=[1.5*inch, 1.2*inch, 3.8*inch]
    )
    story.append(dv_table)
    story.append(Spacer(1, 8))

    story.append(Paragraph("<b>Step 5: Enhance with Bonuses, Guarantees, Scarcity, Urgency</b>", s["h3"]))
    story.append(Spacer(1, 4))
    for b in [
        "<b>Bonuses:</b> Should feel like the natural next step. Related to your offer, adding momentum. "
        "Example: Free peptide protocol guide, body composition analysis, supplement stack recommendation.",
        "<b>Guarantees:</b> Remove risk. Money-back, results-based, or conditional guarantees. "
        "The stronger your guarantee, the more you can charge.",
        "<b>Scarcity:</b> Limited spots (real, not fake). 'I only take 10 clients at a time' works when it is true.",
        "<b>Urgency:</b> Time-limited pricing, seasonal launches, cohort start dates.",
    ]:
        story.append(bullet(b, s))
    story.append(Spacer(1, 8))

    story.append(Paragraph("<b>Step 6: Name It (M.A.G.I.C. Formula)</b>", s["h3"]))
    story.append(Spacer(1, 4))
    for b in [
        "<b>M</b>ake a magnetic reason why (time-bound, seasonal, event-based)",
        "<b>A</b>nnounce your avatar (who it is for specifically)",
        "<b>G</b>ive them a goal (the dream outcome in the name)",
        "<b>I</b>ndicate a time interval (how fast)",
        "<b>C</b>omplete with a container word (challenge, blueprint, system, accelerator)",
    ]:
        story.append(bullet(b, s))
    story.append(Spacer(1, 8))

    story.append(gold_box(
        '<b>Example for your business:</b> "The 90-Day Executive Body Recomp Accelerator" -- '
        'targets busy professionals (avatar), body recomposition (goal), 90 days (time interval), '
        'accelerator (container word).', s))
    story.append(PageBreak())

    # ==========================================================================
    # SECTION 3: THE CORE FOUR
    # ==========================================================================
    story.append(section_title("3. THE CORE FOUR -- Lead Generation Methods", s))
    story.append(Paragraph(
        "From $100M Leads: There are only 4 ways to let people know about your business. "
        "That is it. Every marketing tactic falls into one of these buckets.", s["body"]))
    story.append(Spacer(1, 10))

    core_four = branded_table(
        ["Method", "What It Is", "Cost", "Speed", "Your Application"],
        [
            ["1. Warm Outreach", "Reach out to people who already know you -- friends, family, social followers, past contacts",
             "FREE", "FAST", "DM everyone you know. Text old gym buddies. Message LinkedIn connections."],
            ["2. Cold Outreach", "Contact strangers -- cold email, cold DM, cold call, flyers, door-to-door",
             "FREE", "MEDIUM", "Cold DM fitness accounts. Email local businesses about corporate wellness."],
            ["3. Free Content", "Post valuable content that attracts strangers to you -- social media, YouTube, blog, podcast",
             "FREE", "SLOW", "Post transformation tips, nutrition science, peptide education on Instagram/YouTube."],
            ["4. Paid Ads", "Pay platforms to show your message to targeted strangers -- Meta, Google, TikTok ads",
             "PAID", "FAST", "Facebook ads to local Naples market or online fitness seekers."],
        ],
        col_widths=[1.0*inch, 1.8*inch, 0.5*inch, 0.6*inch, 2.6*inch]
    )
    story.append(core_four)
    story.append(Spacer(1, 12))

    story.append(quote_box(
        "When you have no money, you have time. When you have money, you buy back time. "
        "Start with warm outreach and cold outreach -- they cost nothing but effort.",
        "Alex Hormozi, $100M Leads", s))
    story.append(Spacer(1, 8))

    story.append(Paragraph("<b>The Progression (for someone at zero):</b>", s["h3"]))
    story.append(Spacer(1, 4))
    for n, text in enumerate([
        "<b>Week 1-4:</b> Warm outreach ONLY. Exhaust your entire network. 100 messages per day.",
        "<b>Week 2-8:</b> Add cold outreach. 100 cold DMs/emails per day while continuing warm.",
        "<b>Week 1+:</b> Start posting content daily (compounds over time, builds credibility for outreach).",
        "<b>After first revenue:</b> Reinvest into paid ads to accelerate. Client-financed acquisition.",
    ], 1):
        story.append(numbered(n, text, s))
    story.append(PageBreak())

    # ==========================================================================
    # SECTION 4: RULE OF 100
    # ==========================================================================
    story.append(section_title("4. THE RULE OF 100", s))
    story.append(Spacer(1, 4))

    story.append(quote_box(
        "Do 100 primary actions every single day for 100 days. You will not be the same person at the end.",
        "Alex Hormozi", s))
    story.append(Spacer(1, 10))

    story.append(Paragraph(
        "This is the antidote to 'I tried marketing and it did not work.' You did not do enough volume. "
        "The Rule of 100 forces volume, which creates skill, which creates results.", s["body"]))
    story.append(Spacer(1, 8))

    r100_table = branded_table(
        ["Channel", "The 100", "Daily Commitment", "What Success Looks Like at Day 100"],
        [
            ["Warm Outreach", "100 reach-outs/day", "Personalized DMs, texts, calls to people you know",
             "Exhausted network, 5-15 conversations/day, 2-5 clients"],
            ["Cold Outreach", "100 reach-outs/day", "Cold DMs, cold emails, cold calls to strangers",
             "Refined pitch, thick skin, predictable pipeline"],
            ["Content", "100 minutes/day", "Create + post at least 1 piece of content per day",
             "100+ posts, growing following, inbound inquiries starting"],
            ["Paid Ads", "$100/day", "Run ads, test creatives, optimize daily",
             "Profitable ad creative identified, cost-per-lead dialed in"],
        ],
        col_widths=[1.0*inch, 1.2*inch, 2.0*inch, 2.3*inch]
    )
    story.append(r100_table)
    story.append(Spacer(1, 12))

    story.append(Paragraph("<b>Why Volume Matters:</b>", s["h3"]))
    story.append(Spacer(1, 4))
    for b in [
        "You cannot identify bottlenecks without volume flowing through the system",
        "Your pitch improves through repetition -- message 1 will be terrible, message 100 will convert",
        "Volume creates data. Data reveals what works. What works gets doubled down on.",
        "Most people quit after 10 attempts. You need 100 per DAY.",
        '"Simple scales. Fancy fails. Doing the basics at scale is what makes you advanced."',
    ]:
        story.append(bullet(b, s))
    story.append(Spacer(1, 8))

    story.append(coach_note_box(
        "<b>For you right now:</b> Pick ONE channel (warm outreach). Do 100 reach-outs per day for the next "
        "30 days. Not 10. Not 50. ONE HUNDRED. Track responses in a spreadsheet. After 30 days, add cold outreach.", s))
    story.append(PageBreak())

    # ==========================================================================
    # SECTION 5: FIRST 5 CUSTOMERS
    # ==========================================================================
    story.append(section_title("5. GETTING YOUR FIRST 5 CUSTOMERS", s))
    story.append(Paragraph(
        "Hormozi's exact 10-step playbook for going from zero to your first paying clients:", s["body"]))
    story.append(Spacer(1, 10))

    steps = [
        ("<b>Get a List</b>", "Scrape ALL your contacts across every platform -- phone, Instagram, Facebook, LinkedIn, "
         "email. Export everything. You probably have 500-2000+ contacts you are ignoring."),
        ("<b>Pick Your Platform</b>", "Choose the platform where you have the MOST people. That is where you start. "
         "Do not spread thin across 5 platforms."),
        ("<b>Personalize Your Message</b>", "No copy-paste spam. Reference something specific about them. "
         "'Hey [name], saw you just [specific thing]. Made me think of you because...'"),
        ("<b>Reach Out to 100 People/Day</b>", "This is the Rule of 100 applied. Volume is everything at this stage."),
        ("<b>Use the Magic Script</b>", "'I am looking to take on 5 case studies for [specific problem]. "
         "I am going to do it for free/heavily discounted to build case studies. Do you know anyone who would be a good fit?' "
         "-- 50% of the time they say 'Actually, I might be interested...'"),
        ("<b>Deliver Incredible Results</b>", "Over-deliver massively for these first clients. They are your proof. "
         "Their results become your entire marketing engine."),
        ("<b>Get Testimonials + Referrals</b>", "Document everything. Before/after photos. Video testimonials. "
         "Written reviews. Then ask: 'Who else do you know that wants results like yours?'"),
        ("<b>Charge the Next Batch</b>", "Use the case studies to sell at full price (or higher) to the next group."),
        ("<b>Keep the Outreach Going</b>", "Do not stop reaching out just because you got 5 clients. The pipeline must never stop."),
        ("<b>Increase Price with Every Cohort</b>", "First 5 = free. Next 5 = $100. Next 5 = $300. Next 5 = $500. "
         "Each round your proof is stronger, so your price goes up."),
    ]
    for i, (title, desc) in enumerate(steps, 1):
        story.append(Paragraph(f"<b>Step {i}:</b> {title}", s["h3"]))
        story.append(Paragraph(desc, s["body"]))
        story.append(Spacer(1, 4))

    story.append(Spacer(1, 8))
    story.append(gold_box(
        '<b>The progression Hormozi followed himself:</b><br/>'
        '1. Sold consulting for FREE for 1 year while posting 1 piece of content per day<br/>'
        '2. Increased price to $500 and pitched that for 3 months<br/>'
        '3. Tripled down on first $500 client to create a killer case study<br/>'
        '4. Leveraged those results to sell the next client for $1,000<br/>'
        '5. Kept raising prices as proof accumulated', s))
    story.append(PageBreak())

    # ==========================================================================
    # SECTION 6: PRICING
    # ==========================================================================
    story.append(section_title("6. PRICING STRATEGY -- Charge More, Not Less", s))
    story.append(Spacer(1, 4))

    story.append(quote_box(
        "The goal is not to be the cheapest. The goal is to be the most valuable. "
        "When you charge more, you attract better clients, deliver better results, "
        "and build a business that does not eat you alive.",
        "Alex Hormozi", s))
    story.append(Spacer(1, 10))

    story.append(Paragraph("<b>Why Premium Pricing Works:</b>", s["h3"]))
    story.append(Spacer(1, 4))
    for b in [
        "<b>Better clients:</b> People who pay more are more committed, get better results, and complain less",
        "<b>Better delivery:</b> Higher margins mean you can invest more in each client's experience",
        "<b>Better positioning:</b> Premium price = premium perception. You are not competing with $29/month apps.",
        "<b>Better economics:</b> 10 clients at $2,000 = $20K. You need 400 clients at $50 to match that.",
        "<b>Better results:</b> Clients who invest more follow through more. Their success becomes your marketing.",
    ]:
        story.append(bullet(b, s))
    story.append(Spacer(1, 10))

    story.append(Paragraph("<b>The Two Viable Price Points:</b>", s["h3"]))
    story.append(Paragraph(
        "Hormozi says there are only two strategies that work: sell something extremely expensive to a few people, "
        "or sell something extremely cheap to everyone. The middle is where businesses die.", s["body"]))
    story.append(Spacer(1, 8))

    price_table = branded_table(
        ["Strategy", "Price Range", "Volume Needed", "Your Fit"],
        [
            ["Premium/High-Ticket", "$1,000 - $10,000+", "5-20 clients",
             "1:1 coaching with AI tools, peptide protocols, full transformation packages"],
            ["Mass Market/Low-Ticket", "$9 - $49/month", "1,000+ subscribers",
             "App access, community membership, template library"],
            ["THE DEAD ZONE", "$100 - $500", "Too many for premium service, too few for profit",
             "AVOID THIS. Not enough margin, not enough volume."],
        ],
        col_widths=[1.3*inch, 1.2*inch, 1.1*inch, 2.9*inch]
    )
    story.append(price_table)
    story.append(Spacer(1, 10))

    story.append(Paragraph("<b>Hormozi's Pricing Ladder for New Businesses:</b>", s["h3"]))
    story.append(Spacer(1, 4))
    for n, text in enumerate([
        "Start with high-ticket 1:1 services (maximize learning + cash flow + proof)",
        "Use case studies and testimonials to justify premium pricing",
        "Raise price with every new client until people stop buying (that is your ceiling for now)",
        "THEN scale down with lower-ticket products funded by high-ticket cash flow (Tesla model)",
    ], 1):
        story.append(numbered(n, text, s))
    story.append(Spacer(1, 8))

    story.append(coach_note_box(
        "<b>For your $197/month coaching:</b> This is in the dead zone. Consider restructuring to $997-2,000 for a "
        "90-day transformation package (high-ticket) OR keeping $197 as the entry point into a $2,000+ upsell. "
        "The $197 alone will not build a sustainable business -- the math does not work unless you have 50+ clients.", s))
    story.append(PageBreak())

    # ==========================================================================
    # SECTION 7: LEAD MAGNETS
    # ==========================================================================
    story.append(section_title("7. LEAD MAGNETS -- Give Away Your Best Stuff", s))
    story.append(Spacer(1, 4))

    story.append(quote_box(
        "If your lead magnet is not good enough that people tell other people about it, you have failed. "
        "Give away your secrets. Sell the implementation.",
        "Alex Hormozi", s))
    story.append(Spacer(1, 10))

    story.append(Paragraph("<b>Core Philosophy:</b> The marketplace judges everything you offer -- free or paid. "
                           "Your free content should be SO good that people feel obligated to pay you. "
                           "The give-to-ask ratio should be approximately 3.5:1.", s["body"]))
    story.append(Spacer(1, 8))

    story.append(Paragraph("<b>Types of Lead Magnets (Best to Good):</b>", s["h3"]))
    story.append(Spacer(1, 4))

    lm_table = branded_table(
        ["Type", "What It Is", "Your Version"],
        [
            ["Software/Tools", "Calculators, spreadsheets, apps, templates",
             "Free AI body comp calculator, macro calculator, workout generator"],
            ["Information", "Courses, guides, expert content, checklists",
             "Peptide protocol guide, '30-Day Recomp Blueprint,' evidence-based training PDF"],
            ["Services", "Free audit, assessment, consultation, done-for-you sample",
             "Free body composition analysis, free fitness strategy call, free week of programming"],
            ["Physical Products", "Supplements, charts, assessment tools",
             "Printed meal prep guide, resistance band + program starter kit"],
        ],
        col_widths=[1.1*inch, 2.0*inch, 3.4*inch]
    )
    story.append(lm_table)
    story.append(Spacer(1, 10))

    story.append(Paragraph("<b>The Perfect Lead Magnet Formula:</b>", s["h3"]))
    story.append(Spacer(1, 4))
    for b in [
        "Solves a <b>narrow, specific problem</b> completely (not a broad topic poorly)",
        "Naturally leads to your <b>paid offer</b> as the logical next step",
        "Provides <b>immediate value</b> -- they can use it within minutes",
        "Is <b>shareable</b> -- so good that recipients tell others about it",
        "Demonstrates your <b>expertise</b> and methodology",
    ]:
        story.append(bullet(b, s))
    story.append(PageBreak())

    # ==========================================================================
    # SECTION 8: MARKET SELECTION
    # ==========================================================================
    story.append(section_title("8. MARKET SELECTION -- Finding Starving Crowds", s))
    story.append(Spacer(1, 4))

    story.append(Paragraph(
        "Hormozi's hierarchy of business success factors, in order of importance:", s["body"]))
    story.append(Spacer(1, 8))

    story.append(gold_box(
        '<b>Starving Crowd (Market) &gt; Offer Strength &gt; Persuasion Skills</b><br/><br/>'
        '"If there is a ton of demand for a solution, you can be mediocre at business, have a terrible offer, '
        'and have no ability to persuade people, and you can still make money."', s))
    story.append(Spacer(1, 10))

    story.append(Paragraph("<b>The Three Evergreen Markets:</b>", s["h3"]))
    story.append(Paragraph(
        "There are only three markets that will ALWAYS exist because there is always massive pain when you lack them:", s["body"]))
    story.append(Spacer(1, 4))

    market_table = branded_table(
        ["Market", "Core Pain", "Your Position"],
        [
            ["HEALTH", "How they look, feel, and perform physically",
             "STRONG FIT -- You are a certified trainer with AI tools, peptide knowledge, and evidence-based methods"],
            ["WEALTH", "Making more money, financial freedom",
             "MODERATE -- You build AI tools and could teach others, but not your primary positioning"],
            ["RELATIONSHIPS", "Feeling loved, connected, not alone",
             "WEAK -- Not your space"],
        ],
        col_widths=[1.0*inch, 2.0*inch, 3.5*inch]
    )
    story.append(market_table)
    story.append(Spacer(1, 10))

    story.append(Paragraph("<b>Four Indicators of a Winning Niche:</b>", s["h3"]))
    story.append(Spacer(1, 4))
    for b in [
        "<b>Massive Pain:</b> They are desperate for a solution (not just mildly interested)",
        "<b>Purchasing Power:</b> They can actually afford to pay you (target professionals, not broke college students)",
        "<b>Easy to Target:</b> You can find and reach them efficiently (specific job titles, communities, locations)",
        "<b>Growing Market:</b> The demand is increasing, not shrinking",
    ]:
        story.append(bullet(b, s))
    story.append(Spacer(1, 8))

    story.append(Paragraph("<b>Niching Down Formula:</b>", s["h3"]))
    story.append(Paragraph(
        '"I help [WHO] get [GOOD STUFF] without [BAD STUFF]"',
        ParagraphStyle("NicheFormula", parent=s["body_bold"], fontSize=12, leading=16,
                       textColor=BrandConfig.GOLD_DARK)))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        "Narrow by at least 3 identifiers: age, gender, profession, location, pain point, lifestyle. "
        "The more specific, the more you can charge and the less competition you face.", s["body"]))
    story.append(Spacer(1, 8))

    story.append(gold_box(
        '<b>Your niche statement examples:</b><br/>'
        '"I help busy professionals over 35 build their best physique without spending hours in the gym"<br/>'
        '"I help Naples executives lose 20+ lbs in 90 days without restrictive diets or 6am boot camps"<br/>'
        '"I help men 35-55 optimize their hormones and body composition using evidence-based protocols"', s))
    story.append(PageBreak())

    # ==========================================================================
    # SECTION 9: SKILLS VS PASSION VS MARKET
    # ==========================================================================
    story.append(section_title("9. SKILLS vs PASSION vs MARKET DEMAND", s))
    story.append(Spacer(1, 4))

    story.append(quote_box(
        "Find stuff people already buy and sell it. You can figure out passion and purpose after you learn the basics. "
        "Make a profit. Then get cute. But you may realize you are passionate about making a profit.",
        "Alex Hormozi", s))
    story.append(Spacer(1, 10))

    story.append(Paragraph("<b>Hormozi's Priority Order:</b>", s["h3"]))
    story.append(Spacer(1, 4))
    for n, text in enumerate([
        "<b>Market Demand FIRST</b> -- Is there a starving crowd willing to pay? If no demand exists, nothing else matters.",
        "<b>Skills SECOND</b> -- Can you actually deliver the result? Skills can be learned and hired for.",
        "<b>Passion THIRD</b> -- Do you enjoy it? Nice to have, but passion without demand = expensive hobby.",
    ], 1):
        story.append(numbered(n, text, s))
    story.append(Spacer(1, 10))

    story.append(Paragraph("<b>The Key Insight:</b>", s["h3"]))
    story.append(Paragraph(
        "We are not trying to CREATE demand. We are trying to CHANNEL it. "
        "People already want to lose weight, build muscle, look better, feel confident. "
        "Your job is to be the best vehicle for a desire that already exists.", s["body"]))
    story.append(Spacer(1, 8))

    story.append(Paragraph(
        '"There is a market in desperate need of your abilities. You need to find it. '
        'Do not be romantic about your audience. Serve the people who can pay you what you are worth."',
        ParagraphStyle("QuoteInline", parent=s["body"], textColor=BrandConfig.GOLD_DARK,
                       fontName=BrandConfig.BODY_FONT_BOLD)))
    story.append(Spacer(1, 10))

    story.append(Paragraph("<b>Applied to Your Situation:</b>", s["h3"]))
    story.append(Spacer(1, 4))

    skills_table = branded_table(
        ["What You Have", "Market Demand?", "Verdict"],
        [
            ["AI fitness tools (FitAI, workout generators, meal planners)",
             "HIGH -- every trainer wants automation, every client wants personalization",
             "SELL THIS as part of a premium coaching package"],
            ["Peptide/hormone optimization knowledge",
             "HIGH -- growing market, underserved by mainstream fitness",
             "SELL THIS as a differentiator within your coaching"],
            ["Evidence-based training methodology",
             "HIGH -- trust deficit in fitness industry, people want science",
             "SELL THIS as your credibility anchor"],
            ["Website building / AI development skills",
             "HIGH -- but crowded market with razor-thin margins",
             "USE THIS to build your own marketing, do not sell it yet"],
            ["1:1 coaching infrastructure (Trainerize, etc.)",
             "HIGH -- people pay for accountability and personal attention",
             "SELL THIS -- this is your primary revenue vehicle right now"],
        ],
        col_widths=[2.0*inch, 1.8*inch, 2.7*inch]
    )
    story.append(skills_table)
    story.append(PageBreak())

    # ==========================================================================
    # SECTION 10: GYM LAUNCH / FITNESS
    # ==========================================================================
    story.append(section_title("10. GYM LAUNCH & FITNESS BUSINESS STRATEGIES", s))
    story.append(Paragraph(
        "Hormozi built his empire starting from a single gym. He slept on the gym floor. "
        "Then he built Gym Launch, which helped 6,000+ gyms across 22 countries. Here is what he learned:", s["body"]))
    story.append(Spacer(1, 10))

    story.append(Paragraph("<b>Key Lesson 1: Acquisition Over Perfection</b>", s["h3"]))
    story.append(Paragraph(
        "Most fitness professionals focus too much on perfecting their service and not enough on getting clients. "
        "The fastest path to profitability is: generate leads, close sales, fill spots. "
        "You can refine the service WHILE getting paid. Do not wait until everything is perfect.", s["body"]))
    story.append(Spacer(1, 8))

    story.append(Paragraph("<b>Key Lesson 2: Accountability Over Access</b>", s["h3"]))
    story.append(Paragraph(
        "People do not pay for workouts -- they can get those free on YouTube. "
        "They pay for ACCOUNTABILITY. They pay you to pay attention to them, check in on them, "
        "hold them to their commitments. This is the real product.", s["body"]))
    story.append(Spacer(1, 8))

    story.append(Paragraph("<b>Key Lesson 3: The Challenge Model</b>", s["h3"]))
    story.append(Paragraph(
        "Hormozi's gyms used 6-week challenges as the front-end offer. Low barrier to entry, "
        "high perceived value, creates quick wins, and then ascends clients into long-term membership. "
        "The challenge solves the 'commitment fear' objection.", s["body"]))
    story.append(Spacer(1, 8))

    story.append(Paragraph("<b>Key Lesson 4: Speed-to-Lead</b>", s["h3"]))
    story.append(Paragraph(
        "When a lead comes in, the 5-step follow-up sequence:", s["body"]))
    story.append(Spacer(1, 4))
    for n, text in enumerate([
        "Call within 5 minutes (speed is everything)",
        "If no answer: text immediately",
        "Follow up with a value-based email including a testimonial",
        "Follow up again the next day",
        "Continue 5-touch sequence over 48 hours",
    ], 1):
        story.append(numbered(n, text, s))
    story.append(Spacer(1, 8))

    story.append(Paragraph("<b>Key Lesson 5: Solve Attrition Through Ascension</b>", s["h3"]))
    story.append(Paragraph(
        "Average gym loses 10% of members per month. Hormozi's solution: structured goal reviews, "
        "progress check-ins, community building, and always having a 'next step' for the client. "
        "Retention is cheaper than acquisition.", s["body"]))
    story.append(Spacer(1, 8))

    story.append(Paragraph("<b>Key Lesson 6: The Irresistible Offer in Fitness</b>", s["h3"]))
    story.append(Paragraph(
        "Gym Launch's average result: $28,000 in revenue in the first 30 days of implementation. "
        "The secret was NOT a better workout program. It was a better OFFER -- one that addressed "
        "every objection, stacked bonuses, included guarantees, and made it nearly impossible to say no.", s["body"]))
    story.append(PageBreak())

    # ==========================================================================
    # SECTION 11: STARTING IN 2026
    # ==========================================================================
    story.append(section_title("11. IF STARTING A BUSINESS IN 2026", s))
    story.append(Paragraph(
        "From Hormozi's recent podcast (Episode 977) -- his exact advice for starting from scratch today:", s["body"]))
    story.append(Spacer(1, 10))

    story.append(Paragraph("<b>Step 1: Start with Premium 1:1 Services</b>", s["h3"]))
    story.append(Paragraph(
        "Do not build a course. Do not build an app. Do not build a community. "
        "Sell your time for a premium rate, 1:1, doing an unscalable thing. This is the Tesla Roadster phase. "
        "Maximum learning, maximum cash flow, maximum proof, maximum marketing material.", s["body"]))
    story.append(Spacer(1, 8))

    story.append(Paragraph("<b>Step 2: Use the Money to Fund Experiments</b>", s["h3"]))
    story.append(Paragraph(
        "1:1 service revenue is the cleanest capital a founder can get. Zero cost of goods sold. "
        "After covering living costs, every additional dollar is pure profit to reinvest. "
        "This becomes risk-free capital to build scalable products.", s["body"]))
    story.append(Spacer(1, 8))

    story.append(Paragraph("<b>Step 3: Document Everything</b>", s["h3"]))
    story.append(Paragraph(
        "Every client interaction, every result, every testimonial, every lesson. "
        "This documentation becomes your content engine, your sales proof, and eventually your course/program curriculum.", s["body"]))
    story.append(Spacer(1, 8))

    story.append(Paragraph("<b>Step 4: Scale When You Have Proof</b>", s["h3"]))
    story.append(Paragraph(
        "Only AFTER you have proven results with 10-20 clients should you think about scaling. "
        "Then move from 1:1 to small group, then to one-to-many, then to digital products. "
        "Each stage is funded by the previous stage.", s["body"]))
    story.append(Spacer(1, 10))

    story.append(Paragraph("<b>The Scaling Ladder:</b>", s["h3"]))
    story.append(Spacer(1, 4))
    scale_table = branded_table(
        ["Stage", "Model", "Price", "Clients", "Revenue"],
        [
            ["1. Proof", "1:1 Premium", "$1,500-3,000", "5-10", "$7.5K-30K/mo"],
            ["2. Leverage", "Small Group (4-8)", "$500-1,000/mo", "20-40", "$10K-40K/mo"],
            ["3. Scale", "One-to-Many / Course", "$297-997", "100+", "$30K-100K/mo"],
            ["4. Productize", "App / SaaS / Community", "$29-99/mo", "1,000+", "$29K-99K/mo"],
        ],
        col_widths=[0.8*inch, 1.3*inch, 1.2*inch, 0.9*inch, 1.3*inch]
    )
    story.append(scale_table)
    story.append(PageBreak())

    # ==========================================================================
    # SECTION 12: YOUR ACTION PLAN
    # ==========================================================================
    story.append(section_title("12. APPLIED ACTION PLAN -- Your Situation", s))
    story.append(Spacer(1, 4))

    story.append(Paragraph(
        "You have AI tools, fitness coaching infrastructure, evidence-based knowledge, and zero paying clients. "
        "Here is the Hormozi-aligned plan to go from zero to revenue:", s["body"]))
    story.append(Spacer(1, 10))

    story.append(Paragraph("<b>WEEK 1-2: Offer Construction</b>", s["h3"]))
    story.append(Spacer(1, 4))
    for b in [
        "Define your Grand Slam Offer using the framework in Section 2",
        "Pick ONE niche (recommendation: men 35-55 who want body recomp without living in the gym)",
        "Price it at $997-1,500 for a 90-day transformation (NOT $197/month)",
        "Include: 1:1 coaching, AI-powered programming, nutrition plan, weekly check-ins, peptide guidance",
        "Add guarantee: 'Lose 15 lbs in 90 days or I keep working with you free until you do'",
        "Name it using M.A.G.I.C. formula",
    ]:
        story.append(bullet(b, s))
    story.append(Spacer(1, 8))

    story.append(Paragraph("<b>WEEK 2-4: First 5 Clients (Free/Discounted)</b>", s["h3"]))
    story.append(Spacer(1, 4))
    for b in [
        "Export every contact from phone, Instagram, Facebook, LinkedIn",
        "Send 100 personalized messages per day using the Magic Script (Section 5, Step 5)",
        "Offer 5 FREE case study spots -- 'I built an AI-powered coaching system and I need 5 people to test it'",
        "Over-deliver massively. Get before/after photos. Get video testimonials.",
        "Document every single thing for content",
    ]:
        story.append(bullet(b, s))
    story.append(Spacer(1, 8))

    story.append(Paragraph("<b>WEEK 4-8: Monetize + Scale Outreach</b>", s["h3"]))
    story.append(Spacer(1, 4))
    for b in [
        "Use case study results to sell next batch at $497 (50% of full price)",
        "Add cold outreach: 100 cold DMs per day to fitness-interested profiles",
        "Start posting content daily -- transformation stories, tips, peptide education",
        "Ask every client for 2 referrals",
        "Build a lead magnet: free AI body composition assessment or macro calculator",
    ]:
        story.append(bullet(b, s))
    story.append(Spacer(1, 8))

    story.append(Paragraph("<b>MONTH 3-6: Full Price + Systems</b>", s["h3"]))
    story.append(Spacer(1, 4))
    for b in [
        "Raise to full price ($997-1,500) with proof from first 10-15 clients",
        "Consider running paid ads (reinvest first revenue -- client-financed acquisition)",
        "Build a small group program as the next tier",
        "Create a challenge (6-week body recomp challenge) as a front-end offer",
        "Target: 10 clients at $997 = $9,970/month",
    ]:
        story.append(bullet(b, s))
    story.append(Spacer(1, 10))

    # Final emphasis box
    final_data = [[Paragraph(
        '<b>THE SINGLE MOST IMPORTANT THING:</b><br/><br/>'
        'Stop building. Start selling. You have more than enough infrastructure. '
        'The bottleneck is not your tools, your app, your website, or your systems. '
        'The bottleneck is that nobody knows you exist. Fix that with volume.<br/><br/>'
        '<b>100 reach-outs per day. Starting tomorrow. No excuses.</b>',
        ParagraphStyle("FinalBox", parent=s["body"], fontSize=11, leading=16,
                       textColor=BrandConfig.CHARCOAL))]]
    ft2 = Table(final_data, colWidths=[6.5*inch])
    ft2.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BrandConfig.GOLD_BG),
        ("BOX", (0, 0), (-1, -1), 3, BrandConfig.GOLD),
        ("TOPPADDING", (0, 0), (-1, -1), 16),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 16),
        ("LEFTPADDING", (0, 0), (-1, -1), 16),
        ("RIGHTPADDING", (0, 0), (-1, -1), 16),
    ]))
    story.append(ft2)
    story.append(Spacer(1, 16))

    story.append(Paragraph(
        "<b>Sources:</b> $100M Offers (Alex Hormozi), $100M Leads (Alex Hormozi), "
        "Gym Launch Secrets (Alex Hormozi), The Game Podcast Ep 977, "
        "Acquisition.com training materials, various YouTube and podcast appearances.",
        s["small"]))

    doc.build(story, onFirstPage=_on_page, onLaterPages=_on_page)
    print(f"PDF generated: {OUTPUT}")


if __name__ == "__main__":
    build()
