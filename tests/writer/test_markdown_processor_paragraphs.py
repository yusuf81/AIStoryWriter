#!/usr/bin/env python3
"""
Phase 1 RED Tests: Paragraph Processing in MarkdownProcessor
These tests verify that MarkdownProcessor preserves paragraph breaks and supports
first-line indentation and spacing between paragraphs.
"""

import pytest
from unittest.mock import MagicMock, Mock, patch
import sys

# Mock termcolor before imports
sys.modules['termcolor'] = MagicMock()


class TestMarkdownProcessorParagraphs:
    """RED Tests: These should fail with current implementation"""

    def test_preserves_paragraph_breaks(self):
        """Test that multiple paragraphs are preserved as separate elements"""
        from Writer.MarkdownProcessor import MarkdownProcessor

        # Create markdown with multiple paragraphs
        markdown_content = """First paragraph with some text. This should be a separate paragraph with multiple sentences that form a complete thought.

Second paragraph with different content. There should be a clear separation between this and the previous paragraph.

Third paragraph that demonstrates proper paragraph handling in the MarkdownProcessor."""

        processor = MarkdownProcessor()

        # Act: Process the markdown
        result = processor.process_content(markdown_content)

        # Assert: Should return multiple paragraph elements
        # Current implementation joins ALL lines with spaces, creating one big paragraph
        assert len(result) == 3, f"Expected 3 paragraph elements, got {len(result)}"

        # Verify each paragraph is separate (not joined with spaces)
        assert "First paragraph with some text" in str(result[0])
        assert "Second paragraph with different content" in str(result[1])
        assert "Third paragraph that demonstrates" in str(result[2])

    def test_first_line_indent_style(self):
        """Test that paragraphs can have first-line indentation"""
        from Writer.MarkdownProcessor import MarkdownProcessor

        markdown_content = """This is a paragraph that should have first-line indentation when styled properly.

This is another paragraph that should also have first-line indentation in the final PDF output."""

        processor = MarkdownProcessor()

        # Act: Process markdown
        result = processor.process_content(markdown_content)

        # Assert: Paragraphs should be separate elements
        assert len(result) == 2, f"Expected 2 paragraphs, got {len(result)}"

        # Current processing creates one block, should create separate paragraphs
        # This assertion will fail with current implementation
        assert result[0] != result[1], "Paragraphs should be distinct elements"

    def test_mixed_paragraph_style(self):
        """Test mixed style: first-line indent + spacing between paragraphs"""
        from Writer.MarkdownProcessor import MarkdownProcessor

        # Content that should have both first-line indent and spacing
        markdown_content = """Chapter content with multiple paragraphs. Each paragraph should start with indent and have space after it.

Second paragraph demonstrates the mixed style approach. The combination of indentation and spacing creates better readability.

Third paragraph shows consistent styling throughout the document."""

        processor = MarkdownProcessor()

        # Act: Process the content
        result = processor.process_content(markdown_content)

        # Assert: Should have 3 separate paragraph elements
        assert len(result) == 3, f"Expected 3 paragraphs for mixed style, got {len(result)}"

        # Verify content is in separate paragraphs (not one big text block)
        for i, paragraph in enumerate(result):
            assert f"Chapter content" in str(paragraph) if i == 0 else True
            assert f"Second paragraph" in str(paragraph) if i == 1 else True
            assert f"Third paragraph" in str(paragraph) if i == 2 else True

    def test_empty_lines_between_paragraphs_preserved(self):
        """Test that empty lines between paragraphs are properly handled"""
        from Writer.MarkdownProcessor import MarkdownProcessor

        markdown_content = """First paragraph.

This has two empty lines before next paragraph.

Third paragraph."""

        processor = MarkdownProcessor()

        # Act: Process content with varying empty line gaps
        result = processor.process_content(markdown_content)

        # Assert: Should still create 3 distinct paragraphs
        assert len(result) == 3, f"Expected 3 paragraphs despite empty lines, got {len(result)}"

    def test_single_paragraph_unchanged(self):
        """Test that single paragraph content works correctly"""
        from Writer.MarkdownProcessor import MarkdownProcessor

        markdown_content = "This is a single paragraph without any line breaks."

        processor = MarkdownProcessor()

        # Act: Process single paragraph
        result = processor.process_content(markdown_content)

        # Assert: Should return single paragraph
        assert len(result) == 1, f"Expected 1 paragraph for single content, got {len(result)}"
        assert "single paragraph" in str(result[0])

    def test_markdown_processor_paragraph_boundary_detection(self):
        """Test detection of paragraph boundaries in complex content"""
        from Writer.MarkdownProcessor import MarkdownProcessor

        markdown_content = """Introduction paragraph with multiple sentences. It explains the setting and introduces the main character who is going on an adventure.

Character dialogue paragraph where someone speaks important information that moves the plot forward significantly.

Action paragraph describing the exciting sequence of events that keeps readers engaged with the story."""

        processor = MarkdownProcessor()

        # Act: Process complex paragraph structure
        result = processor.process_content(markdown_content)

        # Assert: Should detect 3 paragraph boundaries correctly
        assert len(result) == 3, f"Expected 3 paragraphs boundaries detected, got {len(result)}"

        # Each paragraph should contain its thematic content
        paragraph_texts = [str(p) for p in result]
        assert any("Introduction paragraph" in text for text in paragraph_texts)
        assert any("Character dialogue" in text for text in paragraph_texts)
        assert any("Action paragraph" in text for text in paragraph_texts)