"""
MarkdownProcessor - Handles conversion of markdown to ReportLab-compatible elements

This module provides a clean interface for converting markdown content
to ReportLab Paragraph elements with proper formatting support.
"""

import re
from reportlab.platypus import Paragraph
from reportlab.lib.units import inch
from Writer.PDFStyles import get_pdf_styles


class MarkdownProcessor:
    """Processes markdown content and converts it to ReportLab elements"""

    def __init__(self, pdf_styles=None):
        """
        Initialize with custom styles or use defaults from PDFStyles.

        Args:
            pdf_styles: Optional dict of PDF styles. If None, uses get_pdf_styles()
        """
        self.pdf_styles = pdf_styles or get_pdf_styles()
        self.styles = self.pdf_styles['base']
        self.section_style = self.pdf_styles['section']
        self.normal_style = self.pdf_styles['normal']

    def process_content(self, markdown_content):
        """
        Convert markdown content to list of ReportLab elements

        Args:
            markdown_content: Raw markdown string

        Returns:
            list of ReportLab elements (Paragraph, Spacer, etc.)
        """
        elements = []

        # Split content by lines to handle different markdown structures
        lines = markdown_content.split('\n')
        current_paragraph = []
        in_code_block = False

        for line in lines:
            # Handle code blocks
            if line.strip().startswith('```'):
                in_code_block = not in_code_block
                continue

            if in_code_block:
                # Add code as preformatted text
                if current_paragraph:
                    elements.extend(self._process_paragraph(current_paragraph))
                    current_paragraph = []
                elements.append(self._create_code_block(line))
                continue

            # Handle headings
            if line.startswith('### '):
                # Section headers within chapters
                if current_paragraph:
                    elements.extend(self._process_paragraph(current_paragraph))
                    current_paragraph = []

                section_title = line[4:].strip()
                elements.append(Paragraph(section_title, self.section_style))
                continue

            # Handle chapter breaks
            if line.strip() == '---':
                if current_paragraph:
                    elements.extend(self._process_paragraph(current_paragraph))
                    current_paragraph = []
                continue

            # Handle empty lines (paragraph breaks)
            if not line.strip():
                if current_paragraph:
                    elements.extend(self._process_paragraph(current_paragraph))
                    current_paragraph = []
                continue

            # Add to current paragraph
            current_paragraph.append(line)

        # Process any remaining content
        if current_paragraph:
            elements.extend(self._process_paragraph(current_paragraph))

        return elements

    def _process_paragraph(self, lines):
        """Process a paragraph and return ReportLab elements"""
        if not lines:
            return []

        paragraph_text = ' '.join(lines)

        # Process inline formatting directly with regex
        return self._process_inline_formatting(paragraph_text)

    def _process_inline_formatting(self, text):
        """
        Process inline formatting like bold and italic using ReportLab XML markup.

        Converts markdown to ReportLab XML tags for proper inline formatting.
        Returns a single Paragraph with embedded formatting.
        """
        if not text or not text.strip():
            return []

        # Convert markdown to ReportLab XML tags
        # Process in order: bold+italic (***), bold (**), italic (*)

        # Bold + Italic: *** or ___ (must be processed first)
        text = re.sub(r'\*\*\*(.+?)\*\*\*', r'<b><i>\1</i></b>', text)
        text = re.sub(r'___(.+?)___', r'<b><i>\1</i></b>', text)

        # Bold: ** or __
        text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
        text = re.sub(r'__(.+?)__', r'<b>\1</b>', text)

        # Italic: * or _
        text = re.sub(r'\*(.+?)\*', r'<i>\1</i>', text)
        text = re.sub(r'_(.+?)_', r'<i>\1</i>', text)

        # Create a single Paragraph with inline formatting
        return [Paragraph(text, self.normal_style)]

    def _create_code_block(self, text):
        """Create a code block element (simplified)"""
        # Use centralized code style from PDFStyles
        return Paragraph(text, self.pdf_styles['code'])

    def process_chapter_title(self, chapter_line):
        """
        Process a chapter title line and extract display title

        Args:
            chapter_line: Line like "## Chapter 1: The Adventure Begins"

        Returns:
            tuple: (chapter_number, display_title)
        """
        # Extract chapter number
        match = re.match(r'##\s+(?:Chapter\s+)?(\d+)(?::?\s*(.*))?', chapter_line)
        if match:
            chapter_num = match.group(1)
            title = match.group(2) or f"Chapter {chapter_num}"
            return chapter_num, title

        # Fallback if pattern doesn't match
        return None, chapter_line.strip()

    def create_title_page(self, title, font_family="Times-Roman", font_size=24):
        """Create a title page element"""
        from reportlab.platypus import Spacer, PageBreak

        # Use centralized title style from PDFStyles
        elements = [
            Spacer(1, 2 * inch),
            Paragraph(title, self.pdf_styles['title']),
            Spacer(1, 1.5 * inch),
            PageBreak()
        ]

        return elements
