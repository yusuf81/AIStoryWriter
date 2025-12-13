"""
Tests for MarkdownProcessor module
"""

import pytest
from unittest.mock import MagicMock
from Writer.MarkdownProcessor import MarkdownProcessor


class TestMarkdownProcessor:
    """Test the MarkdownProcessor class"""

    @pytest.fixture
    def processor(self):
        """Create a MarkdownProcessor instance"""
        return MarkdownProcessor()

    def test_process_simple_paragraph(self, processor):
        """Test processing simple paragraph without formatting"""
        content = "This is a simple paragraph."

        elements = processor.process_content(content)

        assert len(elements) == 1
        assert "This is a simple paragraph" in str(elements[0])

    def test_process_bold_text(self, processor):
        """Test that bold formatting is preserved"""
        content = "This has **bold text** in it."

        elements = processor.process_content(content)

        # Should have bold and normal text elements
        assert len(elements) >= 1

        # Convert to string to check content
        element_strs = [str(e) for e in elements]
        combined = ' '.join(element_strs)

        assert "bold text" in combined

    def test_process_italic_text(self, processor):
        """Test that italic formatting is preserved"""
        content = "This has *italic text* in it."

        elements = processor.process_content(content)

        element_strs = [str(e) for e in elements]
        combined = ' '.join(element_strs)

        assert "italic text" in combined

    def test_process_paragraph_breaks(self, processor):
        """Test proper paragraph separation"""
        content = """First paragraph.

Second paragraph.

Third paragraph."""

        elements = processor.process_content(content)

        # Should create separate Paragraph elements
        from reportlab.platypus import Paragraph
        paragraph_count = sum(1 for e in elements if isinstance(e, Paragraph))

        assert paragraph_count == 3, f"Expected 3 paragraphs, got {paragraph_count}"

    def test_process_section_headers(self, processor):
        """Test H3 headers within chapters"""
        content = """Regular content.

### Section Header
Section content here."""

        elements = processor.process_content(content)

        element_strs = [str(e) for e in elements]

        assert "Section Header" in ' '.join(element_strs)

    def test_process_chapter_titles(self, processor):
        """Test chapter title extraction"""
        # Test with "Chapter 1: Title" format
        num, title = processor.process_chapter_title("## Chapter 1: The Adventure Begins")
        assert num == "1"
        assert title == "The Adventure Begins"

        # Test with "Chapter 1" only
        num, title = processor.process_chapter_title("## Chapter 1")
        assert num == "1"
        assert title == "Chapter 1"

        # Test with just number
        num, title = processor.process_chapter_title("## 1: Simple Title")
        assert num == "1"
        assert title == "Simple Title"

    def test_create_title_page(self, processor):
        """Test title page creation"""
        title_page = processor.create_title_page("Test Story")

        # Should have Spacer, Paragraph, Spacer, PageBreak
        from reportlab.platypus import Spacer, Paragraph, PageBreak

        spacer_count = sum(1 for e in title_page if isinstance(e, Spacer))
        paragraph_count = sum(1 for e in title_page if isinstance(e, Paragraph))
        pagebreak_count = sum(1 for e in title_page if isinstance(e, PageBreak))

        assert spacer_count == 2
        assert paragraph_count == 1
        assert pagebreak_count == 1
        assert "Test Story" in str(title_page[1])

    def test_process_mixed_formatting(self, processor):
        """Test text with mixed bold and italic"""
        content = "This has **bold** and *italic* and ***both*** text."

        elements = processor.process_content(content)

        element_strs = [str(e) for e in elements]
        combined = ' '.join(element_strs)

        assert "bold" in combined
        assert "italic" in combined
        assert "both" in combined

    def test_empty_content(self, processor):
        """Test handling of empty content"""
        elements = processor.process_content("")
        assert len(elements) == 0

    def test_code_blocks(self, processor):
        """Test handling of code blocks (basic)"""
        content = """```
def hello():
    print("Hello")
```"""

        elements = processor.process_content(content)

        # Should have at least one element
        assert len(elements) > 0

    def test_nested_bold_italic(self, processor):
        """Test nested formatting: bold with italic inside"""
        content = "This has **bold with *italic* inside** text"

        elements = processor.process_content(content)

        # Should create single Paragraph with nested XML tags
        assert len(elements) >= 1

        element_strs = [str(e) for e in elements]
        combined = ' '.join(element_strs)

        # Should have both bold and italic
        assert "bold with" in combined or "<b>" in combined
        assert "italic" in combined or "<i>" in combined

    def test_adjacent_formatting(self, processor):
        """Test adjacent formatting: bold immediately followed by italic"""
        content = "**bold***italic* normal"

        elements = processor.process_content(content)

        element_strs = [str(e) for e in elements]
        combined = ' '.join(element_strs)

        # Should separate bold and italic correctly
        assert "bold" in combined
        assert "italic" in combined
        assert "normal" in combined

    def test_multiple_formatting_same_line(self, processor):
        """Test multiple different formatting on same line"""
        content = "**bold** and *italic* and **more bold**"

        elements = processor.process_content(content)

        element_strs = [str(e) for e in elements]
        combined = ' '.join(element_strs)

        # All text should be preserved
        assert "bold" in combined
        assert "italic" in combined
        assert "and" in combined
        assert "more bold" in combined or "more" in combined

    def test_empty_formatting_markers(self, processor):
        """Test empty formatting markers don't break"""
        content = "This has ** ** empty bold and * * empty italic"

        elements = processor.process_content(content)

        # Should handle gracefully without errors
        assert len(elements) >= 1

        element_strs = [str(e) for e in elements]
        combined = ' '.join(element_strs)

        # Text should still be there
        assert "This has" in combined
        assert "empty" in combined

    def test_mismatched_markers(self, processor):
        """Test mismatched markers are handled gracefully"""
        content = "This has **bold* mismatched and *italic** wrong"

        elements = processor.process_content(content)

        # Should not crash, handle gracefully
        assert len(elements) >= 1

        element_strs = [str(e) for e in elements]
        combined = ' '.join(element_strs)

        # Text should be preserved
        assert "This has" in combined
        assert "mismatched" in combined or "wrong" in combined

    def test_formatting_at_boundaries(self, processor):
        """Test formatting at start and end of text"""
        content = "**bold at start** and *italic at end*"

        elements = processor.process_content(content)

        element_strs = [str(e) for e in elements]
        combined = ' '.join(element_strs)

        # Should handle boundary cases
        assert "bold at start" in combined or "bold" in combined
        assert "italic at end" in combined or "italic" in combined

    def test_single_character_formatting(self, processor):
        """Test formatting with single character"""
        content = "**a** single *b* char"

        elements = processor.process_content(content)

        element_strs = [str(e) for e in elements]
        combined = ' '.join(element_strs)

        # Single characters should be formatted too
        assert "a" in combined
        assert "b" in combined
        assert "single" in combined
        assert "char" in combined