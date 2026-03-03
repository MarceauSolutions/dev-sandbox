"""Nutrition Guide PDF Template."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from reportlab.lib.units import inch
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import Spacer, Paragraph, Table, TableStyle

from branded_pdf_engine import (
    register_template, BrandConfig, get_brand_styles,
    section_title, coach_note_box, branded_table, metric_card, bullet_list, HexColor
)


@register_template("nutrition_guide")
def render_nutrition(data: dict, styles: dict):
    story = []

    # Title
    story.append(Spacer(1, 0.3 * inch))
    story.append(Paragraph("Nutrition Guide", styles["title"]))
    story.append(Paragraph(
        f'Prepared for <b>{data.get("client_name", "Client")}</b>',
        styles["subtitle"]
    ))

    if data.get("goal"):
        story.append(Paragraph(f"<b>Goal:</b> {data['goal']}", styles["body"]))
    if data.get("weight_lbs"):
        story.append(Paragraph(f"<b>Current Weight:</b> {data['weight_lbs']} lbs", styles["body"]))
    story.append(Spacer(1, 12))

    # Coach note
    if data.get("coach_note"):
        story.append(coach_note_box(data["coach_note"], styles))
        story.append(Spacer(1, 12))

    # Daily macro targets — metric cards in a row
    targets = data.get("daily_targets", {})
    if targets:
        story.append(section_title("Daily Macro Targets", styles))
        cards = [
            metric_card("Calories", str(targets.get("calories", 0)), BrandConfig.GOLD),
            metric_card("Protein", f'{targets.get("protein_g", 0)}g', BrandConfig.CHARCOAL),
            metric_card("Carbs", f'{targets.get("carbs_g", 0)}g', BrandConfig.GOLD_DARK),
            metric_card("Fat", f'{targets.get("fats_g", 0)}g', BrandConfig.DARK_GRAY),
        ]
        row = Table([cards], colWidths=[1.6 * inch] * 4)
        row.setStyle(TableStyle([
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        story.append(row)
        story.append(Spacer(1, 16))

    # Meal plan
    meal_plan = data.get("meal_plan", [])
    if meal_plan:
        story.append(section_title("Daily Meal Plan", styles))
        for meal in meal_plan:
            title_parts = [meal.get("meal_name", "Meal")]
            if meal.get("time"):
                title_parts.append(f'({meal["time"]})')
            story.append(Paragraph(" ".join(title_parts), styles["h3"]))

            foods = meal.get("foods", [])
            story.extend(bullet_list(foods, styles))

            macros = meal.get("macros")
            if macros:
                macro_text = (f'<i>{macros.get("calories", 0)} cal | '
                              f'{macros.get("protein_g", 0)}P | '
                              f'{macros.get("carbs_g", 0)}C | '
                              f'{macros.get("fats_g", 0)}F</i>')
                story.append(Paragraph(macro_text, styles["small"]))
            story.append(Spacer(1, 8))

    # Food lists
    food_lists = data.get("food_lists")
    if food_lists:
        story.append(section_title("Recommended Foods", styles))
        for category, foods in food_lists.items():
            label = category.replace("_", " ").title()
            story.append(Paragraph(f"<b>{label}</b>", styles["body_bold"]))
            story.append(Paragraph(", ".join(foods), styles["body"]))
            story.append(Spacer(1, 6))
        story.append(Spacer(1, 8))

    # Supplements
    supplements = data.get("supplements")
    if supplements:
        story.append(section_title("Supplements", styles))
        for tier, items in supplements.items():
            label = tier.replace("_", " ").title()
            story.append(Paragraph(f"<b>{label}</b>", styles["body_bold"]))
            story.extend(bullet_list(items, styles))
            story.append(Spacer(1, 6))
        story.append(Spacer(1, 8))

    # Hydration
    if data.get("hydration_oz"):
        story.append(section_title("Hydration", styles))
        story.append(Paragraph(
            f"Aim for <b>{data['hydration_oz']} oz</b> of water daily. "
            "Increase by 16-24 oz on training days.",
            styles["body"]
        ))
        story.append(Spacer(1, 12))

    # Tips
    tips = data.get("tips", [])
    if tips:
        story.append(section_title("Tips for Success", styles))
        story.extend(bullet_list(tips, styles))

    return story
