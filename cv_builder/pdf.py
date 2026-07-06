"""Deterministic PDF rendering from tailored CV content.

Layout is fixed code, not model output, so the same content always renders
the same way regardless of what Claude produced.
"""

from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    ListFlowable,
    ListItem,
)


def _styles():
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="NameHeader",
            parent=styles["Title"],
            alignment=TA_CENTER,
            spaceAfter=4,
        )
    )
    styles.add(
        ParagraphStyle(
            name="ContactLine",
            parent=styles["Normal"],
            alignment=TA_CENTER,
            spaceAfter=12,
            textColor="#444444",
        )
    )
    styles.add(
        ParagraphStyle(
            name="SectionHeading",
            parent=styles["Heading2"],
            spaceBefore=14,
            spaceAfter=6,
            borderPadding=0,
        )
    )
    styles.add(
        ParagraphStyle(
            name="EntryHeading",
            parent=styles["Normal"],
            fontSize=11,
            leading=14,
            spaceBefore=6,
            spaceAfter=2,
        )
    )
    return styles


def render_cv(content: dict, output_path: str) -> str:
    styles = _styles()
    doc = SimpleDocTemplate(
        output_path,
        pagesize=LETTER,
        topMargin=0.6 * inch,
        bottomMargin=0.6 * inch,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
    )

    flow = []

    contact = content["contact"]
    flow.append(Paragraph(contact.get("full_name", ""), styles["NameHeader"]))

    contact_bits = [
        contact.get(key)
        for key in ("email", "phone", "address", "linkedin", "website")
        if contact.get(key)
    ]
    if contact_bits:
        flow.append(Paragraph(" | ".join(contact_bits), styles["ContactLine"]))

    if content.get("summary"):
        flow.append(Paragraph("Summary", styles["SectionHeading"]))
        flow.append(Paragraph(content["summary"], styles["Normal"]))

    experiences = content.get("experiences") or []
    if experiences:
        flow.append(Paragraph("Experience", styles["SectionHeading"]))
        for exp in experiences:
            dates = " - ".join(
                d for d in (exp.get("start_date"), exp.get("end_date")) if d
            )
            heading = f"<b>{exp.get('role', '')}</b>, {exp.get('company', '')}"
            if exp.get("location"):
                heading += f" &mdash; {exp['location']}"
            if dates:
                heading += f" &nbsp;&nbsp;<i>{dates}</i>"
            flow.append(Paragraph(heading, styles["EntryHeading"]))

            bullets = exp.get("bullets") or []
            if bullets:
                flow.append(
                    ListFlowable(
                        [ListItem(Paragraph(b, styles["Normal"])) for b in bullets],
                        bulletType="bullet",
                        leftIndent=16,
                    )
                )

    education = content.get("education") or []
    if education:
        flow.append(Paragraph("Education", styles["SectionHeading"]))
        for edu in education:
            dates = " - ".join(
                d for d in (edu.get("start_date"), edu.get("end_date")) if d
            )
            line = f"<b>{edu.get('degree', '')} {edu.get('field', '')}</b>, {edu.get('institution', '')}".strip()
            if dates:
                line += f" &nbsp;&nbsp;<i>{dates}</i>"
            flow.append(Paragraph(line, styles["EntryHeading"]))

    skills = content.get("skills") or []
    if skills:
        flow.append(Paragraph("Skills", styles["SectionHeading"]))
        flow.append(Paragraph(", ".join(skills), styles["Normal"]))

    doc.build(flow)
    return output_path
