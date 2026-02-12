#!/usr/bin/env python3
"""
Generate a professional PDF brief for Sourcepass Strategic Outreach Plan.
Uses reportlab for better font/encoding support.
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT

OUTPUT_PATH = "/Users/tybibas/Desktop/SOURCEPASS_Strategic_Brief.pdf"

def generate_brief():
    doc = SimpleDocTemplate(OUTPUT_PATH, pagesize=letter,
                            leftMargin=0.75*inch, rightMargin=0.75*inch,
                            topMargin=0.75*inch, bottomMargin=0.75*inch)
    
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#14283C'),
        alignment=TA_CENTER,
        spaceAfter=6
    )
    
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.HexColor('#666666'),
        alignment=TA_CENTER,
        spaceAfter=20
    )
    
    section_style = ParagraphStyle(
        'Section',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#143C64'),
        spaceBefore=15,
        spaceAfter=8
    )
    
    subsection_style = ParagraphStyle(
        'Subsection',
        parent=styles['Heading3'],
        fontSize=11,
        textColor=colors.HexColor('#333333'),
        spaceBefore=10,
        spaceAfter=4
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#444444'),
        spaceAfter=8,
        leading=14
    )
    
    bullet_style = ParagraphStyle(
        'Bullet',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#444444'),
        leftIndent=15,
        spaceAfter=4,
        leading=13
    )
    
    story = []
    
    # Title
    story.append(Paragraph("Strategic Outreach Brief", title_style))
    story.append(Paragraph("SOURCEPASS Client Acquisition Strategy", subtitle_style))
    
    # Executive Summary
    story.append(Paragraph("Executive Summary", section_style))
    story.append(Paragraph(
        "Analysis of <b>18 Sourcepass case studies</b> reveals that Healthcare/Medical is the highest-converting "
        "target industry, driven by compliance requirements (HIPAA, SOC 2) that make IT partnerships "
        "mission-critical. Non-Profit is a strong secondary target due to low competition and accessible "
        "gatekeepers. Commercial sectors should be pursued opportunistically.",
        body_style
    ))
    
    # Resource Allocation Table
    story.append(Paragraph("Recommended Resource Allocation", section_style))
    
    tier_data = [
        ['TIER', 'INDUSTRY', 'EFFORT', 'RATIONALE'],
        ['1', 'Healthcare & Medical', '60%', '6 case studies, highest ROI, clearest triggers'],
        ['2', 'Non-Profit & Housing', '25%', 'Low competition, accessible gatekeepers'],
        ['3', 'Real Estate & Commercial', '15%', 'Opportunistic - pursue on trigger events'],
        ['4', 'Government & Education', '0%', 'RFP-heavy, long cycles - only if strong trigger'],
    ]
    
    tier_table = Table(tier_data, colWidths=[0.5*inch, 1.8*inch, 0.6*inch, 3.5*inch])
    tier_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#143C64')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#E8F5E9')),  # Green tint
        ('BACKGROUND', (0, 2), (-1, 2), colors.HexColor('#E3F2FD')),  # Blue tint
        ('BACKGROUND', (0, 3), (-1, 3), colors.HexColor('#FFF3E0')),  # Orange tint
        ('BACKGROUND', (0, 4), (-1, 4), colors.HexColor('#F5F5F5')),  # Gray tint
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CCCCCC')),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(tier_table)
    story.append(Spacer(1, 15))
    
    # Key Findings
    story.append(Paragraph("Key Research Findings", section_style))
    
    story.append(Paragraph("Healthcare: Why It Wins", subsection_style))
    story.append(Paragraph("&#8226; Compliance is existential: Without HIPAA/SOC 2 certification, organizations cannot operate", bullet_style))
    story.append(Paragraph("&#8226; Quotable outcomes: \"Most professional and thorough audit they had ever conducted\"", bullet_style))
    story.append(Paragraph("&#8226; Clear decision-makers: CIO, CISO, Compliance Officer, CEO (smaller practices)", bullet_style))
    story.append(Paragraph("&#8226; Strong trigger events: Ransomware attacks, audits, IT leadership turnover", bullet_style))
    
    story.append(Paragraph("Non-Profit: The Hidden Opportunity", subsection_style))
    story.append(Paragraph("&#8226; Enterprise MSPs ignore this segment - Sourcepass has limited competition", bullet_style))
    story.append(Paragraph("&#8226; Budget-conscious messaging resonates: \"Enterprise-grade IT without enterprise prices\"", bullet_style))
    story.append(Paragraph("&#8226; Executive Directors are accessible and make decisions quickly", bullet_style))
    
    # Signal-Driven Triggers
    story.append(Paragraph("Signal-Driven Trigger Events", section_style))
    story.append(Paragraph("Monitor these events for high-intent outreach opportunities:", body_style))
    
    story.append(Paragraph("Healthcare Triggers (Priority)", subsection_style))
    story.append(Paragraph("&#8226; New CIO/IT Director appointed (LinkedIn, Becker's Healthcare)", bullet_style))
    story.append(Paragraph("&#8226; HIPAA audit announced (press releases, industry news)", bullet_style))
    story.append(Paragraph("&#8226; Ransomware attack at peer organization (HIPAA Journal)", bullet_style))
    story.append(Paragraph("&#8226; IT leadership resignation/vacancy", bullet_style))
    
    story.append(Paragraph("Non-Profit Triggers", subsection_style))
    story.append(Paragraph("&#8226; Grant funding received for technology upgrades", bullet_style))
    story.append(Paragraph("&#8226; Office move or renovation announcement", bullet_style))
    story.append(Paragraph("&#8226; New Executive Director appointed", bullet_style))
    
    # Target Profiles
    story.append(Paragraph("Ideal Target Profiles", section_style))
    
    story.append(Paragraph("Healthcare Organizations", subsection_style))
    story.append(Paragraph("&#8226; Regional health systems (100-2,000 employees)", bullet_style))
    story.append(Paragraph("&#8226; Medical societies and associations", bullet_style))
    story.append(Paragraph("&#8226; FQHCs (Federally Qualified Health Centers)", bullet_style))
    story.append(Paragraph("&#8226; Specialty practices (fertility, GI, dental groups)", bullet_style))
    
    story.append(Paragraph("Target Titles (Priority Order)", subsection_style))
    story.append(Paragraph("1. Chief Information Officer (CIO)<br/>2. Chief Digital Information Officer (CDIO)<br/>3. VP of IT / IT Director<br/>4. Compliance Officer<br/>5. CEO (smaller practices &lt;100 employees)", body_style))
    
    # Messaging Pillars
    story.append(Paragraph("Core Messaging Pillars", section_style))
    
    pillars = [
        ['PILLAR', 'MESSAGE'],
        ['Compliance Partner', 'We don\'t just manage IT - we prepare you for audits and ensure you pass.'],
        ['48-Hour Emergency Response', 'When your IT Director leaves, we stabilize operations immediately.'],
        ['Quest Platform Visibility', 'Real-time dashboard so you always know your security posture.'],
        ['People-First', 'We become an extension of your team, not another vendor.'],
    ]
    
    pillar_table = Table(pillars, colWidths=[1.8*inch, 4.6*inch])
    pillar_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#143C64')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CCCCCC')),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#FAFAFA')),
    ]))
    story.append(pillar_table)
    story.append(Spacer(1, 15))
    
    # Next Steps Box
    next_steps_style = ParagraphStyle(
        'NextSteps',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#143C64'),
        spaceAfter=4,
        leading=14
    )
    
    story.append(Paragraph("<b>Recommended Next Steps</b>", next_steps_style))
    story.append(Paragraph("1. Build list of 50+ healthcare organizations with recent trigger events<br/>"
                           "2. Add 20-30 non-profit organizations to expand volume<br/>"
                           "3. Set up Google Alerts for HIPAA violations, CIO appointments, ransomware news",
                           body_style))
    
    # Build PDF
    doc.build(story)
    print(f"✓ PDF saved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    generate_brief()
