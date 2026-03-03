"""Workout Program PDF Template."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from reportlab.lib.units import inch
from reportlab.platypus import Spacer, KeepTogether, Paragraph, PageBreak
from reportlab.lib.styles import ParagraphStyle

from branded_pdf_engine import (
    register_template, BrandConfig, get_brand_styles,
    section_title, accent_line, coach_note_box, branded_table, bullet_list
)


MUSCLE_COLORS = {
    "chest": "#ef4444", "back": "#3b82f6", "shoulders": "#8b5cf6",
    "legs": "#f59e0b", "arms": "#C9963C", "core": "#06b6d4",
    "full body": "#ec4899", "push": "#ef4444", "pull": "#3b82f6",
    "upper": "#8b5cf6", "lower": "#f59e0b",
}


@register_template("workout_program")
def render_workout(data: dict, styles: dict):
    story = []

    # Title page
    story.append(Spacer(1, 0.5 * inch))
    story.append(Paragraph(data.get("program_name", "Training Program"), styles["title"]))
    story.append(Paragraph(
        f'Prepared for <b>{data.get("client_name", "Client")}</b>',
        styles["subtitle"]
    ))

    # Program details
    details = []
    for key, label in [("goal", "Goal"), ("experience_level", "Experience"),
                        ("equipment", "Equipment"), ("days_per_week", "Days/Week"),
                        ("start_date", "Start Date")]:
        val = data.get(key)
        if val:
            details.append(f"<b>{label}:</b> {val}")
    if details:
        story.append(Paragraph(" &nbsp;&bull;&nbsp; ".join(details), styles["body"]))
    story.append(Spacer(1, 12))

    # Coach note
    if data.get("coach_note"):
        story.append(coach_note_box(data["coach_note"], styles))
        story.append(Spacer(1, 12))

    # Program notes
    notes = data.get("program_notes")
    if notes:
        story.append(section_title("Program Notes", styles))
        for key, val in notes.items():
            story.append(Paragraph(f"<b>{key.replace('_', ' ').title()}:</b> {val}", styles["body"]))
            story.append(Spacer(1, 4))
        story.append(Spacer(1, 8))

    # Workout days
    for day in data.get("schedule", []):
        focus = day.get("focus", "")
        color_key = focus.lower().split("/")[0].split("&")[0].strip()
        focus_color = MUSCLE_COLORS.get(color_key, "#333333")

        day_label = day.get("day_name") or "Day " + str(day.get("day_number", ""))
        day_title = f'{day_label} — <font color="{focus_color}">{focus}</font>'
        story.append(section_title(day_title, styles))

        if day.get("warmup"):
            story.append(Paragraph(f"<b>Warm-up:</b> {day['warmup']}", styles["body"]))
            story.append(Spacer(1, 6))

        # Exercise table
        exercises = day.get("exercises", [])
        if exercises:
            headers = ["Exercise", "Sets", "Reps", "Rest", "Notes"]
            rows = []
            for ex in exercises:
                rows.append([
                    ex.get("name", ""),
                    str(ex.get("sets", 3)),
                    str(ex.get("reps", "8-12")),
                    f'{ex.get("rest_seconds", 90)}s',
                    ex.get("notes", ""),
                ])
            story.append(branded_table(
                headers, rows,
                col_widths=[2.2 * inch, 0.6 * inch, 0.8 * inch, 0.6 * inch, 2.3 * inch]
            ))

        if day.get("cooldown"):
            story.append(Spacer(1, 6))
            story.append(Paragraph(f"<b>Cool-down:</b> {day['cooldown']}", styles["body"]))

        story.append(Spacer(1, 16))

    return story
