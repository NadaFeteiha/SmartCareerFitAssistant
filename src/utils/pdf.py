""""PDF generation utilities for resumes and cover letters."""

from io import BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
import re

# ── colour palette ─────────────────────────────────────────────────────────────
DARK    = colors.HexColor("#111111")   # name / headings
ACCENT  = colors.HexColor("#000000")   # black for professional resume dividing lines
BODY    = colors.HexColor("#222222")   # body text (dark grey for readability)
LIGHT   = colors.HexColor("#555555")   # dates / location 
WHITE   = colors.white
PAGE_W, PAGE_H  = letter

def _styles():
    base = getSampleStyleSheet()

    name_style = ParagraphStyle(
        "ResumeName",
        parent=base["Normal"],
        fontName="Helvetica-Bold",
        fontSize=24,
        leading=28,
        textColor=DARK,
        spaceAfter=4,
        alignment=TA_CENTER,
    )
    contact_style = ParagraphStyle(
        "ResumeContact",
        parent=base["Normal"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=14,
        textColor=BODY,
        spaceAfter=12,
        alignment=TA_CENTER,
    )
    section_style = ParagraphStyle(
        "ResumeSection",
        parent=base["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=16,
        textColor=DARK,
        spaceBefore=14,
        spaceAfter=2,
        textTransform="uppercase", 
    )
    job_left = ParagraphStyle(
        "ResumeJobLeft",
        parent=base["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=DARK,
    )
    job_right = ParagraphStyle(
        "ResumeJobRight",
        parent=base["Normal"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=14,
        textColor=LIGHT,
        alignment=TA_RIGHT,
    )
    bullet_style = ParagraphStyle(
        "ResumeBullet",
        parent=base["Normal"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=13,
        leftIndent=12,
        firstLineIndent=-12,
        textColor=BODY,
        spaceAfter=3,
        spaceBefore=0,
    )
    normal_style = ParagraphStyle(
        "ResumeNormal",
        parent=base["Normal"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=13,
        textColor=BODY,
        spaceAfter=4,
    )

    return {
        "name": name_style,
        "contact": contact_style,
        "section": section_style,
        "job_left": job_left,
        "job_right": job_right,
        "bullet": bullet_style,
        "normal": normal_style,
    }

def _hr(width=7.5 * inch, thickness=1.0, color=ACCENT, space_after=6, space_before=2):
    return HRFlowable(width=width, thickness=thickness, color=color, spaceAfter=space_after, spaceBefore=space_before)

def _inline_md(text: str) -> str:
    """Convert **bold** and *italic* markdown to ReportLab XML tags."""
    # Bold first (double asterisks)
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    # Italic (single asterisk)
    text = re.sub(r'\*(.+?)\*', r'<i>\1</i>', text)
    # Escape bare & that aren't already entities
    text = re.sub(r'&(?!(amp|lt|gt|nbsp|apos|quot);)', r'&amp;', text)
    return text

def _parse_and_build(resume_content: str, s: dict) -> list:
    """
    Parse markdown resume text and return a list of reportlab flowables.
    """
    story = []
    lines = resume_content.splitlines()
    i = 0
    header_done = False

    while i < len(lines):
        raw = lines[i]
        stripped = raw.strip()

        # ── H1 → candidate name ──────────────────────────────────────────────
        if stripped.startswith("# "):
            name_text = stripped[2:].strip()
            story.append(Paragraph(name_text, s["name"]))
            header_done = False
            i += 1
            continue

        # ── Contact line ───────────────────────────────────────────────────────
        if not header_done and stripped and not stripped.startswith("#") and (
            "|" in stripped or "@" in stripped or "linkedin" in stripped.lower()
        ):
            contact_text = stripped.replace("|", " • ")
            story.append(Paragraph(contact_text, s["contact"]))
            story.append(Spacer(1, 0.05 * inch))
            header_done = True
            i += 1
            continue

        # ── H2 → section header ──────────────────────────────────────────────
        if stripped.startswith("## "):
            section_text = stripped[3:].strip().upper()
            story.append(Paragraph(section_text, s["section"]))
            story.append(_hr(thickness=1.2))
            i += 1
            continue

        # ── H3 → job title / company / degree ───────────────────────────────
        if stripped.startswith("### "):
            job_text = stripped[4:].strip()
            parts = [p.strip() for p in job_text.split("|")]
            
            left_text = ""
            right_text = ""
            if len(parts) >= 3:
                role = parts[0]
                company = parts[1]
                dates = parts[2]
                location = parts[3] if len(parts) > 3 else ""
                left_text = f"<b>{role}</b>, {company}"
                right_text = f"<b>{dates}</b>" + (f" | {location}" if location else "")
            elif len(parts) == 2:
                left_text = f"<b>{parts[0]}</b>, {parts[1]}"
            else:
                left_text = f"<b>{job_text}</b>"

            if right_text:
                col_widths = [4.5 * inch, 3.0 * inch]
                t = Table([
                    [Paragraph(left_text, s["job_left"]), Paragraph(right_text, s["job_right"])]
                ], colWidths=col_widths)
                t.setStyle(TableStyle([
                    ('PADDING', (0,0), (-1,-1), 0),
                    ('VALIGN', (0,0), (-1,-1), 'BOTTOM'),
                ]))
                story.append(Spacer(1, 0.05 * inch))
                story.append(t)
                story.append(Spacer(1, 0.03 * inch))
            else:
                story.append(Spacer(1, 0.05 * inch))
                story.append(Paragraph(left_text, s["job_left"]))
                story.append(Spacer(1, 0.03 * inch))
            i += 1
            continue

        # ── Bullet points (-, *, •) ──────────────────────────────────────────
        if stripped.startswith(("- ", "* ", "• ")):
            bullet_text = stripped[2:].strip()
            bullet_text = _inline_md(bullet_text)
            story.append(Paragraph(f"• &nbsp;{bullet_text}", s["bullet"]))
            i += 1
            continue

        # ── **Label:** value  (skill categories, etc.) ──────────────────────
        if stripped.startswith("**") and ":**" in stripped:
            end_bold = stripped.index(":**")
            label = stripped[2:end_bold]
            value = stripped[end_bold + 3:].strip()
            story.append(Paragraph(f"<b>{label}:</b> {_inline_md(value)}", s["normal"]))
            i += 1
            continue

        # ── Italic meta lines (*text*) ────────────────────────────────────────
        if stripped.startswith("*") and stripped.endswith("*") and len(stripped) > 2:
            inner = stripped[1:-1]
            story.append(Paragraph(f"<i>{inner}</i>", s["job_right"]))
            story.append(Spacer(1, 0.03 * inch))
            i += 1
            continue

        # ── Horizontal rule (---) ─────────────────────────────────────────────
        if stripped in ("---", "***", "___"):
            story.append(_hr(color=colors.HexColor("#CCCCCC"), thickness=0.5))
            i += 1
            continue

        # ── Empty line ────────────────────────────────────────────────────────
        if not stripped:
            story.append(Spacer(1, 0.04 * inch))
            i += 1
            continue

        # ── Plain text / paragraph ────────────────────────────────────────────
        story.append(Paragraph(_inline_md(stripped), s["normal"]))
        i += 1

    return story

def create_resume_pdf(resume_content: str, name: str = "Resume") -> BytesIO:
    """
    Generate a polished, job-ready resume PDF from markdown text.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=0.5 * inch,
        rightMargin=0.5 * inch,
        topMargin=0.5 * inch,
        bottomMargin=0.5 * inch,
        title=name,
        author="SmartCareerFit",
    )

    s = _styles()
    story = _parse_and_build(resume_content, s)

    doc.build(story)
    buffer.seek(0)
    return buffer

def create_cover_letter_pdf(cover_letter_content: str, name: str = "Cover Letter") -> BytesIO:
    """
    Create a professional cover letter PDF.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=1.0 * inch,
        rightMargin=1.0 * inch,
        topMargin=1.0 * inch,
        bottomMargin=1.0 * inch,
        title="Cover Letter",
    )
    base = getSampleStyleSheet()

    header_style = ParagraphStyle(
        "LetterHeader",
        parent=base["Normal"],
        fontSize=11,
        spaceAfter=12,
        leading=16,
        textColor=DARK,
        fontName="Helvetica",
    )
    body_style = ParagraphStyle(
        "LetterBody",
        parent=base["Normal"],
        fontSize=11,
        spaceAfter=12,
        leading=16,
        textColor=BODY,
        fontName="Helvetica",
    )
    signature_style = ParagraphStyle(
        "LetterSignature",
        parent=base["Normal"],
        fontSize=11,
        spaceAfter=8,
        leading=16,
        textColor=DARK,
        fontName="Helvetica-Bold",
    )

    story = []
    current_date = datetime.now().strftime("%B %d, %Y")
    story.append(Paragraph(current_date, header_style))
    story.append(Spacer(1, 0.2 * inch))

    for line in cover_letter_content.splitlines():
        line = line.strip()
        if not line:
            story.append(Spacer(1, 0.06 * inch))
            continue
        if any(line.lower().startswith(kw) for kw in ("sincerely", "best regards", "regards", "thank you")):
            story.append(Spacer(1, 0.2 * inch))
            story.append(Paragraph(line, signature_style))
            story.append(Spacer(1, 0.3 * inch))
            if name and name != "Cover Letter":
                story.append(Paragraph(name, signature_style))
        else:
            story.append(Paragraph(_inline_md(line), body_style))

    doc.build(story)
    buffer.seek(0)
    return buffer
