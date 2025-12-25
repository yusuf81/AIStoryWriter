#!/usr/bin/env python3
"""
Phase 2 RED Tests: PDF Advanced Styling Features
These tests verify advanced PDF formatting for professional book appearance.
"""

from unittest.mock import MagicMock, Mock, patch
import tempfile

# Mock termcolor before imports
import sys
sys.modules['termcolor'] = MagicMock()


class TestPDFAdvancedStyling:
    """RED Tests: These should fail with current implementation due to missing advanced features"""

    def test_chapter_title_formatting_with_numbers(self, mock_logger):
        """Test that chapter titles include proper numbering like 'Chapter 1: Title'"""
        from Writer.PDFGenerator import GeneratePDF

        markdown_content = """# Adventure Story

## Chapter 1

This is chapter 1 content.

## Chapter 2: The Journey Begins

This is chapter 2 content."""

        with patch('Writer.PDFGenerator.SimpleDocTemplate') as mock_doc:
            mock_build = Mock()
            mock_doc.return_value.build = mock_build

            with patch('os.makedirs'):
                with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
                    result, _ = GeneratePDF(
                        Mock(),
                        mock_logger(),
                        markdown_content,
                        tmp_file.name,
                        "Adventure Story"
                    )

            # Get the story elements
            story_elements = mock_build.call_args[0][0]

            # Extract chapter headers
            chapter_headers = []
            for element in story_elements:
                if hasattr(element, 'text'):
                    chapter_headers.append(element.text)

            # RED: Current implementation should have basic titles
            # Should have properly formatted chapter titles with numbering
            expected_chapter1 = "Chapter 1"
            expected_chapter2 = "Chapter 2: The Journey Begins"

            assert any(expected_chapter1 in str(header) for header in chapter_headers), \
                f"Should contain properly formatted chapter title '{expected_chapter1}'"
            assert any(expected_chapter2 in str(header) for header in chapter_headers), \
                f"Should contain properly formatted chapter title '{expected_chapter2}'"

    def test_page_numbers_appear_correctly(self, mock_logger):
        """Test that page numbers appear on all pages except title page"""
        from Writer.PDFGenerator import GeneratePDF

        markdown_content = """# My Title

## Chapter 1

Content for first chapter that should span multiple pages.

## Chapter 2

Content for second chapter."""

        # Mock SimpleDocTemplate to capture canvasmaker parameter
        with patch('Writer.PDFGenerator.SimpleDocTemplate') as mock_doc:
            mock_build = Mock()
            mock_doc.return_value.build = mock_build

            with patch('os.makedirs'):
                with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
                    result, _ = GeneratePDF(
                        Mock(),
                        mock_logger(),
                        markdown_content,
                        tmp_file.name,
                        "My Title"
                    )

            # RED: Should use NumberedCanvas for page numbers
            mock_doc.return_value.build.assert_called_once()

            # Verify canvasmaker parameter was set correctly
            build_call_args, build_call_kwargs = mock_doc.return_value.build.call_args
            canvasmaker = build_call_kwargs.get('canvasmaker')
            assert canvasmaker is not None, "Should use canvasmaker for page numbers"

            # The canvasmaker should be NumberedCanvas class (not an instance)
            assert canvasmaker.__name__ == 'NumberedCanvas', \
                f"Should be NumberedCanvas, got {canvasmaker.__name__}"

    def test_title_page_styling_is_centered_and_spaced(self, mock_logger):
        """Test that title page has proper styling with centering and spacing"""
        from Writer.PDFGenerator import GeneratePDF

        markdown_content = """# The Great Adventure

## Chapter 1

Story begins here."""

        with patch('Writer.PDFGenerator.SimpleDocTemplate') as mock_doc:
            mock_build = Mock()
            mock_doc.return_value.build = mock_build

            with patch('os.makedirs'):
                with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
                    result, _ = GeneratePDF(
                        Mock(),
                        mock_logger(),
                        markdown_content,
                        tmp_file.name,
                        "The Great Adventure"
                    )

            # Get story elements and find title page elements
            story_elements = mock_build.call_args[0][0]

            # Find the title element
            title_element = None
            for element in story_elements:
                if hasattr(element, 'text') and "The Great Adventure" in str(element.text):
                    title_element = element
                    break

            # RED: Should have properly styled title with centering
            assert title_element is not None, "Should have title element"

            # Check if title is centered (alignment=1)
            if hasattr(title_element, 'alignment'):
                assert title_element.alignment == 1, "Title should be centered"

    def test_section_headers_within_chapters(self, mock_logger):
        """Test that section headers (###) are properly styled within chapters"""
        from Writer.PDFGenerator import GeneratePDF

        markdown_content = """# Story

## Chapter 1

### Act I: The Beginning

Content for the first act.

### Act II: The Conflict

Content for the second act."""

        with patch('Writer.PDFGenerator.SimpleDocTemplate') as mock_doc:
            mock_build = Mock()
            mock_doc.return_value.build = mock_build

            with patch('os.makedirs'):
                with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
                    result, _ = GeneratePDF(
                        Mock(),
                        mock_logger(),
                        markdown_content,
                        tmp_file.name,
                        "Story"
                    )

            # Get story elements and find section headers
            story_elements = mock_build.call_args[0][0]

            # Find section header elements
            section_headers = []
            for element in story_elements:
                if hasattr(element, 'text'):
                    text = str(element.text)
                    if "Act I" in text or "Act II" in text:
                        section_headers.append(element)

            # RED: Should properly style section headers within chapters
            assert len(section_headers) >= 1, "Should have at least one section header"

            # Verify section header content
            section_texts = [str(sh.text) for sh in section_headers if hasattr(sh, 'text')]
            assert any("Act I: The Beginning" in text for text in section_texts)
            assert any("Act II: The Conflict" in text for text in section_texts)

    def test_paragraph_maintains_consistent_styling(self, mock_logger):
        """Test that all paragraphs maintain consistent styling throughout the document"""
        from Writer.PDFGenerator import GeneratePDF

        markdown_content = """# Consistent Styling Test

## Chapter 1

First paragraph with some content. This paragraph should use the same styling as other paragraphs.

Second paragraph with different content but same styling.

## Chapter 2

Another paragraph in chapter 2. This should have identical styling to chapter 1 paragraphs.

Final paragraph to test consistency across entire document."""

        with patch('Writer.PDFGenerator.SimpleDocTemplate') as mock_doc:
            mock_build = Mock()
            mock_doc.return_value.build = mock_build

            with patch('os.makedirs'):
                with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
                    result, _ = GeneratePDF(
                        Mock(),
                        mock_logger(),
                        markdown_content,
                        tmp_file.name,
                        "Consistent Styling Test"
                    )

            # Get paragraph elements
            story_elements = mock_build.call_args[0][0]

            # Find all paragraph elements (non-title, non-chapter)
            paragraphs = []
            for element in story_elements:
                if hasattr(element, 'style') and hasattr(element.style, 'name') and element.style.name == 'PDFNormal':
                    paragraphs.append(element)

            # RED: Should have consistent styling across all paragraphs
            assert len(paragraphs) >= 2, "Should have multiple paragraphs to compare"

            # Check that all paragraphs have consistent attributes
            if paragraphs:
                first_font = getattr(paragraphs[0].style, 'fontName', None)
                first_font_size = getattr(paragraphs[0].style, 'fontSize', None)
                first_first_line_indent = getattr(paragraphs[0].style, 'firstLineIndent', None)
                first_space_after = getattr(paragraphs[0].style, 'spaceAfter', None)
                first_leading = getattr(paragraphs[0].style, 'leading', None)

                for para in paragraphs[1:]:
                    para_style = para.style
                    assert getattr(para_style, 'fontName', None) == first_font, \
                        "All paragraphs should have consistent font"
                    assert getattr(para_style, 'fontSize', None) == first_font_size, \
                        "All paragraphs should have consistent font size"
                    assert getattr(para_style, 'firstLineIndent', None) == first_first_line_indent, \
                        "All paragraphs should have consistent first line indent"
                    assert getattr(para_style, 'spaceAfter', None) == first_space_after, \
                        "All paragraphs should have consistent spacing"
                    assert getattr(para_style, 'leading', None) == first_leading, \
                        "All paragraphs should have consistent line height"

    def test_document_structure_maintains_proper_flow(self, mock_logger):
        """Test that document maintains proper flow: Title page → PageBreak → Chapter → Content"""
        from Writer.PDFGenerator import GeneratePDF
        from reportlab.platypus import PageBreak

        markdown_content = """# Epic Story

## Chapter 1: The Adventure

Chapter content here.

## Chapter 2: The Journey

More chapter content."""

        with patch('Writer.PDFGenerator.SimpleDocTemplate') as mock_doc:
            mock_build = Mock()
            mock_doc.return_value.build = mock_build

            with patch('os.makedirs'):
                with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
                    result, _ = GeneratePDF(
                        Mock(),
                        mock_logger(),
                        markdown_content,
                        tmp_file.name,
                        "Epic Story"
                    )

            # Analyze document structure
            story_elements = mock_build.call_args[0][0]

            # Count page breaks to verify structure
            page_breaks = 0
            has_title = False
            has_chapter1 = False
            has_chapter2 = False

            for element in story_elements:
                if isinstance(element, type(PageBreak())):
                    page_breaks += 1
                elif hasattr(element, 'text'):
                    text = str(element.text)
                    if "Epic Story" in text:
                        has_title = True
                    elif "Chapter 1" in text:
                        has_chapter1 = True
                    elif "Chapter 2" in text:
                        has_chapter2 = True

            # RED: Should have proper document structure
            assert has_title, "Should have title"
            assert has_chapter1, "Should have Chapter 1"
            assert has_chapter2, "Should have Chapter 2"

            # Should have page breaks: at least 2 (title→ch1, ch1→ch2)
            assert page_breaks >= 2, f"Should have at least 2 page breaks for proper structure, got {page_breaks}"
