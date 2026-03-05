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
    section_title, accent_line, bullet_list, branded_table
)


def _inline_fmt(text: str) -> str:
    """Apply bold, italic, and code inline formatting."""
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"\*(.+?)\*", r"<i>\1</i>", text)
    text = re.sub(r"`(.+?)`", r'<font face="Courier">\1</font>', text)
    return text


def _parse_md_table(lines: list, start: int):
    """Parse a markdown table starting at `start`. Returns (rows, end_index).
    Each row is a list of cell strings. The separator row is skipped."""
    rows = []
    i = start
    while i < len(lines):
        stripped = lines[i].strip()
        if not stripped.startswith("|"):
            break
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        # Skip separator row (e.g. |---|---|)
        if all(re.match(r"^[-:]+$", c) for c in cells):
            i += 1
            continue
        rows.append([_inline_fmt(c) for c in cells])
        i += 1
    return rows, i


def _markdown_to_flowables(md_text: str, styles: dict):
    """Convert basic markdown to ReportLab flowables."""
    flowables = []
    lines = md_text.split("\n")
    current_list = []
    i = 0

    while i < len(lines):
        stripped = lines[i].strip()

        # Empty line — flush list
        if not stripped:
            if current_list:
                flowables.extend(bullet_list([_inline_fmt(t) for t in current_list], styles))
                current_list = []
            flowables.append(Spacer(1, 6))
            i += 1
            continue

        # Markdown table
        if stripped.startswith("|"):
            if current_list:
                flowables.extend(bullet_list([_inline_fmt(t) for t in current_list], styles))
                current_list = []
            rows, i = _parse_md_table(lines, i)
            if rows:
                headers = rows[0]
                data_rows = rows[1:] if len(rows) > 1 else []
                flowables.append(branded_table(headers, data_rows))
                flowables.append(Spacer(1, 6))
            continue

        # Headers
        if stripped.startswith("### "):
            if current_list:
                flowables.extend(bullet_list([_inline_fmt(t) for t in current_list], styles))
                current_list = []
            flowables.append(Paragraph(_inline_fmt(stripped[4:]), styles["h3"]))
            i += 1
            continue
        if stripped.startswith("## "):
            if current_list:
                flowables.extend(bullet_list([_inline_fmt(t) for t in current_list], styles))
                current_list = []
            flowables.append(section_title(_inline_fmt(stripped[3:]), styles))
            i += 1
            continue
        if stripped.startswith("# "):
            if current_list:
                flowables.extend(bullet_list([_inline_fmt(t) for t in current_list], styles))
                current_list = []
            flowables.append(Paragraph(_inline_fmt(stripped[2:]), styles["h2"]))
            i += 1
            continue

        # Horizontal rule
        if stripped in ("---", "***", "___"):
            if current_list:
                flowables.extend(bullet_list([_inline_fmt(t) for t in current_list], styles))
                current_list = []
            flowables.append(accent_line())
            i += 1
            continue

        # Bullet list
        if stripped.startswith("- ") or stripped.startswith("* "):
            current_list.append(stripped[2:])
            i += 1
            continue

        # Numbered list
        if re.match(r"^\d+\.\s", stripped):
            text = re.sub(r"^\d+\.\s", "", stripped)
            current_list.append(text)
            i += 1
            continue

        # Plain paragraph
        text = _inline_fmt(stripped)

        if current_list:
            flowables.extend(bullet_list([_inline_fmt(t) for t in current_list], styles))
            current_list = []

        flowables.append(Paragraph(text, styles["body"]))
        i += 1

    if current_list:
        flowables.extend(bullet_list([_inline_fmt(t) for t in current_list], styles))

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
