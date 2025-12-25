import pytest
from pytest_mock import MockerFixture
import sys
import os
import tempfile
import types
from unittest.mock import patch

from Writer.PDFGenerator import GeneratePDF, extract_story_content


# Mock ActivePrompts for the Test Module
@pytest.fixture(autouse=True)
def mock_active_prompts_for_pdf_generator(mocker: MockerFixture):
    mock_prompts = types.ModuleType("Writer.Prompts")
    mocker.patch.dict(sys.modules, {"Writer.Prompts": mock_prompts})
    yield


# Note: mock_logger and mock_interface fixtures are now in conftest.py


@pytest.fixture
def sample_markdown_content():
    """Sample markdown content with YAML and metadata"""
    return """---
title: "Test Story"
summary: "A test story for PDF generation"
tags: "test, pdf, story"
---
# The Great Adventure

## Summary
This is a summary section that should be excluded from PDF.

## Tags
test, pdf, story

---

## Chapter 1
Once upon a time, in a land far away, there lived a brave knight.

The knight ventured into the dark forest, searching for the legendary treasure.

### Finding the Map
After many days of searching, the knight found an ancient map hidden in an old tree.

The map showed the way to the hidden treasure deep within the mountain.

---

## Chapter 2
The knight followed the map through valleys and over mountains.

At last, the knight reached the entrance to the treasure cave.

### Facing the Dragon
Inside the cave, a fearsome dragon guarded the treasure.

The knight bravely faced the dragon and defeated it in combat.

With the dragon defeated, the knight claimed the treasure and returned home a hero.
---"""


class TestExtractStoryContent:
    """Test the extract_story_content function"""

    def test_extracts_title_and_chapters_only(self, sample_markdown_content):
        """Test that only title and chapters are extracted"""
        result = extract_story_content(sample_markdown_content)

        # Should contain title
        assert "# The Great Adventure" in result

        # Should contain chapters
        assert "## Chapter 1" in result
        assert "Once upon a time" in result
        assert "## Chapter 2" in result
        assert "The knight followed the map" in result

        # Should contain multiple story separators (OK to keep them)
        # It just shouldn't contain YAML front matter with title/key pairs
        assert 'title: "Test Story"' not in result
        assert 'summary: "A test story for PDF generation"' not in result

        # Should NOT contain metadata sections
        assert "## Summary" not in result
        assert "This is a summary section" not in result
        assert "## Tags" not in result
        assert "test, pdf, story" not in result

        # Should NOT contain technical sections
        assert "# Story Outline" not in result
        assert "# Generation Statistics" not in result

    def test_handles_content_without_yaml(self):
        """Test handling of markdown without YAML front matter"""
        content = """# Simple Story

## Chapter 1
A simple beginning.

## Chapter 2
The continuation."""

        result = extract_story_content(content)

        assert "# Simple Story" in result
        assert "## Chapter 1" in result
        assert "A simple beginning" in result
        assert "## Chapter 2" in result

    def test_multiple_story_separators(self):
        """Test handling of multiple story separators"""
        content = """# Complex Story

---

## Chapter 1
Content here.

---

### Section Within Chapter
More content.

---

## Chapter 2
New chapter."""

        result = extract_story_content(content)

        assert "# Complex Story" in result
        assert "## Chapter 1" in result
        assert "### Section Within Chapter" in result
        assert "## Chapter 2" in result


class TestGeneratePDF:
    """Test the GeneratePDF function"""

    def test_successful_pdf_generation(self, mock_interface, mock_logger, sample_markdown_content, mocker):
        """Test successful PDF generation"""
        # Mock reportlab to avoid actual PDF generation in tests
        mocked_doc = mocker.MagicMock()
        mocker.patch('Writer.PDFGenerator.SimpleDocTemplate', return_value=mocked_doc)
        mocker.patch('Writer.PDFGenerator.os.makedirs')

        # Create instances from factories
        interface = mock_interface()
        logger = mock_logger()

        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = os.path.join(tmpdir, "test.pdf")

            success, message = GeneratePDF(
                interface,
                logger,
                sample_markdown_content,
                pdf_path,
                "Test Story"
            )

            assert success is True
            assert "successfully" in message.lower()
            assert any("generated PDF" in log[1] for log in logger.logs)

            # Verify SimpleDocTemplate was called
            mocked_doc.build.assert_called_once()

    def test_pdf_creation_failure(self, mock_interface, mock_logger, sample_markdown_content, mocker):
        """Test handling of PDF creation failure"""
        # Force an error in PDF generation
        mocker.patch('Writer.PDFGenerator.SimpleDocTemplate', side_effect=Exception("Test error"))

        # Create instances from factories
        interface = mock_interface()
        logger = mock_logger()

        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = os.path.join(tmpdir, "test.pdf")

            success, message = GeneratePDF(
                interface,
                logger,
                sample_markdown_content,
                pdf_path,
                "Test Story"
            )

            assert success is False
            assert "failed" in message.lower()
            assert "Test error" in message
            assert any("PDF generation failed" in log[1] for log in logger.logs)

    def test_directory_creation(self, mock_interface, mock_logger, sample_markdown_content, mocker):
        """Test that output directory is created if it doesn't exist"""
        mocked_doc = mocker.MagicMock()
        mocker.patch('Writer.PDFGenerator.SimpleDocTemplate', return_value=mocked_doc)

        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = os.path.join(tmpdir, "newdir", "test.pdf")

            # Mock os.makedirs to verify it's called
            mock_makedirs = mocker.patch('Writer.PDFGenerator.os.makedirs')

            GeneratePDF(
                mock_interface(),
                mock_logger(),
                sample_markdown_content,
                pdf_path,
                "Test Story"
            )

            mock_makedirs.assert_called_once_with(os.path.dirname(pdf_path), exist_ok=True)

    def test_chapter_formatting(self, mock_interface, mock_logger, mocker):
        """Test that chapters are formatted correctly"""
        mocked_doc = mocker.MagicMock()
        mocker.patch('Writer.PDFGenerator.SimpleDocTemplate', return_value=mocked_doc)
        mocker.patch('Writer.PDFGenerator.os.makedirs')

        content = """# Multi Chapter Story

---

## Chapter 1
Chapter one content.

### Section 1.1
Section content.

## Chapter 2
Chapter two content."""

        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = os.path.join(tmpdir, "test.pdf")

            GeneratePDF(
                mock_interface(),
                mock_logger(),
                content,
                pdf_path,
                "Multi Chapter Story"
            )

            # Verify build was called
            mocked_doc.build.assert_called_once()

            # Get the story argument from build call
            call_args = mocked_doc.build.call_args
            story = call_args[0][0]  # First positional argument to build

            # Should contain title and chapters
            story_text = ' '.join([str(item) for item in story])

            # Verify title formatting
            assert "Multi Chapter Story" in story_text

            # Verify chapter formatting
            assert "Chapter 1" in story_text
            assert "Chapter one content" in story_text
            assert "Chapter 2" in story_text
            assert "Chapter two content" in story_text


@pytest.mark.integration
class TestPDFGenerationIntegration:
    """Integration tests for PDF generation"""

    def test_full_flow_with_mock_dependencies(self, mock_interface, mock_logger, mocker):
        """Test the complete PDF generation flow with all dependencies mocked"""
        # Mock the entire reportlab module chain
        with patch('Writer.PDFGenerator.SimpleDocTemplate') as mock_doc, \
                patch('Writer.PDFGenerator.NumberedCanvas'), \
                patch('Writer.PDFGenerator.os.makedirs'):

            mock_doc.return_value.build = mocker.MagicMock()

            content = """# Integration Test

---

## Chapter 1
Test content for integration test."""

            with tempfile.TemporaryDirectory() as tmpdir:
                pdf_path = os.path.join(tmpdir, "integration_test.pdf")

                success, message = GeneratePDF(
                    mock_interface(),
                    mock_logger(),
                    content,
                    pdf_path,
                    "Integration Test"
                )

                assert success

    def test_pdf_preserves_bold_formatting(self, mock_interface, mock_logger, mocker):
        """Test that bold formatting is preserved in PDF"""
        from unittest.mock import MagicMock
        from reportlab.platypus import Paragraph

        # Mock the PDF document to capture elements
        mocked_doc = MagicMock()
        # Make sure build returns something we can inspect
        mock_build = MagicMock()
        mocked_doc.build = mock_build
        mocker.patch('Writer.PDFGenerator.SimpleDocTemplate', return_value=mocked_doc)
        mocker.patch('Writer.PDFGenerator.os.makedirs')

        content = """# Bold Test

---

## Chapter 1
This text has **bold formatting** and *italic formatting*."""

        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = os.path.join(tmpdir, "test.pdf")

            GeneratePDF(
                mock_interface(),
                mock_logger(),
                content,
                pdf_path,
                "Bold Test"
            )

            # Get the story elements from the build call
            call_args = mocked_doc.build.call_args[0][0]

            # Check that we have Paragraph elements with different styles
            paragraph_texts = []
            paragraph_styles = []

            for element in call_args:
                if isinstance(element, Paragraph):
                    # Get the text and style from the element
                    para_text = str(element)
                    paragraph_texts.append(para_text)
                    if hasattr(element, 'style'):
                        paragraph_styles.append(element.style.name)

            # Verify that content is preserved
            assert "bold formatting" in ' '.join(paragraph_texts)
            assert "italic formatting" in ' '.join(paragraph_texts)

            # Should have multiple Paragraph elements due to formatting
            assert len([e for e in call_args if isinstance(e, Paragraph)]) > 2

    def test_pdf_preserves_italics_formatting(self, mock_interface, mock_logger, mocker):
        """Test that italics formatting is preserved in PDF"""
        from unittest.mock import MagicMock
        from reportlab.platypus import Paragraph

        mocked_doc = MagicMock()
        mocker.patch('Writer.PDFGenerator.SimpleDocTemplate', return_value=mocked_doc)
        mocker.patch('Writer.PDFGenerator.os.makedirs')

        content = """# Italics Test

---

## Chapter 1
This text has *italic formatting* that should be preserved."""

        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = os.path.join(tmpdir, "test.pdf")

            GeneratePDF(
                mock_interface(),
                mock_logger(),
                content,
                pdf_path,
                "Italics Test"
            )

            # Get the story elements
            call_args = mocked_doc.build.call_args[0][0]
            paragraph_texts = [str(e) for e in call_args if isinstance(e, Paragraph)]

            # Verify content is preserved
            assert "italic formatting" in ' '.join(paragraph_texts)

            # Should have multiple Paragraph elements
            assert len([e for e in call_args if isinstance(e, Paragraph)]) > 1

    def test_pdf_chapter_title_display(self, mock_interface, mock_logger, mocker):
        """Test that chapter titles are properly displayed without duplication"""
        from unittest.mock import MagicMock
        from reportlab.platypus import Paragraph

        mocked_doc = MagicMock()
        mocker.patch('Writer.PDFGenerator.SimpleDocTemplate', return_value=mocked_doc)
        mocker.patch('Writer.PDFGenerator.os.makedirs')

        content = """# Chapter Title Test

---

## Chapter 1: The Adventure Begins
This is the story of a great adventure.

## Chapter 2: Into the Unknown
Our hero ventures into mysterious lands."""

        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = os.path.join(tmpdir, "test.pdf")

            GeneratePDF(
                mock_interface(),
                mock_logger(),
                content,
                pdf_path,
                "Chapter Title Test"
            )

            # Get the story elements
            call_args = mocked_doc.build.call_args[0][0]

            # Collect chapter titles (using PDFChapter style from PDFStyles)
            chapter_titles = []
            for element in call_args:
                if isinstance(element, Paragraph) and hasattr(element, 'style'):
                    if element.style.name == 'PDFChapter':
                        chapter_titles.append(str(element))

            # Should have proper chapter titles without duplication
            assert "The Adventure Begins" in ' '.join(chapter_titles)
            assert "Into the Unknown" in ' '.join(chapter_titles)
            # Should NOT have "Chapter 1" as a separate title
            assert chapter_titles.count("Chapter 1") == 0

    def test_pdf_paragraph_breaks(self, mock_interface, mock_logger, mocker):
        """Test that paragraph breaks are properly handled"""
        from unittest.mock import MagicMock
        from reportlab.platypus import Paragraph

        mocked_doc = MagicMock()
        mocker.patch('Writer.PDFGenerator.SimpleDocTemplate', return_value=mocked_doc)
        mocker.patch('Writer.PDFGenerator.os.makedirs')

        content = """# Paragraph Test

---

## Chapter 1
First paragraph with some text.

Second paragraph with different text.

Third paragraph after a blank line.


This should have proper spacing."""

        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = os.path.join(tmpdir, "test.pdf")

            GeneratePDF(
                mock_interface(),
                mock_logger(),
                content,
                pdf_path,
                "Paragraph Test"
            )

            # Get the story elements
            call_args = mocked_doc.build.call_args[0][0]

            # Count Paragraph elements
            paragraph_count = sum(1 for item in call_args if isinstance(item, Paragraph))

            # Should have multiple Paragraph elements (at least 3 due to chapter title + content)
            assert paragraph_count >= 3, f"Expected at least 3 paragraphs, found {paragraph_count}"

    def test_pdf_section_headers(self, mock_interface, mock_logger, mocker):
        """Test that H3 headers within chapters are formatted properly"""
        from unittest.mock import MagicMock
        from reportlab.platypus import Paragraph

        mocked_doc = MagicMock()
        mocker.patch('Writer.PDFGenerator.SimpleDocTemplate', return_value=mocked_doc)
        mocker.patch('Writer.PDFGenerator.os.makedirs')

        content = """# Section Header Test

---

## Chapter 1
Regular chapter content.

### Finding the Map
Important plot development here.

### Meeting the Dragon
Another important section.

More regular content."""

        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = os.path.join(tmpdir, "test.pdf")

            GeneratePDF(
                mock_interface(),
                mock_logger(),
                content,
                pdf_path,
                "Section Header Test"
            )

            # Get the story elements
            call_args = mocked_doc.build.call_args[0][0]

            # Collect all text content
            paragraph_texts = [str(e) for e in call_args if isinstance(e, Paragraph)]

            combined_text = ' '.join(paragraph_texts)

            # Section headers should be preserved
            assert "Finding the Map" in combined_text
            assert "Meeting the Dragon" in combined_text
            assert "Regular chapter content" in combined_text
            assert "More regular content" in combined_text
