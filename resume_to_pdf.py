#!/usr/bin/env python3
"""
resume_to_pdf.py — Converts resume.md into a professionally styled PDF.

Usage:
    python resume_to_pdf.py [INPUT_MD] [OUTPUT_PDF]

Defaults:
    INPUT_MD  = resume.md
    OUTPUT_PDF = resume.pdf

Dependencies:
    pip install reportlab markdown

Designed to run in a GitHub Actions pipeline. See the accompanying
github workflow example in .github/workflows/resume.yml
"""

import sys
import re
from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, HRFlowable,
)


# ──────────────────────────────────────────────
# Theme — edit these to change the look
# ──────────────────────────────────────────────
THEME = {
    "dark":       "#1a1a2e",
    "accent":     "#2d6a8f",
    "text":       "#333333",
    "gray":       "#555555",
    "light_gray": "#888888",
    "rule":       "#cccccc",
    "font":       "Helvetica",
    "font_bold":  "Helvetica-Bold",
    "font_italic": "Helvetica-Oblique",
}

MARGIN_TOP    = 0.5 * inch
MARGIN_BOTTOM = 0.5 * inch
MARGIN_LEFT   = 0.65 * inch
MARGIN_RIGHT  = 0.65 * inch


# ──────────────────────────────────────────────
# Styles
# ──────────────────────────────────────────────
def build_styles():
    T = THEME
    return {
        "name": ParagraphStyle(
            "Name", fontSize=22, leading=26,
            textColor=HexColor(T["dark"]), fontName=T["font_bold"],
            spaceAfter=2, alignment=TA_LEFT,
        ),
        "subtitle": ParagraphStyle(
            "Subtitle", fontSize=11, leading=14,
            textColor=HexColor(T["accent"]), fontName=T["font"],
            spaceAfter=2,
        ),
        "contact": ParagraphStyle(
            "Contact", fontSize=9, leading=12,
            textColor=HexColor(T["gray"]), fontName=T["font"],
            spaceAfter=4,
        ),
        "section": ParagraphStyle(
            "Section", fontSize=12, leading=15,
            textColor=HexColor(T["accent"]), fontName=T["font_bold"],
            spaceBefore=10, spaceAfter=4,
        ),
        "role": ParagraphStyle(
            "Role", fontSize=11, leading=14,
            textColor=HexColor(T["dark"]), fontName=T["font_bold"],
            spaceBefore=6, spaceAfter=1,
        ),
        "company": ParagraphStyle(
            "Company", fontSize=9.5, leading=12,
            textColor=HexColor(T["gray"]), fontName=T["font"],
            spaceAfter=3,
        ),
        "body": ParagraphStyle(
            "Body", fontSize=9.5, leading=13.5,
            textColor=HexColor(T["text"]), fontName=T["font"],
            spaceAfter=2,
        ),
        "bullet": ParagraphStyle(
            "Bullet", fontSize=9.5, leading=13,
            textColor=HexColor(T["text"]), fontName=T["font"],
            leftIndent=14, firstLineIndent=-10, spaceAfter=2,
        ),
        "italic_label": ParagraphStyle(
            "ItalicLabel", fontSize=9.5, leading=13,
            textColor=HexColor(T["accent"]), fontName=T["font_italic"],
            spaceBefore=4, spaceAfter=2,
        ),
        "skills": ParagraphStyle(
            "Skills", fontSize=9, leading=12.5,
            textColor=HexColor("#444444"), fontName=T["font"],
            spaceAfter=1,
        ),
    }


# ──────────────────────────────────────────────
# Markdown parser (resume-specific, no deps on
# heavy markdown-to-pdf libs)
# ──────────────────────────────────────────────
def md_inline(text: str) -> str:
    """Convert inline markdown (**bold**, *italic*, [text](url)) to ReportLab XML."""
    # Links: [text](url) → <a href="url" color="#2d6a8f">text</a>
    text = re.sub(
        r'\[([^\]]+)\]\(([^)]+)\)',
        rf'<a href="\2" color="{THEME["accent"]}">\1</a>',
        text
    )
    # Bold: **text** → <b>text</b>
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    # Italic: *text* → <i>\1</i>
    text = re.sub(r'\*(.+?)\*', r'<i>\1</i>', text)
    # Escape ampersands that aren't already entities
    text = re.sub(r'&(?!amp;|lt;|gt;|quot;|#)', '&amp;', text)
    return text


def parse_resume_md(md_text: str, styles: dict) -> list:
    """Parse the resume markdown and return a list of ReportLab flowables."""
    lines = md_text.split('\n')
    story = []
    i = 0
    is_header_done = False
    current_section = None

    def hr():
        return HRFlowable(width="100%", thickness=0.3, color=HexColor(THEME["rule"]),
                          spaceBefore=4, spaceAfter=4)

    def thick_hr():
        return HRFlowable(width="100%", thickness=0.5, color=HexColor(THEME["rule"]),
                          spaceAfter=6)

    while i < len(lines):
        line = lines[i].rstrip()

        # Skip empty lines
        if not line:
            i += 1
            continue

        # Horizontal rule ---
        if re.match(r'^-{3,}$', line):
            if not is_header_done:
                story.append(thick_hr())
                is_header_done = True
            else:
                story.append(hr())
            i += 1
            continue

        # H1 — Name
        if line.startswith('# ') and not line.startswith('## '):
            story.append(Paragraph(md_inline(line[2:].strip()), styles["name"]))
            i += 1
            continue

        # H2 — Section headers
        if line.startswith('## '):
            current_section = line[3:].strip()
            story.append(Paragraph(current_section.upper(), styles["section"]))
            i += 1
            continue

        # H3 — Role or sub-section titles
        if line.startswith('### '):
            title = line[4:].strip()
            story.append(Paragraph(md_inline(title), styles["role"]))
            i += 1
            continue

        # Bold-only line right after header (subtitle or company line)
        # e.g. **Getir** | 2025 – Present
        if re.match(r'^\*\*[^*]+\*\*', line) and '|' in line:
            story.append(Paragraph(md_inline(line), styles["company"]))
            i += 1
            continue

        # Subtitle line (bold-wrapped line before the first ---)
        if re.match(r'^\*\*(.+)\*\*$', line) and not is_header_done:
            inner = re.match(r'^\*\*(.+)\*\*$', line).group(1)
            story.append(Paragraph(md_inline(inner), styles["subtitle"]))
            i += 1
            continue

        # Italic-only lines (sub-labels like *Organizational Impact...*)
        if re.match(r'^\*[^*]+\*$', line):
            label = line.strip('*').strip()
            story.append(Paragraph(label, styles["italic_label"]))
            i += 1
            continue

        # Bullet points
        if line.startswith('- '):
            text = line[2:].strip()
            # Collect continuation lines
            while i + 1 < len(lines) and lines[i + 1].startswith('  ') and not lines[i + 1].strip().startswith('- '):
                i += 1
                text += ' ' + lines[i].strip()
            story.append(Paragraph(f"&#8226; &nbsp;{md_inline(text)}", styles["bullet"]))
            i += 1
            continue

        # Contact line (contains | separator and email-like content, after subtitle)
        if '|' in line and '@' in line:
            # Clean up markdown links for contact line
            contact = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', line)
            contact = contact.replace('|', '&nbsp;|&nbsp;')
            story.append(Paragraph(contact, styles["contact"]))
            i += 1
            continue

        # Skills lines (contain **Label:** pattern inside a Technical Expertise section)
        if current_section and 'expertise' in current_section.lower() and '**' in line:
            story.append(Paragraph(md_inline(line), styles["skills"]))
            i += 1
            continue

        # Default body paragraph
        para_text = line
        while i + 1 < len(lines) and lines[i + 1].strip() and \
              not lines[i + 1].startswith('#') and not lines[i + 1].startswith('- ') and \
              not re.match(r'^-{3,}$', lines[i + 1]) and not lines[i + 1].startswith('**'):
            i += 1
            para_text += ' ' + lines[i].strip()
        story.append(Paragraph(md_inline(para_text), styles["body"]))
        i += 1

    return story


# ──────────────────────────────────────────────
# PDF generation
# ──────────────────────────────────────────────
def generate_pdf(md_path: str, pdf_path: str):
    md_text = Path(md_path).read_text(encoding="utf-8")
    styles = build_styles()
    story = parse_resume_md(md_text, styles)

    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        topMargin=MARGIN_TOP,
        bottomMargin=MARGIN_BOTTOM,
        leftMargin=MARGIN_LEFT,
        rightMargin=MARGIN_RIGHT,
        title="Lorem Ipsum — Resume",
        author="Lorem Ipsum",
    )
    num_elements = len(story)
    doc.build(story)
    print(f"✓ Generated {pdf_path} ({num_elements} flowables)")


# ──────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────
if __name__ == "__main__":
    input_md  = sys.argv[1] if len(sys.argv) > 1 else "resume.md"
    output_pdf = sys.argv[2] if len(sys.argv) > 2 else "resume.pdf"

    if not Path(input_md).exists():
        print(f"Error: {input_md} not found", file=sys.stderr)
        sys.exit(1)

    generate_pdf(input_md, output_pdf)
