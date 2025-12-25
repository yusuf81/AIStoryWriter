#!/usr/bin/env python3
"""
Phase 1 RED Tests: PDF Generation Readability Issues
These tests verify the real problems with PDF generation that users find eye-straining.
"""

from unittest.mock import MagicMock, Mock, patch
import tempfile

# Mock termcolor before imports
import sys
sys.modules['termcolor'] = MagicMock()


class TestPDFGenerationReadability:
    """RED Tests: These should fail with current implementation due to readability issues"""

    def test_first_chapter_starts_on_new_page_after_title(self, mock_logger):
        """Test that first chapter starts on a new page after title (current implementation doesn't)"""
        from Writer.PDFGenerator import GeneratePDF

        # Create markdown content with title and first chapter
        markdown_content = """# My Story Title

## Chapter 1: The Beginning

This is the first chapter content that should start on a new page after the title page, not immediately after it.

The current implementation puts it on the same page as the title which doesn't look like a proper book."""

        # Mock SimpleDocTemplate to track story elements
        with patch('Writer.PDFGenerator.SimpleDocTemplate') as mock_doc:
            mock_build = Mock()
            mock_doc.return_value.build = mock_build

            with patch('os.makedirs'):
                with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
                    result, message = GeneratePDF(
                        Mock(),
                        mock_logger(),
                        markdown_content,
                        tmp_file.name,
                        "My Story Title"
                    )

            # Assert: PDF generation succeeded
            assert result is True

            # Get the story elements that would be built
            story_elements = mock_build.call_args[0][0]

            # Current implementation should NOT have PageBreak after title (this is the bug)
            # After fixing, there should be both title page elements AND a PageBreak before first chapter
            elements_after_title = []
            found_title = False
            found_first_paragraph = False

            for i, element in enumerate(story_elements):
                if hasattr(element, 'getPlainText'):
                    text = element.getPlainText()
                    if "My Story Title" in text:
                        found_title = True
                        continue
                    elif "This is the first chapter content" in text:
                        found_first_paragraph = True

                # Check if there's a PageBreak between title and first paragraph
                if found_title and not found_first_paragraph:
                    elements_after_title.append(element)

            # RED: Current implementation lacks PageBreak after title
            # Element types should contain PageBreak class instance between title and chapter
            from reportlab.platypus import PageBreak
            has_page_break = any(isinstance(elem, type(PageBreak())) for elem in elements_after_title)
            assert has_page_break, "First chapter should start on a new page after title"

    def test_margins_are_not_cramped(self, mock_logger):
        """Test that margins are comfortable to read, not cramped 72px"""
        from Writer.PDFGenerator import GeneratePDF

        markdown_content = """# Test Story

## Chapter 1

Content with proper margins."""

        with patch('Writer.PDFGenerator.SimpleDocTemplate') as mock_doc:
            mock_doc.return_value.build = Mock()

            with patch('os.makedirs'):
                with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
                    result, _ = GeneratePDF(
                        Mock(),
                        mock_logger(),
                        markdown_content,
                        tmp_file.name,
                        "Test Story"
                    )

            # Get SimpleDocTemplate initialization arguments
            doc_init_call = mock_doc.call_args
            doc_kwargs = doc_init_call[1] if doc_init_call else {}

            # Current implementation uses cramped 72px margins all around
            # Should use improved margins for better readability
            current_left_margin = doc_kwargs.get('leftMargin', 72)
            current_right_margin = doc_kwargs.get('rightMargin', 72)
            current_top_margin = doc_kwargs.get('topMargin', 72)
            current_bottom_margin = doc_kwargs.get('bottomMargin', 72)

            # RED: Current uses 72px which is too cramped
            # Should be more spacious (e.g., 90px左右, 75px上下 as planned)
            assert current_left_margin > 72, "Left margin should be wider than cramped 72px"
            assert current_right_margin > 72, "Right margin should be wider than cramped 72px"
            assert current_top_margin != 72, "Top margin should be optimized for readability"

    def test_paragraph_has_first_line_indent(self, mock_logger):
        """Test that paragraphs have first-line indentation for book-like appearance"""
        from Writer.PDFStyles import get_pdf_styles

        # Get current paragraph style
        pdf_styles = get_pdf_styles()
        normal_style = pdf_styles.get('normal')

        if normal_style:
            # Check if firstLineIndent is set for book-like appearance
            first_line_indent = getattr(normal_style, 'firstLineIndent', 0)

            # RED: Current implementation likely has no first line indent
            # Should have first line indent (e.g., 12pt) for book appearance
            assert first_line_indent > 0, "Paragraphs should have first-line indentation"

    def test_paragraph_spacing_between_paragraphs(self, mock_logger):
        """Test that there's proper spacing between paragraphs"""
        from Writer.PDFStyles import get_pdf_styles

        pdf_styles = get_pdf_styles()
        normal_style = pdf_styles.get('normal')

        if normal_style:
            # Check spacing after paragraphs
            space_after = getattr(normal_style, 'spaceAfter', 0)

            # RED: Current implementation likely has minimal spacing
            # Should have space after paragraphs (e.g., 6pt) for readability
            assert space_after > 0, "Should have spacing between paragraphs"

    def test_font_fallback_chain_for_eye_comfort(self, mock_logger):
        """Test that font fallback chain provides eye-comfortable fonts"""
        from Writer.PDFStyles import get_pdf_styles

        pdf_styles = get_pdf_styles()
        font_family = pdf_styles.get('font_family', 'Times-Roman')

        # RED: Current implementation may have limited font fallback
        # Should have eye-friendly font chain: Georgia → Palatino → Times-Roman
        # For now test that we at least have a serif font, but later test for Georgia fallback
        from reportlab.pdfbase import pdfmetrics

        # Check if Georgia is available and would be preferred
        try:
            pdfmetrics.getFont('Georgia')
            georgia_available = True
        except BaseException:
            georgia_available = False

        # If Georgia is available, it should be used as primary
        if georgia_available:
            assert 'Georgia' in font_family or font_family == 'Georgia', \
                "Georgia should be preferred for eye comfort when available"
        else:
            # Should at least use a readable serif font
            readable_fonts = ['Times-Roman', 'Palatino', 'Georgia']
            assert font_family in readable_fonts, \
                f"Font should be readable serif, got: {font_family}"

    def test_line_height_for_eye_comfort(self, mock_logger):
        """Test that line height is comfortable for reading"""
        from Writer.PDFStyles import get_pdf_styles

        pdf_styles = get_pdf_styles()
        normal_style = pdf_styles.get('normal')

        if normal_style:
            # Check line height/leading
            leading = getattr(normal_style, 'leading', normal_style.fontSize)
            font_size = getattr(normal_style, 'fontSize', 12)

            # Calculate line height ratio
            line_height_ratio = leading / font_size if font_size > 0 else 1.0

            # RED: Current line height might be too tight
            # Should be comfortable for reading (e.g., 1.15 ratio)
            assert line_height_ratio >= 1.15, \
                f"Line height ratio {line_height_ratio:.2f} should be >= 1.15 for comfort"
