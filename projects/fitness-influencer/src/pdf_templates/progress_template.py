"""Progress Report PDF Template."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from reportlab.lib.units import inch
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Spacer, Paragraph, Table, TableStyle

from branded_pdf_engine import (
    register_template, BrandConfig, get_brand_styles,
    section_title, coach_note_box, branded_table, metric_card, bullet_list, HexColor
)


@register_template("progress_report")
def render_progress(data: dict, styles: dict):
    story = []

    # Title
    story.append(Spacer(1, 0.3 * inch))
    story.append(Paragraph("Progress Report", styles["title"]))
    story.append(Paragraph(
        f'<b>{data.get("client_name", "Client")}</b> — {data.get("report_period", "")}',
        styles["subtitle"]
    ))

    # Coach note
    if data.get("coach_note"):
        story.append(coach_note_box(data["coach_note"], styles))
        story.append(Spacer(1, 12))

    # Adherence metric card
    adherence = data.get("adherence_pct", 0)
    adherence_color = BrandConfig.GREEN if adherence >= 80 else (BrandConfig.AMBER if adherence >= 60 else BrandConfig.RED)

    # Body metrics history
    metrics = data.get("metrics_history", [])
    if metrics:
        story.append(section_title("Body Composition", styles))

        # Summary cards: first vs last
        if len(metrics) >= 2:
            first, last = metrics[0], metrics[-1]
            weight_change = last.get("weight_lbs", 0) - first.get("weight_lbs", 0)
            sign = "+" if weight_change > 0 else ""
            cards = [
                metric_card("Start Weight", f'{first.get("weight_lbs", 0)} lbs'),
                metric_card("Current Weight", f'{last.get("weight_lbs", 0)} lbs'),
                metric_card("Change", f'{sign}{weight_change:.1f} lbs',
                            BrandConfig.GREEN if weight_change <= 0 else BrandConfig.AMBER),
                metric_card("Adherence", f'{adherence:.0f}%', adherence_color),
            ]
            row = Table([cards], colWidths=[1.6 * inch] * 4)
            row.setStyle(TableStyle([
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]))
            story.append(row)
            story.append(Spacer(1, 12))

        # History table
        headers = ["Date", "Weight (lbs)", "Body Fat %"]
        rows = []
        for m in metrics:
            rows.append([
                m.get("date", ""),
                f'{m.get("weight_lbs", 0):.1f}',
                f'{m.get("body_fat_pct", 0):.1f}%' if m.get("body_fat_pct") else "—",
            ])
        story.append(branded_table(headers, rows,
                                    col_widths=[2.0 * inch, 2.0 * inch, 2.5 * inch]))
        story.append(Spacer(1, 16))

    # Strength gains
    gains = data.get("strength_gains", [])
    if gains:
        story.append(section_title("Strength Progress", styles))
        headers = ["Exercise", "Previous", "Current", "Change"]
        rows = []
        for g in gains:
            pct = g.get("change_pct", 0)
            color = "#C9963C" if pct > 0 else ("#ef4444" if pct < 0 else "#64748b")
            sign = "+" if pct > 0 else ""
            change_text = f'<font color="{color}"><b>{sign}{pct:.1f}%</b></font>'
            rows.append([
                g.get("exercise", ""),
                g.get("previous", ""),
                g.get("current", ""),
                Paragraph(change_text, styles["body"]),
            ])
        story.append(branded_table(headers, rows,
                                    col_widths=[2.2 * inch, 1.4 * inch, 1.4 * inch, 1.5 * inch]))
        story.append(Spacer(1, 16))

    # Highlights
    highlights = data.get("highlights", [])
    if highlights:
        story.append(section_title("Highlights", styles))
        story.extend(bullet_list(highlights, styles))
        story.append(Spacer(1, 12))

    # Areas to improve
    areas = data.get("areas_to_improve", [])
    if areas:
        story.append(section_title("Focus Areas", styles))
        story.extend(bullet_list(areas, styles))
        story.append(Spacer(1, 12))

    # Next phase
    if data.get("next_phase"):
        story.append(section_title("What's Next", styles))
        story.append(Paragraph(data["next_phase"], styles["body"]))

    return story
