"""
PDFStyles - Centralized PDF style definitions

This module provides a single source of truth for all PDF styling,
eliminating duplication between PDFGenerator and MarkdownProcessor.
"""

from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.colors import black
import Writer.Config


def get_pdf_styles():
    """
    Get all PDF styles in one place.

    Returns:
        dict: Dictionary containing all PDF styles:
            - 'base': Base styles from reportlab
            - 'title': Title page style
            - 'chapter': Chapter heading style
            - 'section': Section (H3) heading style
            - 'normal': Normal paragraph style
            - 'code': Code block style
    """
    styles = getSampleStyleSheet()

    # Determine font family
    font_family = "Times-Roman"  # Always available in reportlab
    if Writer.Config.PDF_FONT_FAMILY.lower() == "georgia":
        font_family = "Times-Roman"  # Georgia not available, fallback to Times

    # Title style for cover page
    title_style = ParagraphStyle(
        'PDFTitle',
        parent=styles['Title'],
        fontName=font_family,
        fontSize=Writer.Config.PDF_TITLE_SIZE,
        textColor=black,
        alignment=1,  # Center
        spaceAfter=30
    )

    # Chapter heading style
    chapter_style = ParagraphStyle(
        'PDFChapter',
        parent=styles['Heading1'],
        fontName=font_family,
        fontSize=Writer.Config.PDF_CHAPTER_SIZE,
        textColor=black,
        spaceBefore=30,
        spaceAfter=20
    )

    # Section heading style (H3)
    section_style = ParagraphStyle(
        'PDFSection',
        parent=styles['Heading2'],
        fontName='Times-Bold',
        fontSize=14,
        textColor=black,
        spaceBefore=12,
        spaceAfter=6
    )

    # Normal paragraph style
    normal_style = ParagraphStyle(
        'PDFNormal',
        parent=styles['Normal'],
        fontName=font_family,
        fontSize=Writer.Config.PDF_FONT_SIZE,
        textColor=black,
        spaceAfter=12
    )

    # Code block style
    code_style = ParagraphStyle(
        'PDFCode',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=10,
        leftIndent=0.5,
        textColor=black,
        backgroundColor=(0.95, 0.95, 0.95)
    )

    return {
        'base': styles,
        'title': title_style,
        'chapter': chapter_style,
        'section': section_style,
        'normal': normal_style,
        'code': code_style,
        'font_family': font_family
    }
