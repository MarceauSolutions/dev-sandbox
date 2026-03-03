"""Generic Document PDF Template — renders markdown content with brand wrapper."""

import sys
import re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from reportlab.lib.units import inch
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Spacer, Paragraph

from branded_pdf_engine import (
    register_template, BrandConfig, get_brand_styles,
    section_title, accent_line, bullet_list
)


def _markdown_to_flowables(md_text: str, styles: dict):
    """Convert basic markdown to ReportLab flowables."""
    flowables = []
    lines = md_text.split("\n")
    current_list = []

    for line in lines:
        stripped = line.strip()

        # Empty line — flush list
        if not stripped:
            if current_list:
                flowables.extend(bullet_list(current_list, styles))
                current_list = []
            flowables.append(Spacer(1, 6))
            continue

        # Headers
        if stripped.startswith("### "):
            if current_list:
                flowables.extend(bullet_list(current_list, styles))
                current_list = []
            flowables.append(Paragraph(stripped[4:], styles["h3"]))
            continue
        if stripped.startswith("## "):
            if current_list:
                flowables.extend(bullet_list(current_list, styles))
                current_list = []
            flowables.append(section_title(stripped[3:], styles))
            continue
        if stripped.startswith("# "):
            if current_list:
                flowables.extend(bullet_list(current_list, styles))
                current_list = []
            flowables.append(Paragraph(stripped[2:], styles["h2"]))
            continue

        # Horizontal rule
        if stripped in ("---", "***", "___"):
            if current_list:
                flowables.extend(bullet_list(current_list, styles))
                current_list = []
            flowables.append(accent_line())
            continue

        # Bullet list
        if stripped.startswith("- ") or stripped.startswith("* "):
            current_list.append(stripped[2:])
            continue

        # Numbered list
        if re.match(r"^\d+\.\s", stripped):
            text = re.sub(r"^\d+\.\s", "", stripped)
            current_list.append(text)
            continue

        # Bold/italic inline
        text = stripped
        text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
        text = re.sub(r"\*(.+?)\*", r"<i>\1</i>", text)
        text = re.sub(r"`(.+?)`", r'<font face="Courier">\1</font>', text)

        if current_list:
            flowables.extend(bullet_list(current_list, styles))
            current_list = []

        flowables.append(Paragraph(text, styles["body"]))

    if current_list:
        flowables.extend(bullet_list(current_list, styles))

    return flowables


@register_template("generic_document")
def render_generic(data: dict, styles: dict):
    story = []

    # Title
    story.append(Spacer(1, 0.3 * inch))
    story.append(Paragraph(data.get("title", "Document"), styles["title"]))
    if data.get("subtitle"):
        story.append(Paragraph(data["subtitle"], styles["subtitle"]))

    author = data.get("author", "William Marceau")
    date = data.get("date", "")
    if author or date:
        meta = " | ".join(filter(None, [author, date]))
        story.append(Paragraph(meta, styles["small"]))
    story.append(Spacer(1, 12))

    # Content
    content = data.get("content_markdown", "")
    if content:
        story.extend(_markdown_to_flowables(content, styles))

    return story
