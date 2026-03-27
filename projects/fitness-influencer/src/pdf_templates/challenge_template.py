"""Challenge Workout PDF Template."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from reportlab.lib.units import inch
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Spacer, Paragraph, Table, TableStyle

from branded_pdf_engine import (
    register_template, BrandConfig, get_brand_styles,
    section_title, coach_note_box, branded_table, bullet_list, HexColor
)


@register_template("challenge_workout")
def render_challenge(data: dict, styles: dict):
    story = []

    # Title
    story.append(Spacer(1, 0.3 * inch))
    story.append(Paragraph(
        data.get("challenge_name", "7-Day Body Recomp Challenge"), styles["title"]
    ))
    story.append(Paragraph(
        f'{data.get("duration_days", 7)} Days | '
        f'{data.get("difficulty", "Beginner")} | '
        f'{data.get("equipment_needed", "Bodyweight")}',
        styles["subtitle"]
    ))

    # Coach note
    if data.get("coach_note"):
        story.append(coach_note_box(data["coach_note"], styles))
        story.append(Spacer(1, 12))

    # Rules
    rules = data.get("rules", [])
    if rules:
        story.append(section_title("Challenge Rules", styles))
        story.extend(bullet_list(rules, styles))
        story.append(Spacer(1, 12))

    # Daily workouts
    for day in data.get("days", []):
        day_num = day.get("day_number", 0)
        title = day.get("title", f"Day {day_num}")

        story.append(section_title(f"Day {day_num}: {title}", styles))

        # Motivational quote
        quote = day.get("motivation_quote")
        if quote:
            quote_data = [[Paragraph(f'<i>"{quote}"</i>', ParagraphStyle(
                "Quote", fontName=BrandConfig.BODY_FONT,
                fontSize=10, textColor=BrandConfig.GOLD_DARK,
                leading=14,
            ))]]
            qt = Table(quote_data, colWidths=[6.5 * inch])
            qt.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), BrandConfig.GOLD_BG),
                ("LEFTPADDING", (0, 0), (-1, -1), 12),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]))
            story.append(qt)
            story.append(Spacer(1, 6))

        # Exercises
        exercises = day.get("exercises", [])
        if exercises:
            headers = ["Exercise", "Sets", "Reps", "Rest"]
            rows = []
            for ex in exercises:
                rows.append([
                    ex.get("name", ""),
                    str(ex.get("sets", 3)),
                    str(ex.get("reps", "10-12")),
                    f'{ex.get("rest_seconds", 60)}s',
                ])
            story.append(branded_table(
                headers, rows,
                col_widths=[2.8 * inch, 0.8 * inch, 1.2 * inch, 1.0 * inch]
            ))

        # Tip
        tip = day.get("tip")
        if tip:
            story.append(Spacer(1, 6))
            tip_data = [[Paragraph(f'<b>Tip:</b> {tip}', styles["body"])]]
            tt = Table(tip_data, colWidths=[6.5 * inch])
            tt.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), BrandConfig.LIGHT_GRAY),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]))
            story.append(tt)

        story.append(Spacer(1, 16))

    return story
