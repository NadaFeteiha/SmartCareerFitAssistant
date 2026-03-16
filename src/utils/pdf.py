"""Professional PDF generation utilities for resumes and cover letters."""

from io import BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, 
    TableStyle, HRFlowable, PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
import re
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER
# ── Professional Color Palette ─────────────────────────────────────────────
PRIMARY = colors.HexColor("#2C3E50")      # Dark blue-gray for headings
SECONDARY = colors.HexColor("#3498DB")    # Professional blue for accents
TEXT_DARK = colors.HexColor("#2C3E50")    # Dark text
TEXT_MEDIUM = colors.HexColor("#34495E")  # Medium text
TEXT_LIGHT = colors.HexColor("#7F8C8D")   # Light text for dates/location
ACCENT = colors.HexColor("#2980B9")       # Darker blue for lines
WHITE = colors.white
BLACK = colors.black

PAGE_WIDTH, PAGE_HEIGHT = letter

# ── Layout Constants ──────────────────────────────────────────────────────
LEFT_MARGIN = 0.7 * inch
RIGHT_MARGIN = 0.7 * inch
TOP_MARGIN = 0.6 * inch
BOTTOM_MARGIN = 0.6 * inch
CONTACT_ICON_SPACE = 0.15 * inch
SECTION_SPACING = 0.2 * inch
BULLET_INDENT = 0.25 * inch

def _get_styles():
    """Create and return professional paragraph styles."""
    base = getSampleStyleSheet()
    
    styles = {
        # Name header - prominent and professional
        "name": ParagraphStyle(
            "ProfessionalName",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=28,
            leading=34,
            textColor=PRIMARY,
            spaceAfter=8,
            alignment=TA_CENTER,
            underlineWidth=0,
        ),
        
        # Contact information with icons or separators
        "contact": ParagraphStyle(
            "ProfessionalContact",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=10,
            leading=16,
            textColor=TEXT_MEDIUM,
            spaceAfter=16,
            alignment=TA_CENTER,
        ),
        
        # Section headers with subtle styling
        "section": ParagraphStyle(
            "ProfessionalSection",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=14,
            leading=18,
            textColor=PRIMARY,
            spaceBefore=12,
            spaceAfter=4,
            alignment=TA_LEFT,
            textTransform="uppercase",
            letterSpacing=1,
        ),
        
        # Job title/company left aligned
        "job_left": ParagraphStyle(
            "ProfessionalJobLeft",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=16,
            textColor=TEXT_DARK,
            alignment=TA_LEFT,
        ),
        
        # Company name (if separate from job title)
        "company": ParagraphStyle(
            "ProfessionalCompany",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=11,
            leading=16,
            textColor=TEXT_MEDIUM,
            alignment=TA_LEFT,
        ),
        
        # Dates right aligned
        "job_right": ParagraphStyle(
            "ProfessionalJobRight",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=10,
            leading=16,
            textColor=TEXT_LIGHT,
            alignment=TA_RIGHT,
        ),
        
        # Location style
        "location": ParagraphStyle(
            "ProfessionalLocation",
            parent=base["Normal"],
            fontName="Helvetica-Oblique",
            fontSize=10,
            leading=16,
            textColor=TEXT_LIGHT,
            alignment=TA_RIGHT,
        ),
        
        # Bullet points with proper indentation
        "bullet": ParagraphStyle(
            "ProfessionalBullet",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=10,
            leading=15,
            leftIndent=BULLET_INDENT,
            firstLineIndent=-BULLET_INDENT,
            textColor=TEXT_DARK,
            spaceAfter=4,
            spaceBefore=0,
        ),
        
        # Normal paragraph text
        "normal": ParagraphStyle(
            "ProfessionalNormal",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=10,
            leading=15,
            textColor=TEXT_DARK,
            spaceAfter=6,
        ),
        
        # Skills and tags style
        "skill_tag": ParagraphStyle(
            "ProfessionalSkillTag",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=14,
            textColor=TEXT_MEDIUM,
            alignment=TA_LEFT,
            spaceAfter=4,
        ),
    }
    
    return styles

def _create_horizontal_rule(thickness=1.0, color=ACCENT, space_after=8, space_before=2, width_percent=0.9):
    """Create a professional horizontal rule."""
    return HRFlowable(
        width=width_percent * (PAGE_WIDTH - LEFT_MARGIN - RIGHT_MARGIN),
        thickness=thickness,
        color=color,
        spaceAfter=space_after,
        spaceBefore=space_before,
        hAlign='CENTER',
    )

def _format_contact_line(text: str) -> str:
    """Format contact line with professional separators."""
    # Replace common separators with professional bullet
    text = re.sub(r'[|•·]', ' • ', text)
    # Remove extra spaces
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def _parse_markdown_inline(text: str) -> str:
    """Convert markdown to ReportLab XML tags."""
    # Bold with **
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    # Italic with *
    text = re.sub(r'\*(.+?)\*', r'<i>\1</i>', text)
    # Underline with __ (if needed)
    text = re.sub(r'__(.+?)__', r'<u>\1</u>', text)
    # Escape XML entities
    text = re.sub(r'&(?!(?:amp|lt|gt|nbsp|quot|apos);)', '&amp;', text)
    return text

def _create_job_entry(parts: list, styles: dict) -> list:
    """
    Create a formatted job entry table.
    Expected formats:
    - Role | Company | Date | Location
    - Role | Company | Date
    - Role, Company, Date, Location
    """
    flowables = []
    
    # Parse the parts
    if len(parts) >= 3:
        role = parts[0].strip()
        company = parts[1].strip()
        date = parts[2].strip()
        location = parts[3].strip() if len(parts) > 3 else ""
        
        # Left column: Role and Company
        left_text = f"<b>{role}</b>"
        if company:
            left_text += f", <font name='Helvetica'>{company}</font>"
        
        # Right column: Date and Location
        right_text = f"<b>{date}</b>"
        if location:
            right_text += f"<br/><font name='Helvetica-Oblique' color='{TEXT_LIGHT.hexval()}'>{location}</font>"
        
        # Create table for proper alignment
        col_widths = [4.2 * inch, 3.0 * inch]
        data = [
            [Paragraph(left_text, styles["job_left"]), 
             Paragraph(right_text, styles["job_right"])]
        ]
        
        table = Table(data, colWidths=col_widths)
        table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (0, -1), 0),
            ('RIGHTPADDING', (0, 0), (0, -1), 0),
            ('LEFTPADDING', (1, 0), (1, -1), 10),
            ('RIGHTPADDING', (1, 0), (1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ]))
        
        flowables.append(Spacer(1, 0.1 * inch))
        flowables.append(table)
    else:
        # Simple entry without dates
        flowables.append(Spacer(1, 0.1 * inch))
        flowables.append(Paragraph(f"<b>{parts[0]}</b>", styles["job_left"]))
    
    return flowables

def _parse_resume_content(content: str, styles: dict) -> list:
    """
    Parse markdown resume content into professional flowables.
    """
    story = []
    lines = content.split('\n')
    i = 0
    in_header = True
    
    while i < len(lines):
        line = lines[i].rstrip()
        stripped = line.strip()
        
        # Skip empty lines at start
        if not stripped and in_header:
            i += 1
            continue
        
        # Name (H1)
        if stripped.startswith('# '):
            name_text = stripped[2:].strip()
            story.append(Paragraph(name_text, styles["name"]))
            in_header = False
            i += 1
            continue
        
        # Contact information - after name
        if in_header and not stripped.startswith('#'):
            # Format contact line with professional separators
            contact_text = _format_contact_line(stripped)
            story.append(Paragraph(contact_text, styles["contact"]))
            # Add a subtle line after contact
            story.append(_create_horizontal_rule(thickness=1, color=PRIMARY, width_percent=0.15))
            story.append(Spacer(1, 0.1 * inch))
            in_header = False
            i += 1
            continue
        
        # Section headers (H2)
        if stripped.startswith('## '):
            section_text = stripped[3:].strip().upper()
            story.append(Paragraph(section_text, styles["section"]))
            story.append(_create_horizontal_rule(thickness=1, color=ACCENT, width_percent=1.0))
            i += 1
            continue
        
        # Job/education entries (H3)
        if stripped.startswith('### '):
            entry_text = stripped[4:].strip()
            # Split by common separators
            parts = re.split(r'[|,]', entry_text)
            parts = [p.strip() for p in parts if p.strip()]
            
            job_flowables = _create_job_entry(parts, styles)
            story.extend(job_flowables)
            i += 1
            continue
        
        # Bullet points
        if stripped.startswith(('- ', '* ', '• ')):
            bullet_text = stripped[2:].strip()
            bullet_text = _parse_markdown_inline(bullet_text)
            story.append(Paragraph(f"• {bullet_text}", styles["bullet"]))
            i += 1
            continue
        
        # Skill categories (bold label: value)
        if ':**' in stripped and stripped.startswith('**'):
            parts = stripped.split(':**', 1)
            if len(parts) == 2:
                label = parts[0].strip('* ')
                value = parts[1].strip()
                formatted_text = f"<b>{label}:</b> {_parse_markdown_inline(value)}"
                story.append(Paragraph(formatted_text, styles["skill_tag"]))
            i += 1
            continue
        
        # Horizontal rule
        if stripped in ('---', '***', '___'):
            story.append(_create_horizontal_rule(color=TEXT_LIGHT, thickness=0.5))
            i += 1
            continue
        
        # Regular paragraph
        if stripped:
            story.append(Paragraph(_parse_markdown_inline(stripped), styles["normal"]))
            i += 1
            continue
        
        # Empty line
        if not stripped and story:  # Only add spacer if we have content
            story.append(Spacer(1, 0.08 * inch))
        i += 1
    
    return story

def create_cover_letter_pdf(cover_letter_content: str, name: str = "Cover Letter") -> BytesIO:
    """
    Create a professional cover letter PDF.
    
    Args:
        cover_letter_content: Cover letter text
        name: Applicant name for signature
    
    Returns:
        BytesIO buffer containing the PDF
    """
    buffer = BytesIO()
    
    # Cover letter specific margins (wider for better readability)
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=1.2 * inch,
        rightMargin=1.2 * inch,
        topMargin=1.0 * inch,
        bottomMargin=1.0 * inch,
        title="Cover Letter",
        author="Professional Cover Letter",
    )
    
    base = getSampleStyleSheet()
    
    # Professional cover letter styles
    date_style = ParagraphStyle(
        "CoverDate",
        parent=base["Normal"],
        fontName="Helvetica",
        fontSize=11,
        leading=16,
        textColor=TEXT_MEDIUM,
        alignment=TA_RIGHT,
        spaceAfter=24,
    )
    
    recipient_style = ParagraphStyle(
        "CoverRecipient",
        parent=base["Normal"],
        fontName="Helvetica",
        fontSize=11,
        leading=16,
        textColor=TEXT_DARK,
        spaceAfter=12,
    )
    
    body_style = ParagraphStyle(
        "CoverBody",
        parent=base["Normal"],
        fontName="Helvetica",
        fontSize=11,
        leading=18,
        textColor=TEXT_DARK,
        spaceAfter=12,
        alignment=TA_LEFT,
    )
    
    signature_style = ParagraphStyle(
        "CoverSignature",
        parent=base["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=18,
        textColor=TEXT_DARK,
        spaceBefore=24,
        spaceAfter=4,
    )
    
    story = []
    
    # Add date
    current_date = datetime.now().strftime("%B %d, %Y")
    story.append(Paragraph(current_date, date_style))
    
    # Process cover letter content
    lines = cover_letter_content.split('\n')
    in_signature = False
    
    for line in lines:
        stripped = line.strip()
        
        if not stripped:
            story.append(Spacer(1, 0.1 * inch))
            continue
        
        # Check for signature indicators
        if any(stripped.lower().startswith(kw) for kw in 
               ["sincerely", "best regards", "regards", "thank you", "yours truly"]):
            story.append(Spacer(1, 0.3 * inch))
            story.append(Paragraph(stripped, signature_style))
            in_signature = True
        elif in_signature:
            # This is likely the name after signature
            story.append(Paragraph(stripped, signature_style))
            in_signature = False
        else:
            # Regular paragraph
            story.append(Paragraph(_parse_markdown_inline(stripped), body_style))
    
    doc.build(story)
    buffer.seek(0)
    return buffer



# ----------------------------------
# ── Modern professional color palette ────────────────────────────────────────
DARK_GRAY     = colors.HexColor("#0F172A")   # almost black – headings, name
ACCENT_BLACK  = colors.HexColor("#111111")   # rules, strong text
BODY_TEXT     = colors.HexColor("#1E293B")   # main content
LIGHT_GRAY    = colors.HexColor("#475569")   # dates, locations, secondary info
SUBTLE_GRAY   = colors.HexColor("#64748B")   # very light meta text

def create_styles():
    """Central place for all typography styles – easy to tweak."""
    base = getSampleStyleSheet()

    return {
        "name": ParagraphStyle(
            name="Name",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=22,
            leading=26,
            textColor=DARK_GRAY,
            alignment=TA_CENTER,
            spaceAfter=6,
        ),
        "contact": ParagraphStyle(
            name="Contact",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=9.8,
            leading=13,
            textColor=BODY_TEXT,
            alignment=TA_CENTER,
            spaceAfter=18,
        ),
        "section": ParagraphStyle(
            name="SectionHeader",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=12.5,
            leading=15,
            textColor=DARK_GRAY,
            spaceBefore=18,
            spaceAfter=4,
            textTransform="uppercase",
            letterSpacing=0.4,
        ),
        "job_title": ParagraphStyle(
            name="JobTitle",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            textColor=DARK_GRAY,
            spaceAfter=1,
        ),
        "job_meta": ParagraphStyle(
            name="JobMeta",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=9.8,
            leading=13,
            textColor=LIGHT_GRAY,
            alignment=TA_RIGHT,
        ),
        "bullet": ParagraphStyle(
            name="Bullet",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=10,
            leading=13.5,
            leftIndent=14,
            firstLineIndent=-14,
            spaceBefore=1,
            spaceAfter=3,
            textColor=BODY_TEXT,
        ),
        "normal": ParagraphStyle(
            name="Normal",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=10,
            leading=13.5,
            textColor=BODY_TEXT,
            spaceAfter=5,
        ),
        "skill_label": ParagraphStyle(
            name="SkillLabel",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9.5,
            leading=13,
            textColor=DARK_GRAY,
        ),
        "skill_value": ParagraphStyle(
            name="SkillValue",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=13,
            textColor=BODY_TEXT,
        ),
    }


def hr(thickness=0.8, color=ACCENT_BLACK, width="100%", spaceBefore=4, spaceAfter=8):
    return HRFlowable(
        width=width,
        thickness=thickness,
        lineCap="round",
        color=color,
        spaceBefore=spaceBefore,
        spaceAfter=spaceAfter,
    )


def bold_italic_to_xml(text: str) -> str:
    """Very simple markdown → ReportLab XML conversion"""
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'\*(.+?)\*', r'<i>\1</i>', text)
    text = re.sub(r'&(?!(amp|lt|gt|nbsp|apos|quot);)', r'&amp;', text)
    return text


def parse_resume_to_flowables(md_text: str, styles: dict) -> list:
    story = []
    lines = [line.rstrip() for line in md_text.splitlines()]
    i = 0

    in_header = True

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if not stripped:
            if story:  # avoid leading empty lines
                story.append(Spacer(1, 0.04 * inch))
            i += 1
            continue

        # ── Name (only once at top) ───────────────────────────────────────────
        if in_header and stripped.startswith("# "):
            name = stripped[2:].strip()
            story.append(Paragraph(name, styles["name"]))
            in_header = False
            i += 1
            continue

        # ── Contact info (right after name) ───────────────────────────────────
        if in_header and ("@" in stripped or "linkedin" in stripped.lower() or "|" in stripped):
            contact = stripped.replace("|", "  •  ").strip()
            story.append(Paragraph(contact, styles["contact"]))
            story.append(Spacer(1, 0.12 * inch))
            story.append(hr(thickness=1.1, spaceBefore=0, spaceAfter=10))
            in_header = False
            i += 1
            continue

        # ── Section header ────────────────────────────────────────────────────
        if stripped.startswith("## "):
            title = stripped[3:].strip().upper()
            story.append(Paragraph(title, styles["section"]))
            story.append(hr(thickness=1.0, spaceBefore=2, spaceAfter=6))
            i += 1
            continue

        # ── Job / Education entry ─────────────────────────────────────────────
        if stripped.startswith("### "):
            parts = [p.strip() for p in stripped[4:].split("|")]
            role, company, date_loc = "", "", ""

            if len(parts) >= 2:
                role = parts[0]
                company = parts[1]
                date_loc = " | ".join(parts[2:]) if len(parts) > 2 else ""

            left = f'<b>{role}</b>, {company}' if company else f'<b>{role}</b>'
            right = f'<b>{date_loc}</b>' if date_loc else ""

            if right:
                table = Table(
                    [[Paragraph(left, styles["job_title"]),
                      Paragraph(right, styles["job_meta"])]],
                    colWidths=[4.9 * inch, 2.6 * inch],
                    spaceBefore=8,
                    spaceAfter=2,
                )
                table.setStyle(TableStyle([
                    ('VALIGN', (0,0), (-1,-1), 'BOTTOM'),
                    ('TOPPADDING', (0,0), (-1,-1), 0),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 0),
                    ('LEFTPADDING', (0,0), (0,0), 0),
                    ('RIGHTPADDING', (1,0), (1,0), 0),
                ]))
                story.append(table)
            else:
                story.append(Spacer(1, 0.08 * inch))
                story.append(Paragraph(left, styles["job_title"]))

            i += 1
            continue

        # ── Bullet points ─────────────────────────────────────────────────────
        if stripped.startswith(("- ", "* ", "• ")):
            content = bold_italic_to_xml(stripped[2:].strip())
            story.append(Paragraph(f"• {content}", styles["bullet"]))
            i += 1
            continue

        # ── **Key:** value  (skills, tools, etc.) ─────────────────────────────
        if stripped.startswith("**") and ":**" in stripped:
            skill_rows = []

            # Collect consecutive skill lines
            while i < len(lines):
                current_line = lines[i].strip()
                if current_line.startswith("**") and ":**" in current_line:
                    idx = current_line.index(":**")
                    label = current_line[2:idx]
                    value = bold_italic_to_xml(current_line[idx + 3:].strip())
                    skill_rows.append((label, value))
                    i += 1
                else:
                    break

            if skill_rows:
                LABEL_COL = 1.55 * inch
                VALUE_COL = PAGE_WIDTH - 1.2 * inch - LABEL_COL  # matches doc margins

                ROW_BG_ODD  = colors.HexColor("#EEF2FF")   # soft indigo tint for odd rows
                ROW_BG_EVEN = colors.white
                BORDER_COLOR = colors.HexColor("#CBD5E1")   # slate-300

                table_data = [
                    [
                        Paragraph(label, styles["skill_label"]),
                        Paragraph(value, styles["skill_value"]),
                    ]
                    for label, value in skill_rows
                ]

                row_bgs = []
                for r in range(len(skill_rows)):
                    bg = ROW_BG_ODD if r % 2 == 0 else ROW_BG_EVEN
                    row_bgs.append(("BACKGROUND", (0, r), (-1, r), bg))

                skills_table = Table(
                    table_data,
                    colWidths=[LABEL_COL, VALUE_COL],
                    spaceBefore=4,
                    spaceAfter=6,
                )
                skills_table.setStyle(TableStyle([
                    ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING",   (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
                    ("TOPPADDING",    (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ("BOX",           (0, 0), (-1, -1), 0.5, BORDER_COLOR),
                    ("INNERGRID",     (0, 0), (-1, -1), 0.5, BORDER_COLOR),
                    # Label column: slightly darker background always
                    ("BACKGROUND",    (0, 0), (0, -1), colors.HexColor("#E0E7FF")),
                    *row_bgs,
                    # Re-apply label column bg on top of row bgs
                    ("BACKGROUND",    (0, 0), (0, -1), colors.HexColor("#E0E7FF")),
                ]))
                story.append(skills_table)

            continue

        # ── Fallback – plain line ─────────────────────────────────────────────
        story.append(Paragraph(bold_italic_to_xml(stripped), styles["normal"]))
        i += 1

    return story


def create_resume_pdf(markdown_content: str, filename_title: str = "Resume") -> BytesIO:
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=0.6 * inch,
        rightMargin=0.6 * inch,
        topMargin=0.6 * inch,
        bottomMargin=0.7 * inch,
        title=filename_title,
    )

    styles = create_styles()
    story = parse_resume_to_flowables(markdown_content, styles)

    # Optional: add page number or very light footer if desired
    # doc.addPageTemplates([...])

    doc.build(story)
    buffer.seek(0)
    return buffer

