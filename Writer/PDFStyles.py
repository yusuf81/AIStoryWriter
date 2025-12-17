"""
PDFStyles - Centralized PDF style definitions

This module provides a single source of truth for all PDF styling,
eliminating duplication between PDFGenerator and MarkdownProcessor.
"""

from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.colors import black
import Writer.Config


def _get_eye_comfort_font():
    """
    Get the best available eye-comfort font with proper fallback chain.

    Returns:
        str: Available font name in order of preference:
            Georgia → Palatino → Times-Roman
    """
    if Writer.Config.PDF_FONT_FAMILY.lower() == "georgia":
        try:
            from reportlab.pdfbase import pdfmetrics
            pdfmetrics.getFont('Georgia')  # Check if Georgia is available
            return "Georgia"
        except:
            pass

    # Try Palatino as second choice
    try:
        from reportlab.pdfbase import pdfmetrics
        pdfmetrics.getFont('Palatino')  # Check if Palatino is available
        return "Palatino"
    except:
        pass

    # Always available fallback
    return "Times-Roman"


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

    # Determine font family with better fallback chain for eye comfort
    font_family = "Times-Roman"  # Always available in reportlab

    # Try to use eye-friendly fonts in order of preference
    font_family = _get_eye_comfort_font()

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

    # Normal paragraph style with improved readability
    # Calculate leading based on line height ratio for comfortable reading
    leading = Writer.Config.PDF_FONT_SIZE * Writer.Config.PDF_LINE_HEIGHT

    normal_style = ParagraphStyle(
        'PDFNormal',
        parent=styles['Normal'],
        fontName=font_family,
        fontSize=Writer.Config.PDF_FONT_SIZE,
        textColor=black,
        leading=leading,
        firstLineIndent=Writer.Config.PDF_PARAGRAPH_FIRST_LINE_INDENT,
        spaceAfter=Writer.Config.PDF_PARAGRAPH_SPACING,
        spaceBefore=0  # No space before paragraphs (handled by firstLineIndent)
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
