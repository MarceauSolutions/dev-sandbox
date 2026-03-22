#!/usr/bin/env python3
"""
One-time script: Generate a reassuring document for Angela Marceau
and email it as a PDF attachment.
"""

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether
)

load_dotenv()

# --- Brand colors ---
GOLD = HexColor("#C9963C")
GOLD_BG = HexColor("#FDF8EF")
CHARCOAL = HexColor("#333333")
WHITE = HexColor("#FFFFFF")
LIGHT_GRAY = HexColor("#F5F5F5")

OUTPUT_PATH = Path(__file__).parent.parent / "outputs" / "letter-for-mom.pdf"


def build_pdf():
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(OUTPUT_PATH),
        pagesize=letter,
        leftMargin=0.85 * inch,
        rightMargin=0.85 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "DocTitle", parent=styles["Title"],
        fontSize=22, textColor=CHARCOAL, spaceAfter=6,
        alignment=TA_CENTER, fontName="Helvetica-Bold",
    )
    subtitle_style = ParagraphStyle(
        "DocSubtitle", parent=styles["Normal"],
        fontSize=12, textColor=GOLD, spaceAfter=20,
        alignment=TA_CENTER, fontName="Helvetica-Oblique",
    )
    section_style = ParagraphStyle(
        "SectionHead", parent=styles["Heading2"],
        fontSize=14, textColor=GOLD, spaceBefore=18, spaceAfter=8,
        fontName="Helvetica-Bold", borderPadding=(0, 0, 4, 0),
    )
    body_style = ParagraphStyle(
        "BodyText2", parent=styles["Normal"],
        fontSize=11, textColor=CHARCOAL, leading=16,
        alignment=TA_JUSTIFY, spaceAfter=8,
        fontName="Helvetica",
    )
    bullet_style = ParagraphStyle(
        "BulletItem", parent=body_style,
        leftIndent=24, bulletIndent=12, spaceAfter=5,
        bulletFontSize=11, bulletColor=GOLD,
    )
    callout_style = ParagraphStyle(
        "Callout", parent=body_style,
        fontSize=11, textColor=CHARCOAL, leading=16,
        backColor=GOLD_BG, borderPadding=(12, 12, 12, 12),
        borderWidth=1, borderColor=GOLD, borderRadius=4,
        spaceAfter=14, spaceBefore=8,
    )
    closing_style = ParagraphStyle(
        "Closing", parent=body_style,
        fontSize=12, textColor=CHARCOAL, leading=18,
        alignment=TA_LEFT, fontName="Helvetica-Oblique",
        spaceBefore=16,
    )
    footer_style = ParagraphStyle(
        "Footer", parent=styles["Normal"],
        fontSize=9, textColor=HexColor("#999999"),
        alignment=TA_CENTER, spaceBefore=30,
    )

    story = []

    # --- Header ---
    story.append(Paragraph("How You Can Help William Right Now", title_style))
    story.append(Paragraph("A Practical Guide for Mom — March 2026", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=2, color=GOLD, spaceAfter=16))

    # --- Opening ---
    story.append(Paragraph(
        "Mom,", body_style
    ))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        "I know you worry. That's what moms do — and I'm grateful you care enough to worry. "
        "But I want you to see what I see: I'm not struggling without a plan. I have a very clear plan, "
        "I'm executing on it every single day, and things are genuinely moving in the right direction. "
        "This document lays out exactly where I am, where I'm headed, and the specific ways you can help "
        "that will make the biggest difference.",
        body_style
    ))

    # --- Section: Where I Am Right Now ---
    story.append(Paragraph("Where I Am Right Now", section_style))
    story.append(Paragraph(
        "Yes, I'm living in a camper on the side of your house. That's a temporary situation — not a permanent one. "
        "Here's what's actually happening beneath the surface:",
        body_style
    ))

    items = [
        ("<b>New job secured.</b> I start as an Electrical Technician with Collier County Wastewater "
         "on <b>April 6, 2026</b>. That's a stable government position — benefits, consistent schedule "
         "(7 AM – 3 PM weekdays), and a paycheck I can count on."),
        ("<b>My business is real and growing.</b> Marceau Solutions isn't a dream on paper — it's an active "
         "company with built infrastructure, real tools, and active client outreach. I'm running a focused "
         "sprint right now (March 23 – April 5) to land my first AI automation client before the job starts."),
        ("<b>My medical situation is managed.</b> My dystonia is currently controlled with clonazepam "
         "(prescribed, 0.5 mg twice daily). I'm sleeping, the pain is manageable, and I'm functional. "
         "This is the best my condition has been managed in years."),
        ("<b>I'm not winging it.</b> I have documented systems, structured daily routines, accountability "
         "workflows, and AI tools I built myself to keep me on track — even on hard days."),
    ]
    for item in items:
        story.append(Paragraph(item, bullet_style, bulletText="●"))

    # --- Section: What I Need From You ---
    story.append(Paragraph("What I Need From You (And What Actually Helps)", section_style))
    story.append(Paragraph(
        "You want to help — and I want to let you. Here are the specific things that make the "
        "biggest positive impact:",
        body_style
    ))

    # Sub-items with gold bullets
    helps = [
        ("<b>Believe in the plan.</b>",
         "When you express doubt or panic, it doesn't motivate me — it drains energy I need for execution. "
         "The single most powerful thing you can do is say: <i>\"I see you working hard. I believe in you.\"</i> "
         "That costs nothing and gives me everything."),
        ("<b>Give me space to work.</b>",
         "My business requires deep focus — writing code, building systems, doing outreach. "
         "Interruptions during work blocks (especially mornings 9 AM – 12 PM) break my flow and cost real productivity. "
         "If the camper door is closed, I'm working."),
        ("<b>Don't compare my timeline to others.</b>",
         "I had brain surgery at 17. I live with a chronic neurological condition. I medically withdrew from a "
         "master's program because doctors mismanaged my medication. My path doesn't look like other people's "
         "paths — and that's okay. I'm building something real on my own terms."),
        ("<b>Help with the basics when you can.</b>",
         "A home-cooked meal, helping with laundry, a grocery run — these small acts free up hours of my time "
         "for the work that will get me out of the camper. Practical help > emotional worry."),
        ("<b>Be a sounding board, not a critic.</b>",
         "When I share what I'm building, I'm not asking for validation or criticism — I'm sharing because you're "
         "my mom and I want you involved. Ask questions. Be curious. <i>\"Tell me more about that\"</i> "
         "is always better than <i>\"But what if it doesn't work?\"</i>"),
        ("<b>Trust my medical decisions.</b>",
         "I've been through 40+ medications, DBS surgery, and a medical withdrawal. I know my body and my condition "
         "better than anyone. My current treatment plan is working. Please don't suggest new treatments, "
         "supplements, or doctors unless I ask."),
    ]
    for title, detail in helps:
        story.append(Paragraph(title, bullet_style, bulletText="●"))
        story.append(Paragraph(detail, ParagraphStyle(
            "SubDetail", parent=body_style, leftIndent=36, spaceAfter=10, fontSize=10.5,
        )))

    # --- Section: What NOT To Do ---
    story.append(Paragraph("What Doesn't Help (Even Though You Mean Well)", section_style))

    donts = [
        "<b>Panicking or catastrophizing.</b> I need calm, steady support — not crisis energy. Things are hard, "
        "but they're not falling apart.",
        "<b>Suggesting I \"just get a regular job and forget the business.\"</b> I AM getting a regular job — "
        "AND building a business. They're not mutually exclusive. The job provides stability while the business grows.",
        "<b>Hovering or checking in constantly.</b> A daily \"how are you doing?\" is great. Checking in every "
        "few hours or asking if I've eaten/slept/worked out creates pressure, not support.",
        "<b>Talking to others about my situation in a worried tone.</b> When family and friends hear worry, "
        "they reflect it back. That creates a cycle of concern that doesn't match reality.",
    ]
    for item in donts:
        story.append(Paragraph(item, bullet_style, bulletText="✕"))

    # --- Callout box ---
    story.append(Paragraph(
        "<b>The big picture:</b> In 3 months, I'll have a stable paycheck, a growing side business, "
        "and enough saved to move into my own place. The camper is a launchpad, not a destination. "
        "Every day I'm in it, I'm working toward getting out of it.",
        callout_style
    ))

    # --- Section: The Concrete Plan ---
    story.append(Paragraph("The Concrete Plan (So You Can See It's Real)", section_style))

    # Timeline table
    timeline_data = [
        ["Timeline", "What's Happening"],
        ["Now – April 5", "AI client acquisition sprint. Active outreach to businesses.\n"
         "Building portfolio, filming content, booking discovery calls."],
        ["April 6", "First day at Collier County. Orientation + onboarding."],
        ["April – June", "Work 7–3, business development evenings & weekends.\n"
         "Training at 3 PM daily (non-negotiable for dystonia management)."],
        ["By July", "First full paycheck cycle. Savings building.\n"
         "Business revenue supplementing income."],
        ["By September", "Target: move into own apartment/rental.\n"
         "Business established with recurring clients."],
    ]
    table = Table(timeline_data, colWidths=[1.5 * inch, 4.8 * inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), GOLD),
        ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('TEXTCOLOR', (0, 1), (-1, -1), CHARCOAL),
        ('BACKGROUND', (0, 1), (-1, -1), LIGHT_GRAY),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, LIGHT_GRAY]),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor("#DDDDDD")),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(table)
    story.append(Spacer(1, 14))

    # --- Section: About My Health ---
    story.append(Paragraph("About My Health — What You Should Know", section_style))
    story.append(Paragraph(
        "I know my dystonia scares you. Here's where things actually stand:",
        body_style
    ))
    health_items = [
        "<b>The pain is managed.</b> Clonazepam controls both the muscle tone and the pain. "
        "I'm sleeping through the night. I'm functional during the day.",
        "<b>I exercise daily.</b> Strength training at 3 PM is part of my treatment protocol — "
        "it reduces spasticity, improves mood, and keeps me physically capable.",
        "<b>I monitor it.</b> I have automated research alerts tracking the latest dystonia "
        "treatments and clinical trials. I'm not ignoring it — I'm managing it proactively.",
        "<b>Bad days happen.</b> Some days the pain is worse. On those days, I adjust — "
        "lighter workload, more rest, modified training. That's not failure, that's management.",
    ]
    for item in health_items:
        story.append(Paragraph(item, bullet_style, bulletText="●"))

    # --- Closing ---
    story.append(HRFlowable(width="100%", thickness=1, color=GOLD, spaceBefore=20, spaceAfter=12))
    story.append(Paragraph(
        "Mom — I love you. I know this situation isn't what either of us imagined. "
        "But I need you to see the trajectory, not just the snapshot. I'm not stuck. "
        "I'm launching. And having you in my corner — calm, supportive, believing in me — "
        "is the most valuable thing you can give me right now.",
        closing_style
    ))
    story.append(Spacer(1, 12))
    story.append(Paragraph(
        "Love,<br/>William",
        ParagraphStyle("SignOff", parent=body_style, fontSize=13, fontName="Helvetica-Bold"),
    ))
    story.append(Paragraph(
        f"Generated {datetime.now().strftime('%B %d, %Y')}",
        footer_style
    ))

    doc.build(story)
    print(f"PDF created: {OUTPUT_PATH}")
    return OUTPUT_PATH


def send_email(pdf_path):
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USERNAME")
    smtp_pass = os.getenv("SMTP_PASSWORD")
    sender_email = smtp_user

    msg = MIMEMultipart()
    msg["Subject"] = "From William — Please Read This"
    msg["From"] = f"William Marceau <{sender_email}>"
    msg["To"] = "angelamarceau2@gmail.com"

    body = MIMEText(
        "Hi Mom,\n\n"
        "I put together a document for you that explains where I am, where I'm headed, "
        "and the best ways you can support me right now. Please read it when you have a quiet moment.\n\n"
        "I love you.\n\n"
        "— William",
        "plain"
    )
    msg.attach(body)

    with open(pdf_path, "rb") as f:
        attachment = MIMEApplication(f.read(), _subtype="pdf")
        attachment.add_header("Content-Disposition", "attachment", filename="How-You-Can-Help-William.pdf")
        msg.attach(attachment)

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.send_message(msg)

    print(f"Email sent to angelamarceau2@gmail.com")


if __name__ == "__main__":
    pdf = build_pdf()
    send_email(pdf)
